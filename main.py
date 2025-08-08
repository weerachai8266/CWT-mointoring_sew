from database import DatabaseManager
from scanner import Scanner
from dashboard import Dashboard
import pygame

if __name__ == '__main__':
    db_manager = None
    dashboard = None    

    try:
        print("กำลังเริ่มต้นโปรแกรม...")
        db_manager = DatabaseManager(line_name="SUB")
        if db_manager.is_connected():
            db_manager.add_index_created_at(db_manager.tables["sewing_table"])
            db_manager.add_index_created_at(db_manager.tables["qc_table"])
            db_manager.add_index_created_at("qc_ng")
            db_manager.add_composite_index("qc_ng", ["process", "created_at"], "idx_process_created_at")

        try:
            scanner1 = Scanner(device_path='/dev/input/scanner1')
        except Exception as e:
            print(f"⚠️ ไม่พบ scanner1: {e}")
            scanner1 = None
        try:
            scanner2 = Scanner(device_path='/dev/input/scanner2')
        except Exception as e:
            print(f"⚠️ ไม่พบ scanner2: {e}")
            scanner2 = None
            
        dashboard = Dashboard(db_manager, scanner1, scanner2)
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
        except Exception as e:
            print(f"❌ ปิดโปรแกรมผิดพลาด: {e}")