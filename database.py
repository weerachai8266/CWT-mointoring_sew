import pymysql
import sys
from datetime import datetime, timedelta, time
import json

BREAK_PERIODS = [
    (time(8, 0), time(8, 10)),
    (time(10, 0), time(10, 10)),
    (time(12, 10), time(13, 10)),
    (time(15, 0), time(15, 10)),
    (time(16, 50), time(17, 0)),
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

class DatabaseManager:
    def __init__(self, line_name):
        # โหลด mapping
        with open("mapping.json", encoding="utf-8") as f:
            self.mapping = json.load(f)
        self.line_name = line_name
        self.tables = self.mapping[self.line_name]

        # เชื่อมต่อฐานข้อมูล
        try:
            self.db = pymysql.connect(
                host="192.168.100.10",
                user="user",
                password="user",
                database="automotive"
            )
            self.cursor = self.db.cursor()
            print("✅ เชื่อมต่อฐานข้อมูลสำเร็จ")
        except Exception as e:
            print(f"❌ เชื่อมต่อฐานข้อมูลล้มเหลว: {e}")
            # sys.exit(1)
            self.db = None
            self.cursor = None

    def is_connected(self):
        # ตรวจสอบสถานะการเชื่อมต่อแบบง่าย
        try:
            if self.db is None or self.cursor is None:
                return False
            self.db.ping(reconnect=True)
            return True
        except Exception:
            return False

    def insert_pd(self, item_code):
        item_code = item_code.upper()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = f"INSERT INTO {self.tables['sewing_table']} (item, qty, status, created_at) VALUES (%s, 1, 10, %s)"
        try:
            self.cursor.execute(sql, (item_code, now))
            self.db.commit()
            print(f"✅ บันทึกข้อมูล: {item_code}")
        except pymysql.err.IntegrityError as e:
            print(f"❌ ไม่สามารถบันทึก: {item_code} (อาจซ้ำ)")

    def insert_qc(self, item_code):
        item_code = item_code.upper()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = f"INSERT INTO {self.tables['qc_table']} (item, qty, status, created_at) VALUES (%s, 1, 10, %s)"
        try:
            self.cursor.execute(sql, (item_code, now))
            self.db.commit()
            print(f"✅ QC บันทึกข้อมูล: {item_code}")
        except pymysql.err.IntegrityError as e:
            print(f"❌ QC ไม่สามารถบันทึก: {item_code} (อาจซ้ำ)")

    def get_target_from_cap(self):
        try:
            sql = f"SELECT {self.tables['target_field']} FROM sewing_target ORDER BY created_at DESC LIMIT 1"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result and result[0] is not None else "0"
        except Exception as e:
            print(f"Error fetching cap target: {e}")
            return "0"

    def get_productivity_plan(self):
        try:
            sql = f"SELECT {self.tables['target_field']} FROM sewing_productivity_plan ORDER BY created_at DESC LIMIT 1"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result and result[0] is not None else "0"
        except Exception as e:
            print(f"Error fetching productivity plan: {e}")
            return "0"

    def get_man_plan(self):
        try:
            sql = f"SELECT `{self.tables['man_plan_field']}` FROM sewing_man_plan ORDER BY created_at DESC LIMIT 1"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result and result[0] is not None else "0"
        except Exception as e:
            print(f"Error fetching man plan: {e}")
            return "0"

    def get_man_act(self):
        # ดึงข้อมูล man_act ตามช่วงเวลาปัจจุบัน (แทนการดึงค่าล่าสุด)
        return self.get_man_act_by_period()

    def get_man_act_by_period(self):
        # ดึงข้อมูล man_act ตามช่วงเวลาปัจจุบัน
        
        current_time = datetime.now().time()
        if current_time >= time(8, 0) and current_time < time(13, 0):
            return self.get_man_act_for_period('เช้า')
        elif current_time >= time(13, 0) and current_time < time(17, 0):
            return self.get_man_act_for_period('บ่าย')
        elif current_time >= time(17, 0) and current_time < time(23, 0):
            return self.get_man_act_for_period('OT')
        else:
            return 0  # นอกเวลาทำงาน
            
    def get_man_act_for_period(self, shift):
        # ดึงข้อมูล man_act ตามช่วงเวลา (shift) ที่ระบุ
        # shift: 'เช้า', 'บ่าย', หรือ 'OT'
        try:
            # ดึงข้อมูลของวันนี้และตามช่วงเวลาที่ระบุ
            sql = f"""
                SELECT `{self.tables['man_act_field']}` 
                FROM sewing_man_act 
                WHERE DATE(created_at) = CURDATE() 
                AND shift = %s 
                ORDER BY created_at DESC 
                LIMIT 1
            """
            self.cursor.execute(sql, (shift,))
            result = self.cursor.fetchone()
            
            if result and result[0] is not None:
                return str(result[0])
            else:
                # ถ้าไม่มีข้อมูลของวันนี้ ให้ลองดึงข้อมูลของวันก่อนหน้าและช่วงเวลาเดียวกัน
                sql_previous = f"""
                    SELECT `{self.tables['man_act_field']}` 
                    FROM sewing_man_act 
                    WHERE shift = %s 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """
                self.cursor.execute(sql_previous, (shift,))
                prev_result = self.cursor.fetchone()
                return str(prev_result[0]) if prev_result and prev_result[0] is not None else "0"
        except Exception as e:
            print(f"Error fetching man act for period {shift}: {e}")
            return "0"

    def get_output_count_pd(self):
        try:
            sql = f"SELECT COUNT(1) FROM `{self.tables['sewing_table']}` WHERE status = 10 AND DATE(created_at) = CURDATE()"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result and result[0] is not None else "0"
        except Exception as e:
            print(f"Error fetching output count: {e}")
            return "0"

    def get_output_count_qc(self):
        try:
            sql = f"SELECT COUNT(1) FROM `{self.tables['qc_table']}` WHERE status = 10 AND DATE(created_at) = CURDATE()"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result and result[0] is not None else "0"
        except Exception as e:
            print(f"Error fetching output count: {e}")
            return "0"

    def get_ng(self):
        try:
            sql = f"SELECT sum(`qty`) FROM `qc_ng` WHERE `process` = '{self.tables['qc_ng_field']}' AND DATE(created_at) = CURDATE()"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result and result[0] is not None else "0"
        except Exception as e:
            print(f"Error fetching NG count: {e}")
            return "0"

    def get_hourly_output(self):
        sql = f"""
            SELECT HOUR(created_at) AS hr, COUNT(*) AS pcs
            FROM {self.tables['sewing_table']}
            WHERE DATE(created_at) = CURDATE() and status = 10
            GROUP BY hr
            ORDER BY hr
        """
        try:
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            output = {int(row[0]): int(row[1]) for row in results}
            return output
        except Exception as e:
            print(f"Error fetching hourly output: {e}")
            return {}
            
    def get_hourly_output_detailed(self, for_date=None):
        if not for_date:
            for_date = datetime.now().strftime("%Y-%m-%d")
        sql = f"""
            SELECT HOUR(created_at), MINUTE(created_at)
            FROM {self.tables['sewing_table']}
            WHERE DATE(created_at) = %s and status = 10
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

    def get_hourly_qc_output(self):
        sql = f"""
            SELECT HOUR(created_at) AS hr, COUNT(*) AS pcs
            FROM {self.tables['qc_table']}
            WHERE DATE(created_at) = CURDATE() and status = 10
            GROUP BY hr
            ORDER BY hr
        """
        try:
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            output = {int(row[0]): int(row[1]) for row in results}
            return output
        except Exception as e:
            print(f"Error fetching hourly output: {e}")
            return {}

    def get_hourly_qc_output_detailed(self, for_date=None):
        if not for_date:
            for_date = datetime.now().strftime("%Y-%m-%d")
        sql = f"""
            SELECT HOUR(created_at), MINUTE(created_at)
            FROM {self.tables['qc_table']}
            WHERE DATE(created_at) = %s
        """
        self.cursor.execute(sql, (for_date,))
        results = self.cursor.fetchall()
        hourly_minutes = {}
        for hr, mn in results:
            dt = datetime(2000, 1, 1, hr, mn)
            if not is_break(dt):
                hourly_minutes.setdefault(hr, set()).add(mn)
        hourly_output = {hr: len(mns) for hr, mns in hourly_minutes.items()}
        return hourly_output

    def add_index_created_at(self, table_name):
        index_name = f"idx_{table_name}_created_at"

        # เช็กก่อนว่ามี index นี้แล้วหรือยัง
        check_sql = """
            SELECT COUNT(1)
            FROM INFORMATION_SCHEMA.STATISTICS
            WHERE table_schema = DATABASE()
            AND table_name = %s
            AND index_name = %s
        """
        self.cursor.execute(check_sql, (table_name, index_name))
        exists = self.cursor.fetchone()[0]

        if exists:
            print(f"ℹ️ {table_name}.{index_name} มีอยู่แล้ว")
            return

        # ถ้ายังไม่มี index ให้เพิ่มเข้าไป
        sql = f"ALTER TABLE `{table_name}` ADD INDEX `{index_name}` (`created_at`);"
        try:
            self.cursor.execute(sql)
            self.db.commit()
            print(f"✅ เพิ่ม index {index_name} สำเร็จที่ {table_name}")
        except pymysql.MySQLError as e:
            print(f"❌ เพิ่ม index ไม่สำเร็จ: {e}")

    def add_composite_index(self, table_name, fields, index_name):
        # ตรวจสอบก่อนว่ามี index นี้แล้วไหม
        check_sql = """
            SELECT COUNT(1)
            FROM INFORMATION_SCHEMA.STATISTICS
            WHERE table_schema = DATABASE()
            AND table_name = %s
            AND index_name = %s
        """
        self.cursor.execute(check_sql, (table_name, index_name))
        exists = self.cursor.fetchone()[0]

        if exists:
            print(f"ℹ️ {table_name}.{index_name} มีอยู่แล้ว")
            return

        fields_str = ", ".join([f"`{field}`" for field in fields])
        sql = f"ALTER TABLE `{table_name}` ADD INDEX `{index_name}` ({fields_str});"
        try:
            self.cursor.execute(sql)
            self.db.commit()
            print(f"✅ เพิ่ม composite index {index_name} สำเร็จที่ {table_name}")
        except pymysql.MySQLError as e:
            print(f"❌ เพิ่ม composite index ไม่สำเร็จ: {e}")

    def close(self):
        try:
            if hasattr(self, 'cursor') and self.cursor:
                self.cursor.close()
            if hasattr(self, 'db') and self.db:
                self.db.close()
            print("✅ ปิดการเชื่อมต่อฐานข้อมูล")
        except Exception as e:
            print(f"❌ ปิดการเชื่อมต่อฐานข้อมูลผิดพลาด: {e}")

