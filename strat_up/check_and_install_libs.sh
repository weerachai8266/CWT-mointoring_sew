#!/bin/bash

# อัปเดตฐานข้อมูลแพ็คเกจ
sudo apt update

# รายชื่อไลบรารีที่ติดตั้งผ่าน apt
APT_PACKAGES=(
    python3
    python3-pip
    python3-dev
    python3-pygame>=2.0,<2.1
    python3-evdev
    python3-pymysql    # เพิ่มตรงนี้: ติดตั้ง PyMySQL ผ่าน apt
)

echo "ตรวจสอบและติดตั้งไลบรารีระบบ (apt)..."
for pkg in "${APT_PACKAGES[@]}"; do
    if dpkg -s "$pkg" >/dev/null 2>&1; then
        echo "พบ $pkg แล้ว"
    else
        echo "กำลังติดตั้ง $pkg ..."
        sudo apt install -y "$pkg"
    fi
done

echo ""
echo "ติดตั้งไลบรารี Python เพิ่มเติมที่จำเป็น (pip3)..."
pip3 install --upgrade pip
pip3 install evdev

echo ""
echo "ติดตั้งไลบรารีทั้งหมดเสร็จสิ้น!"
