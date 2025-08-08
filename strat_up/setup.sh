#!/bin/bash

echo "🚀 เริ่มการติดตั้งระบบสแกน Sewing QC..."

# อัพเดทระบบ
echo "📦 กำลังอัพเดทระบบ..."
sudo apt-get update
sudo apt-get upgrade -y

# ติดตั้ง Python และ pip
echo "🐍 กำลังติดตั้ง Python และ pip..."
sudo apt-get install -y python3 python3-pip python3-dev

# ติดตั้ง required packages
echo "🔧 กำลังติดตั้ง packages ที่จำเป็น..."
sudo apt-get install -y \
    python3-evdev \
    python3-dev \
    default-libmysqlclient-dev

# ติดตั้ง Python packages
echo "📚 กำลังติดตั้ง Python libraries..."
pip3 install evdev pymysql

# สร้าง udev rules สำหรับ scanner
echo "⚙️ กำลังตั้งค่า udev rules สำหรับสแกนเนอร์..."
echo 'KERNEL=="event*", SUBSYSTEM=="input", KERNELS=="1-1.2", SYMLINK+="input/scan_ok"' | sudo tee /etc/udev/rules.d/99-scanner-ok.rules
echo 'KERNEL=="event*", SUBSYSTEM=="input", KERNELS=="1-1.3", SYMLINK+="input/scan_ng"' | sudo tee /etc/udev/rules.d/99-scanner-ng.rules

# รีโหลด udev rules
echo "🔄 กำลังรีโหลด udev rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger

# เพิ่มผู้ใช้เข้ากลุ่ม input
echo "👥 กำลังเพิ่มสิทธิ์ผู้ใช้..."
sudo usermod -a -G input weerachai8266

# สร้างโฟลเดอร์สำหรับโปรแกรมและ logs
echo "📁 กำลังสร้างโครงสร้างโฟลเดอร์..."
mkdir -p ~/sewing/logs

# สร้าง service file สำหรับ systemd
echo "⚙️ กำลังสร้าง systemd service..."
echo "[Unit]
Description=Sewing QC Scanner Service
After=network.target

[Service]
Type=simple
User=sewing
WorkingDirectory=/home/sewing/sewing
ExecStart=/usr/bin/python3 /home/sewing/sewing/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/sewing-scanner.service

# รีโหลด systemd
echo "🔄 กำลังรีโหลด systemd..."
sudo systemctl daemon-reload

# เปิดใช้งาน service
echo "✨ กำลังเปิดใช้งาน service..."
sudo systemctl enable sewing-scanner.service

echo "
✅ การติดตั้งเสร็จสมบูรณ์!

คำสั่งที่มีประโยชน์:
1. ดูสถานะ service:
   sudo systemctl status sewing-scanner

2. ดู logs:
   journalctl -u sewing-scanner -f

3. ตรวจสอบการเชื่อมต่อสแกนเนอร์:
   ls -l /dev/input/scan*

4. ตรวจสอบ USB ports:
   ls -l /sys/bus/usb/devices/

5. ดู realtime events จากสแกนเนอร์:
   sudo evtest /dev/input/scan_ok
   sudo evtest /dev/input/scan_ng

การจัดการ service:
- เริ่มการทำงาน:    sudo systemctl start sewing-scanner
- หยุดการทำงาน:     sudo systemctl stop sewing-scanner
- รีสตาร์ท:         sudo systemctl restart sewing-scanner
- ดูสถานะ:         sudo systemctl status sewing-scanner

⚠️ หมายเหตุ:
1. เสียบสแกนเนอร์ OK ที่พอร์ต USB 1-1.2
2. เสียบสแกนเนอร์ NG ที่พอร์ต USB 1-1.3
3. ติดฉลากที่พอร์ต USB และสแกนเนอร์ให้ชัดเจน
4. ไฟล์โปรแกรมหลักควรอยู่ที่ ~/sewing/main.py

"

read -p "🔄 ต้องการ reboot เครื่องเดี๋ยวนี้หรือไม่? (y/n): " choice
if [ "$choice" = "y" ] || [ "$choice" = "Y" ]; then
    sudo reboot
else
    echo "⚠️ กรุณา reboot เครื่องในภายหลังเพื่อให้การตั้งค่าทั้งหมดมีผล"
fi