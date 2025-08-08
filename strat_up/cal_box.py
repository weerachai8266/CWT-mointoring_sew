# ข้อมูลตั้งต้น
screen_width = 1920
margin = 30           # ขอบซ้ายและขวา
spacing = 30          # ระยะห่างระหว่างกล่อง
box_count = 2         # จำนวนกล่อง

# คำนวณความกว้างของกล่อง
total_spacing = (box_count - 1) * spacing
usable_width = screen_width - (2 * margin) - total_spacing
box_width = usable_width / box_count

print(f"กล่องทั้งหมด {box_count} กล่อง")
print(f"ความกว้างกล่อง: {box_width:.2f} px\n")

# แสดงตำแหน่ง x ของแต่ละกล่อง
for i in range(box_count):
    x = margin + i * (box_width + spacing)
    print(f"กล่องที่ {i+1}: x = {x:.2f}, width = {box_width:.2f}")
