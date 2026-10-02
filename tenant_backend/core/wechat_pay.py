"""微信支付 APIv3（JSAPI，公众号）封装。
- 默认 WECHAT_MOCK=True：返回模拟预付单，不真正请求微信（联调用）。
- 真实模式：APIv3 证书签名 + 统一下单；回调验签/解密需配置平台证书后启用。
租户自己的商户号，与平台无关。
"""
import os
import time
import json
import uuid
import base64
import logging

logger = logging.getLogger(__name__)

try:
    from cryptography.hazmat.primitives.asymmetric import padding as _rsa_padding
    from cryptography.hazmat.primitives import hashes as _hashes
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
except Exception as e:  # pragma: no cover
    logger.warning('cryptography 未安装: %s', e)
    load_pem_private_key = None


def _now_ts():
    return str(int(time.time()))


def _nonce():
    return uuid.uuid4().hex


def _cfg():
    from console.models import TenantConfig
    return TenantConfig.get()


def _load_private_key():
    p = _cfg().wechat_private_key_path or os.environ.get('WECHAT_PRIVATE_KEY_PATH', '')
    if not p or not os.path.exists(p) or load_pem_private_key is None:
        return None
    with open(p, 'rb') as f:
        return load_pem_private_key(f.read(), password=None)


def _sign(message, key):
    sig = key.sign(message.encode('utf-8'), _rsa_padding.PKCS1v15(), _hashes.SHA256())
    return base64.b64encode(sig).decode()


def _build_auth(method, url_path, body):
    key = _load_private_key()
    if key is None:
        raise RuntimeError('缺少微信支付私钥')
    cfg = _cfg()
    mchid = cfg.wechat_mchid
    serial = cfg.wechat_serial_no
    ts = _now_ts()
    nonce = _nonce()
    message = f'{method}\n{url_path}\n{ts}\n{nonce}\n{body}\n'
    sig = _sign(message, key)
    return (f'WECHATPAY2-SHA256-RSA2048 mchid="{mchid}",nonce_str="{nonce}",'
            f'signature="{sig}",timestamp="{ts}",serial_no="{serial}"')


def _build_pay_params(prepay_id, key, appid):
    ts = _now_ts()
    nonce = _nonce()
    pkg = f'prepay_id={prepay_id}'
    message = f'{appid}\n{ts}\n{nonce}\n{pkg}\n'
    pay_sign = _sign(message, key)
    return {'appId': appid, 'timeStamp': ts, 'nonceStr': nonce,
            'package': pkg, 'signType': 'RSA', 'paySign': pay_sign}


def create_jsapi_order(order):
    """创建 JSAPI 预付单，返回给前端的 pay 参数。"""
    cfg = _cfg()
    if cfg.wechat_mock:
        prepay = 'MOCKPREPAY' + order.order_no
        order.wechat_prepay_id = prepay
        order.save(update_fields=['wechat_prepay_id'])
        return {'mock': True, 'prepay_id': prepay}

    key = _load_private_key()
    if key is None:
        raise RuntimeError('缺少微信支付私钥')
    appid = cfg.wechat_appid
    mchid = cfg.wechat_mchid
    serial = cfg.wechat_serial_no
    url = 'https://api.mch.weixin.qq.com/v3/pay/transactions/jsapi'
    body = json.dumps({
        'appid': appid, 'mchid': mchid,
        'description': cfg.tenant_name or '数据查询',
        'out_trade_no': order.order_no,
        'notify_url': cfg.wechat_notify_url or '',
        'amount': {'total': order.amount_fen},
        'payer': {'openid': order.openid},
    }, ensure_ascii=False)
    auth = _build_auth('POST', '/v3/pay/transactions/jsapi', body)
    import requests
    r = requests.post(url, data=body.encode('utf-8'),
                     headers={'Authorization': auth, 'Content-Type': 'application/json'}, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f'微信下单失败 {r.status_code} {r.text[:200]}')
    prepay = r.json()['prepay_id']
    order.wechat_prepay_id = prepay
    order.save(update_fields=['wechat_prepay_id'])
    return {'mock': False, 'prepay_id': prepay,
            'pay_params': _build_pay_params(prepay, key, appid)}


def verify_notify(request):
    """解析并验签微信回调。返回 (out_trade_no, ok)。"""
    if _cfg().wechat_mock:
        try:
            data = json.loads(request.body or '{}')
            return data.get('out_trade_no'), True
        except Exception:
            return None, False
    # 真实模式：用平台证书验签 + AES-GCM 解密 resource。
    # 需先下载并缓存平台证书（WECHAT_CERT_DIR），此处留待接入真实商户后实现。
    raise NotImplementedError('真实微信回调验签需配置平台证书后启用')
