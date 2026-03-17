import os
from threading import Thread
import subprocess
import socket
import time
from loguru import logger
import queue
import threading
import datetime

class Recorder:
    def __init__(self, filename, serial):
        self.filename = filename
        self.serial = serial
        self.process = None
        self.queue = queue.Queue()
        self.running = False
        self.thread = None
        self.buffer = bytearray()
        self.header_sent = False
        self.packet_count = 0

    def start(self):
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        cmd = [
            'ffmpeg', '-y',
            '-f', 'h264',
            '-i', 'pipe:0',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-r', '25',
            '-vsync', 'cfr',  # или -fps_mode cfr
            self.filename
        ]
        try:
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,  # захватываем stderr для логирования
                universal_newlines=False
            )
            # logger.info(f"FFmpeg запущен для {self.serial}")
        except FileNotFoundError:
            # logger.error("FFmpeg не найден. Запись видео отключена.")
            return
        self.running = True
        self.thread = threading.Thread(target=self._writer, daemon=True)
        self.thread.start()
        # Поток для чтения stderr ffmpeg (для отладки)
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def _read_stderr(self):
        if self.process:
            for line in self.process.stderr:
                ...
                # logger.debug(f"FFmpeg [{self.serial}]: {line.decode().strip()}")

    def _writer(self):
        while self.running:
            try:
                data = self.queue.get(timeout=0.5)
                if data is None:
                    break
                self.process.stdin.write(data)
                self.process.stdin.flush()
                self.packet_count += 1
                if self.packet_count % 100 == 0:
                    ...
                    # logger.debug(f"Записано {self.packet_count} пакетов для {self.serial}")
            except queue.Empty:
                # Если очередь пуста, ffmpeg может подумать, что поток закончился
                # Поэтому периодически шлём keep-alive? Не нужно.
                continue
            except Exception as e:
                # logger.error(f"Ошибка записи для {self.serial}: {e}")
                break

    def write(self, data):
        if not self.running:
            return
        if len(data) < 4:
            # logger.debug(f"Пропущен короткий пакет ({len(data)} байт) для {self.serial}")
            return

        if not self.header_sent:
            self.buffer.extend(data)
            start_code = b'\x00\x00\x00\x01'
            pos = 0
            while pos <= len(self.buffer) - 4:
                if self.buffer[pos:pos + 4] == start_code:
                    nal_type = self.buffer[pos + 4] & 0x1F
                    if nal_type == 7:  # SPS
                        # Отправляем всё, начиная с этого SPS
                        self.queue.put(bytes(self.buffer[pos:]))
                        self.header_sent = True
                        # logger.info(
                        #     f"SPS найден для {self.serial}, отправлено {len(self.buffer) - pos} байт с позиции {pos}")
                        self.buffer = None
                        return
                    pos += 4
                else:
                    pos += 1
            # Если буфер слишком большой, сбрасываем всё (fallback)
            if len(self.buffer) > 1024 * 1024:
                # logger.warning(f"Буфер для {self.serial} достиг 1 МБ без SPS, сбрасываем всё")
                self.queue.put(bytes(self.buffer))
                self.header_sent = True
                self.buffer = None
            return
        else:
            self.queue.put(data)

    def stop(self):
        logger.info(f"Остановка записи для {self.serial}, видео сохранено")
        self.running = False
        if self.thread:
            self.thread.join(timeout=3)
        if self.process:
            try:
                self.process.stdin.close()
            except:
                pass
            # Ждём завершения ffmpeg
            self.process.wait(timeout=5)
            # logger.info(f"FFmpeg для {self.serial} завершён, записано пакетов: {self.packet_count}")

class Scrcpy:
    def __init__(self, serial_number: str, local_port: int):
        self.video_socket = None
        self.audio_socket = None
        self.control_socket = None

        self.android_thread = None
        self.video_thread = None
        self.audio_thread = None
        self.control_thread = None
        self.android_process = None

        self.serial_number = serial_number
        self.local_port = local_port
        self.adb_path = "adb"
        self.server_path = rf"{os.getcwd()}\scrcpy-server"
        self.stop = False

    def push_server_to_device(self):
        device_server_path = "/data/local/tmp/scrcpy-server.jar"
        result = subprocess.run(
            [self.adb_path, "-s", self.serial_number, "push", self.server_path, device_server_path],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            logger.error(f"Error pushing server: {result.stderr}")
            return False
        return True

    def setup_adb_forward(self):
        subprocess.run(
            [self.adb_path, "-s", self.serial_number, "forward", f"tcp:{self.local_port}", "localabstract:scrcpy"],
            check=True
        )

    def remove_adb_forward(self):
        subprocess.run(
            [self.adb_path, "-s", self.serial_number, "forward", "--remove", f"tcp:{self.local_port}"],
            capture_output=True
        )

    def start_server(self):
        device_server_path = "/data/local/tmp/scrcpy-server.jar"
        cmd = [
            self.adb_path, "-s", self.serial_number, "shell",
            f"CLASSPATH={device_server_path} app_process / com.genymobile.scrcpy.Server 3.1 "
            f"tunnel_forward=true log_level=VERBOSE video_bit_rate={self.video_bit_rate}"
        ]
        self.android_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while not self.stop:
            stderr_line = self.android_process.stderr.readline().decode().strip()
            if not stderr_line:
                break
            if stderr_line:
                logger.error(f"Server error: {stderr_line}")
        self.android_process.wait()

    def receive_video_data(self):
        logger.info("Receiving video data (H.264)...")
        self.video_socket.settimeout(1.0)
        try:
            self.video_socket.recv(1)  # dummy byte
        except socket.timeout:
            pass
        while not self.stop:
            try:
                data = self.video_socket.recv(262144)
                if not data:
                    break
                if self.recorder:
                    self.recorder.write(data)
                self.video_callback(data)
            except socket.timeout:
                continue
            except Exception as e:
                if self.stop:
                    break
                logger.error(f"Video socket error: {e}")
                break
        logger.warning("Video data reception stopped")

    def receive_audio_data(self):
        self.audio_socket.settimeout(1.0)  # таймаут 1 секунда
        try:
            self.audio_socket.recv(1)  # dummy byte
        except socket.timeout:
            pass
        except Exception:
            pass
        while not self.stop:
            try:
                data = self.audio_socket.recv(1024)
                if not data:
                    break
                if self.recorder:
                    self.recorder.write(data)
            except socket.timeout:
                continue
            except (socket.error, ConnectionError) as e:
                if self.stop:
                    break
                break

    def handle_control_conn(self):
        if not self.control_socket:
            return
        self.control_socket.settimeout(1.0)
        try:
            self.control_socket.recv(1)
        except socket.timeout:
            pass
        except Exception:
            pass
        while not self.stop:
            try:
                data = self.control_socket.recv(1024)
                if not data:
                    break
            except socket.timeout:
                continue
            except (socket.error, ConnectionError) as e:
                if self.stop:
                    break
                break

    def scrcpy_start(self, video_callback, video_bit_rate, record=True):
        self.video_bit_rate = video_bit_rate
        self.video_callback = video_callback
        self.stop = False
        self.recorder = None

        if not self.push_server_to_device():
            return

        self.setup_adb_forward()
        self.android_thread = Thread(target=self.start_server, daemon=True)
        self.android_thread.start()
        time.sleep(2)

        # video connection
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.video_socket.connect(('localhost', self.local_port))

        # audio connection
        self.audio_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.audio_socket.connect(('localhost', self.local_port))

        # control connection
        self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.control_socket.connect(('localhost', self.local_port))

        if record:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"logs/recordings/{self.serial_number}_{timestamp}.mp4"
            self.recorder = Recorder(filename, self.serial_number)
            self.recorder.start()

        self.video_thread = Thread(target=self.receive_video_data, daemon=True)
        self.audio_thread = Thread(target=self.receive_audio_data, daemon=True)
        self.control_thread = Thread(target=self.handle_control_conn, daemon=True)
        self.video_thread.start()
        self.audio_thread.start()
        self.control_thread.start()

    def scrcpy_stop(self):
        self.stop = True
        # закрываем сокеты для выхода из циклов
        if self.video_socket:
            self.video_socket.shutdown(socket.SHUT_RDWR)
            self.video_socket.close()
        if self.audio_socket:
            self.audio_socket.close()
        if self.control_socket:
            self.control_socket.shutdown(socket.SHUT_RDWR)
            self.control_socket.close()
        if self.recorder:
            self.recorder.stop()

        if self.video_thread:
            self.video_thread.join()
        if self.audio_thread:
            self.audio_thread.join()
        if self.control_thread:
            self.control_thread.join()

        if self.android_process:
            self.android_process.terminate()
        if self.android_thread:
            self.android_thread.join()

        self.remove_adb_forward()

    def scrcpy_send_control(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        self.control_socket.send(data)