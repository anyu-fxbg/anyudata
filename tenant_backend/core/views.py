"""租户版核心视图：白标 / 套餐 / 下单 / 微信回调 / 报告。"""
import threading
import logging

from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import LocalOrder
from .platform_client import execute_query
from . import wechat_pay
from console.models import TenantConfig, Package, CustUser, Distributor

logger = logging.getLogger(__name__)


def _pkg_by_id(pid):
    return Package.objects.filter(query_config_id=pid, enabled=True).first()


class BrandView(APIView):
    """白标配置（前端读取品牌名/logo/主色）。"""
    def get(self, request):
        c = TenantConfig.get()
        return Response({'code': 0, 'message': 'ok', 'data': {
            'tenant_name': c.tenant_name,
            'logo_url': c.logo_url,
            'primary_color': c.primary_color,
            'public_base_url': c.public_base_url,
            'oauth_enabled': bool(c.wechat_appid),
        }})


class PackagesView(APIView):
    """对客套餐列表（id 对应平台 QueryConfig.id，price 为租户定价，分）。"""
    def get(self, request):
        items = [{
            'id': p.query_config_id, 'name': p.name, 'price': p.price_fen,
            'price_yuan': p.price_fen / 100.0, 'desc': p.desc,
        } for p in Package.objects.filter(enabled=True)]
        return Response({'code': 0, 'message': 'ok', 'data': items})


class OrderCreateView(APIView):
    """C 端客户下单：校验 → 建本地订单 → 调微信支付出预付单。"""
    def post(self, request):
        d = request.data
        pid = d.get('package_id')
        name = (d.get('name') or '').strip()
        id_card = (d.get('id_card') or '').strip()
        phone = (d.get('phone') or '').strip()
        purpose = (d.get('purpose') or '').strip()
        openid = (d.get('openid') or '').strip()
        nickname = (d.get('nickname') or '').strip()
        dist_code = (d.get('dist_code') or '').strip()
        if not pid or not name or not id_card:
            return Response({'code': 400, 'message': '套餐/姓名/身份证必填', 'data': None}, status=400)
        pkg = _pkg_by_id(int(pid)) if pid is not None else None
        if not pkg:
            return Response({'code': 404, 'message': '套餐不存在', 'data': None}, status=404)

        # 拉黑用户禁止下单
        if openid:
            blocked = CustUser.objects.filter(openid=openid, is_blocked=True).first()
            if blocked:
                return Response({'code': 403, 'message': '该账号已被限制下单', 'data': None}, status=403)

        order = LocalOrder.objects.create(
            package_id=int(pid), package_name=pkg.name,
            subject_name=name, subject_id_card=id_card, subject_phone=phone,
            purpose=purpose, openid=openid, amount_fen=pkg.price_fen)
        # 分销 / 用户统计（安全包裹，失败不影响下单）
        try:
            _attach_order_meta(order, dist_code, nickname)
        except Exception as e:  # noqa
            logger.exception('attach order meta failed: %s', e)
        try:
            pay = wechat_pay.create_jsapi_order(order)
        except Exception as e:
            order.status = 'failed'
            order.err_msg = str(e)
            order.save(update_fields=['status', 'err_msg'])
            logger.exception('create_jsapi_order failed')
            return Response({'code': 500, 'message': f'创建支付失败: {e}', 'data': None}, status=500)
        return Response({'code': 0, 'message': 'ok', 'data': {
            'order_no': order.order_no, 'amount_fen': order.amount_fen, 'pay': pay}})


@method_decorator(csrf_exempt, name='dispatch')
class WechatNotifyView(APIView):
    """微信支付回调：标记已支付 → 触发调平台查询（异步）。"""
    def post(self, request):
        out_trade_no, ok = wechat_pay.verify_notify(request)
        if not ok or not out_trade_no:
            return Response({'code': 'FAIL', 'message': 'verify failed'}, status=400)
        order = LocalOrder.objects.filter(order_no=out_trade_no).first()
        if not order:
            return Response({'code': 'FAIL', 'message': 'order not found'}, status=400)
        if order.status == 'unpaid':
            order.status = 'paid'
            order.paid_at = timezone.now()
            order.save(update_fields=['status', 'paid_at'])
            threading.Thread(target=_run_query, args=(order.order_no,), daemon=True).start()
        return Response({'code': 'SUCCESS', 'message': 'ok'})


@method_decorator(csrf_exempt, name='dispatch')
class MockPayView(APIView):
    """本地联调：模拟微信支付成功（仅 wechat_mock 模式可用，不接真实微信）。"""
    def post(self, request, order_no):
        if not TenantConfig.get().wechat_mock:
            return Response({'code': 403, 'message': '仅 MOCK 模式可用'}, status=403)
        order = LocalOrder.objects.filter(order_no=order_no).first()
        if not order:
            return Response({'code': 404, 'message': '订单不存在'}, status=404)
        order.status = 'paid'
        order.paid_at = timezone.now()
        order.save(update_fields=['status', 'paid_at'])
        threading.Thread(target=_run_query, args=(order.order_no,), daemon=True).start()
        return Response({'code': 0, 'message': 'mock paid', 'data': {'order_no': order_no}})


class OrderReportView(APIView):
    """按订单号取报告（客户报告页轮询/加载）。"""
    def get(self, request, order_no):
        order = LocalOrder.objects.filter(order_no=order_no).first()
        if not order:
            return Response({'code': 404, 'message': '订单不存在', 'data': None}, status=404)
        if order.status != 'done':
            return Response({'code': 0, 'message': 'ok', 'data': {'status': order.status, 'report': None}})
        return Response({'code': 0, 'message': 'ok', 'data': {
            'status': order.status, 'subject_name': order.subject_name,
            'subject_id_card': order.subject_id_card, 'report': order.report_json}})


def _attach_order_meta(order, dist_code, nickname):
    """下单后：upsert C 端用户 + 按邀请码记分销商佣金（不可影响主下单流程）。"""
    now = timezone.now()
    # 1) C 端用户统计
    if order.openid:
        u, created = CustUser.objects.get_or_create(
            openid=order.openid,
            defaults={'nickname': nickname, 'phone': order.subject_phone or '',
                      'order_count': 1, 'total_fen': order.amount_fen})
        if not created:
            if nickname:
                u.nickname = nickname
            if order.subject_phone:
                u.phone = order.subject_phone
            u.order_count = (u.order_count or 0) + 1
            u.total_fen = (u.total_fen or 0) + order.amount_fen
        u.last_order_at = now
        u.save()

    # 2) 分销商佣金
    if dist_code and order.amount_fen > 0:
        dist = Distributor.objects.filter(code=dist_code, enabled=True).first()
        if dist:
            commission = int(round(order.amount_fen * float(dist.rate or 0)))
            if commission > 0:
                order.dist_code = dist_code
                order.distributor_id = dist.id
                order.commission_fen = commission
                order.save(update_fields=['dist_code', 'distributor_id', 'commission_fen'])
                dist.unsettled_fen = (dist.unsettled_fen or 0) + commission
                dist.save(update_fields=['unsettled_fen'])


def _run_query(order_no):
    """异步：支付成功后调平台查询，落库报告。"""
    from django.db import close_old_connections
    try:
        order = LocalOrder.objects.get(order_no=order_no)
        order.status = 'querying'
        order.save(update_fields=['status'])
        res = execute_query(order.package_id, order.subject_name,
                            order.subject_id_card, order.subject_phone, order.purpose)
        if res.get('code') == 0 and res.get('data'):
            order.platform_query_id = res['data'].get('query_id', '')
            order.report_json = res['data'].get('report', {})
            order.status = 'done'
        else:
            order.status = 'failed'
            order.err_msg = str(res.get('message', '查询失败'))
        order.save(update_fields=['platform_query_id', 'report_json', 'status', 'err_msg'])
    except Exception as e:  # noqa
        try:
            order = LocalOrder.objects.get(order_no=order_no)
            order.status = 'failed'
            order.err_msg = str(e)
            order.save(update_fields=['status', 'err_msg'])
        except Exception:
            pass
    finally:
        close_old_connections()


# ===================== 公众号网页授权（OAuth）=====================
def _safe_redirect(target, cfg, request):
    """仅允许回跳到已配置的对外域名或当前站点的主机，防开放重定向。"""
    from urllib.parse import urlparse
    try:
        p = urlparse(target)
    except Exception:  # noqa
        return False
    if p.scheme not in ('http', 'https') or not p.netloc:
        return False
    allowed = set()
    if cfg.public_base_url:
        allowed.add(urlparse(cfg.public_base_url).netloc)
    try:
        allowed.add(request.get_host())
    except Exception:  # noqa
        pass
    return p.netloc in allowed


def _exchange_oauth_code(appid, secret, code):
    """用授权 code 换 openid（snsapi_base 仅返回 openid）。失败返回 None。"""
    if not appid or not secret or not code:
        return None
    try:
        import requests
        r = requests.get(
            'https://api.weixin.qq.com/sns/oauth2/access_token',
            params={'appid': appid, 'secret': secret, 'code': code,
                    'grant_type': 'authorization_code'},
            timeout=10,
        )
        data = r.json()
        if data.get('openid'):
            return data['openid']
        logger.warning('oauth exchange no openid: %s', data)
        return None
    except Exception as e:  # noqa
        logger.exception('oauth exchange failed: %s', e)
        return None


class WechatOauthStartView(APIView):
    """C 端发起网页授权：返回微信 authorize 跳转地址。redirect=授权后回跳的前端地址。"""
    def get(self, request):
        c = TenantConfig.get()
        if not c.wechat_appid:
            return Response({'code': 1, 'message': '未配置公众号 AppID（请在「公众号设置 / 支付设置」填写）', 'data': None})
        redirect = (request.GET.get('redirect') or '').strip() or (c.public_base_url.rstrip('/') + '/')
        if not _safe_redirect(redirect, c, request):
            return Response({'code': 1, 'message': 'redirect 域名不合法', 'data': None})
        callback = (c.public_base_url.rstrip('/') + '/api/wechat/oauth/callback/') \
            if c.public_base_url else request.build_absolute_uri('/api/wechat/oauth/callback/')
        scope = c.oa_scope or 'snsapi_base'
        from urllib.parse import urlencode
        params = {
            'appid': c.wechat_appid,
            'redirect_uri': callback,
            'response_type': 'code',
            'scope': scope,
            'state': redirect,
        }
        url = 'https://open.weixin.qq.com/connect/oauth2/authorize?' + urlencode(params) + '#wechat_redirect'
        return Response({'code': 0, 'message': 'ok', 'data': {'url': url}})


class WechatOauthCallbackView(APIView):
    """微信授权回跳：用 code 换 openid，再 302 回跳前端并带上 openid（或 oauth_error）。"""
    def get(self, request):
        code = request.GET.get('code')
        state = (request.GET.get('state') or '/').strip() or '/'
        c = TenantConfig.get()
        if not code:
            return self._redirect(state, c, request, error='1')
        openid = _exchange_oauth_code(c.wechat_appid, c.wechat_appsecret, code)
        if not openid:
            return self._redirect(state, c, request, error='1')
        return self._redirect(state, c, request, openid=openid)

    def _redirect(self, state, cfg, request, openid=None, error=None):
        if not _safe_redirect(state, cfg, request):
            state = '/'
        sep = '&' if '?' in state else '?'
        if openid:
            tail = f'{sep}openid={openid}'
        else:
            tail = f'{sep}oauth_error={error or "1"}'
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(state + tail)
