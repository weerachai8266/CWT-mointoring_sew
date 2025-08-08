import pygame
from datetime import datetime
from database import working_minutes_in_hour
import socket

class Dashboard:
    def __init__(self, db_manager, scanner1, scanner2):
        self.db_manager = db_manager
        self.scanner1 = scanner1
        self.scanner2 = scanner2
        pygame.init()
        self.UPDATE_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(self.UPDATE_EVENT, 1000)
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)  # ซ่อนเมาส์
        pygame.display.set_caption("Production Dashboard")
        self.width, self.height = self.screen.get_size()
        self.setup_fonts()
        self.setup_colors()
        self.last_pd_barcode = ""
        self.error_message = ""
        self.show_error = False
        self.last_qc_barcode = ""
        self.qc_error_message = ""
        self.qc_show_error = False

        self.man_plan = self.db_manager.get_man_plan()
        self.man_act = self.db_manager.get_man_act()
        self.sum_ng = self.db_manager.get_ng()
        self.output_value_pd = self.db_manager.get_output_count_pd()
        self.hourly_output = self.db_manager.get_hourly_output_detailed()
        self.hourly_output_qc = self.db_manager.get_hourly_qc_output_detailed()
        self.target_value = int(self.db_manager.get_target_from_cap())
        self.productivity_value = float(self.db_manager.get_productivity_plan())

    def setup_fonts(self):
        self.font_header = pygame.font.SysFont('Arial', 50, bold=True)
        self.font_title = pygame.font.SysFont('Arial', 60, bold=True)
        self.font_label = pygame.font.SysFont('Arial', 40, bold=True)
        self.font_percent = pygame.font.SysFont('Arial', 80, bold=True)
        self.font_small = pygame.font.SysFont('Arial', 30, bold=True)
        self.font_mini = pygame.font.SysFont('Arial', 15, bold=True)
        self.font_item = pygame.font.SysFont('Consolas', 60, bold=True)
        self.font_TH = pygame.font.SysFont('FreeSerif', 30, bold=True) # TH
        self.font_TH_small = pygame.font.SysFont('FreeSerif', 15, bold=False) # TH

    def setup_colors(self):
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 175, 0)
        self.ORANGE = (255, 140, 0)
        self.RED = (175, 0, 0)
        self.GREY = (128, 128, 128)
        self.PINK = (255, 192, 203)
        self.BLUE = (50, 150, 255)

    def get_threshold_color(self, value, green=93, orange=80):
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

    def process_pd_scan(self, barcode):
        if 2< len(barcode) <= 30:
            # แปลงรหัสสั้นเป็นรหัสเต็ม
            processed_barcode = self.expand_barcode(barcode)

            self.last_pd_barcode = processed_barcode
            self.db_manager.insert_pd(processed_barcode)
            self.show_error = False
            self.error_message = ""
        else:
            self.error_message = f"ไม่บันทึก กรุณาสแกนใหม่ ({barcode})"
            self.show_error = True

    # แสดงข้อความที่ขยายแล้ว
    def expand_barcode(self, barcode):
        # ตรวจสอบและแทนที่ suffix
        if barcode.endswith('-G'):
            return barcode.replace('-G', ' G-LEATHER')
        elif barcode.endswith('-XS'):
            return barcode.replace('-XS', ' X-SERIES')
        elif barcode.endswith('-XT'):
            return barcode.replace('-XT', ' X-TERRAIN')
        elif barcode.endswith('-2C'):
            return barcode.replace('-2C', ' 2-TONE')
        elif barcode.endswith('-T'):
            return barcode.replace('-T', ' TRICOT')
        elif barcode.endswith('-V'):
            return barcode.replace('-V', ' V-CROSS')
        else:
            # ถ้าไม่ตรงกับรูปแบบไหน ส่งคืนข้อความเดิม
            return barcode

    def process_qc_scan(self, barcode):
        if barcode.startswith("NI") and len(barcode) > 12:
            self.last_qc_barcode = barcode
            self.db_manager.insert_qc(barcode)
            self.qc_show_error = False
            self.qc_error_message = ""
        else:
            self.qc_error_message = f"ไม่บันทึก กรุณาสแกนใหม่ ({barcode})"
            self.qc_show_error = True

    def get_ip_address(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("192.168.100.10", 80))  # ใช้ gateway ของคุณ
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "0.0.0.0"

    def is_network_connected(self):
        try:
            ip = self.get_ip_address()
            return not ip.startswith("127.") and ip != "0.0.0.0"
        except:
            return False

    def get_network_info(self):
        try:
            import subprocess
            
            # ตรวจสอบการเชื่อมต่อ LAN ก่อน
            ip_cmd = "ip link show | grep 'state UP'"
            lan_check = subprocess.check_output(ip_cmd, shell=True).decode()
            if 'eth' in lan_check or 'enp' in lan_check:
                return "LAN", True
                
            # ถ้าไม่ใช่ LAN ค่อยตรวจสอบ WiFi
            try:
                wifi_cmd = "iwgetid -r"
                wifi_name = subprocess.check_output(wifi_cmd, shell=True).decode().strip()
                if wifi_name:
                    return wifi_name, True
            except:
                pass
                    
            return "Disconnected", False
        except Exception as e:
            print(f"Network info error: {e}")
            return "Disconnected", False

    def draw_dashboard(self):
        self.screen.fill(self.BLACK)

        # Header
        self.draw_box((30, 20, 915, 100))
        # self.draw_text(f"Line Name : {self.db_manager.line_name}", self.font_title, (50, 45))
        self.draw_text(f"Line Name : {self.db_manager.mapping[self.db_manager.line_name].get('display_name', self.db_manager.line_name)}",self.font_title, (50, 45))


        x_start = 975
        # box 2
        gap = 25
        box_width = 445

        # box 3
        # gap = 20
        # box_width = 300

        # DateTime
        self.draw_box((x_start, 20, box_width, 100))
        now = datetime.now()
        self.draw_text(" DATE : " + now.strftime("%d/%m/%Y"), self.font_small, (990, 35))
        self.draw_text(" TIME  : " + now.strftime("%H:%M:%S"), self.font_small, (990, 75))

        # status
        status_x = x_start + box_width + gap
        self.draw_box((status_x, 20, box_width, 100))        # box 3 : box_width - 15
        self.draw_text("Status", pygame.font.SysFont("Arial", 20), (status_x + 20, 30), self.BLUE)

        # ตรวจสอบสถานะ db
        if self.db_manager and self.db_manager.is_connected():
            db_status = "Database: Connected"
            db_color = self.GREEN
        else:
            db_status = "Database: Disconnected"
            db_color = self.RED        
        self.draw_text(db_status, pygame.font.SysFont("Arial", 18), (status_x + 20, 55), db_color)

        # ตรวจสอบสถานะ scanner1
        if self.scanner1 and self.scanner1.is_connected():
            scanner1_status = "Scanner1: Connected"
            scanner1_color = self.GREEN
        else:
            scanner1_status = "Scanner1: Missing"
            scanner1_color = self.RED
        self.draw_text(scanner1_status, pygame.font.SysFont("Arial", 18), (status_x + 20, 75), scanner1_color)

        # ตรวจสอบสถานะ scanner2
        if self.scanner2 and self.scanner2.is_connected():
            scanner2_status = "Scanner2: Connected"
            scanner2_color = self.GREEN
        else:
            scanner2_status = "Scanner2: Missing"
            scanner2_color = self.RED
        self.draw_text(scanner2_status, pygame.font.SysFont("Arial", 18), (status_x + 20, 95), scanner2_color)

        # network connetcion
        if self.is_network_connected():
            ip = self.get_ip_address()
            network_name, _ = self.get_network_info()
            network_status = f"Network: {network_name}"
            network_color = self.GREEN
            self.draw_text(f"IP: {ip}", pygame.font.SysFont("Arial", 18), (status_x + 230, 75), network_color)
        else:
            network_status = "Network: Disconnected"
            network_color = self.RED
        self.draw_text(network_status, pygame.font.SysFont("Arial", 18), (status_x + 230, 55), network_color)

        # info
        # info_x = x_start + box_width + gap + box_width - 15 + gap
        # self.draw_box((info_x, 20, box_width-10, 100))
        # self.draw_text("Info", pygame.font.SysFont("Arial", 20), (info_x + 20, 30), self.BLUE)
        # self.draw_text("Line: A", pygame.font.SysFont("Arial", 18), (info_x + 20, 60), self.GREY)
        # self.draw_text("User: weerachai8266", pygame.font.SysFont("Arial", 18), (info_x + 20, 90), self.GREY)

        # Barcode Display Production
        self.draw_box((30, 140, 915, 100))
        self.draw_text("Production", self.font_mini, (50, 150), self.BLUE)
        if self.show_error:
            self.draw_text("Error:" + self.error_message, self.font_TH, (50, 155), self.RED)
        else:
            self.draw_text("Model:" + self.last_pd_barcode, self.font_item, (50, 165))

        # Barcode Display QC
        self.draw_box((975, 140, 915, 100))
        self.draw_text("QC", self.font_mini, (995, 150), self.BLUE)
        if self.qc_show_error:
            self.draw_text("Error:" + self.qc_error_message, self.font_TH, (995, 180), self.RED)
        else:
            self.draw_text("Part:" + self.last_qc_barcode, self.font_item, (995, 165))

        # Right Panel
        self.draw_box((975, 260, 915, 810))
        gap_right_label =   50
        px_right_x  =   985
        px_right_y  =   310

        bar_x = 1675               # ตำแหน่ง X bar
        bar_height = 30            # ความสูง bar
        bar_max_width = 200        # ความกว้าง bar 100%
        bar_y_start = px_right_y

        gab_line_x = 130
        pygame.draw.line(self.screen, self.GREY, (px_right_x, 305), (1875, 305), 1)
        pygame.draw.line(self.screen, self.GREY, (1120, 270), (1120, 1055), 1)                                      # Time
        pygame.draw.line(self.screen, self.GREY, (1120 + gab_line_x * 1, 270), (1120 + gab_line_x * 1, 1055), 1);   # PD
        pygame.draw.line(self.screen, self.GREY, (1120 + gab_line_x * 2, 270), (1120 + gab_line_x * 2, 1055), 1);   # QC
        pygame.draw.line(self.screen, self.GREY, (1110 + gab_line_x * 3, 270), (1110 + gab_line_x * 3, 1055), 1);   # Tar
        pygame.draw.line(self.screen, self.GREY, (1140 + gab_line_x * 4, 270), (1140 + gab_line_x * 4, 1055), 1);   # OA

        px_right_y_header = 270
        self.draw_text("Time", self.font_small, (1010, px_right_y_header), self.BLUE)
        self.draw_text("Product", self.font_small, (1127, px_right_y_header), self.BLUE)
        self.draw_text("QC", self.font_small, (1290, px_right_y_header), self.BLUE)
        self.draw_text("Target", self.font_small, (1392, px_right_y_header), self.BLUE)
        self.draw_text("OA %", self.font_small, (1550, px_right_y_header), self.BLUE)
        # self.draw_text("Bar", self.font_small, (1740, px_right_y_header), self.BLUE)

        pygame.draw.rect(self.screen, self.RED, (bar_x, 270, 150, bar_height))
        pygame.draw.rect(self.screen, self.ORANGE, (bar_x+149, 270, 25, bar_height))
        pygame.draw.rect(self.screen, self.GREEN, (bar_x+173, 270, 25, bar_height))

        # pygame.draw.rect(self.screen, self.GREY, (bar_x, 270, 150, bar_height), 2)
        # pygame.draw.rect(self.screen, self.GREY, (bar_x+149, 270, 25, bar_height), 2)
        # pygame.draw.rect(self.screen, self.GREY, (bar_x+173, 270, 25, bar_height), 2)
        pygame.draw.rect(self.screen, self.GREY, (bar_x, 270, bar_max_width, bar_height), 2)

        eff_per_hour = []
        for i, hour in enumerate(range(8, 23)):
            hour = 8 + i
            pcs_pd = self.hourly_output.get(hour, 0)
            pcs_qc = self.hourly_output_qc.get(hour, 0)

            work_min = working_minutes_in_hour(hour)                                     #   hour
            target = int(self.target_value) if str(self.target_value).isdigit() else 0
            target_hr = int(round(target * (work_min / 60))) if work_min else 0                 #   target / hr
            diff_hr = pcs_pd - target_hr                                                    #   diff / hr

            if pcs_pd != 0:
                target = int(self.target_value) if str(self.target_value).isdigit() else 0
                percent = (pcs_pd / target_hr) * 100 if target_hr > 0 else 0
                # pcs_per_hour = f"{pcs_pd} / {target_hr} Pcs"
                oa_per_hour = f"{percent:5.2f}"
                eff_per_hour.append(percent)  # เก็บค่า OA % สำหรับคำนวณประสิทธิภาพรวม
                percent_color = self.get_threshold_color(percent)
                bar_color = percent_color
                bar_width = int(min(percent, 100) / 100 * bar_max_width)
            else:
                # pcs_per_hour = ""
                oa_per_hour = ""
                percent_color = self.BLACK
                bar_color = self.GREY
                bar_width = 0

            y = bar_y_start + gap_right_label * i

            self.draw_text(f"{i+8:02d}:00", self.font_header, (px_right_x, px_right_y+(gap_right_label*i))) # Time
            self.draw_text(pcs_pd, self.font_header, (1210, y), percent_color, align="right")               # PD
            self.draw_text(pcs_qc, self.font_header, (1340, y), percent_color, align="right")               # QC
            self.draw_text(target_hr, self.font_header, (1470, y), percent_color, align="right")            # TARGET
            self.draw_text(oa_per_hour, self.font_header, (1653, y), percent_color, align="right")          # OA
            # % bar
            pygame.draw.rect(self.screen, bar_color, (bar_x, y+8, bar_width, bar_height))
            pygame.draw.rect(self.screen, self.GREY, (bar_x, y+8, bar_max_width, bar_height), 2)

        # Left Panel
        self.draw_box((30, 260, 915, 810))
        gab_left = 100
        px_left_x_label = 50
        px_left_x_value = 910
        px_left_y = 275
        px_left_y_line  =   350
        
        if eff_per_hour:
            efficiency = sum(eff_per_hour) / len(eff_per_hour)
        else:
            efficiency = 0.0

        self.efficiency = efficiency
        eff_color = self.get_threshold_color(self.efficiency)
        self.draw_text("OA %", self.font_title, (px_left_x_label, px_left_y))

        # self.draw_text("Operational Availability", self.font_TH_small, (px_left_x_label + 50, px_left_y))

        pygame.draw.line(self.screen, self.GREY, (px_left_x_label, px_left_y_line), (px_left_x_value, px_left_y_line), 1)
        self.draw_text(f"{self.efficiency:5.2f}", self.font_percent, (px_left_x_value, px_left_y), eff_color, align="right")

        self.draw_text("Output (Pcs)", self.font_title, (px_left_x_label, px_left_y+(gab_left*1)))
        pygame.draw.line(self.screen, self.GREY, (px_left_x_label, px_left_y_line+(gab_left*1)), (px_left_x_value, px_left_y_line+(gab_left*1)), 1)
        self.draw_text(self.output_value_pd, self.font_percent, (px_left_x_value, px_left_y+(gab_left*1)), self.GREEN, align="right")

        self.draw_text("Target / Hr (Pcs)", self.font_title, (px_left_x_label, px_left_y+(gab_left*2)))
        pygame.draw.line(self.screen, self.GREY, (px_left_x_label, px_left_y_line+(gab_left*2)), (px_left_x_value, px_left_y_line+(gab_left*2)), 1)
        self.draw_text(self.target_value, self.font_percent, (px_left_x_value, px_left_y+(gab_left*2)), self.GREEN, align="right")

        diff_each_hour = []
        for hour in self.hourly_output:
            pcs = self.hourly_output.get(hour, 0)
            work_min = working_minutes_in_hour(hour)
            target = int(self.target_value) if str(self.target_value).isdigit() else 0
            target_hr = int(round(target * (work_min / 60))) if work_min else 0 
            diff_hr = pcs - target_hr
            diff_each_hour.append(diff_hr)

        diff_total = sum(diff_each_hour)
        if diff_total < 0:
            diff_color = self.RED
        elif diff_total == 0:
            diff_color = self.GREEN
        else:
            diff_color = self.ORANGE

        self.draw_text("Diff (Pcs)", self.font_title, (px_left_x_label, px_left_y+(gab_left*3)))
        pygame.draw.line(self.screen, self.GREY, (px_left_x_label, px_left_y_line+(gab_left*3)), (px_left_x_value, px_left_y_line+(gab_left*3)), 1)
        self.draw_text(f"{diff_total}", self.font_percent, (px_left_x_value, px_left_y+(gab_left*3)), diff_color, align="right")

        self.draw_text("NG (Pcs)", self.font_title, (px_left_x_label, px_left_y+(gab_left*4)))
        pygame.draw.line(self.screen, self.GREY, (px_left_x_label, px_left_y_line+(gab_left*4)), (px_left_x_value, px_left_y_line+(gab_left*4)), 1)
        self.draw_text(f"{self.sum_ng}", self.font_percent, (px_left_x_value, px_left_y+(gab_left*4)), self.RED, align="right")

        num_hours = len(self.hourly_output)
        if int(self.man_plan) > 0:
            productivity_plan = int(self.target_value) / int(self.man_plan)
        else:
            productivity_plan = 0.0
        if int(self.man_act) > 0 and num_hours > 0:
            productivity_act = int(self.output_value_pd) / int(self.man_act) / num_hours
        else:
            productivity_act = 0.0   

        self.draw_text("Productivity Plan", self.font_title, (px_left_x_label, px_left_y+(gab_left*5)))
        pygame.draw.line(self.screen, self.GREY, (px_left_x_label, px_left_y_line+(gab_left*5)), (px_left_x_value, px_left_y_line+(gab_left*5)), 1)
        # self.draw_text(f"{productivity_plan:.1f}", self.font_percent, (px_left_x_value, px_left_y+(gab_left*5)), self.GREEN, align="right")
        # self.draw_text(f"{self.db_manager.tables['productivity_plan']}", self.font_percent, (px_left_x_value, px_left_y+(gab_left*5)), self.GREEN, align="right")
        self.draw_text(f"{self.productivity_value}", self.font_percent, (px_left_x_value, px_left_y+(gab_left*5)), self.GREEN, align="right")

        self.draw_text("Productivity Act", self.font_title, (px_left_x_label, px_left_y+(gab_left*6)))
        pygame.draw.line(self.screen, self.GREY, (px_left_x_label, px_left_y_line+(gab_left*6)), (px_left_x_value, px_left_y_line+(gab_left*6)), 1)
        self.draw_text(f"{productivity_act:.1f}", self.font_percent, (px_left_x_value, px_left_y+(gab_left*6)), self.GREEN, align="right")

        self.draw_text("Man (Act / Plan)", self.font_title, (px_left_x_label, px_left_y+(gab_left*7)))
        pygame.draw.line(self.screen, self.GREY, (px_left_x_label, px_left_y_line+(gab_left*7)), (px_left_x_value, px_left_y_line+(gab_left*7)), 1)
        self.draw_text(f"{self.man_act} / {self.man_plan}", self.font_percent, (px_left_x_value, px_left_y+(gab_left*7)), self.GREEN, align="right")

    def run(self):
        try:
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        print("กำลังปิดโปรแกรม...")
                        self.cleanup()
                        pygame.quit()
                        import os
                        os._exit(0)
                    elif event.type == self.UPDATE_EVENT:
                        self.target_value = self.db_manager.get_target_from_cap()
                        self.man_plan = self.db_manager.get_man_plan()
                        self.man_act = self.db_manager.get_man_act()
                        self.sum_ng = self.db_manager.get_ng()
                        self.output_value_pd = self.db_manager.get_output_count_pd()
                        self.eff = round(float(self.output_value_pd) / float(self.target_value) * 100, 2) if float(self.target_value) != 0 else 0.00
                        self.hourly_output = self.db_manager.get_hourly_output()
                        self.hourly_output_qc = self.db_manager.get_hourly_qc_output()

                barcode1 = self.scanner1.get_barcode() if self.scanner1 else None
                barcode2 = self.scanner2.get_barcode() if self.scanner2 else None

                if barcode1:
                    self.process_pd_scan(barcode1)
                if barcode2:
                    self.process_qc_scan(barcode2)

                self.draw_dashboard()
                pygame.display.flip()
        except Exception as e:
            print(f"Dashboard error: {e}")
            import os
            os._exit(1)

    def cleanup(self):
        try:
            if hasattr(self, 'scanner1'):
                self.scanner1.cleanup()
            if hasattr(self, 'scanner2'):
                self.scanner2.cleanup()
        except Exception as e:
            print(f"Dashboard cleanup error: {e}")