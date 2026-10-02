"""租户版后端配置。
所有外部依赖均走环境变量（docker/.env），不写死任何密钥。
🔴 本服务只持有：平台 API Key + 租户自己的微信支付凭证 + 白标配置。
   绝不持有天远密钥（天远只在平台侧）。
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'change-me-tenant-edition')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'rest_framework',
    'core',
    'console',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tenant_backend.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
    ]},
}]

WSGI_APPLICATION = 'tenant_backend.wsgi.application'

# 后台管理员初始密码（init_tenant 使用；上线前务必修改）
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# 数据库：默认 sqlite（单租户足够）；可通过环境变量切到 postgres
if os.environ.get('POSTGRES_DB'):
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['POSTGRES_DB'],
        'USER': os.environ.get('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
        'HOST': os.environ.get('POSTGRES_HOST', 'db'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }}
else:
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }}

AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
}

# ===== 白标 / 平台 / 微信支付 配置 =====
TENANT_NAME = os.environ.get('TENANT_NAME', '我的数据查询服务')
TENANT_LOGO_URL = os.environ.get('TENANT_LOGO_URL', '')
PRIMARY_COLOR = os.environ.get('PRIMARY_COLOR', '#6C63FF')
PUBLIC_BASE_URL = os.environ.get('PUBLIC_BASE_URL', 'http://localhost:8000')

# 平台 OpenAPI（默认指向你的平台 218.201.234.118）
PLATFORM_API_BASE = os.environ.get('PLATFORM_API_BASE', 'http://218.201.234.118/api')
PLATFORM_API_KEY = os.environ.get('PLATFORM_API_KEY', '')
# 本地联调用：不真正打平台 / 不真正打微信（避免花钱），生产改为 False
PLATFORM_MOCK = os.environ.get('PLATFORM_MOCK', 'True') == 'True'
WECHAT_MOCK = os.environ.get('WECHAT_MOCK', 'True') == 'True'

# 对客套餐（租户自定义）：id 必须与平台 QueryConfig.id 对应
import json
try:
    PACKAGES = json.loads(os.environ.get(
        'PACKAGES_JSON',
        '[{"id": 1, "name": "个人标准套餐", "price": 2200, "desc": "5合1 综合报告（风险/司法/婚姻/车辆/信用分）"}]'
    ))
except Exception:
    PACKAGES = [{'id': 1, 'name': '个人标准套餐', 'price': 2200,
                 'desc': '5合1 综合报告（风险/司法/婚姻/车辆/信用分）'}]

# 微信支付 APIv3（租户自己的）
WECHAT_APPID = os.environ.get('WECHAT_APPID', '')
WECHAT_MCHID = os.environ.get('WECHAT_MCHID', '')
WECHAT_APIV3_KEY = os.environ.get('WECHAT_APIV3_KEY', '')          # 证书/报文解密
WECHAT_SERIAL_NO = os.environ.get('WECHAT_SERIAL_NO', '')          # 商户 API 证书序列号
WECHAT_PRIVATE_KEY_PATH = os.environ.get('WECHAT_PRIVATE_KEY_PATH', '')
WECHAT_CERT_DIR = os.environ.get('WECHAT_CERT_DIR', '/certs')      # 平台证书缓存目录
WECHAT_NOTIFY_URL = os.environ.get('WECHAT_NOTIFY_URL',
                                   f'{PUBLIC_BASE_URL}/api/wechat/notify')
