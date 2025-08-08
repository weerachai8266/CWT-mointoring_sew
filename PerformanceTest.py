import time
import statistics
import pygame
from scanner import Scanner
from database import DatabaseManager
from random import choice
from string import ascii_uppercase

# === CONFIGURATION ===
WIDTH, HEIGHT = 1920, 1080
TEST_DURATION_SEC = 30
LINE_NAME = "F/C"
SCANNER1_PATH = "/dev/input/scanner1"
SCANNER2_PATH = "/dev/input/scanner2"

# === INITIAL SETUP ===
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CWT Full System + Heavy DB Stress Test")
font = pygame.font.Font(None, 32)

# Try scanners
def try_scanner(device_path):
    try:
        scanner = Scanner(device_path=device_path)
        print(f"✅ Scanner connected: {device_path}")
        return scanner
    except Exception as e:
        print(f"❌ Scanner not found: {device_path} ({e})")
        return None

scanner1 = try_scanner(SCANNER1_PATH)
scanner2 = try_scanner(SCANNER2_PATH)

# Connect DB
try:
    db_manager = DatabaseManager(line_name=LINE_NAME)
    db_status = db_manager.is_connected()
    print("✅ Database connected." if db_status else "❌ Database not connected.")
except Exception as e:
    db_manager = None
    db_status = False
    print(f"❌ Database connection error: {e}")

# Setup visual elements
rects = [(x * 20, y * 20, 18, 18) for x in range(WIDTH // 20) for y in range(HEIGHT // 20)]
colors = [(255, 255, 255)] * len(rects)

# Metrics
frame_times, db_times, scan1_times, scan2_times = [], [], [], []
insert_times, select_times, ping_times = [], [], []
scan1_count = 0
scan2_count = 0
frame_count = 0
insert_success = 0
select_success = 0
ping_success = 0
start_time = time.time()
running = True

# === MAIN STRESS TEST LOOP ===
while running and time.time() - start_time < TEST_DURATION_SEC:
    loop_start = time.perf_counter()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Scanner 1 ---
    s1_start = time.perf_counter()
    barcode1 = scanner1.get_barcode() if scanner1 else None
    s1_end = time.perf_counter()
    if barcode1:
        scan1_count += 1
    scan1_times.append(s1_end - s1_start)

    # --- Scanner 2 ---
    s2_start = time.perf_counter()
    barcode2 = scanner2.get_barcode() if scanner2 else None
    s2_end = time.perf_counter()
    if barcode2:
        scan2_count += 1
    scan2_times.append(s2_end - s2_start)

    # --- DB PING ---
    db_ping_start = time.perf_counter()
    try:
        if db_manager and db_manager.is_connected():
            ping_success += 1
            db_status = True
        else:
            db_status = False
    except:
        db_status = False
    db_ping_end = time.perf_counter()
    ping_times.append(db_ping_end - db_ping_start)

    # --- DB INSERT TEST ---
    insert_start = time.perf_counter()
    try:
        item_code = ''.join(choice(ascii_uppercase) for _ in range(6))
        sql = f"INSERT INTO {db_manager.tables['sewing_table']} (item, qty, status, created_at) VALUES (%s, 1, 10, NOW())"
        db_manager.cursor.execute(sql, (item_code,))
        db_manager.db.commit()
        insert_success += 1
    except:
        pass
    insert_end = time.perf_counter()
    insert_times.append(insert_end - insert_start)

    # --- DB SELECT TEST ---
    select_start = time.perf_counter()
    try:
        sql = f"SELECT * FROM {db_manager.tables['sewing_table']} ORDER BY created_at DESC LIMIT 5"
        db_manager.cursor.execute(sql)
        _ = db_manager.cursor.fetchall()
        select_success += 1
    except:
        pass
    select_end = time.perf_counter()
    select_times.append(select_end - select_start)

    # --- Visual update ---
    for i in range(len(colors)):
        r = (colors[i][0] + 3) % 256
        g = (colors[i][1] + 5) % 256
        b = (colors[i][2] + 7) % 256
        colors[i] = (r, g, b)

    screen.fill((0, 0, 0))
    for (x, y, w, h), color in zip(rects, colors):
        pygame.draw.rect(screen, color, (x, y, w, h))

    fps_text = font.render(f"FPS: {frame_count / (time.time() - start_time):.2f}", True, (255, 255, 255))
    db_text = font.render(f"DB: {'OK' if db_status else 'ERROR'}", True, (0, 255, 0) if db_status else (255, 0, 0))
    scan1_text = font.render(f"Scan1: {scan1_count}", True, (200, 200, 255))
    scan2_text = font.render(f"Scan2: {scan2_count}", True, (255, 200, 200))
    insert_text = font.render(f"INSERT ops: {insert_success}", True, (0, 200, 255))
    select_text = font.render(f"SELECT ops: {select_success}", True, (0, 255, 200))
    screen.blit(fps_text, (10, 10))
    screen.blit(db_text, (10, 50))
    screen.blit(scan1_text, (10, 90))
    screen.blit(scan2_text, (10, 130))
    screen.blit(insert_text, (10, 170))
    screen.blit(select_text, (10, 210))

    pygame.display.flip()
    frame_count += 1
    frame_times.append(time.perf_counter() - loop_start)

pygame.quit()
if db_manager:
    db_manager.close()

# === SUMMARY ===
def summarize(label, times, success_count):
    return {
        f"{label} ops": success_count,
        f"{label} min": min(times),
        f"{label} max": max(times),
        f"{label} avg": statistics.mean(times),
        f"{label} stddev": statistics.stdev(times) if len(times) > 1 else 0
    }

summary = {
    "Total Frames": frame_count,
    "Total Scan1": scan1_count,
    "Total Scan2": scan2_count,
    "Test Duration (s)": time.time() - start_time,
    "Estimated FPS": frame_count / (time.time() - start_time)
}
summary.update(summarize("Frame Time", frame_times, frame_count))
summary.update(summarize("Scan1 Time", scan1_times, scan1_count))
summary.update(summarize("Scan2 Time", scan2_times, scan2_count))
summary.update(summarize("Ping", ping_times, ping_success))
summary.update(summarize("Insert", insert_times, insert_success))
summary.update(summarize("Select", select_times, select_success))

# print summary as fallback if ace_tools is not available
print("=== Test Summary ===")
for key, value in summary.items():
    print(f"{key:25}: {value:.4f}" if isinstance(value, float) else f"{key:25}: {value}")
