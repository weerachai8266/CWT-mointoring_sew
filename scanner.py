import os
import threading
import queue
import select
from evdev import InputDevice, ecodes, list_devices
import time

class Scanner:
    def __init__(self, device_path=None, device_index=None):
        print("\nกำลังค้นหาอุปกรณ์...")

        if device_path:
            print(f"[Scanner] Using fixed device path: {device_path}")
            self.device = InputDevice(device_path)
        else:
            self.device = self.find_scanner(device_index)

        if not self.device:
            print("\n❌ ไม่พบอุปกรณ์ที่ใช้งานได้")
            os._exit(1)

        try:
            self.device.read()  # ล้าง events เก่า
            self.device.grab()  # จอง device ไว้ใช้งาน

            import fcntl
            flag = fcntl.fcntl(self.device.fd, fcntl.F_GETFL)                   # อ่าน flags ปัจจุบัน
            fcntl.fcntl(self.device.fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)    # ตั้งค่าเป็น non-blocking mode

            print(f"✅ เริ่มใช้งานอุปกรณ์สำเร็จ")
        except Exception as e:
            print(f"❌ ไม่สามารถใช้งานอุปกรณ์ได้: {e}")
            print("ลองรันโปรแกรมด้วย sudo")
            os._exit(1)

        self.buffer = ''                        # เก็บข้อมูลที่อ่านได้
        self.last_key_time = time.monotonic()   # เวลาที่อ่านคีย์ล่าสุด
        self.barcode_queue = queue.Queue()      # คิวสำหรับเก็บบาร์โค้ดที่อ่านได้
        self._stop_event = threading.Event()    # อีเวนต์สำหรับหยุดการทำงานของ thread
        self.thread = threading.Thread(target=self._barcode_loop, daemon=True)  # สร้าง thread สำหรับอ่านบาร์โค้ด
        self.thread.start()                     # เริ่ม thread ทันที

    def find_scanner(self, device_index=None):
        devices = [InputDevice(path) for path in list_devices()]
        
        skip_keywords = [
            'consumer control', 'system control', 'mouse', 'dell',
            'vc4-hdmi', 'keyboard system', 'keyboard consumer', 'touchpad'
        ]
        scanner_keywords = [
            'scanner', 'barcode', 'newtologic', 'datalogic',
            'honeywell', 'zebra', 'symbol'
        ]

        available_devices = []
        for dev in devices:
            name = dev.name.lower()
            if any(keyword in name for keyword in skip_keywords):
                continue
            if any(keyword in name for keyword in scanner_keywords):
                available_devices.append(dev)
                continue
            if 'keyboard' in name and not any(skip in name for skip in skip_keywords):
                available_devices.append(dev)

        if not available_devices:
            print("❌ ไม่พบ Scanner หรือ อุปกรณ์ที่ใช้งานได้")
            return None

        if device_index is not None:
            if 0 <= device_index < len(available_devices):
                selected_device = available_devices[device_index]
                print(f"✅ เลือกใช้: {selected_device.path} ({selected_device.name})")
                return selected_device
            else:
                print(f"❌ ไม่พบอุปกรณ์ index={device_index}")
                return None

        # ถ้าไม่ได้ระบุ index เลือกอันแรก
        return available_devices[0]

    def _barcode_loop(self):
        shift = False
        last_key_time = time.monotonic()

        # เพิ่ม timeout ให้นานขึ้นสำหรับสแกนเนอร์ไร้สาย
        inter_char_timeout = 3  # เพิ่มจาก 0.5 เป็น 3 วินาที

        # เพิ่มตัวแปรเพื่อตรวจสอบสถานะการสแกน
        scan_start_time = None
        scanning_active = False

        while not self._stop_event.is_set():
            # 1. ตรวจสอบ Timeout ก่อน: ถ้าเวลาผ่านไปนานนับจากคีย์ล่าสุด ให้ส่งข้อมูลใน buffer ออกไป
            now = time.monotonic()

            # ตรวจสอบ timeout เฉพาะเมื่อมีข้อมูลใน buffer และไม่ได้สแกนอยู่
            if self.buffer and (now - last_key_time > inter_char_timeout):
                print(f"[DEBUG] Timeout - sending buffer: '{self.buffer}'")  # Debug line
                self.barcode_queue.put(self.buffer)
                self.buffer = ''
                scanning_active = False

            # 2. รอ event ใหม่ โดยใช้ timeout สั้นๆ เพื่อให้ loop ตอบสนองได้เร็ว
            # ใช้ timeout ยาวขึ้นเพื่อลด CPU usage และให้เวลา scanner ส่งข้อมูล
            r, _, _ = select.select([self.device.fd], [], [], 0.1)  # เพิ่มจาก 0.05 เป็น 0.1
            if not r:
                continue  # ไม่มี event ใหม่, วนกลับไปเช็ค timeout ต่อ

            try:
                events = list(self.device.read())  # อ่านทุก event ที่มี
                if not events:
                    continue

                # มี event เข้ามา แสดงว่ากำลังสแกนอยู่
                scanning_active = True
                last_key_time = now  # อัปเดตเวลาล่าสุด

                # 3. เมื่อมี event เข้ามา ให้อ่านและประมวลผลทั้งหมด
                for event in events:
                    if event.type != ecodes.EV_KEY:
                        continue

                    # จัดการ Shift keys
                    if event.code in (ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT):
                        shift = event.value in (1, 2)
                        continue

                    # สนใจเฉพาะการกดปุ่ม (key press)
                    if event.value not in (1, 2):
                        continue

                    # จัดการ Enter key
                    if event.code == ecodes.KEY_ENTER:
                        if self.buffer:
                            # print(f"[DEBUG] Enter pressed - sending buffer: '{self.buffer}'")  # Debug line
                            self.barcode_queue.put(self.buffer)
                        self.buffer = ''
                        shift = False
                        scanning_active = False
                        continue

                    # แปลงรหัสปุ่มเป็นตัวอักษร
                    try:
                        key = ecodes.KEY[event.code].replace('KEY_', '')
                        char = self.translate_key(key, shift)
                        if char is not None:
                            self.buffer += char
                            # print(f"[DEBUG] Added char: '{char}' - buffer now: '{self.buffer}'")  # Debug line
                    except KeyError:
                        # ไม่สนใจปุ่มที่ไม่รู้จัก
                        continue
            except BlockingIOError:
                # เป็นเรื่องปกติในโหมด non-blocking ไม่ต้องทำอะไร
                pass
            except OSError as e:
                if e.errno == 19:  # No such device
                    print("❌ Scanner disconnected")
                    break
                else:
                    print(f"❌ OS Error: {e}")
            except Exception as e:
                print(f"❌ เกิดข้อผิดพลาดใน scanner loop: {e}")
                # รีเซ็ต buffer เมื่อมีปัญหา
                self.buffer = ''
                scanning_active = False

    def get_barcode(self):
        try:
            return self.barcode_queue.get_nowait()
        except queue.Empty:
            return None

    def translate_key(self, key, shift=False):
        try:
            if key.isdigit():
                shifted_digits = {
                    '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
                    '6': '^', '7': '&', '8': '*', '9': '(', '0': ')'
                }
                return shifted_digits[key] if shift else key

            elif len(key) == 1 and key.isalpha():
                return key.upper() if not shift else key.upper()

            special_chars = {
                'MINUS': '_' if shift else '-',
                'EQUAL': '+' if shift else '=',
                'LEFTBRACE': '{' if shift else '[',
                'RIGHTBRACE': '}' if shift else ']',
                'SEMICOLON': ':' if shift else ';',
                'APOSTROPHE': '"' if shift else "'",
                'GRAVE': '~' if shift else '`',
                'BACKSLASH': '|' if shift else '\\',
                'COMMA': '<' if shift else ',',
                'DOT': '>' if shift else '.',
                'SLASH': '?' if shift else '/',
                'SPACE': ' '
            }

            return special_chars.get(key, None)
        except Exception as e:
            print(f"❌ แปลงคีย์ผิดพลาด: {e}")
            return None


    def is_connected(self):
        # ตรวจสอบว่า device path ของ scanner นี้ยังมีอยู่ในระบบหรือไม่
        try:
            return os.path.exists(self.device.path)
        except Exception:
            return False

    def cleanup(self):
        self._stop_event.set()                          # ตั้งค่าอีเวนต์เพื่อหยุด thread
        
        # รอให้ thread จบการทำงาน
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        # ปลดการจอง device
        if hasattr(self, 'device') and self.device:
            try:
                self.device.ungrab()
            except Exception as e:
                print(f"Warning: Could not ungrab device: {e}")