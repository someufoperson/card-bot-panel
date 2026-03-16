import logging
import os
import shutil
import subprocess
import threading
import time

logger = logging.getLogger(__name__)

_POLL_INTERVAL = 30        # секунд
_BASE_PORT = 27100         # базовый порт для scrcpy-серверов
_SCRCPY_VERSION = "2.7"   # версия протокола scrcpy-server
_SERVER_REMOTE_PATH = "/data/local/tmp/scrcpy-server"


def _find_scrcpy_server() -> str | None:
    """Ищет scrcpy-server рядом с бинарником scrcpy."""
    scrcpy_bin = shutil.which("scrcpy")
    if not scrcpy_bin:
        return None
    scrcpy_dir = os.path.dirname(os.path.realpath(scrcpy_bin))
    for name in ("scrcpy-server", "scrcpy-server.jar"):
        path = os.path.join(scrcpy_dir, name)
        if os.path.exists(path):
            return path
    return None


def _run(cmd: list[str], timeout: int = 5) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


class DeviceManager:
    """
    Управляет scrcpy-процессами для каждого подключённого ADB-устройства.
    Запускает фоновый поток, который каждые 30 сек синхронизирует состояние.
    """

    def __init__(self):
        self._devices: dict[str, dict] = {}  # device_id → info dict
        self._lock = threading.Lock()
        self._next_port = _BASE_PORT
        self._server_jar = _find_scrcpy_server()
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="DevicePoller")

    def start(self) -> None:
        if self._server_jar:
            logger.info("scrcpy-server найден: %s", self._server_jar)
        else:
            logger.warning("scrcpy-server не найден — устройства не будут запущены автоматически")
        self._sync_devices()
        self._thread.start()
        logger.info("DeviceManager запущен (интервал %ds)", _POLL_INTERVAL)

    # ── публичный API ────────────────────────────────────────────────────────

    def get_all(self) -> list[dict]:
        """Список всех известных устройств для /api/devices."""
        with self._lock:
            return [
                {
                    "device_id": device_id,
                    "model": info["model"],
                    "adb_status": info["adb_status"],
                }
                for device_id, info in self._devices.items()
            ]

    def get_device(self, device_id: str) -> dict | None:
        with self._lock:
            return self._devices.get(device_id)

    def get_port(self, device_id: str) -> int | None:
        with self._lock:
            info = self._devices.get(device_id)
            return info["port"] if info else None

    # ── внутренняя логика ────────────────────────────────────────────────────

    def _poll_loop(self) -> None:
        while True:
            time.sleep(_POLL_INTERVAL)
            try:
                self._sync_devices()
            except Exception as exc:
                logger.error("Ошибка при синхронизации устройств: %s", exc)

    def _get_adb_devices(self) -> list[str]:
        try:
            result = _run(["adb", "devices"])
            devices = []
            for line in result.stdout.splitlines()[1:]:
                line = line.strip()
                if line.endswith("\tdevice"):
                    devices.append(line.split("\t")[0])
            return devices
        except Exception as exc:
            logger.error("adb devices failed: %s", exc)
            return []

    def _get_model(self, device_id: str) -> str:
        try:
            result = _run(["adb", "-s", device_id, "shell", "getprop", "ro.product.model"])
            return result.stdout.strip() or "Unknown"
        except Exception:
            return "Unknown"

    def _alloc_port(self) -> int:
        port = self._next_port
        self._next_port += 1
        return port

    def _start_scrcpy_server(self, device_id: str) -> tuple[subprocess.Popen, int]:
        """Запускает scrcpy-server на устройстве и настраивает ADB port forward."""
        if not self._server_jar:
            raise RuntimeError("scrcpy-server не найден")

        port = self._alloc_port()

        # 1. Загружаем сервер на устройство
        subprocess.run(
            ["adb", "-s", device_id, "push", self._server_jar, _SERVER_REMOTE_PATH],
            check=True, capture_output=True, timeout=15,
        )

        # 2. Запускаем сервер на устройстве
        server_cmd = [
            "adb", "-s", device_id, "shell",
            f"CLASSPATH={_SERVER_REMOTE_PATH}",
            "app_process", "/",
            "com.genymobile.scrcpy.Server",
            _SCRCPY_VERSION,
            "tunnel_forward=true",
            "control=true",
            "video=true",
            "audio=false",
            "cleanup=false",
            "max_size=0",
            "video_bit_rate=8000000",
            "max_fps=60",
        ]
        process = subprocess.Popen(
            server_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # 3. Небольшая пауза чтобы сервер успел запуститься
        time.sleep(1.0)

        # 4. Пробрасываем порт
        subprocess.run(
            ["adb", "-s", device_id, "forward", f"tcp:{port}", "localabstract:scrcpy"],
            check=True, capture_output=True, timeout=5,
        )

        logger.info("scrcpy запущен для %s на порту %d", device_id, port)
        return process, port

    def _stop_device(self, device_id: str, info: dict) -> None:
        """Останавливает scrcpy-процесс и убирает ADB forward."""
        try:
            proc = info.get("process")
            if proc and proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=5)
        except Exception as exc:
            logger.warning("Не удалось остановить процесс для %s: %s", device_id, exc)
        try:
            _run(["adb", "-s", device_id, "forward", "--remove", f"tcp:{info['port']}"])
        except Exception:
            pass

    def _sync_devices(self) -> None:
        current_ids = set(self._get_adb_devices())

        with self._lock:
            known_ids = set(self._devices.keys())

            # Новые устройства
            for device_id in current_ids - known_ids:
                try:
                    model = self._get_model(device_id)
                    process, port = self._start_scrcpy_server(device_id)
                    self._devices[device_id] = {
                        "process": process,
                        "port": port,
                        "model": model,
                        "adb_status": "online",
                    }
                    logger.info("Устройство подключено: %s (%s)", device_id, model)
                except Exception as exc:
                    logger.error("Не удалось запустить scrcpy для %s: %s", device_id, exc)

            # Отключённые устройства
            for device_id in known_ids - current_ids:
                info = self._devices.pop(device_id)
                self._stop_device(device_id, info)
                logger.info("Устройство отключено: %s", device_id)

            # Проверяем зависшие процессы у онлайн-устройств
            for device_id, info in list(self._devices.items()):
                proc = info.get("process")
                if proc and proc.poll() is not None:
                    logger.warning("Процесс scrcpy для %s упал, перезапускаем", device_id)
                    try:
                        process, port = self._start_scrcpy_server(device_id)
                        info["process"] = process
                        info["port"] = port
                    except Exception as exc:
                        logger.error("Перезапуск не удался для %s: %s", device_id, exc)
