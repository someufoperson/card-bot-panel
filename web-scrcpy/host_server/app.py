from gevent import monkey

monkey.patch_all()
from flask import Flask, render_template, request, abort
from flask_socketio import SocketIO, emit, join_room, leave_room
from scrcpy import Scrcpy
import os
import queue
import random
import shutil
import socket
import subprocess
import threading
import requests
from loguru import logger
import config_log
from utils import send_message_to_telegram
from typing import Dict, Set

active_connections: Dict[str, dict] = {}  # serial -> {scrcpy, queue, task}
sid_to_device: Dict[str, str] = {}        # sid -> serial
room_clients: Dict[str, Set[str]] = {}    # serial -> set(sid)

API = "http://localhost:8001/api/v1"


def _move_video_and_log(serial: str, src: str) -> None:
    """
    Background task: move recorded video to the configured folder (if set),
    verify the copy, delete the original, then push a log entry with the
    absolute final path.
    """
    abs_src = os.path.abspath(src)
    final_path = abs_src  # default: stay in place

    try:
        # Fetch video_folder setting from backend
        dest_dir = None
        try:
            res = requests.get(f"{API}/settings/video_folder", timeout=5)
            if res.status_code == 200:
                dest_dir = (res.json().get("value") or "").strip() or None
        except Exception:
            pass

        if dest_dir and os.path.isfile(abs_src):
            os.makedirs(dest_dir, exist_ok=True)
            abs_dest = os.path.join(dest_dir, os.path.basename(abs_src))

            shutil.copy2(abs_src, abs_dest)

            # Verify by size before removing original
            if os.path.getsize(abs_dest) == os.path.getsize(abs_src):
                os.remove(abs_src)
                final_path = abs_dest
                logger.info(f"Video for {serial} moved to {final_path}")
            else:
                # Bad copy — remove it, keep original
                try:
                    os.remove(abs_dest)
                except Exception:
                    pass
                logger.warning(f"Video move failed (size mismatch) for {serial}, keeping {abs_src}")

    except Exception as e:
        logger.error(f"Error moving video for {serial}: {e}")

    # Always log the final location
    try:
        requests.post(
            f"{API}/devices/{serial}/logs",
            json={"event_type": "video_saved", "detail": final_path},
            timeout=5,
        )
    except Exception:
        pass


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(
    app,
    async_mode='gevent',
    cors_allowed_origins="*",
    binary=True,
)


def find_free_port() -> int:
    while True:
        port = random.randint(30000, 40000)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port


def is_device_available(serial: str) -> bool:
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines()[1:]:
            if line.strip() and serial in line and "device" in line:
                return True
        return False
    except Exception as e:
        logger.error(f"ADB devices check failed: {e}")
        return False


def video_send_task(serial: str):
    conn = active_connections.get(serial)
    if not conn:
        return
    q = conn['queue']
    logger.info(f"Video send task started for {serial}")
    while serial in active_connections:
        try:
            data = q.get(timeout=0.001)
            socketio.emit('video_data', data, room=serial)
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Error sending video for {serial}: {e}")
    logger.info(f"Video send task stopped for {serial}")


@app.route('/favicon.ico')
def favicon():
    return '', 204, {'Content-Type': 'image/x-icon'}



@app.route('/notifications', methods=['POST'])
def receive_notification():
    data = request.get_json(silent=True) or request.form.to_dict() or request.data
    logger.info(f"[NOTIFICATION] headers={dict(request.headers)}")
    logger.info(f"[NOTIFICATION] body={data}")
    print(f"[NOTIFICATION] headers={dict(request.headers)}")
    print(f"[NOTIFICATION] body={data}")
    return {'status': 'received'}, 200


def _get_inactivity_ms() -> int:
    """Fetch inactivity_timeout (minutes) from backend and convert to ms. Default 3 min."""
    try:
        res = requests.get(f"{API}/settings/inactivity_timeout", timeout=3)
        if res.status_code == 200:
            minutes = int(res.json().get("value", 3))
            return max(1, minutes) * 60 * 1000
    except Exception:
        pass
    return 180000  # fallback: 3 minutes


@app.route('/<serial_number>')
def device_page(serial_number):
    if serial_number in room_clients and room_clients[serial_number]:
        return render_template('403.html'), 403

    try:
        res = requests.get(f"{API}/devices/device/status/{serial_number}", timeout=5)
        if res.status_code == 404:
            return render_template('404.html'), 404
        res.raise_for_status()
        device_data = res.json()
        if device_data.get("session_status") == "ACTIVE" and device_data.get("status_device") == "ONLINE":
            return render_template(
                'index.html',
                title=device_data.get("label", serial_number),
                inactivity_limit_ms=_get_inactivity_ms(),
            )
        else:
            return {"status": "Device not available or offline"}
    except Exception as e:
        logger.error(f"Failed to fetch device status for {serial_number}: {e}")
        abort(500, description="Backend service unavailable")


@socketio.on('connect')
def handle_connect(auth=None):
    serial = request.args.get('device')
    if not serial:
        logger.warning("Connect without device parameter")
        return False

    if not is_device_available(serial):
        logger.warning(f"Device {serial} not available via ADB")
        return False

    if serial in room_clients and room_clients[serial]:
        logger.warning(f"Device {serial} already has active client(s). Rejecting.")
        return False

    sid = request.sid
    sid_to_device[sid] = serial
    room_clients.setdefault(serial, set()).add(sid)

    if serial in active_connections:
        join_room(serial, sid=sid)
        return

    local_port = find_free_port()
    sc = Scrcpy(serial_number=serial, local_port=local_port)
    q = queue.Queue()

    def video_callback(data):
        q.put(data)

    sc.scrcpy_start(video_callback, 1024000)

    try:
        requests.patch(f"{API}/devices/update-status/connect/{serial}/connect", timeout=5)
    except Exception:
        pass

    try:
        label_res = requests.get(f"{API}/devices/device/{serial}", timeout=5)
        label = label_res.json().get("label", serial)
    except Exception:
        label = serial

    text_log = f"Сессия с девайсом {label} началась"
    logger.bind(connection=True).info(text_log)
    try:
        send_message_to_telegram(f"🟢 {text_log} 🟢")
    except Exception:
        pass

    active_connections[serial] = {
        'scrcpy': sc,
        'queue': q,
        'task': socketio.start_background_task(video_send_task, serial),
    }

    join_room(serial, sid=sid)


@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    serial = sid_to_device.pop(sid, None)
    if not serial:
        return

    leave_room(serial, sid=sid)
    clients = room_clients.get(serial, set())
    clients.discard(sid)

    try:
        requests.patch(f"{API}/devices/update-status/connect/{serial}/disconnect", timeout=5)
        label_res = requests.get(f"{API}/devices/device/{serial}", timeout=5)
        label = label_res.json().get("label", serial)
    except Exception:
        label = serial

    text_log = f"Сессия с девайсом {label} закончилась"
    logger.bind(connection=True).info(text_log)
    try:
        send_message_to_telegram(f"🔴 {text_log} 🔴")
    except Exception:
        pass

    if not clients:
        conn = active_connections.pop(serial, None)
        if conn:
            logger.info(f"Stopping scrcpy for {serial} (no clients)")
            sc = conn['scrcpy']
            sc.scrcpy_stop()
            if sc.recorder:
                threading.Thread(
                    target=_move_video_and_log,
                    args=(serial, sc.recorder.filename),
                    daemon=True,
                ).start()
        room_clients.pop(serial, None)
    else:
        logger.debug(f"Client {sid} left, still {len(clients)} clients for {serial}")


@socketio.on('control_data')
def handle_control_data(data):
    sid = request.sid
    serial = sid_to_device.get(sid)
    if not serial:
        return
    conn = active_connections.get(serial)
    if conn:
        conn['scrcpy'].scrcpy_send_control(data)


@socketio.on('inactivity_timeout')
def handle_inactivity_timeout():
    try:
        sid = request.sid
        serial = sid_to_device.pop(sid, None)
        if not serial:
            return

        leave_room(serial, sid=sid)
        clients = room_clients.get(serial, set())
        clients.discard(sid)

        try:
            requests.patch(f"{API}/devices/update-status/connect/{serial}/timeout", timeout=5)
            label_res = requests.get(f"{API}/devices/device/{serial}", timeout=5)
            label = label_res.json().get("label", serial)
        except Exception:
            label = serial

        text_log = f"Сессия с девайсом {label} закончилась из-за бездействия"
        logger.bind(connection=True).info(text_log)
        try:
            send_message_to_telegram(f"🔴 {text_log} 🔴")
        except Exception:
            pass

        if not clients:
            conn = active_connections.pop(serial, None)
            if conn:
                sc = conn['scrcpy']
                sc.scrcpy_stop()
                if sc.recorder:
                    threading.Thread(
                        target=_move_video_and_log,
                        args=(serial, sc.recorder.filename),
                        daemon=True,
                    ).start()
            room_clients.pop(serial, None)
    except Exception:
        logger.warning("Ошибка в handle_inactivity_timeout")


if __name__ == '__main__':
    subprocess.Popen([
        rf"{os.getcwd()}\.venv\Scripts\python.exe",
        rf"{os.getcwd()}\host_server\device_support.py",
    ])
    logger.info("Starting server on port 5000")
    socketio.run(app, host='0.0.0.0', port=5000)
