#!/bin/bash
# SaaS 后端启动脚本（由 systemd 调用）
set -e
export DJANGO_SETTINGS_MODULE=saas.settings
export DJANGO_SECRET_KEY='m5tJ1tX_Y7zmdSxtYCeW3g2buYAhKmBFUz_jNUWP8jLpSGmKLvavOwMjxSosN2pbXE0'
export DJANGO_DEBUG=False
export DJANGO_ALLOWED_HOSTS='218.201.234.118,localhost,127.0.0.1'
export TIANYUAN_APP_KEY='YOUR_TIANYUAN_APP_KEY'
export TIANYUAN_APP_SECRET='YOUR_TIANYUAN_APP_SECRET'
export CORS_ALLOW_ALL='1'
cd /www/wwwroot/SaaS/backend
exec /www/wwwroot/SaaS/backend/venv/bin/gunicorn saas.wsgi:application \
  --bind 127.0.0.1:8001 \
  --workers 3 \
  --timeout 120 \
  --access-logfile /var/log/saas-backend.access.log \
  --error-logfile /var/log/saas-backend.error.log
