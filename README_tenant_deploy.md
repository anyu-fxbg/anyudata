# 租户版 SaaS 部署指南（C 端自助查询 H5）

一套**可独立部署**到租户自己服务器、用租户自己域名与微信支付的白标查询系统。
租户后端只通过**平台 API Key** 调用你（平台）的 OpenAPI 查数据，**绝不持有天远密钥**。

---

## 架构

| 角色 | 位置 | 持有 | 职责 |
|---|---|---|---|
| 平台 | `api联系客服获取`（你） | 密钥、API Key、余额、充值 | 暴露 OpenAPI（`/saas/api/query/openapi/*`） |
| 租户后端 | 租户服务器（`tenant_backend/`） | 平台 API Key、租户微信支付凭证、白标配置 | 订单、微信支付、调平台查、出报告 |
| 租户前端 | 租户服务器（`tenant_frontend/`） | 无密钥 | C 端 H5 + **租户管理后台 `/admin`** |
| nginx | 租户服务器 | 白标域名反代 | `/api`→后端， `/`→前端 |

**🔴 铁律：禁止租户带查询** —— 租户包里没有任何天远 client / 凭证，数据源只在平台。

商业闭环：C 端客户付**租户定价**（微信支付）→ 平台按调用从租户余额扣费 → 租户赚差价。
**充值 / 余额仍在平台控制台**，租户管理员登录那里领 Key + 充值。

所有白标 / 套餐 / 微信 / 平台 Key 配置，既可在 `.env` 写好初次种子值，也可在**租户管理后台界面**热更新（无需重启）。

---

## 一、平台侧（一次性）
1. 登录平台控制台 → 开发者中心 → 生成 **API Key**。
2. 充值余额（余额 / 充值只在平台侧，不走租户）。
3. 把 `API 地址`（默认 `api联系客服获取`）+ **API Key** 交给租户。

## 二、配置租户后端
```
cp tenant_backend/.env.example tenant_backend/.env
python manage.py migrate
ADMIN_PASSWORD=你的后台密码 python manage.py init_tenant   # 建管理员(admin) + 写初始配置 + 导入套餐
```
关键字段（仅作**首次种子值**，之后在后台界面改更方便）：
- `PLATFORM_API_BASE`：默认 `api联系客服获取`
- `PLATFORM_API_KEY`：平台发的 Key
- `PLATFORM_MOCK`：先 `True` 联调（返回假报告、不打平台）；上线改 `False`
- `TENANT_NAME` / `PRIMARY_COLOR` / `PUBLIC_BASE_URL`：白标
- `PACKAGES_JSON`：`id` 必须对应**平台 `QueryConfig.id`**，`price` 为你的对客定价（单位：分）
- 微信支付：先 `WECHAT_MOCK=True` 跑通；上线填 `WECHAT_APPID/WECHAT_MCHID/WECHAT_APIV3_KEY/WECHAT_SERIAL_NO/WECHAT_PRIVATE_KEY_PATH`，并把 `WECHAT_MOCK=False`
- `ADMIN_PASSWORD`：后台管理员初始密码（默认 `admin123`，**务必修改**）

## 二之一、租户管理后台（新增）
部署后访问 `http://你的域名/admin` → 登录（默认 `admin` / `ADMIN_PASSWORD`）。
后台可**界面化、热更新**以下配置（等价于改 `.env`，但不用重启）：
- **概览 / 测试平台连接**：用当前 Key 调平台余额接口，验证连通性。
- **站点管理**：站点名称、Logo、主色、对外域名。
- **套餐管理**：增删改对客套餐（平台 QueryConfig id + 租户定价）。
- **支付设置**：微信 AppID / 商户号 / APIv3 密钥 / 序列号 / 回调地址 / 私钥（粘贴 PEM 自动落盘）；模拟支付开关。
- **API & Key**：平台 API 地址、API Key、模拟平台开关；可一键「测试连接」。
- **订单管理**：查看 / 筛选（状态、关键词）全部 C 端订单；详情内可「标记已付 / 标记失败 / 重新查询 / 退款 / 改备注」。退款会自动冲减对应分销商的未结佣金。
- **分销管理**：维护分销商（邀请码 + 分成比例）；C 端下单携带 `dist_code` 即按分成计佣金（累计到「未结」），可「结算」把未结转入「已结」并留结算记录。C 端下单页已支持：推广链接带 `?dist=邀请码` 会自动识别并持久化，用户也可在下单页手动填写「分销码（选填）」。
- **用户管理**：按微信 openid 聚合的 C 端客户（订单数、累计消费）；可拉黑（拉黑后该 openid 下单直接 403）/ 解除拉黑 / 备注，并查看其近期订单。

> 修改即时生效（C 端品牌、套餐、支付均实时读取数据库配置）。

## 三、启动（docker compose）
```
docker compose up -d --build
```
浏览器开 `http://你的域名` → 选套餐 → 填信息 → （mock）模拟支付 → 看报告。
管理后台开 `http://你的域名/admin`。

## 四、上线真实支付 + HTTPS
1. 公众号后台配置**网页授权域名**与**微信支付**；把商户证书 / 私钥放到 `certs/` 并挂载进后端容器。
2. 关闭 `WECHAT_MOCK` 与 `PLATFORM_MOCK`（改 `False`）。
3. `nginx/tenant.conf` 启用 443 + 证书，`docker-compose.yml` 端口改 `443:443`。
4. `WECHAT_NOTIFY_URL` 必须是 **https**。

> 真实 JSAPI 支付需要被查询人微信 **openid**：生产环境请在租户后端加公众号 OAuth（code→openid）端点，
> 前端下单时带上 openid。当前 `mock` 模式不依赖 openid。

## 五、本地联调（无需 docker）
```
# 后端
cd tenant_backend && pip install -r requirements.txt
export PLATFORM_MOCK=True WECHAT_MOCK=True DJANGO_SECRET_KEY=dev
python manage.py migrate && python manage.py runserver 8000
# 前端
cd ../tenant_frontend && npm install && npm run dev
```

---

## 目录
- `tenant_backend/` —— Django 后端（平台 OpenAPI 客户端 + 微信支付 + 订单 / 授权书）
- `tenant_frontend/` —— Nuxt3 前端 H5（复用 5 合 1 报告卡片 + 新拟态风格）
- `nginx/tenant.conf` —— 白标反代配置
- `docker-compose.yml` —— 三服务编排
