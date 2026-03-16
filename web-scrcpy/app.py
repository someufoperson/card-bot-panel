import logging
import os
import socket
import threading

from flask import Flask, jsonify, render_template, request
from flask_sock import Sock

from device_manager import DeviceManager
from session_manager import SessionManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
sock = Sock(app)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

device_manager = DeviceManager()
session_manager = SessionManager(redis_url=REDIS_URL)


# ── HTTP роуты ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    devices = device_manager.get_all()
    return render_template("index.html", devices=devices)


@app.route("/<device_id>")
def device_page(device_id: str):
    device = device_manager.get_device(device_id)
    if not device:
        return render_template(
            "index.html",
            devices=device_manager.get_all(),
            error=f"Устройство {device_id} недоступно",
        ), 404

    existing_session = session_manager.get_session(device_id)
    if existing_session:
        return render_template("busy.html", device_id=device_id, session=existing_session)

    session_id = session_manager.acquire(device_id)
    return render_template(
        "device.html",
        device_id=device_id,
        session_id=session_id,
        model=device["model"],
    )


@app.route("/api/release/<device_id>", methods=["POST"])
def api_release(device_id: str):
    session_manager.release(device_id)
    return jsonify({"status": "released", "device_id": device_id})


@app.route("/api/devices")
def api_devices():
    """Используется FastAPI DeviceService для получения списка устройств."""
    return jsonify(device_manager.get_all())


# ── WebSocket прокси к scrcpy-серверу ───────────────────────────────────────

@sock.route("/ws/<device_id>")
def ws_proxy(ws, device_id: str):
    """
    Двунаправленный прокси: браузер WebSocket ↔ TCP scrcpy-сервер.
    При закрытии WebSocket снимает Redis-блокировку устройства.
    """
    port = device_manager.get_port(device_id)
    if not port:
        logger.warning("ws_proxy: устройство %s не найдено", device_id)
        return

    try:
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.settimeout(5)
        tcp.connect(("127.0.0.1", port))
        tcp.settimeout(None)
    except Exception as exc:
        logger.error("ws_proxy: не удалось подключиться к scrcpy на порту %d: %s", port, exc)
        return

    stop_event = threading.Event()

    def tcp_to_ws() -> None:
        """Читает из TCP и пишет в WebSocket."""
        try:
            while not stop_event.is_set():
                data = tcp.recv(65536)
                if not data:
                    break
                ws.send(data)
        except Exception:
            pass
        finally:
            stop_event.set()

    forwarder = threading.Thread(target=tcp_to_ws, daemon=True)
    forwarder.start()

    try:
        while not stop_event.is_set():
            data = ws.receive(timeout=1)
            if data is None:
                break
            if isinstance(data, str):
                data = data.encode()
            tcp.sendall(data)
    except Exception:
        pass
    finally:
        stop_event.set()
        tcp.close()
        session_manager.release(device_id)
        logger.info("ws_proxy: сессия %s завершена", device_id)


# ── Точка входа ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    device_manager.start()
    port = int(os.environ.get("SCRCPY_HOST_PORT", 5000))
    logger.info("web-scrcpy запущен на 0.0.0.0:%d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
