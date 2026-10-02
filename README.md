# 安遇数据查询 · 租户独立部署版（White-label Tenant Edition）

> 一套**可独立部署到租户自己服务器**、使用**租户自己域名与微信支付**的白标数据查询系统。
> 租户后端只通过**平台 API Key** 调用上游平台的 OpenAPI 查询数据，**绝不持有任何数据源密钥**。

---

## 一、项目简介

本项目是「安遇大数据」SaaS 平台的**租户发行版**（Tenant / White-label Edition）。它把一套面向 C 端用户的「个人综合数据查询」业务，封装成一个**自包含、可一键交给下游代理商 / 企业客户独立运营**的部署包。

核心定位：

- **白标（White-label）**：租户可自定义站点名称、Logo、主题色、对外域名，对外完全以「租户自己的品牌」呈现。
- **独立计费闭环**：C 端用户向**租户**付款（微信支付）→ 平台按调用从租户余额扣费 → 租户赚差价。充值与余额在平台侧管理，租户只管运营。
- **零数据源耦合**：租户包内**没有任何第三方数据源的 client 或密钥**，所有查询都走平台 OpenAPI，从源头杜绝密钥泄露与越权调用。
- **开箱即用**：默认 SQLite 存储、内置 mock 模式（联调用假数据、零扣费），单机即可跑通全流程，无需 MySQL/Redis。

### ✨ 功能特性

- **C 端自助查询 H5**：选套餐 → 填被查询人信息 → 微信支付 → 查看 5 合 1 综合报告（风险 / 司法涉诉 / 婚姻状况 / 车辆信息 / 信用分）。
- **租户管理后台**（`/admin`）：站点与品牌配置、套餐管理、支付设置、平台 API 对接与连通性测试、订单管理、分销（多级返佣）、C 端客户管理。
- **分销体系**：支持邀请码发展下级分销商，按下级消费自动返佣（未结 / 已结），后台可结算。
- **配置热更新**：品牌、套餐、支付、平台 Key 等既可在 `.env` 写种子值，也可在后台界面实时修改，**无需重启**。
- **生产友好**：提供 Docker Compose、Nginx 反代模板、systemd 单元，SQLite / PostgreSQL 双数据库支持。

---

## 二、技术栈

| 层 | 选型 |
|---|---|
| 后端 | Django 5.2 + Django REST Framework + gunicorn |
| 前端 | Nuxt 3（Vue 3）+ TailwindCSS + 新拟态 UI 风格；SPA 模式（`ssr: false`） |
| 数据库 | 默认 SQLite 3.31+（内置 `pysql3-binary` 兼容老系统）；可选 PostgreSQL |
| 支付 | 微信支付 APIv3（JSAPI），内置模拟支付开关 |
| 部署 | Docker Compose / Nginx + systemd / 宝塔面板 |

---

## 三、系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      公网（租户自有域名）                      │
│                     Nginx 反向代理 / HTTPS                    │
│   /api/  ──►  租户后端 (tenant_backend, :8000)                │
│   /  ·  /admin  ──►  租户前端 (tenant_frontend, :3000)        │
└───────────────────────────┬─────────────────────────────────┘
                            │  仅通过 API Key 调用
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              平台 OpenAPI  (gemidaojia.com/saas/api)          │
│   持有数据源密钥 · 余额/充值 · 生成 API Key              │
└─────────────────────────────────────────────────────────────┘
```

> 🔴 **铁律：禁止租户带查询**
> 租户包里**没有任何数据源 client / 凭证**，数据源只在平台。租户后端只是「下单 + 转发 + 出报告」的壳，密钥与计费权完全在上游平台。

---

## 四、目录结构

```
SaaS/
├── tenant_backend/            # Django 后端（平台 OpenAPI 客户端 + 微信支付 + 订单/授权书/分销）
│   ├── tenant_backend/        # 项目配置（settings / urls / wsgi）
│   ├── console/               # 租户管理后台 API（管理员/配置/套餐/订单/分销/客户）
│   ├── core/                  # 平台客户端 platform_client / 微信支付 / C 端查询接口
│   ├── requirements.txt
│   ├── .env.example           # 配置示例（复制为 .env 填写）
│   └── manage.py
├── tenant_frontend/           # Nuxt 3 前端 H5（C 端查询 + 租户管理后台 /admin）
│   ├── pages/  components/  composables/  middleware/
│   ├── nuxt.config.ts         # runtimeConfig.apiBase 等
│   ├── package.json
│   └── Dockerfile
├── nginx/tenant.conf          # 白标反代配置（含 HTTPS 示例）
├── docker-compose.yml         # 后端 + 前端 + Nginx 三服务编排
├── docs/                      # 深度文档：ARCHITECTURE / DEPLOY / SECURITY / OPENAPI
└── README_tenant_deploy.md    # 部署专项指南（本文的扩展版）
```

---

## 五、快速开始（Docker Compose）

适合本地验证或容器化部署，一条命令拉起全部服务：

```bash
# 1. 准备后端配置
cp tenant_backend/.env.example tenant_backend/.env
#   按需编辑 .env：至少填写 PLATFORM_API_KEY、PUBLIC_BASE_URL、TENANT_NAME

# 2. 启动（构建后端 + 前端 + Nginx）
docker compose up -d --build

# 3. 初始化租户（建管理员 + 写初始配置 + 导入套餐）
docker compose exec backend sh -c "cd /app && python manage.py migrate && \
  ADMIN_PASSWORD=123456 python manage.py init_tenant"
```

启动后访问：

- 前台 H5：`http://你的域名/`（或 `http://localhost`）
- 管理后台：`http://你的域名/admin`，默认账号 `admin` / `123456`

> 默认 `PLATFORM_MOCK=True`、`WECHAT_MOCK=True`，无需真实平台与微信即可跑通「选套餐 → 模拟支付 → 看（假）报告」全流程。

---

## 六、手动安装部署

适合直接部署到云主机 / 宝塔环境。以下以 Linux（Ubuntu 22.04+）为例。

### 6.1 后端

```bash
cd tenant_backend

# 1. Python 虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
#   注：部分老系统自带 SQLite < 3.31，requirements 已含 pysqlite3-binary 作为兼容；
#       若仍报错，见「常见问题」。

# 2. 配置
cp .env.example .env
#   编辑 .env 填写各项（见第七节配置说明）

# 3. 初始化数据库与管理员
python manage.py migrate
ADMIN_PASSWORD=123456 python manage.py init_tenant

# 4. 启动（gunicorn，生产）
gunicorn tenant_backend.wsgi:application \
  --bind 127.0.0.1:8000 --workers 2 --threads 4 --timeout 120
```

### 6.2 前端

```bash
cd tenant_frontend

npm install
# 构建时注入后端 API 基地址（必须构建前设置，构建后内联）
NUXT_API_BASE=/api npm run build
#   NUXT_APP_BASE_URL=/   # 若部署在子路径下再设置，默认根路径

# 运行（Nitro 产出，默认监听 3000）
PORT=3000 node .output/server/index.mjs
```

> ⚠️ 前端为 **SPA 模式（`ssr: false`）**：API 调用只在浏览器侧发起，相对路径 `/api` 经 Nginx 同域代理到后端，避免服务端自调用死循环。

### 6.3 Nginx 反向代理（单机）

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    client_max_body_size 10m;

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 前端 H5 + 管理后台 /admin
    location / {
        proxy_pass http://127.0.0.1:3000;
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

上线 HTTPS 时改为 `listen 443 ssl` 并配置证书（可参考 `nginx/tenant.conf` 中的 HTTPS 示例）。

### 6.4 systemd 托管（推荐，重启自启）

`/etc/systemd/system/tenant-backend.service`

```ini
[Unit]
Description=Tenant Backend (gunicorn)
After=network.target

[Service]
User=www
WorkingDirectory=/path/to/tenant_backend
EnvironmentFile=/path/to/tenant_backend/.env
ExecStart=/path/to/tenant_backend/venv/bin/gunicorn tenant_backend.wsgi:application \
          --bind 127.0.0.1:8000 --workers 2 --threads 4 --timeout 120
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/tenant-frontend.service`

```ini
[Unit]
Description=Tenant Frontend (Nuxt Nitro)
After=network.target

[Service]
User=www
WorkingDirectory=/path/to/tenant_frontend
Environment=PORT=3000 HOST=127.0.0.1 NODE_ENV=production
ExecStart=/usr/bin/node /path/to/tenant_frontend/.output/server/index.mjs
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

---

## 七、配置说明（`.env`）

| 字段 | 说明 | 默认值 |
|---|---|---|
| `DEBUG` | 调试模式 | `False` |
| `DJANGO_SECRET_KEY` | Django 密钥（生产务必改为随机串） | `change-me-tenant-edition` |
| `ALLOWED_HOSTS` | 允许访问的域名（逗号分隔），生产勿用 `*` | `*` |
| `ADMIN_PASSWORD` | 后台管理员初始密码（init_tenant 使用） | `123456` |
| `TENANT_NAME` | 站点 / 品牌名称（白标） | `我的数据查询服务` |
| `TENANT_LOGO_URL` | 品牌 Logo 地址 | 空 |
| `PRIMARY_COLOR` | 主题色（白标） | `#6C63FF` |
| `PUBLIC_BASE_URL` | 站点对外域名（回调 / 分享用） | `https://your-domain.com` |
| `PLATFORM_API_BASE` | 上游平台 OpenAPI 地址 | `https://www.gemidaojia.com/saas/api` |
| `PLATFORM_API_KEY` | 平台发放的 API Key（**必填**，向平台方获取） | 空 |
| `PLATFORM_MOCK` | `True` 联调返回假报告、不打平台；上线改 `False` | `True` |
| `PACKAGES_JSON` | 对客套餐（`id` 须对应平台 `QueryConfig.id`，`price` 为租户定价，单位：分） | 见示例 |
| `WECHAT_MOCK` | `True` 模拟支付跑通流程；上线填真实凭证后改 `False` | `True` |
| `WECHAT_APPID` / `WECHAT_MCHID` / `WECHAT_APIV3_KEY` / `WECHAT_SERIAL_NO` / `WECHAT_PRIVATE_KEY_PATH` | 租户自己的微信支付 APIv3 凭证 | 空 |
| `WECHAT_CERT_DIR` | 微信平台证书存放目录 | `/certs` |
| `WECHAT_NOTIFY_URL` | 微信支付回调地址（**必须 https**） | `https://your-domain.com/api/wechat/notify` |

> 数据库默认 SQLite（`db.sqlite3`），单机足够；如需 PostgreSQL，取消 `.env` 中 `POSTGRES_*` 注释并安装 `psycopg2` 即可切换。

---

## 八、租户管理后台

部署后访问 `http://你的域名/admin`，登录默认 `admin` / `123456`（**上线前务必修改**）。

后台可按界面热更新以下配置（等价于改 `.env`，但无需重启）：

- **概览 / 测试平台连接**：用当前 Key 调平台余额接口，验证连通性。
- **站点管理**：站点名称、Logo、主色、对外域名。
- **套餐管理**：增删改对客套餐（平台 QueryConfig id + 租户定价）。
- **支付设置**：微信 AppID / 商户号 / APIv3 密钥 / 序列号 / 回调地址 / 私钥（粘贴 PEM 自动落盘）；模拟支付开关。
- **API & Key**：平台 API 地址、API Key、模拟平台开关；可一键「测试连接」。
- **订单管理**：查看 / 筛选全部 C 端订单；详情可「标记已付 / 标记失败 / 重新查询 / 退款 / 改备注」。
- **分销管理**：维护分销商（邀请码 + 分成比例）；C 端下单携带 `dist_code` 即按分成计佣金，可「结算」转入已结。C 端下单页支持推广链接 `?dist=邀请码` 自动识别与持久化。
- **用户管理**：按微信 openid 聚合的 C 端客户（订单数、累计消费）；可拉黑（拉黑后下单直接 403）/ 解除 / 备注。

---

## 九、生产上线清单

1. **修改默认密码**：后台或 `ADMIN_PASSWORD` 改掉 `admin / 123456`。
2. **平台对接**：向平台方获取 `PLATFORM_API_KEY`，填入 `.env` 并把 `PLATFORM_MOCK` 改为 `False`。
3. **微信支付**：在微信商户平台与公众号后台配置网页授权域名、支付目录、APIv3 证书；把 `WECHAT_*` 真实凭证填入 `.env`，`WECHAT_MOCK` 改 `False`。`WECHAT_NOTIFY_URL` 必须是 https。
4. **HTTPS**：Nginx 启用 443 + 证书（`nginx/tenant.conf` 有示例），并把 `PUBLIC_BASE_URL` 改为 https 地址。
5. **收紧安全项**：`DEBUG=False`、`ALLOWED_HOSTS` 写具体域名、`DJANGO_SECRET_KEY` 改为随机串。
6. **公众号 OAuth（真实 openid）**：生产环境若需被查询人真实 openid，请在后端补充「公众号 code→openid」端点，前端下单时带上 openid（`mock` 模式不依赖 openid）。

---

## 十、安全与合规

- **数据隔离**：租户包内不含任何数据源密钥，所有查询必须经平台 OpenAPI 鉴权，从源头杜绝越权。
- **等保 / 安全基线**：详见 `docs/SECURITY.md`（安全响应头、登录限流、审计日志、密钥管理等）。
- **⚠️ 合规前置（务必重视）**：本系统涉及个人敏感信息查询，**上线商用前必须满足**：
  - 《个人信息保护法》：每一次查询都需取得**被查询人单独、明确的授权**，授权链（`AuthorizationLetter`）须完整可追溯；
  - 上游数据源接口的「转售 / 分发」条款是否允许本模式，须由**法务确认**；
  - 禁止将本系统用于任何未经授权的个人信息获取。

---

## 十一、常见问题

**Q1：迁移 / 启动报 `SQLite 3.31 or later required`**
→ 老系统自带 SQLite 过旧。`requirements.txt` 已含 `pysqlite3-binary` 作为兼容方案；若仍报错，确认虚拟环境已激活并重新 `pip install -r requirements.txt`。

**Q2：前端 `apiBase` 仍是 localhost / 接口 404**
→ `NUXT_API_BASE` 在**构建时**内联，必须在 `npm run build` **之前**设置后重新构建；并通过 Nginx 把 `/api/` 同域代理到后端。

**Q3：前端 `ssr` 死循环 / CPU 打满**
→ 本项目已设为 `ssr: false`（SPA）。请勿改回 SSR，否则服务端相对 `/api` 自调用会无限递归。

**Q4：Nginx `DisallowedHost`（Django 400）**
→ 在 `.env` 的 `ALLOWED_HOSTS` 加入实际访问域名（逗号分隔），并 `systemctl restart tenant-backend`。

**Q5：微信支付回调收不到**
→ 确认 `WECHAT_NOTIFY_URL` 为 https、域名已备案且在微信商户平台配置；证书 / 私钥路径正确。

**Q6：想换数据库为 PostgreSQL**
→ 取消 `.env` 中 `POSTGRES_*` 注释并填值，安装 `psycopg2-binary`，重启后端即可（代码已支持）。

---

## 十二、许可证与免责声明

- 本仓库代码以 **MIT 许可证**开源（详见 `LICENSE`）。
- **免责声明**：本项目仅供被查询人**本人授权后**的合法数据查询场景使用。使用者须自行确保符合所在地法律法规（含《个人信息保护法》等），就数据来源合法性、授权完整性、使用合规性承担全部责任。作者 / 平台方不对任何滥用、越权或违规使用造成的损失负责。
- 上游数据源接口的使用须遵守其服务条款；本发行版本身不包含任何数据源密钥。

---

## 相关文档

- `docs/ARCHITECTURE.md` —— 整体架构与数据模型
- `docs/DEPLOY.md` —— 平台版深度部署文档（含 MySQL / Redis / 多租户）
- `docs/SECURITY.md` —— 安全与等保基线
- `docs/OPENAPI.md` —— 平台 OpenAPI 接口说明
- `README_tenant_deploy.md` —— 租户版部署专项指南（本文扩展版）
