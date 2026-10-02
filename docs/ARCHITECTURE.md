# 安遇大数据 · SaaS 化重塑架构方案

> 目标：在 `SaaS/` 目录从零重塑一套多租户 SaaS 平台，复用原项目的天远查询/报告渲染业务逻辑，按多租户（Tenant）架构重写，支持「平台方 + N 个 B 端租户（代理商/企业/开发者）各自运营、各自用户、各自计费、各自品牌」。
>
> 原则：**原项目（后端/前端/小程序端）一律不改动**，全部代码落在 `SaaS/`；技术栈沿用原栈；业务逻辑复用重构而非重写。

---

## 1. 技术栈（沿用原栈 + 必要扩展）

| 层 | 选型 | 说明 |
|---|---|---|
| 前端 | Nuxt 3.17 + Vue 3.5 + TailwindCSS + Iconify + Chart.js | 与原前端同栈，报告渲染组件可直接迁移思路 |
| 后端 | Django 5.2 + **Django REST Framework** | 原项目用原生 view，SaaS 需 OpenAPI/多租户 REST，引入 DRF（Django 官方生态，不违背原栈） |
| 数据库 | MySQL 8 | 与原库同；新增 `tenant` 维度表 |
| 缓存/限流 | Redis | 租户级配额、API 限流、会话 |
| 部署 | gunicorn/uvicorn + Nginx | 与原运维一致；多租户共用一套实例（行级隔离） |
| 支付 | 支付宝 SDK + 微信支付 | 复用原 `python-alipay-sdk`；新增租户预充值 |

**新增依赖**：`djangorestframework`、`django-cors-headers`、`redis`、`djangorestframework-simplejwt`（JWT 鉴权）。

---

## 2. 目录结构

```
SaaS/
├── backend/                         # Django 后端（SaaS 平台）
│   ├── manage.py
│   ├── saas_platform/
│   │   ├── settings.py              # 多租户 settings（DB 路由/中间件/Redis）
│   │   ├── urls.py                  # 总路由：platform / tenant / openapi
│   │   └── wsgi.py
│   ├── tenants/                     # 租户核心 app
│   │   ├── models.py                # Tenant / TenantUser / TenantBrand / Invite
│   │   ├── middleware.py            # 强制按 tenant 过滤（安全底座）
│   │   └── permissions.py           # 租户级权限
│   ├── billing/                     # 计费 app
│   │   ├── models.py                # Wallet / Transaction / Plan / Subscription
│   │   └── services.py             # 充值 / 扣费 / 套餐校验
│   ├── queries/                     # 查询业务 app（复用原逻辑）
│   │   ├── models.py                # ApiConfig / QueryConfig / Order / QueryResult / ExternalApiConfig
│   │   ├── tianyuan_client.py      # 原 tianyuan_client 迁移
│   │   ├── payment_config.py        # 原 payment_config 迁移 + 多租户重构
│   │   └── report_transforms/      # 报告渲染（复用 reportMap/reportView 思路）
│   ├── api/                         # REST / OpenAPI
│   │   ├── serializers.py
│   │   ├── tenant_views.py          # 租户后台接口
│   │   └── openapi_views.py        # 开发者 OpenAPI（tenant_api_key）
│   └── users/                       # 平台 + 租户用户
├── frontend/                        # Nuxt3 前端
│   ├── pages/
│   │   ├── index.vue                # 平台 landing
│   │   ├── auth/                    # 租户注册/登录
│   │   ├── dashboard/               # 租户后台（查询/报告/计费/白标/OpenAPI）
│   │   ├── queries/                 # 查询与报告展示
│   │   └── developer/               # 开发者中心（API Key/文档）
│   ├── middleware/
│   │   └── tenant.ts                # 白标：按域名解析 Tenant → 注入 brand
│   ├── composables/
│   └── components/
├── docs/
│   └── ARCHITECTURE.md              # 本文件
└── README.md
```

---

## 3. 核心数据模型（Tenant 抽象，向上兼容原 owner_id/agent）

### 3.1 租户核心 `tenants/models.py`
```python
class Tenant(models.Model):
    TYPES = [('platform','平台方'),('agent','代理商'),('reseller','分销商'),('enterprise','企业租户')]
    name = CharField(...)               # 租户名称
    slug = SlugField(unique=True)       # 子域名前缀：{slug}.yourdomain.com
    custom_domain = CharField(null=True)# 自定义域名（白标）
    owner_type = CharField(choices=TYPES, default='agent')
    parent = FK('self', null=True)      # 上级租户 → 支持多级分销
    status = CharField(choices=[('active','启用'),('suspended','停用')])
    brand = JSONField(default=dict)     # {logo, title, primary_color, ...} 白标
    created_at = DateTimeField(auto_now_add=True)

class TenantUser(models.Model):
    tenant = FK(Tenant, on_delete=CASCADE)
    user = FK('users.User')
    role = CharField(choices=[('owner','主理人'),('admin','运营'),('member','成员')])
```
> **迁移策略**：原 `owner_id`+`owner_type` 行级隔离不变，新增 `tenant` FK 作为统一抽象层；`AgentUser` 升级为 `Tenant(owner_type='agent')` 的特例，原 `domain_suffix` 升级为 `slug`/`custom_domain` 完整白标。

### 3.2 计费 `billing/models.py`
```python
class Wallet(models.Model):            # 租户预充值余额
    tenant = OneToOneField(Tenant)
    balance = DecimalField(default=0)

class Plan(models.Model):             # 订阅套餐（月费包量）
    name = CharField(); price = DecimalField(); quota = IntegerField()  # 月度查询额度

class Subscription(models.Model):     # 租户订阅
    tenant = FK(Tenant); plan = FK(Plan); start = DateField(); end = DateField()

class Transaction(models.Model):      # 充值/扣费流水
    tenant = FK(Tenant); type = CharField(choices=[('recharge','充值'),('deduct','扣费')])
    amount = DecimalField(); ref = CharField()  # 关联 Order
```
> 查询扣费：`ApiConfig.cost`（原成本字段复用）× 租户 markup → 从 `Wallet` 扣；余额不足拦截。

### 3.3 查询业务 `queries/models.py`
沿用原 `ApiConfig / QueryConfig / Order / QueryResult / ExternalApiConfig`，全部加 `tenant` FK；`payment_config.py`、`tianyuan_client.py`、报告转换逻辑整体迁移并按 tenant 重构。

---

## 4. 多租户隔离与安全（最重要）

- **沿用行级隔离**（不改用 schema 隔离）：所有业务查询强制 `filter(tenant=request.tenant)`。
- **强制中间件** `tenants/middleware.py`：每个请求解析 `tenant`（域名/API Key/登录态），注入 `request.tenant`，并在 DRF 基类 `get_queryset` 中强制过滤——**防止串租户数据**。
- **审计**：上线前逐接口核查是否真的按 tenant 隔离；清掉原 `api_combination` 里 `id=0` 这类脏数据。
- **数据不出域 / 等保**：租户隔离做到审计级，符合政务项目同等要求。

---

## 5. 白标方案（前端）

`frontend/middleware/tenant.ts`：根据请求域名（子域或自定义域）解析 Tenant，拉取 `brand`（logo/标题/主色），注入全局 `useTenant()` 组合式，全站组件读取品牌配置。
> 复用原 `domain_suffix` 思路，升级为完整白标（logo + 标题 + 配色 + 协议文案）。

---

## 6. OpenAPI / 开发者平台

- `api/openapi_views.py`：`POST /api/v1/tenant/query`，鉴权用 `tenant_api_key`（每租户可生成多个）。
- 复用现有天远调用链（`tianyuan_client` + `payment_config`），仅在外层加租户上下文与配额校验。
- 配额/限流：Redis 记录每 `tenant_api_key` 的日/月调用量与 QPS，超限返回 429。
- 开发者中心（`frontend/pages/developer/`）：API Key 管理、用量看板、接口文档。

---

## 7. 分阶段实施计划

| 阶段 | 范围 | 交付物 | 验收 |
|---|---|---|---|
| **阶段0 骨架** | 后端 Django+DRF 初始化、Tenant 模型、隔离中间件、settings、Redis；前端 Nuxt 初始化 | `backend/`、`frontend/` 可 `manage.py check` / `nuxt build` 跑通 | 两端空壳可启动 |
| **阶段1 主链路** | 租户注册/登录、租户后台、Wallet 预充值、基础查询（复用天远逻辑）、报告展示 | 端到端：注册→充值→查询→看报告→扣费 | 一条真实查询跑通并扣余额 |
| **阶段2 白标门户** | 前端白标中间件、租户品牌配置后台、平台 landing | 不同域名显示不同品牌 | 多品牌切换正确 |
| **阶段3 OpenAPI** | 开发者平台、tenant_api_key、配额限流、用量看板 | 第三方用 API Key 查得报告 | 配额超限返回 429 |
| **阶段4 生态** | 多级分销（Tenant.parent）、订阅套餐、租户数据分析后台、等保加固 | 分销商可发展下级并分润 | 分销分润正确 |

> **建议**：先落地 **阶段0+1**（跑通 SaaS 主链路），再逐阶段叠加。每阶段完成后请你确认再进下一阶段。

---

## 8. 合规提醒（先于技术）

- **《个人信息保护法》**：每条查询需被查询人单独授权，租户级授权链（`AuthorizationLetter`）必须完整可追溯，禁止跨租户串数据。
- **天远接口「转售/分发」条款**：SaaS 多租户是否违反与天远的服务协议，上线前需法务确认。
- 合规与隔离中间件应**先于**业务逻辑落地（阶段0 即包含隔离底座）。

---

## 9. 与原项目的关系

- 原项目保留为「单体版」参考实现；SaaS 版为新分支，逻辑复用但架构重写。
- 报告渲染（司法/风险/案由常显/长文合并/脱敏）的业务规则从 `reportMap.js`/`reportView.js`/`payment_config.py` 迁移，保证双端显示规则一致。
- 原小程序端/公众号端不在本次 SaaS 重构范围（如需多端接入，后续在阶段2+ 评估）。

---

## 10. 实施进度（截至 2026-09-29）

阶段0~4 已全部落地，全部代码在 `SaaS/`，原项目未改动。

### 阶段2 白标门户（本次新增）
- 后端：`BrandUpdateView`（`PATCH /api/tenant/brand/update/`，owner/admin 改 brand_name/logo_url/theme_color/custom_domain）；`CreateInviteCodeView`（`POST /api/tenant/invite/create/`）；`ChildrenView`（`GET /api/tenant/children/`）。
- 注册已支持 `invite_code` 绑定上级（`Tenant.parent`），形成多级分销关系。
- 前端：平台 landing（`/`）、品牌配置页（`/settings/brand`，实时预览 + 刷新全站主题色）、全局白标中间件（`middleware/tenant.global.ts` + `useBrand`）。
- 登录失败限流：`tenant/throttles.py` `LoginThrottle`（10 次/小时/IP）。

### 阶段4 生态（本次新增）
- 多级分销：`DistributionEarning` 模型 + `billing.services.distribute_commission`（下级消费按 `DISTRIBUTION_RATE=0.10` 自动给直推上级返佣，写入钱包流水）。
- 订阅套餐：`Plan`/`Subscription` 模型 + `SubscribeView`(`/billing/subscribe/`)、`MySubscriptionsView`(`/billing/subscriptions/`)、`PlanListView`；`billing.services.subscribe` 按月扣费激活；前端 `/subscription`。
- 用量分析：`UsageStatsView`(`/query/stats/`) 聚合查询数/消费/下级/7日趋势；前端 `/analytics`。
- 等保加固：见 `SaaS/docs/SECURITY.md`。

### 部署提醒（每次上线）
- 迁移新表：`python manage.py makemigrations && migrate`（新增 audit_logs / distribution_earnings / plans / subscriptions / 字段 custom_domain 等）。
- 初始化/更新种子：`python manage.py seed_saas [--demo-tenant]`（已含默认订阅套餐）。
- 本地验证：`py_compile` 后端 + 前端 `@vue/compiler-sfc` 语法校验（沙箱禁 nuxt build 的 safe-delete，故不跑整包构建）。
