# SaaS 多租户风险报告平台 —— 部署文档

> 适用范围：安遇大数据新版 UI 的 `SaaS/` 重构版本（独立于原项目，互不影响）。
> 本文件覆盖 **后端（Django 5.2 + DRF + MySQL 8 + Redis）** 与 **前端（Nuxt 3）** 从零到生产上线的完整步骤，含反向代理、白标、分销、OpenAPI、等保加固。

---

## 1. 系统架构与目录

```
SaaS/
├── backend/                 # Django 后端
│   ├── saas/                # 项目配置（settings/urls/wsgi/exception_handler）
│   ├── tenant/              # 租户 / 白标 / 邀请码 / 多级关系
│   ├── billing/             # 钱包 / 交易 / 套餐 / 订阅 / 分销返佣
│   ├── query/               # 接口配置 / 查询 / 报告 / OpenAPI
│   ├── requirements.txt
│   └── manage.py
├── frontend/                # Nuxt 3 前端
│   ├── pages/               # index/query/wallet/report/settings/subscription/distribution/analytics
│   ├── components/ReportView.vue
│   ├── composables/         # useAuth / useApi / useBrand
│   ├── middleware/tenant.global.ts  # 白标中间件
│   ├── nuxt.config.ts       # runtimeConfig.apiBase
│   └── package.json
└── docs/                    # ARCHITECTURE.md / SECURITY.md / 本文
```

数据隔离采用**行级隔离**（所有表带 `tenant` 字段），由 `TenantIsolationMiddleware` + DRF 基类强制按租户过滤。

---

## 2. 环境要求

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.11+ | 推荐 3.11/3.12（Django 5.2 支持） |
| Node.js | 18.20+ / 20 LTS | 前端 Nuxt 3 构建与运行 |
| MySQL | 8.0 | `utf8mb4` 字符集 |
| Redis | 6.0+ | 限流 / 缓存（默认库 1） |
| Nginx | 1.20+ | 反向代理（可选但生产推荐） |

后端第三方库（见 `requirements.txt`）：
`Django 5.2.4` / `djangorestframework 3.15.2` / `djangorestframework-simplejwt 5.3.1`
`PyMySQL 1.1.1` / `mysqlclient 2.2.4` / `gunicorn 23.0.0` / `django-cors-headers 4.4.0`
`redis 5.1.1` / `requests 2.32.3` / `PyJWT 2.9.0` / `reportlab 4.2.2` / `Pillow 10.4.0` / `python-alipay-sdk 3.1.0`

---

## 3. 后端部署

### 3.1 创建数据库与用户（MySQL）

```sql
CREATE DATABASE saas_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'saas'@'127.0.0.1' IDENTIFIED BY 'saas_pwd';
GRANT ALL PRIVILEGES ON saas_db.* TO 'saas'@'127.0.0.1';
FLUSH PRIVILEGES;
```

确保 Redis 已启动：`redis-cli ping` 应返回 `PONG`。

### 3.2 安装系统编译依赖（mysqlclient 需要）

- **Debian / Ubuntu**：
  ```bash
  sudo apt update && sudo apt install -y default-libmysqlclient-dev pkg-config build-essential
  ```
- **CentOS / Rocky**：
  ```bash
  sudo yum install -y mysql-devel pkgconfig gcc
  ```
> 若不想编译 mysqlclient，可改用 PyMySQL：在 `saas/__init__.py` 加入
> `import pymysql; pymysql.install_as_MySQLdb()`，并从 `requirements.txt` 移除 mysqlclient。

### 3.3 虚拟环境与依赖

```bash
cd SaaS/backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.4 生产配置（不要改 `settings.py`，新建 `saas/settings_prod.py`）

为不污染开发配置，新建一个生产配置覆盖项：

```python
# SaaS/backend/saas/settings_prod.py
import os
from .settings import *  # noqa: F401,F403

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
DEBUG = False
ALLOWED_HOSTS = [h for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if h]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ['REDIS_URL'],
    }
}

TIANYUAN_APP_KEY = os.environ['TIANYUAN_APP_KEY']
TIANYUAN_APP_SECRET = os.environ['TIANYUAN_APP_SECRET']

# 白标自定义域名兜底清单（数据库 Tenant.custom_domain 同样生效）
ALLOWED_TENANT_DOMAINS = [h for h in os.environ.get('TENANT_DOMAINS', '').split(',') if h]

# CORS：生产务必收紧为前端域名白名单
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [o for o in os.environ.get('CORS_ORIGINS', '').split(',') if o]

# 等保安全头（HTTPS 环境开启）
_SEC = os.environ.get('SECURE_SSL', '0') == '1'
SECURE_SSL_REDIRECT = _SEC
SESSION_COOKIE_SECURE = _SEC
CSRF_COOKIE_SECURE = _SEC
SECURE_HSTS_SECONDS = 31536000 if _SEC else 0
```

### 3.5 数据库迁移

```bash
export DJANGO_SETTINGS_MODULE=saas.settings_prod
# 先写入环境变量（示例）
export DJANGO_SECRET_KEY="$(python3 -c 'import secrets;print(secrets.token_urlsafe(50))')"
export DJANGO_ALLOWED_HOSTS="api.yourdomain.com,yourdomain.com"
export DB_NAME=saas_db DB_USER=saas DB_PASSWORD=saas_pwd DB_HOST=127.0.0.1 DB_PORT=3306
export REDIS_URL="redis://127.0.0.1:6379/1"
export TIANYUAN_APP_KEY="YOUR_TIANYUAN_APP_KEY"
export TIANYUAN_APP_SECRET="YOUR_TIANYUAN_APP_SECRET"
export CORS_ORIGINS="https://yourdomain.com"
export SECURE_SSL=1

python manage.py makemigrations
python manage.py migrate
```

### 3.6 初始化种子数据

```bash
python manage.py seed_saas --demo-tenant
```

- 创建平台租户 `platform` 及超级管理员 `platform_admin / Admin@2026`
- 创建默认接口 `DWBG8B4D`（风险 4.5 元）、`FLXG7E8F`（司法 1.8 元）
- 创建平台默认套餐、订阅三档（基础版 99 元 / 专业版 399 元 / 旗舰版 999 元，单位：元）
- 带 `--demo-tenant` 额外创建体验租户 `demo / Demo@2026`

> 首次上线后再执行 `python manage.py createsuperuser` 可另建管理后台账号。
> 务必上线后修改默认管理员密码。

### 3.7 启动后端（gunicorn，生产）

```bash
gunicorn saas.wsgi:application \
  --bind 127.0.0.1:8001 \
  --workers 3 \
  --timeout 120 \
  --access-logfile - --error-logfile -
```

推荐用 systemd 托管（见第 5 节模板）。

---

## 4. 前端部署

### 4.1 安装与构建

```bash
cd SaaS/frontend
npm install

# 构建前注入后端 API 基地址（务必使用你自己的域名）
API_BASE="https://api.yourdomain.com/api" npm run build
```

> `apiBase` 来自 `nuxt.config.ts` 的 `runtimeConfig.public.apiBase`，默认值
> `http://localhost:8001/api`。生产构建**必须**通过 `API_BASE` 环境变量覆盖。

### 4.2 运行

```bash
# 默认监听 3001
PORT=3001 node .output/server/index.mjs
```

或用 PM2：

```bash
PORT=3001 pm2 start .output/server/index.mjs --name saas-frontend
```

### 4.3 反向代理前必读

前端采用 **SPA 模式（`ssr: false`）**，由 Nitro 托管静态单页应用。Nginx 将域名反代到
`127.0.0.1:3001`，并把 `/api/` 路径转发到后端 `127.0.0.1:8001`。

> ⚠️ **为什么必须 SPA 而非 SSR**：最初用 SSR 时，`useBrand` 等 composable 在服务端用
> 相对 `baseURL: '/api'` 调用 `$fetch`，服务端会把相对路径解析成**前端自身**（3001）而非后端，
> 触发「请求自身 `/api/...` → 又跑一遍全局中间件 → 再次 fetch 自身」的无限递归，进程 100% CPU 空转。
> 改 SPA 后 API 调用只在浏览器侧发起，相对 `/api` 经 Nginx 正确代理到 8001，问题消除。

---

## 5. Nginx 反向代理

### 5.1 前端站点（yourdomain.com）

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5.2 后端独立子域（api.yourdomain.com，可选）

若希望后端使用独立域名（OpenAPI 调用更清晰）：

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

此时前端 `API_BASE` 设为 `https://api.yourdomain.com/api`。

### 5.3 白标自定义域名

每个租户可在「品牌配置」页设置 `custom_domain`。新增白标域名时，在 Nginx 增加
一个独立的 `server_name`，反代到**同一个前端端口 3001**（中间件按 `Host` 自动解析
品牌名 / Logo / 主题色）：

```nginx
server {
    listen 80;
    server_name partner-a.com;     # 租户自定义域名
    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_set_header Host $host;
        # 其余 header 同上
    }
}
```

### 5.4 systemd 后端服务（可选）

`/etc/systemd/system/saas-backend.service`：

```ini
[Unit]
Description=SaaS Backend (gunicorn)
After=network.target

[Service]
User=www
WorkingDirectory=/path/to/SaaS/backend
EnvironmentFile=/path/to/SaaS/backend/.env
ExecStart=/path/to/SaaS/backend/venv/bin/gunicorn saas.wsgi:application \
          --bind 127.0.0.1:8001 --workers 3 --timeout 120
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

`/path/to/SaaS/backend/.env` 写入第 3.5 节的环境变量（注意 `DJANGO_SETTINGS_MODULE=saas.settings_prod`）。

---

## 6. 初始化与默认账号

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 平台管理员 | `platform_admin` | `Admin@2026` | 可登录 `/admin` 与平台后台 |
| 体验租户 | `demo_owner` | `Demo@2026` | 仅 `--demo-tenant` 时创建 |

> **安全提示**：上线后立即修改以上默认密码；`/admin` 仅限平台方访问。

---

## 7. 生产环境必改清单

| 配置项 | 位置 | 状态 |
|--------|------|------|
| `SECRET_KEY` | `settings_prod.py` 读环境变量 | 必须 |
| `DEBUG = False` | `settings_prod.py` | 必须 |
| `ALLOWED_HOSTS` | `settings_prod.py` | 必须（禁止 `*`） |
| MySQL 账密 | `DATABASES` | 必须 |
| Redis URL | `CACHES` | 必须 |
| 天远 `TIANYUAN_APP_KEY/SECRET` | `settings.py` / 环境变量 | 必须 |
| `CORS_ALLOWED_ORIGINS` | `settings_prod.py` | 必须（禁止全开） |
| `SECURE_SSL_*` | `settings_prod.py` | HTTPS 环境必须 |
| `DISTRIBUTION_RATE` | `settings.py`（默认 0.10） | 按需 |
| `OPENAPI_DEFAULT_DAILY_QUOTA` / `OPENAPI_RATE_QPS` | `settings.py` | 按需 |

---

## 8. 功能使用指南

### 8.1 白标（自定义品牌）

1. 租户 owner 登录后进入「品牌配置」`/settings/brand`；
2. 填写品牌名 / Logo URL / 主题色 / 自定义域名，保存即实时生效；
3. 全站主题色经 `useBrand` + `tenant.global.ts` 中间件自动套用。

### 8.2 分销（多级 + 返佣）

- 注册时填写 `invite_code` 即绑定上级（`Tenant.parent`）；
- 下级每次消费，系统按 `DISTRIBUTION_RATE`（默认 10%）给直推上级返佣，
  记录于 `DistributionEarning`；
- 在「分销」页 `/distribution` 查看下级租户、邀请码与返佣明细。

### 8.3 OpenAPI（开发者接入）

创建 API Key：

```bash
curl -X POST https://api.yourdomain.com/api/query/openapi/keys/ \
  -H "Authorization: Bearer <登录JWT>"
```

发起查询（用 `X-Api-Key` 头）：

```bash
curl -X POST https://api.yourdomain.com/api/query/openapi/query/ \
  -H "X-Api-Key: <你的API Key>" \
  -H "Content-Type: application/json" \
  -d '{"api_code":"DWBG8B4D","name":"张三","id_card":"1101...","phone":"138..."}'
```

查询余额：

```bash
curl https://api.yourdomain.com/api/query/openapi/balance/ -H "X-Api-Key: <你的API Key>"
```

吊销密钥：

```bash
curl -X POST https://api.yourdomain.com/api/query/openapi/keys/revoke/ \
  -H "X-Api-Key: <你的API Key>"
```

> 限流：`OPENAPI_RATE_QPS`（默认 `60/min`）+ 每日配额 `Tenant.api_daily_quota`（默认 1000）。
> 密钥认证由 `query/auth.py: ApiKeyAuthentication` 处理。

---

## 9. 安全与等保

详见 `docs/SECURITY.md`。部署前重点：

1. 启用 HTTPS（Let's Encrypt），置 `SECURE_SSL=1`；
2. 登录失败限流 `LoginThrottle`（10 次/小时/IP）已内置；
3. 敏感操作写入 `AuditLog`（注册 / 登录 / 扣费 / 品牌变更 / API Key 操作）；
4. 数据严格行级隔离，`TenantIsolationMiddleware` 强制按 `request.tenant` 过滤；
5. **合规前置**：个保法授权链 + 天远接口「转售/分发」条款需法务确认后方可正式商用；
6. 默认密码、密钥、CORS 全开均属高风险，上线前必须闭环。

---

## 10. 常见问题

**Q1：`pip install mysqlclient` 失败 / 报 `mysql_config not found`**
→ 按第 3.2 节安装系统库；或改用 PyMySQL（见 3.2 提示）。

**Q2：前端报 `API_BASE` 仍是 localhost**
→ `apiBase` 在构建时内联，必须在 `npm run build` **之前**设置 `API_BASE` 环境变量，重新构建。

**Q3：Redis 连接报错**
→ 确认 `redis-server` 已启动且 `REDIS_URL` 与 `CACHES.LOCATION` 一致（默认库 1）。

**Q4：白标域名打不开 / 显示平台默认品牌**
→ 确认 Nginx 已为自定义域名加 `server` 反代到前端 3001，且 `Tenant.custom_domain` 已保存；
   兜底域名也可写入 `ALLOWED_TENANT_DOMAINS`。

**Q5：迁移报 `api_daily_quota` / `audit_logs` 等字段不存在**
→ 先 `makemigrations`（已含新增字段与表），再 `migrate`；若用老库，删库重建或 `migrate --fake-initial` 谨慎处理。

**Q6：`ALLOWED_HOSTS` 403 / DisallowedHost**
→ 在 `DJANGO_ALLOWED_HOSTS` 环境变量中加入实际访问域名（逗号分隔）。

---

## 11. 本次实装修正记录（2026-09-29，服务器 218.201.234.118）

以下为首次上线踩过的真实坑，后续重装务必先读：

1. **迁移前必须先建 `migrations/` 包**。三个业务 app（tenant/billing/query）最初**没有**
   `migrations/` 目录，Django 会静默跳过这些 app（表现为 `makemigrations` 报
   "No changes detected" 假象、实际表未建）。正确顺序：
   ```bash
   for a in tenant billing query; do
     mkdir -p $a/migrations && touch $a/migrations/__init__.py
   done
   python manage.py makemigrations tenant billing query
   python manage.py migrate
   ```
2. **前端必须 SPA（`ssr: false`）**，原因见 4.3。否则服务端自调用死循环、CPU 打满。
3. **`pycryptodome` 精确版本**须用存在的版本（如 `3.21.0`）；`3.21.1` 在 PyPI 不存在会导致
   整轮 `pip install` 中止、所有包装不上。
4. **前端 systemd 服务必须加 `Environment=PORT=3001`**：Nitro 默认监听 3000，不加会
   `EADDRINUSE: :::3000` 启动失败。
5. **本机 Nginx 是宝塔版**：站点配置目录为 `/www/server/panel/vhost/nginx/*.conf`
   （主配置 `include` 该目录），非 `/etc/nginx/conf.d/`。
6. **宝塔 Nginx 默认无 `/var/log/nginx/` 目录**：本配置在该目录写 `saas.access.log`，
   `nginx -t` 会报 `open() failed (No such file or directory)`，需先 `mkdir -p /var/log/nginx`。
7. **前端 `apiBase` 构建时注入相对 `/api`**：`API_BASE=/api npm run build`，由 Nginx 同域代理
   到后端 8001。若前端/后端分域名，则改为 `https://api.xxx.com/api`。
8. **生产配置落地方式**：未新建 `settings_prod.py`，而是在 `saas/settings.py` 末尾加了
   环境变量覆盖块（`DJANGO_SECRET_KEY / DJANGO_DEBUG / DJANGO_ALLOWED_HOSTS / TIANYUAN_* /
   CORS_ALLOW_ALL`），由 `backend/run.sh` 统一 export 后由 systemd 拉起。

> 启动脚本与服务文件见 `SaaS/deploy/`：`backend_run.sh`、`saas-backend.service`、
> `saas-frontend.service`、`nginx_saas.conf`。

