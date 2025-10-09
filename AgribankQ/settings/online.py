from .base import *
import dj_database_url

# TẠM THỜI BẬT DEBUG ĐỂ XEM LỖI CHI TIẾT
DEBUG = True

SECRET_KEY = os.environ.get('SECRET_KEY')

ALLOWED_HOSTS = ['*'] # Tạm thời cho phép mọi kết nối để tránh lỗi DisallowedHost

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600)
}

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}