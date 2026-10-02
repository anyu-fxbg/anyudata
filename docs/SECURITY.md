# SaaS 平台安全与等保合规清单

> 面向政务 / 金融场景的多租户风险报告平台。下列条目为部署前需逐项确认的加固与合规基线。
> 代码层面已在 `SaaS/` 内实现的部分已标注 ✅；其余为上线前运维 / 法务动作。

---

## 1. 多租户数据隔离（核心）

- ✅ **行级隔离**：所有业务表带 `tenant` 外键；`TenantIsolationMiddleware` 强制解析 `request.tenant`（按 登录用户 / X-Api-Key / HTTP Host），下游视图一律以 `request.tenant` 过滤。
- ✅ **强制兜底**：中间件 `STRICT=False` 时回退平台租户，避免空租户绕过；生产建议结合审计日志核查每个接口是否真正按 `tenant` 过滤。
- ✅ **API Key 隔离**：`ApiKeyAuthentication` 仅匹配 `role=developer` 的 `TenantUser`，且写回 `request.tenant`，与主链路同源隔离逻辑。
- ⚠️ **上线前**：逐接口核对 `filter(tenant=...)` 是否覆盖（尤其新增的 brand/children/stats）；清理原项目遗留的 `api_combination id=0` 脏数据。

## 2. 传输与通道安全

- ✅ `SECURE_CONTENT_TYPE_NOSNIFF=True`、`SECURE_BROWSER_XSS_FILTER=True`、`X_FRAME_OPTIONS='DENY'`（防点击劫持）。
- ⚠️ 生产环境（DEBUG=False）开启：`SECURE_SSL_REDIRECT`、`SESSION_COOKIE_SECURE`、`CSRF_COOKIE_SECURE`、`SECURE_HSTS_SECONDS=31536000`（见 `saas/settings.py` 注释）。
- ⚠️ 全站 HTTPS（Nginx 终止 + HSTS），API 与前端同源或显式 CORS 白名单（当前 `CORS_ALLOW_ALL_ORIGINS=True`，生产收紧为白名单）。

## 3. 身份认证与暴力防护

- ✅ JWT 鉴权（`rest_framework_simplejwt`，access 2h / refresh 7d）。
- ✅ **登录限流**：`tenant/throttles.py` `LoginThrottle` = 10 次/小时/IP，防密码爆破。
- ⚠️ 密码策略：当前 `AUTH_PASSWORD_VALIDATORS` 仅最小长度，生产加 `CommonPasswordValidator` / 复杂度。
- ⚠️ 开发者 API Key 泄露应急：控制台一键吊销（`/api/query/openapi/keys/revoke/`），立即失效旧 Key。

## 4. 敏感数据脱敏与留存

- ✅ 被查询人姓名/身份证/手机号在返回与落库时脱敏（`payment_config.mask_name / mask_id_card / mask_phone`）。
- ✅ 每次查询落 `AuthorizationLetter`（被查询人、用途、IP、协议版本），满足《个人信息保护法》单独授权留痕。
- ⚠️ 原始天远返回 `raw_results` 仅内部留档，建议设定留存期（如 180 天）后定期清理，避免超期存储。

## 5. 操作审计（等保"审计性"）

- ✅ `AuditLog` 模型记录 login / query / recharge / subscribe / brand_update / invite_create / apikey / distribution 等敏感操作（tenant + 操作人 + IP + 时间）。
- ⚠️ 生产将 `AuditLog` 接入集中日志（ELK / 云审计），设置防篡改与定期归档。

## 6. 合规（先于技术）

- ⚠️ **《个人信息保护法》**：每条查询需被查询人单独授权，授权链（`AuthorizationLetter`）必须完整可追溯，禁止跨租户串数据。
- ⚠️ **天远接口「转售/分发」条款**：SaaS 多租户是否违反与天远的服务协议，上线前需法务确认（见 ARCHITECTURE.md 第 8 节）。
- ⚠️ 等保测评：二级/三级备案、边界防护、入侵检测、数据备份与恢复演练，按属地网信/公安要求执行。

## 7. 部署与密钥

- ⚠️ `SECRET_KEY`、`TIANYUAN_APP_KEY/SECRET` 必须替换为环境变量注入，禁止明文提交。
- ⚠️ MySQL 用独立账号最小权限；Redis 启用 `requirepass` 并仅内网可达。
- ✅ 余额变更全部经 `billing.services.charge/recharge` 原子操作 + 流水，防止并发超扣。
