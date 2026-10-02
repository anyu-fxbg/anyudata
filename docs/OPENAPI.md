# SaaS OpenAPI 文档

风险报告 SaaS 平台对外提供的 HTTP 查询接口。开发者凭 **API Key** 调用，走与主链路完全相同的查询 / 扣费 / 脱敏 / 存库逻辑，仅认证方式不同。

---

## 1. 认证

所有 OpenAPI 请求需在 Header 携带 API Key：

```
X-Api-Key: <你的 API Key>
```

- 仅 `role=developer` 的租户成员可生成 / 使用 API Key。
- Key 在「开发者中心」生成（见第 5 节），吊销后立即失效。

---

## 2. 获取 API Key

### 生成 / 重置
```http
POST /api/query/openapi/keys/
Authorization: Bearer <JWT>          # 控制台登录态
```
响应：
```json
{ "code": 0, "message": "ok", "data": { "api_key": "xxxx.yyyy" } }
```

### 吊销
```http
POST /api/query/openapi/keys/revoke/
Authorization: Bearer <JWT>
```

> 生成与吊销使用控制台 JWT 登录态（非 API Key 本身）。

---

## 3. 提交查询

```http
POST /api/query/openapi/query/
X-Api-Key: <API Key>
Content-Type: application/json

{
  "query_config_id": 1,            // 套餐 ID（同主链路）
  "name": "张三",
  "id_card": "110101199001010011",
  "phone": "13800000000",          // 视套餐是否需要，可空
  "purpose": "风控核查"             // 查询用途（个保法留痕）
}
```

### 响应（成功）
```json
{
  "code": 0,
  "message": "查询成功",
  "data": {
    "query_id": "Qxxxxxxxxxxxx",
    "status": "success",
    "cost": 4.5,
    "report": {
      "DWBG8B4D": { "success": true, "data": { /* 风险报告 */ } },
      "FLXG7E8F": { "success": true, "data": { /* 司法涉诉 */ } }
    },
    "quota": { "used": 3, "limit": 1000 }
  }
}
```

- `report` 结构与主链路一致，前端按 `api_code` 渲染。
- `cost` 为本次扣费金额（元），已按租户 `markup` 加成。
- 被查询人姓名 / 身份证 / 手机号在返回中已脱敏。

### 错误码
| HTTP | code | 含义 |
|---|---|---|
| 400 | - | 参数校验失败 |
| 401 | - | API Key 无效或非 developer |
| 402 | 402 | 余额不足 |
| 404 | 404 | 套餐不存在 |
| 429 | 429 | 超出日配额（或 QPS 限流） |
| 207 | - | 部分接口失败（`data.report` 中含失败项） |

---

## 4. 余额与配额

```http
GET /api/query/openapi/balance/
X-Api-Key: <API Key>
```
响应：
```json
{
  "code": 0,
  "data": {
    "balance": 120.00,
    "quota_used": 12,
    "quota_limit": 1000,
    "quota_remain": 988
  }
}
```

---

## 5. 配额限制

| 维度 | 默认值 | 说明 |
|---|---|---|
| QPS | 60/min | 基于 API Key 的速率限制（DRF SimpleRateThrottle） |
| 日配额 | 1000/天 | 基于 Redis 计数，按 `Tenant.api_daily_quota` 配置，0 表示不限 |

- 日配额每日 00:00 重置。
- 超限返回 429，响应体含已用 / 限额。

---

## 6. 调用示例

### curl
```bash
curl -X POST "https://your-saas.com/api/query/openapi/query/" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: YOUR_API_KEY" \
  -d '{"query_config_id":1,"name":"张三","id_card":"110101199001010011"}'
```

### JavaScript (fetch)
```js
const res = await fetch('https://your-saas.com/api/query/openapi/query/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'X-Api-Key': KEY },
  body: JSON.stringify({ query_config_id: 1, name: '张三', id_card: '110101199001010011' }),
})
const data = await res.json()
console.log(data.data.report)
```

### Python
```python
import requests
r = requests.post('https://your-saas.com/api/query/openapi/query/',
    headers={'X-Api-Key': KEY},
    json={'query_config_id': 1, 'name': '张三', 'id_card': '110101199001010011'})
print(r.json()['data']['report'])
```

---

## 7. 合规说明

- 每次调用都会落一条 `AuthorizationLetter`（被查询人、用途、IP、协议版本），满足《个人信息保护法》对单独授权的留痕要求。
- API Key 等同于账户凭证，请妥善保管，泄露后请立即在开发者中心吊销。
- 多租户数据按 `tenant` 行级隔离，跨租户查询会被拒绝。

---

## 8. 部署须知

- 后端正通过 `TenantIsolationMiddleware` 解析 `X-Api-Key`（与 `X-Tenant-Key` 等效），无需额外配置。
- 配额计数依赖 Redis（`settings.CACHES['default']`）。
- `Tenant.api_daily_quota` 字段为新增，部署后需 `python manage.py makemigrations && migrate`。
- 开发者角色：在后台将 `TenantUser.role` 设为 `developer` 后方可生成 Key。
