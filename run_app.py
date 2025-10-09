# run_app.py
import os
import django
from django.core.management import call_command

def main():
    # Thiết lập môi trường, trỏ đến file settings của dự án
    # Hãy chắc chắn 'AgribankQ.settings' là đúng với tên thư mục cấu hình của bạn
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AgribankQ.settings')
    django.setup()

    # Gọi lệnh runserver một cách tự động từ trong code
    # host='0.0.0.0' để có thể truy cập từ máy khác trong mạng
    # --noreload để tránh lỗi bên trong PyInstaller
    # --insecure để BẮT BUỘC server phát triển phải phục vụ file static (CSS, JS)
    print("--- Starting Django development server on http://0.0.0.0:8000 ---")
    call_command('runserver', '0.0.0.0:5002', '--noreload', '--insecure')

if __name__ == '__main__':
    main()