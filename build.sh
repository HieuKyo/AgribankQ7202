#!/usr/bin/env bash
set -o errexit

pip install -r requirements_online.txt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py create_initial_superuser
