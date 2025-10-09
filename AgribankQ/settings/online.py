# AgribankQ/settings/online.py
from .base import *
import dj_database_url

DEBUG = False # BẮT BUỘC PHẢI LÀ FALSE

SECRET_KEY = os.environ.get('SECRET_KEY')

ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
}

# Cấu hình quan trọng cho WhiteNoise để phục vụ file tĩnh
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}