@echo off
echo "========================================================"
echo "    KHOI DONG SERVER UNG DUNG TRAC NGHIEM AGRIBANK"
echo "    CHE DO OFFLINE / NOI BO"
echo "========================================================"

REM Kiem tra xem may da cai dat Python chua
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo "LOI: Khong tim thay Python. Vui long cai dat Python va dam bao da chon 'Add to PATH'."
    pause
    exit /b
)

REM Kiem tra xem thu muc moi truong ao 'venv' co ton tai khong
IF NOT EXIST venv (
    echo "Thiet lap moi truong lan dau (co the mat vai phut)..."
    python -m venv venv
)

echo "Kich hoat moi truong ao..."
call venv\Scripts\activate.bat

echo "Cai dat cac thu vien can thiet tu thu muc 'packages' (khong can Internet)..."
REM Su dung cac tham so --no-index va --find-links de cai dat offline
pip install --no-index --find-links=packages -r requirements.txt

echo "========================================================"
echo "    SERVER DANG CHAY!"
echo "    Mo trinh duyet va truy cap dia chi:"
echo "    - Tren may nay: http://localhost:8000"
echo "    - Tu may khac trong mang: http://<IP-CUA-MAY-NAY>:8000"
echo "    DE TAT SERVER, HAY DONG CUA SO NAY."
echo "========================================================"

REM Lenh nay da duoc cau hinh san de phuc vu cho mang noi bo (host=0.0.0.0)
waitress-serve --host=0.0.0.0 --port=8000 AgribankQ.wsgi:application

pause