__version__ = "1.0.0"
__author__ = "Weerachai"
__date__ = "2025-05-10"

'''
โปรแกรมนี้เป็น Dashboard สำหรับแสดงผลการผลิตในสายการผลิต
โดยจะเชื่อมต่อกับฐานข้อมูล MySQL และใช้ Scanner สำหรับสแกนบาร์โค้ด
แสดงข้อมูลต่างๆ เช่น
- เปอร์เซ็นต์ OA
- จำนวนชิ้นงานที่ผลิต
- เป้าหมายการผลิต
- การเปรียบเทียบกับแผนการผลิต
- ประสิทธิภาพการผลิต


โปรแกรมนี้จะทำงานบนระบบปฏิบัติการ Linux
และต้องการสิทธิ์ในการเข้าถึงอุปกรณ์ Scanner
โปรแกรมนี้จะทำงานในโหมด Fullscreen
และสามารถปิดได้ด้วยการกดปุ่ม ESC

v1.0.0
    โปรแกรมนี้ใช้ไลบรารีดังต่อไปนี้:
    - pygame
    - threading
    - pymysql
    - select
    - queue
    - evdev
เลือกตัวสแกนได้ 1 ตัว
'''

import os
import sys
import pygame
import threading
import pymysql
import select
import queue
from datetime import time, timedelta, datetime
from evdev import InputDevice, categorize, ecodes, list_devices

class Scanner:
    def __init__(self):
        print("\nกำลังค้นหาอุปกรณ์...")
        self.device = self.find_scanner()
        if not self.device:
            print("\n❌ ไม่พบอุปกรณ์ที่ใช้งานได้")
            print("โปรดตรวจสอบ:")
            print("1. เสียบ Scanner เรียบร้อยแล้ว")
            print("2. Scanner เปิดทำงานอยู่")
            print("3. ถ้าจำเป็นให้รันด้วย sudo")
            os._exit(1)

        try:
            self.device.read()  # ล้าง events เก่า
            self.device.grab()  # จอง device ไว้ใช้งาน

            import fcntl
            flag = fcntl.fcntl(self.device.fd, fcntl.F_GETFL)
            fcntl.fcntl(self.device.fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)

            print(f"✅ เริ่มใช้งานอุปกรณ์สำเร็จ")
        except Exception as e:
            print(f"❌ ไม่สามารถใช้งานอุปกรณ์ได้: {e}")
            print("ลองรันโปรแกรมด้วย sudo")
            os._exit(1)

        self.buffer = ''
        self.barcode_queue = queue.Queue()
        self._stop_event = threading.Event()
        self.thread = threading.Thread(target=self._barcode_loop, daemon=True)
        self.thread.start()

    def find_scanner(self):
        devices = [InputDevice(path) for path in list_devices()]
        print("\nรายการอุปกรณ์ที่พบทั้งหมด:")
        print("-" * 50)
        for i, dev in enumerate(devices):
            print(f"{i+1}. {dev.path}: {dev.name}")
        print("-" * 50)

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

        if len(available_devices) == 1:
            selected_device = available_devices[0]
            print(f"✅ พบอุปกรณ์ที่ใช้งานได้: {selected_device.path} ({selected_device.name})")
            return selected_device

        print("\nพบหลายอุปกรณ์ที่ใช้งานได้:")
        for i, dev in enumerate(available_devices):
            print(f"{i+1}. {dev.path}: {dev.name}")
        while True:
            try:
                choice = input("\nเลือกอุปกรณ์ (1-" + str(len(available_devices)) + "): ")
                idx = int(choice) - 1
                if 0 <= idx < len(available_devices):
                    selected_device = available_devices[idx]
                    print(f"✅ เลือกใช้: {selected_device.path} ({selected_device.name})")
                    return selected_device
                else:
                    print("❌ กรุณาเลือกหมายเลขที่ถูกต้อง")
            except ValueError:
                print("❌ กรุณาป้อนตัวเลขเท่านั้น")

    def _barcode_loop(self):
        while not self._stop_event.is_set():
            try:
                r, _, _ = select.select([self.device.fd], [], [], 0.01)
                if not r:
                    continue
                for event in self.device.read():
                    if event.type == ecodes.EV_KEY and event.value == 1:
                        if event.code == ecodes.KEY_ENTER:
                            if len(self.buffer) > 0:
                                self.barcode_queue.put(self.buffer)
                                self.buffer = ''
                        else:
                            try:
                                key = ecodes.KEY[event.code].replace('KEY_', '')
                                char = self.translate_key(key)
                                if char:
                                    self.buffer += char
                            except Exception:
                                pass
            except Exception:
                self.buffer = ''
                continue

    def get_barcode(self):
        try:
            return self.barcode_queue.get_nowait()
        except queue.Empty:
            return None

    def translate_key(self, key):
        try:
            if key.isdigit():
                return key
            elif len(key) == 1 and key.isalpha():
                return key.upper()
            special_chars = {
                'MINUS': '-', 'EQUAL': '=', 'LEFTBRACE': '[', 'RIGHTBRACE': ']',
                'SEMICOLON': ';', 'APOSTROPHE': "'", 'GRAVE': '`', 'BACKSLASH': '\\',
                'COMMA': ',', 'DOT': '.', 'SLASH': '/'
            }
            if key in special_chars:
                return special_chars[key]
            print(f"Unknown key: {key}")
            return None
        except Exception as e:
            print(f"❌ แปลงคีย์ผิดพลาด: {e}")
            return None

    def cleanup(self):
        self._stop_event.set()
        if hasattr(self, 'device') and self.device:
            self.device.ungrab()

class DatabaseManager:
    def __init__(self):
        try:
            self.db = pymysql.connect(
                host="192.168.0.14",
                user="sew_py",
                password="cwt258963",
                database="automotive"
            )
            self.cursor = self.db.cursor()
            print("✅ เชื่อมต่อฐานข้อมูลสำเร็จ")
        except Exception as e:
            print(f"❌ เชื่อมต่อฐานข้อมูลล้มเหลว: {e}")
            sys.exit(1)

    def insert_ok(self, item_code):
        item_code = item_code.upper()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = "INSERT INTO sewing_3rd (item, qty, status, created_at) VALUES (%s, 1, 10, %s)"
        try:
            self.cursor.execute(sql, (item_code, now))
            self.db.commit()
            print(f"✅ บันทึกข้อมูล: {item_code}")
        except pymysql.err.IntegrityError as e:
            print(f"❌ ไม่สามารถบันทึก: {item_code} (อาจซ้ำ)")

    def get_target_from_cap(self):
        try:
            sql = "SELECT `3rd` FROM sewing_cap ORDER BY created_at DESC LIMIT 1"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result else "00"
        except Exception as e:
            print(f"Error fetching cap target: {e}")
            return "00"

    def get_man_plan(self):
        try:
            sql = "SELECT `3rd_plan` FROM sewing_man ORDER BY created_at DESC LIMIT 1"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result else "00"
        except Exception as e:
            print(f"Error fetching man plan: {e}")
            return "00"

    def get_man_act(self):
        try:
            sql = "SELECT `3rd_act` FROM sewing_man ORDER BY created_at DESC LIMIT 1"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result else "00"
        except Exception as e:
            print(f"Error fetching man act: {e}")
            return "00"

    def get_output_count(self):
        try:
            sql = "SELECT COUNT(`qty`) FROM `sewing_3rd` WHERE DATE(created_at) = CURDATE() LIMIT 1"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result else "00"
        except Exception as e:
            print(f"Error fetching output count: {e}")
            return "00"

    def get_hourly_output(self):
        sql = """
            SELECT HOUR(created_at) AS hr, COUNT(*) AS pcs
            FROM sewing_3rd
            WHERE DATE(created_at) = CURDATE()
            GROUP BY hr
            ORDER BY hr
        """
        try:
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            # แปลงเป็น dict: {hour: count}
            output = {int(row[0]): int(row[1]) for row in results}
            return output
        except Exception as e:
            print(f"Error fetching hourly output: {e}")
            return {}
            
    def get_hourly_output_detailed(self, for_date=None):
        """
        Return dict: {hour: count} for output, and {hour: [minute list]} for production minutes
        """
        if not for_date:
            for_date = datetime.now().strftime("%Y-%m-%d")
        sql = """
            SELECT HOUR(created_at), MINUTE(created_at)
            FROM sewing_3rd
            WHERE DATE(created_at) = %s
        """
        self.cursor.execute(sql, (for_date,))
        results = self.cursor.fetchall()
        hourly_minutes = {}
        for hr, mn in results:
            dt = datetime(2000,1,1,hr,mn)
            if not is_break(dt):
                hourly_minutes.setdefault(hr, set()).add(mn)
        hourly_output = {hr: len(mns) for hr, mns in hourly_minutes.items()}
        return hourly_output

    def close(self):
        try:
            if hasattr(self, 'cursor') and self.cursor:
                self.cursor.close()
            if hasattr(self, 'db') and self.db:
                self.db.close()
            print("✅ ปิดการเชื่อมต่อฐานข้อมูล")
        except Exception as e:
            print(f"❌ ปิดการเชื่อมต่อฐานข้อมูลผิดพลาด: {e}")

# ---- Break periods ----
BREAK_PERIODS = [
    (time(10, 0), time(10, 10)),
    (time(12, 10), time(13, 10)),
    (time(15, 0), time(15, 10)),
    (time(17, 0), time(17, 30)),
]

def is_break(dt):
    t = dt.time() if hasattr(dt, "time") else dt
    for start, end in BREAK_PERIODS:
        if start <= t < end:
            return True
    return False

def working_minutes_in_hour(hour):
    count = 0
    current = datetime(2000,1,1, hour,0)
    end = datetime(2000,1,1, hour+1,0)
    while current < end:
        if not is_break(current):
            count += 1
        current += timedelta(minutes=1)
    return count

class Dashboard:
    def __init__(self, db_manager, scanner):
        self.db_manager = db_manager
        self.scanner = scanner
        pygame.init()
        self.UPDATE_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(self.UPDATE_EVENT, 1000)
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Production Dashboard")
        self.width, self.height = self.screen.get_size()
        self.setup_fonts()
        self.setup_colors()
        self.last_ok_barcode = ""
        self.error_message = ""
        self.show_error = False

        self.target_value = self.db_manager.get_target_from_cap()
        self.man_plan = self.db_manager.get_man_plan()
        self.man_act = self.db_manager.get_man_act()
        self.output_value = self.db_manager.get_output_count()
        self.hourly_output = self.db_manager.get_hourly_output_detailed()
        self.target_value = int(self.db_manager.get_target_from_cap())

    def setup_fonts(self):
        self.font_header = pygame.font.SysFont('Arial', 50, bold=True)
        self.font_label = pygame.font.SysFont('Arial', 40, bold=True)
        self.font_percent = pygame.font.SysFont('Arial', 60, bold=True)
        self.font_small = pygame.font.SysFont('Arial', 30, bold=True)
        self.font_big = pygame.font.SysFont('Consolas', 150, bold=True)
        self.font_TH = pygame.font.SysFont('FreeSerif', 80, bold=True) # TH

    def setup_colors(self):
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 175, 0)
        self.ORANGE = (255, 140, 0)
        self.RED = (175, 0, 0)
        self.GREY = (128, 128, 128)

    def get_threshold_color(self, value, green=90, orange=80):
        if value >= green:
            return self.GREEN
        elif value >= orange:
            return self.ORANGE
        else:
            return self.RED

    def draw_box(self, rect, fill_color=None, border_color=None, border=3, radius=10):
        if fill_color is None: fill_color = self.BLACK
        if border_color is None: border_color = self.GREY
        pygame.draw.rect(self.screen, fill_color, rect, border_radius=radius)
        pygame.draw.rect(self.screen, border_color, rect, border, border_radius=radius)

    def draw_text(self, text, font, pos, color=None, align="left"):
        if color is None:
            color = self.WHITE
        surface = font.render(str(text), True, color)
        rect = surface.get_rect()
        x, y = pos

        if align == "center":
            rect.center = (x, y)
        elif align == "right":
            rect.topright = (x, y)
        else:  # "left"
            rect.topleft = (x, y)

        self.screen.blit(surface, rect)

    def process_ok_scan(self, barcode):
        if 12 < len(barcode) <= 17:
            self.last_ok_barcode = barcode
            self.db_manager.insert_ok(barcode)
            self.show_error = False
            self.error_message = ""
        else:
            if len(barcode) <= 15:
                self.error_message = "ไม่บันทึก กรุณาสแกนใหม่ (" + barcode +")"
                # self.error_message = barcode
            else:
                self.error_message = "ไม่บันทึก กรุณาสแกนใหม่ ("+ barcode +")"
                # self.error_message = barcode
            self.show_error = True

    def draw_dashboard(self):
        self.screen.fill(self.BLACK)

        # Header
        self.draw_box((30, 20, 1300, 100))
        self.draw_text("Line Name : 3RD", self.font_header, (50, 45))

        # DateTime
        self.draw_box((1350, 20, 538, 100))
        now = datetime.now()
        self.draw_text(" DATE : " + now.strftime("%d/%m/%Y"), self.font_small, (1380, 35))
        self.draw_text(" TIME  : " + now.strftime("%H:%M:%S"), self.font_small, (1380, 75))

        # Barcode Display
        self.draw_box((30, 150, self.width - 60, 170))
        self.draw_text("Part", self.font_label, (50, 160))
        if self.show_error:
            self.draw_text(self.error_message, self.font_TH, (150, 170), self.RED)
        else:
            self.draw_text(self.last_ok_barcode, self.font_big, (150, 170))

        # Right Panel
        gap_right_label =   47
        gap_right_value =   80
        px_right_x  =   995
        px_right_y  =   362

        bar_x = 1650               # ตำแหน่ง X bar
        bar_height = 30            # ความสูง bar
        bar_max_width = 200        # ความกว้าง bar 100%
        bar_y_start = px_right_y

        self.draw_box((975, 350, 915, 720))

        eff_per_hour = []
        for i, hour in enumerate(range(8, 23)):
            hour = 8 + i
            pcs = self.hourly_output.get(hour, 0)
            work_min = working_minutes_in_hour(hour)                                     #   hour
            target = int(self.target_value) if str(self.target_value).isdigit() else 0
            target_hr = int(target * (work_min / 60)) if work_min else 0                 #   target / hr
            diff_hr = pcs - target_hr                                                    #   diff / hr

            # if pcs is not 0:
            if pcs != 0:
                target = int(self.target_value) if str(self.target_value).isdigit() else 0
                percent = (pcs / target_hr) * 100 if target_hr > 0 else 0
                pcs_per_hour = f"{pcs} / {target_hr} Pcs"
                oa_per_hour = f"{percent:5.2f} %"
                eff_per_hour.append(percent)  # เก็บค่า OA % สำหรับคำนวณประสิทธิภาพรวม
                
                # กำหนดสีตามเกณฑ์
                percent_color = self.get_threshold_color(percent)  # ใช้เมธอดกำหนดสี
                bar_color = percent_color
                bar_width = int(min(percent, 100) / 100 * bar_max_width)
            else:
                pcs_per_hour = ""
                oa_per_hour = ""
                percent_color = self.BLACK   # กำหนดค่า default
                bar_color = self.GREY
                bar_width = 0

            y = bar_y_start + gap_right_label * i

            self.draw_text(f"{i+8:02d}:00", self.font_label, (px_right_x, px_right_y+(gap_right_label*i)))  #   Time
            self.draw_text(pcs_per_hour, self.font_label, (1400, y), percent_color, align="right")          #   Pcs
            self.draw_text(oa_per_hour, self.font_label, (1620, y), percent_color, align="right")            #   Percent
            
            pygame.draw.rect(self.screen, bar_color, (bar_x, y, bar_width, bar_height))                     #   bar_inner
            pygame.draw.rect(self.screen, self.GREY, (bar_x, y, bar_max_width, bar_height), 2)              #   bar_outter

        # Left Panel
        gab_left_label  =   85
        gab_left_draw   =   85
        gab_left_value  =   85
        self.draw_box((30, 350, 915, 720))   
        
        # Calculate overall efficiency
        if eff_per_hour:
            efficiency = sum(eff_per_hour) / len(eff_per_hour)
        else:
            efficiency = 0.0

        # print(list(self.hourly_output.items()))
        # print(eff_per_hour)
        # print(efficiency)
        self.efficiency = efficiency
        eff_color = self.get_threshold_color(self.efficiency)
        self.draw_text("OA %", self.font_header, (50, 370))
        pygame.draw.line(self.screen, self.GREY, (50, 430), (910, 430), 1)
        self.draw_text(f"{self.efficiency:5.2f}", self.font_percent, (910, 360), eff_color, align="right")

        self.draw_text("Output (Pcs)", self.font_header, (50, 370+(gab_left_label*1)))
        pygame.draw.line(self.screen, self.GREY, (50, 430+(gab_left_draw*1)), (910, 430+(gab_left_draw*1)), 1)
        self.draw_text(self.output_value, self.font_percent, (910, 360+(gab_left_value*1)), self.GREEN, align="right")

        # target = int(self.target_value) if str(self.target_value).isdigit() else 0
        self.draw_text("Target / Hr (Pcs)", self.font_header, (50, 370+(gab_left_label*2)))
        pygame.draw.line(self.screen, self.GREY, (50, 430+(gab_left_draw*2)), (910, 430+(gab_left_draw*2)), 1)
        self.draw_text(self.target_value, self.font_percent, (910, 360+(gab_left_value*2)), self.GREEN, align="right")
        # self.draw_text(str(target), self.font_percent, (910, 360+(gab_left_value*2)), self.GREEN, align="right")

        
        diff_each_hour = []
        for hour in self.hourly_output:
            pcs = self.hourly_output.get(hour, 0)
            work_min = working_minutes_in_hour(hour)
            target = int(self.target_value) if str(self.target_value).isdigit() else 0
            target_hr = int(target * (work_min / 60)) if work_min else 0
            diff_hr = pcs - target_hr
            diff_each_hour.append(diff_hr)

        diff_total = sum(diff_each_hour)
        # diff color
        if diff_total < 0:
            diff_color = self.RED
        elif diff_total == 0:
            diff_color = self.GREEN
        else:
            diff_color = self.ORANGE

        self.draw_text("Diff (Pcs)", self.font_header, (50, 370+(gab_left_label*3)))
        pygame.draw.line(self.screen, self.GREY, (50, 430+(gab_left_draw*3)), (910, 430+(gab_left_draw*3)), 1)
        self.draw_text(f"{diff_total}", self.font_percent, (910, 360+(gab_left_value*3)), diff_color, align="right")

        self.draw_text("NG (Pcs)", self.font_header, (50, 370+(gab_left_label*4)))
        pygame.draw.line(self.screen, self.GREY, (50, 430+(gab_left_draw*4)), (910, 430+(gab_left_draw*4)), 1)
        self.draw_text("00", self.font_percent, (910, 360+(gab_left_value*4)), self.RED, align="right")

        # Productivity 
        num_hours = len(self.hourly_output)  # จำนวนชั่วโมงที่มีการบันทึก
        if int(self.man_plan) > 0:
            productivity_plan = int(self.target_value) / int(self.man_plan)
        else:
            productivity_plan = 0.0
        if int(self.man_act) > 0:
            productivity_act = int(self.output_value) / int(self.man_act) / num_hours
        else:
            productivity_act = 0.0   

        self.draw_text("Productivity Plan", self.font_header, (50, 370+(gab_left_label*5)))
        pygame.draw.line(self.screen, self.GREY, (50, 430+(gab_left_draw*5)), (910, 430+(gab_left_draw*5)), 1)
        self.draw_text(f"{productivity_plan:.1f}", self.font_percent, (910, 360+(gab_left_value*5)), self.GREEN, align="right")

        self.draw_text("Productivity Act", self.font_header, (50, 370+(gab_left_label*6)))
        pygame.draw.line(self.screen, self.GREY, (50, 430+(gab_left_draw*6)), (910, 430+(gab_left_draw*6)), 1)
        self.draw_text(f"{productivity_act:.1f}", self.font_percent, (910, 360+(gab_left_value*6)), self.GREEN, align="right")

        self.draw_text("Man (Act / Plan)", self.font_header, (50, 370+(gab_left_label*7)))
        pygame.draw.line(self.screen, self.GREY, (50, 430+(gab_left_draw*7)), (910, 430+(gab_left_draw*7)), 1)
        self.draw_text(f"{self.man_act} / {self.man_plan}", self.font_percent, (910, 360+(gab_left_value*7)), self.GREEN, align="right")

    def run(self):
        try:
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        print("กำลังปิดโปรแกรม...")
                        self.cleanup()
                        pygame.quit()
                        os._exit(0)
                    elif event.type == self.UPDATE_EVENT:
                        self.target_value = self.db_manager.get_target_from_cap()
                        self.man_plan = self.db_manager.get_man_plan()
                        self.man_act = self.db_manager.get_man_act()
                        self.output_value = self.db_manager.get_output_count()
                        self.eff = round(float(self.output_value) / float(self.target_value) * 100, 2) if float(self.target_value) != 0 else 0.00
                        self.hourly_output = self.db_manager.get_hourly_output()

                barcode = self.scanner.get_barcode()
                if barcode:
                    self.process_ok_scan(barcode)

                self.draw_dashboard()
                pygame.display.flip()
        except Exception as e:
            print(f"Dashboard error: {e}")
            os._exit(1)  # ปิดโปรแกรมเมื่อเกิดข้อผิดพลาด

    def cleanup(self):
        try:
            if hasattr(self, 'scanner'):
                self.scanner.cleanup()
        except Exception as e:
            print(f"Dashboard cleanup error: {e}")

if __name__ == '__main__':
    db_manager = None
    scanner = None
    dashboard = None
    
    try:
        print("กำลังเริ่มต้นโปรแกรม...")
        db_manager = DatabaseManager()
        scanner = Scanner()
        dashboard = Dashboard(db_manager, scanner)
        dashboard.run()
    except Exception as e:
        print(f"❌ โปรแกรมผิดพลาด: {e}")
    finally:
        try:
            if dashboard:
                dashboard.cleanup()
            if db_manager:
                db_manager.close()
            pygame.quit()
            print("กำลังปิดโปรแกรม...")
            os._exit(0)  # ใช้ os._exit แทน sys.exit
        except Exception as e:
            print(f"❌ ปิดโปรแกรมผิดพลาด: {e}")
            os._exit(1)