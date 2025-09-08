# ✅ วิธีติดตั้ง Python
##🔹 บน Debian / Ubuntu / Raspberry Pi OS
~~~bash
sudo apt update
sudo apt install python3 python3-pip
~~~
## ตรวจสอบ:
~~~bash
python3 --version
pip3 --version
~~~
---
# install packages 
### รายชื่อไลบรารีที่ต้องใช้
- pymysql (pip)
- evdev (apt และ pip)
- pygame (apt)
- python3, python3-pip, python3-dev (apt)
- select, datetime, sys, os, threading, queue (built-in Python)

### วิธีใช้

- บันทึกไฟล์นี้เป็น `check_and_install_libs.sh`
- ให้สิทธิ์รัน:`chmod +x check_and_install_libs.sh`
- รัน:`./check_and_install_libs.sh`

### ติดตั้ง required packages
~~~ echo "🔧 กำลังติดตั้ง packages ที่จำเป็น..."
sudo apt-get install -y \
    python3-evdev \
    python3-dev \
    default-libmysqlclient-dev
~~~

### ติดตั้ง Python packages
~~~ echo "📚 กำลังติดตั้ง Python libraries..."
sudo apt install python3-evdev python3-pymysql
~~~

### เพิ่มผู้ใช้เข้ากลุ่ม input
~~~ echo "👥 กำลังเพิ่มสิทธิ์ผู้ใช้..."
sudo usermod -a -G input weerachai8266
~~~

### สร้างโฟลเดอร์สำหรับโปรแกรมและ logs
~~~ echo "📁 กำลังสร้างโครงสร้างโฟลเดอร์..."
mkdir -p ~/sewing/logs
~~~
---

# ✅ วิธีตั้งค่า Wi-Fi ผ่าน CLI บน Raspberry Pi OS (Bookworm หรือใหม่กว่า) ที่ใช้ NetworkManager
### สแกนใหม่ก่อนเชื่อม:
~~~
sudo nmcli device wifi rescan
sleep 2
nmcli device wifi list
~~~

### เชื่อมต่อ Access Point แบบ Manual และตั้ง Static IP ด้วย nmcli
~~~
sudo nmcli connection add type wifi ifname wlan0 con-name Monitor_02 autoconnect yes \
ssid "Monitor_02" \
-- wifi-sec.key-mgmt wpa-psk wifi-sec.psk "LTM.lg1750" \
ipv4.method manual \
ipv4.addresses 192.168.100.53/24 \
ipv4.gateway 192.168.100.10 \
ipv4.dns "8.8.8.8 1.1.1.1"
~~~

### 🟢 เปิดการเชื่อมต่อ:
~~~
sudo nmcli connection up Monitor_02
~~~

### 🟢 (แนะนำ) ลบโปรไฟล์ AP_Ubi3 เดิม:
~~~
sudo nmcli connection delete "AP_Ubi3"
~~~

---

# 🔧 วิธีตั้งค่าแบบ Fix ตามพอร์ต USB เท่านั้น
### 1. เปิดไฟล์ rule:
~~~bash
sudo nano /etc/udev/rules.d/99-barcode.rules
~~~

### 2. วางโค้ด
~~~udev
# PI3
KERNEL=="event*", SUBSYSTEM=="input", KERNELS=="1-1.2", SYMLINK+="input/scanner1"
KERNEL=="event*", SUBSYSTEM=="input", KERNELS=="1-1.3", SYMLINK+="input/scanner2"

# PI4
KERNEL=="event*", SUBSYSTEM=="input", KERNELS=="1-1.3", SYMLINK+="input/scanner1"
KERNEL=="event*", SUBSYSTEM=="input", KERNELS=="1-1.4", SYMLINK+="input/scanner2"
~~~

บันทึกและออก (Ctrl+O, Enter, แล้ว Ctrl+X)

### 3. โหลด rule ใหม่:
~~~bash
sudo udevadm control --reload-rules
sudo udevadm trigger
~~~

### 4. ตรวจสอบว่า symlink ถูกสร้าง:
~~~bash
ls -l /dev/input/scan*
~~~

---

# ✅ ขั้นตอนการตั้งค่า systemd ให้รัน monitor.py อัตโนมัติ
### 1. สร้างไฟล์ systemd service
~~~bash
sudo nano /etc/systemd/system/monitor.service
~~~

🔧 ใส่เนื้อหาดังนี้:
~~~ini
[Unit]
Description=Sewing Machine Monitor
After=network.target home.mount

[Service]
ExecStart=/usr/bin/python3 /home/cwt/sew/main.py
WorkingDirectory=/home/cwt/sew
Restart=always
User=cwt
Environment=PYTHONUNBUFFERED=1
Environment=XDG_RUNTIME_DIR=/run/user/1000

[Install]
WantedBy=multi-user.target

~~~
- เปลี่ยนชื่อ User= ให้ตรงกับชื่อผู้ใช้ (ของคุณคือ 3rd)
- เปลี่ยน path ให้ตรงกับตำแหน่งไฟล์ของคุณ

### 2. โหลด service และเปิดใช้งาน
~~~bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable monitor.service
sudo systemctl start monitor.service
~~~
### 3. ตรวจสอบสถานะการทำงาน
~~~bash
sudo systemctl status monitor.service
~~~
คุณควรเห็นสถานะเป็น active (running)
หากสแกนบาร์โค้ด → จะทำงานและบันทึกทันทีแม้ไม่เปิด terminal

---

# รีบูตอัตโนมัติ
~~~bash
sudo crontab -e
10 0 * * * /sbin/shutdown -r now
~~~

# ตั้ง Resolution FHD 1920*1080 สำหรับ cli

~~~ini
sudo nano /boot/firmware/config.txt
~~~
### เพิ่มหรือแก้ส่วน [all] ให้เป็นแบบนี้:
~~~ini
[all]
hdmi_force_hotplug=1
hdmi_group=1
hdmi_mode=16
hdmi_drive=2
~~~

### ✅ วิธี บังคับความละเอียดจริง ๆ ใน KMS mode:
🔧 แก้ /boot/firmware/config.txt เพิ่ม video= เพื่อบังคับผ่าน kernel cmdline:
 1.เปิดไฟล์:
~~~ini
sudo nano /boot/firmware/cmdline.txt
~~~
 2.เพิ่มค่า video=HDMI-A-1:1920x1080@60 ไว้ในบรรทัดเดียวกัน (ห้ามขึ้นบรรทัดใหม่!)
~~~ini
video=HDMI-A-1:1920x1080@60
~~~
📌 อย่าลืมเว้นวรรคคั่นคำสั่ง video=... และอย่าลบคำอื่นในบรรทัด

🛠 หรือใช้ vc4.force_hotplug=1 เสริมด้วย:
~~~ini
... video=HDMI-A-1:1920x1080@60 vc4.force_hotplug=1
~~~


### 
~~~bash
~~~

### 
~~~bash
~~~
