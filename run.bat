@echo off
echo "========================================================"
echo "    KHOI DONG SERVER UNG DUNG TRAC NGHIEM AGRIBANK"
echo "========================================================"
REM ... (các lệnh tạo và kích hoạt môi trường ảo) ...
call venv\Scripts\activate.bat
pip install --no-index --find-links=packages -r requirements_base.txt
echo "========================================================"
echo "    SERVER DANG CHAY!"
echo "    Mo trinh duyet va truy cap dia chi:"
echo "    - Tren may nay: http://localhost:8000"
echo "    - Tu may khac trong mang: http://<IP-CUA-MAY-NAY>:8000"
echo "========================================================"

REM Dòng quan trọng: --host=0.0.0.0
waitress-serve --host=0.0.0.0 --port=5002 AgribankQ.wsgi:application
pause