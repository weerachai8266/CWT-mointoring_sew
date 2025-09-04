import os
import threading
import queue
import select
from evdev import InputDevice, ecodes, list_devices
import time

class Scanner:
    def __init__(self, device_path=None, device_index=None):
        if device_path:
            self.device = InputDevice(device_path)
        else:
            self.device = self.find_scanner(device_index)

        if not self.device:
            print("❌ ไม่พบอุปกรณ์ที่ใช้งานได้")
            os._exit(1)

        try:
            self.device.read()  # ล้าง events เก่า
            self.device.grab()  # จอง device ไว้ใช้งาน
            # ใช้ blocking mode เพื่อให้อ่านข้อมูลได้ครบถ้วน
        except Exception as e:
            print(f"❌ ไม่สามารถใช้งานอุปกรณ์ได้: {e}")
            print("ลองรันโปรแกรมด้วย sudo")
            os._exit(1)

        self.buffer = ''                        # เก็บข้อมูลที่อ่านได้
        self.last_key_time = time.monotonic()   # เวลาที่อ่านคีย์ล่าสุด
        self.barcode_queue = queue.Queue()      # คิวสำหรับเก็บบาร์โค้ดที่อ่านได้
        self.event_queue = queue.Queue(maxsize=500) # คิวสำหรับเก็บ events ระหว่าง threads
        self._stop_event = threading.Event()    # อีเวนต์สำหรับหยุดการทำงานของ thread
        
        # สร้าง thread สำหรับอ่านข้อมูลจากอุปกรณ์ (producer)
        self.reader_thread = threading.Thread(target=self._event_reader, daemon=True)
        
        # สร้าง thread สำหรับประมวลผลข้อมูล (consumer)
        self.processor_thread = threading.Thread(target=self._event_processor, daemon=True)
        
        # เริ่ม threads
        self.reader_thread.start()
        self.processor_thread.start()

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
                return selected_device
            else:
                print(f"❌ ไม่พบอุปกรณ์ index={device_index}")
                return None

        # ถ้าไม่ได้ระบุ index เลือกอันแรก
        return available_devices[0]

    def _event_reader(self):
        """Thread สำหรับอ่าน events จากอุปกรณ์ (producer)"""
        while not self._stop_event.is_set():
            # รอ event ใหม่
            r, _, _ = select.select([self.device.fd], [], [], 0.2)
            if not r:
                continue  # ไม่มี event ใหม่, วนลูปต่อ

            try:
                # อ่าน events ทั้งหมดที่มีในขณะนั้น และส่งเข้า queue
                events = list(self.device.read())
                if events:
                    for event in events:
                        try:
                            # ส่ง event เข้า queue ระหว่าง threads (ไม่รอหากเต็ม)
                            self.event_queue.put(event, block=False)
                        except queue.Full:
                            # ถ้า queue เต็ม ให้ลองเคลียร์ queue แล้วเริ่มใหม่
                            try:
                                while not self.event_queue.empty():
                                    self.event_queue.get_nowait()
                            except:
                                pass
            except OSError as e:
                if e.errno == 19:  # No such device
                    # อุปกรณ์ถูกถอด
                    break
            except:
                # ไม่สนใจข้อผิดพลาดอื่นๆ
                pass
    
    def _event_processor(self):
        """Thread สำหรับประมวลผล events (consumer)"""
        shift = False
        last_key_time = time.monotonic()
        scanning_active = False
        inter_char_timeout = 2.0
        
        while not self._stop_event.is_set():
            now = time.monotonic()
            
            # ตรวจสอบ timeout เมื่อมีข้อมูลในบัฟเฟอร์และไม่มีการสแกนเป็นเวลานาน
            if self.buffer and (now - last_key_time > inter_char_timeout):
                if len(self.buffer) > 3:  # ต้องมีความยาวอย่างน้อย 4 ตัวอักษร
                    self.barcode_queue.put(self.buffer)
                self.buffer = ''
                scanning_active = False
            
            # รอ event จาก queue
            try:
                event = self.event_queue.get(timeout=0.2)
                scanning_active = True
                last_key_time = time.monotonic()
                
                # ประมวลผล event
                if event.type != ecodes.EV_KEY:
                    continue
                
                # จัดการ Shift keys
                if event.code in (ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT):
                    shift = event.value in (1, 2)
                    continue
                
                # สนใจเฉพาะการกดปุ่ม (key press)
                if event.value != 1:  # เฉพาะการกดปุ่มใหม่ ไม่รวมการกดค้าง
                    continue
                
                # จัดการ Enter key
                if event.code == ecodes.KEY_ENTER:
                    if self.buffer:
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
                except KeyError:
                    # ไม่สนใจปุ่มที่ไม่รู้จัก
                    continue
                except Exception:
                    # ไม่สนใจข้อผิดพลาด
                    continue
                    
            except queue.Empty:
                # ไม่มี event ใน queue
                continue
            except Exception:
                # เมื่อเกิดข้อผิดพลาดร้ายแรง
                scanning_active = False
    
    # คงเมธอดเดิมไว้เพื่อความเข้ากันได้กับโค้ดเก่า
    def _barcode_loop(self):
        """Legacy method, not used with dual-thread approach"""
        pass

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
                return key.upper()

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
        except Exception:
            return None


    def is_connected(self):
        # ตรวจสอบว่า device path ของ scanner นี้ยังมีอยู่ในระบบหรือไม่
        try:
            return os.path.exists(self.device.path)
        except Exception:
            return False

    def cleanup(self):
        self._stop_event.set()                          # ตั้งค่าอีเวนต์เพื่อหยุด threads
        
        # รอให้ threads จบการทำงาน
        if hasattr(self, 'reader_thread') and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1.0)
            
        if hasattr(self, 'processor_thread') and self.processor_thread.is_alive():
            self.processor_thread.join(timeout=1.0)
        
        # สำหรับเข้ากันได้กับโค้ดเก่า
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        
        # ปลดการจอง device
        if hasattr(self, 'device') and self.device:
            try:
                self.device.ungrab()
            except Exception:
                pass
