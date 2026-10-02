"""租户管理后台视图：登录 / 配置（站点+支付+APIKey）/ 套餐 / 平台连通性测试。
鉴权：Django session（同源 Cookie）。所有写操作 csrf_exempt（SPA 内部后台）。
"""
import os
import json
import logging

from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import AdminUser, TenantConfig, Package, Distributor, CustUser, DistributorSettlement
from core.models import LocalOrder

logger = logging.getLogger(__name__)

CONFIG_FIELDS = [
    'tenant_name', 'logo_url', 'primary_color', 'public_base_url',
    'platform_api_base', 'platform_api_key', 'platform_mock',
    'wechat_mock', 'wechat_appid', 'wechat_mchid', 'wechat_apiv3_key',
    'wechat_serial_no', 'wechat_cert_dir', 'wechat_notify_url',
    'wechat_appsecret', 'oa_scope',
]


def _admin_user(request):
    aid = request.session.get('admin_id')
    if not aid:
        return None
    return AdminUser.objects.filter(id=aid).first()


def _deny():
    return Response({'code': 401, 'message': '未登录', 'data': None}, status=401)


@method_decorator(csrf_exempt, name='dispatch')
class AdminLoginView(APIView):
    def post(self, request):
        d = request.data or {}
        username = (d.get('username') or '').strip()
        password = d.get('password') or ''
        user = AdminUser.objects.filter(username=username).first()
        if not user or not user.verify_password(password):
            return Response({'code': 401, 'message': '用户名或密码错误', 'data': None}, status=401)
        request.session['admin_id'] = user.id
        request.session.modified = True
        return Response({'code': 0, 'message': 'ok', 'data': user.to_dict()})


@method_decorator(csrf_exempt, name='dispatch')
class AdminLogoutView(APIView):
    def post(self, request):
        request.session.flush()
        return Response({'code': 0, 'message': 'ok'})


class AdminMeView(APIView):
    def get(self, request):
        user = _admin_user(request)
        if not user:
            return _deny()
        return Response({'code': 0, 'message': 'ok', 'data': user.to_dict()})


@method_decorator(csrf_exempt, name='dispatch')
class ConfigView(APIView):
    def get(self, request):
        if not _admin_user(request):
            return _deny()
        return Response({'code': 0, 'message': 'ok', 'data': TenantConfig.get().to_dict()})

    def put(self, request):
        user = _admin_user(request)
        if not user:
            return _deny()
        c = TenantConfig.get()
        d = request.data or {}
        for f in CONFIG_FIELDS:
            if f in d:
                setattr(c, f, d[f])
        # 微信私钥：粘 PEM 文本则落盘并记路径（无需重启）
        pk = d.get('wechat_private_key')
        if pk and pk.strip():
            path = _save_private_key(c.wechat_cert_dir, pk.strip())
            if path:
                c.wechat_private_key_path = path
        c.save()
        return Response({'code': 0, 'message': 'ok', 'data': c.to_dict()})


def _save_private_key(cert_dir, pem_text):
    try:
        os.makedirs(cert_dir, exist_ok=True)
        path = os.path.join(cert_dir, 'apiclient_key.pem')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(pem_text)
            if not pem_text.endswith('\n'):
                f.write('\n')
        os.chmod(path, 0o600)
        return path
    except Exception as e:  # noqa
        logger.error('save private key failed: %s', e)
        return ''


@method_decorator(csrf_exempt, name='dispatch')
class PackageAdminView(APIView):
    def get(self, request):
        if not _admin_user(request):
            return _deny()
        items = [p.to_dict() for p in Package.objects.all()]
        return Response({'code': 0, 'message': 'ok', 'data': items})

    def post(self, request):
        user = _admin_user(request)
        if not user:
            return _deny()
        d = request.data or {}
        try:
            price_yuan = float(d.get('price_yuan') or 0)
        except (TypeError, ValueError):
            price_yuan = 0
        p = Package.objects.create(
            query_config_id=int(d.get('query_config_id') or 0),
            name=(d.get('name') or '').strip(),
            price_fen=int(round(price_yuan * 100)),
            desc=(d.get('desc') or '').strip(),
            sort=int(d.get('sort') or 0),
            enabled=bool(d.get('enabled', True)),
        )
        return Response({'code': 0, 'message': 'ok', 'data': p.to_dict()})


@method_decorator(csrf_exempt, name='dispatch')
class PackageDetailView(APIView):
    def put(self, request, pk):
        user = _admin_user(request)
        if not user:
            return _deny()
        p = Package.objects.filter(id=pk).first()
        if not p:
            return Response({'code': 404, 'message': '套餐不存在', 'data': None}, status=404)
        d = request.data or {}
        if 'query_config_id' in d:
            p.query_config_id = int(d['query_config_id'])
        if 'name' in d:
            p.name = d['name']
        if 'price_yuan' in d:
            try:
                p.price_fen = int(round(float(d['price_yuan']) * 100))
            except (TypeError, ValueError):
                pass
        if 'desc' in d:
            p.desc = d['desc']
        if 'sort' in d:
            p.sort = int(d['sort'])
        if 'enabled' in d:
            p.enabled = bool(d['enabled'])
        p.save()
        return Response({'code': 0, 'message': 'ok', 'data': p.to_dict()})

    def delete(self, request, pk):
        user = _admin_user(request)
        if not user:
            return _deny()
        Package.objects.filter(id=pk).delete()
        return Response({'code': 0, 'message': 'ok'})


@method_decorator(csrf_exempt, name='dispatch')
class TestPlatformView(APIView):
    """用当前配置的 APIKey 调平台余额接口，验证连通性与 Key 有效性。"""
    def post(self, request):
        user = _admin_user(request)
        if not user:
            return _deny()
        try:
            from core import platform_client
            res = platform_client.get_balance()
        except Exception as e:  # noqa
            logger.exception('test platform failed')
            return Response({'code': 500, 'message': f'调用失败: {e}', 'data': None}, status=500)
        return Response({'code': 0, 'message': 'ok', 'data': res})


def _paginate(qs, request, default_size=20, max_size=100):
    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        size = min(max_size, max(1, int(request.GET.get('page_size', default_size))))
    except (TypeError, ValueError):
        size = default_size
    total = qs.count()
    start = (page - 1) * size
    items = qs[start:start + size]
    pages = (total + size - 1) // size if total else 0
    return {'page': page, 'page_size': size, 'total': total, 'pages': pages}, items


# ============================ 订单管理 ============================
@method_decorator(csrf_exempt, name='dispatch')
class OrderAdminView(APIView):
    def get(self, request):
        if not _admin_user(request):
            return _deny()
        qs = LocalOrder.objects.all()
        status = request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        dist = request.GET.get('distributor_id')
        if dist:
            qs = qs.filter(distributor_id=dist)
        kw = (request.GET.get('kw') or '').strip()
        if kw:
            qs = qs.filter(Q(order_no__icontains=kw) | Q(subject_name__icontains=kw) |
                          Q(openid__icontains=kw) | Q(subject_id_card__icontains=kw))
        pg, items = _paginate(qs, request)
        return Response({'code': 0, 'message': 'ok', 'data': {
            'list': [o.to_dict() for o in items], **pg}})


class OrderDetailView(APIView):
    def get(self, request, order_no):
        if not _admin_user(request):
            return _deny()
        o = LocalOrder.objects.filter(order_no=order_no).first()
        if not o:
            return Response({'code': 404, 'message': '订单不存在', 'data': None}, status=404)
        d = o.to_dict()
        d['report'] = o.report_json
        return Response({'code': 0, 'message': 'ok', 'data': d})


@method_decorator(csrf_exempt, name='dispatch')
class OrderActionView(APIView):
    def post(self, request, order_no):
        user = _admin_user(request)
        if not user:
            return _deny()
        o = LocalOrder.objects.filter(order_no=order_no).first()
        if not o:
            return Response({'code': 404, 'message': '订单不存在', 'data': None}, status=404)
        d = request.data or {}
        action = d.get('action')
        from django.utils import timezone
        if action == 'set_remark':
            o.admin_remark = (d.get('remark') or '').strip()
            o.save(update_fields=['admin_remark'])
            return Response({'code': 0, 'message': 'ok', 'data': o.to_dict()})
        if action == 'mark_paid':
            o.status = 'paid'
            o.paid_at = timezone.now()
            o.save(update_fields=['status', 'paid_at'])
            return Response({'code': 0, 'message': 'ok', 'data': o.to_dict()})
        if action == 'mark_failed':
            o.status = 'failed'
            o.save(update_fields=['status'])
            return Response({'code': 0, 'message': 'ok', 'data': o.to_dict()})
        if action == 'refund':
            if o.refunded_at:
                return Response({'code': 400, 'message': '已退款，不可重复', 'data': None}, status=400)
            o.refunded_at = timezone.now()
            o.save(update_fields=['refunded_at'])
            if o.distributor_id and o.commission_fen:
                dist = Distributor.objects.filter(id=o.distributor_id).first()
                if dist and dist.unsettled_fen >= o.commission_fen:
                    dist.unsettled_fen -= o.commission_fen
                    dist.save(update_fields=['unsettled_fen'])
            return Response({'code': 0, 'message': '已标记退款并冲减佣金', 'data': o.to_dict()})
        if action == 'resync':
            try:
                from core.views import _run_query
                import threading
                threading.Thread(target=_run_query, args=(o.order_no,), daemon=True).start()
                return Response({'code': 0, 'message': '已触发重新查询', 'data': o.to_dict()})
            except Exception as e:  # noqa
                logger.exception('resync failed')
                return Response({'code': 500, 'message': f'触发失败: {e}', 'data': None}, status=500)
        return Response({'code': 400, 'message': '未知操作', 'data': None}, status=400)


# ============================ 分销管理 ============================
@method_decorator(csrf_exempt, name='dispatch')
class DistributorAdminView(APIView):
    def get(self, request):
        if not _admin_user(request):
            return _deny()
        qs = Distributor.objects.all()
        kw = (request.GET.get('kw') or '').strip()
        if kw:
            qs = qs.filter(Q(name__icontains=kw) | Q(code__icontains=kw) | Q(contact__icontains=kw))
        enabled = request.GET.get('enabled')
        if enabled in ('0', '1'):
            qs = qs.filter(enabled=enabled == '1')
        items = [x.to_dict() for x in qs]
        return Response({'code': 0, 'message': 'ok', 'data': items})

    def post(self, request):
        user = _admin_user(request)
        if not user:
            return _deny()
        d = request.data or {}
        code = (d.get('code') or '').strip()
        if not code:
            return Response({'code': 400, 'message': '邀请码必填', 'data': None}, status=400)
        if Distributor.objects.filter(code=code).exists():
            return Response({'code': 400, 'message': '邀请码已存在', 'data': None}, status=400)
        try:
            rate = float(d.get('rate', 0.1))
        except (TypeError, ValueError):
            rate = 0.1
        dist = Distributor.objects.create(
            code=code, name=(d.get('name') or '').strip(), contact=(d.get('contact') or '').strip(),
            rate=rate, enabled=bool(d.get('enabled', True)), note=(d.get('note') or '').strip())
        return Response({'code': 0, 'message': 'ok', 'data': dist.to_dict()})


@method_decorator(csrf_exempt, name='dispatch')
class DistributorDetailView(APIView):
    def get(self, request, pk):
        if not _admin_user(request):
            return _deny()
        dist = Distributor.objects.filter(id=pk).first()
        if not dist:
            return Response({'code': 404, 'message': '分销商不存在', 'data': None}, status=404)
        data = dist.to_dict()
        data['settlements'] = [s.to_dict() for s in dist.settlements.all()[:20]]
        data['order_count'] = LocalOrder.objects.filter(distributor_id=pk).count()
        return Response({'code': 0, 'message': 'ok', 'data': data})

    def put(self, request, pk):
        user = _admin_user(request)
        if not user:
            return _deny()
        dist = Distributor.objects.filter(id=pk).first()
        if not dist:
            return Response({'code': 404, 'message': '分销商不存在', 'data': None}, status=404)
        d = request.data or {}
        if 'code' in d and d['code'].strip() and d['code'].strip() != dist.code:
            if Distributor.objects.filter(code=d['code'].strip()).exclude(id=pk).exists():
                return Response({'code': 400, 'message': '邀请码已存在', 'data': None}, status=400)
            dist.code = d['code'].strip()
        if 'name' in d:
            dist.name = d['name']
        if 'contact' in d:
            dist.contact = d['contact']
        if 'rate' in d:
            try:
                dist.rate = float(d['rate'])
            except (TypeError, ValueError):
                pass
        if 'enabled' in d:
            dist.enabled = bool(d['enabled'])
        if 'note' in d:
            dist.note = d['note']
        dist.save()
        return Response({'code': 0, 'message': 'ok', 'data': dist.to_dict()})

    def delete(self, request, pk):
        user = _admin_user(request)
        if not user:
            return _deny()
        Distributor.objects.filter(id=pk).delete()
        return Response({'code': 0, 'message': 'ok'})


@method_decorator(csrf_exempt, name='dispatch')
class DistributorSettleView(APIView):
    def post(self, request, pk):
        user = _admin_user(request)
        if not user:
            return _deny()
        dist = Distributor.objects.filter(id=pk).first()
        if not dist:
            return Response({'code': 404, 'message': '分销商不存在', 'data': None}, status=404)
        d = request.data or {}
        try:
            amount = int(d.get('amount_fen') or 0)
        except (TypeError, ValueError):
            amount = 0
        if amount <= 0:
            amount = dist.unsettled_fen
        if amount > dist.unsettled_fen:
            amount = dist.unsettled_fen
        if amount <= 0:
            return Response({'code': 400, 'message': '无未结佣金', 'data': None}, status=400)
        dist.unsettled_fen -= amount
        dist.settled_fen += amount
        dist.save(update_fields=['unsettled_fen', 'settled_fen'])
        s = DistributorSettlement.objects.create(
            distributor=dist, amount_fen=amount,
            operator=(user.username if user else ''), note=(d.get('note') or '').strip())
        return Response({'code': 0, 'message': 'ok', 'data': {
            'distributor': dist.to_dict(), 'settlement': s.to_dict()}})


# ============================ 用户管理 ============================
@method_decorator(csrf_exempt, name='dispatch')
class CustUserAdminView(APIView):
    def get(self, request):
        if not _admin_user(request):
            return _deny()
        qs = CustUser.objects.all()
        kw = (request.GET.get('kw') or '').strip()
        if kw:
            qs = qs.filter(Q(openid__icontains=kw) | Q(nickname__icontains=kw) | Q(phone__icontains=kw))
        blocked = request.GET.get('blocked')
        if blocked in ('0', '1'):
            qs = qs.filter(is_blocked=blocked == '1')
        pg, items = _paginate(qs, request)
        return Response({'code': 0, 'message': 'ok', 'data': {
            'list': [u.to_dict() for u in items], **pg}})


class CustUserDetailView(APIView):
    def get(self, request, openid):
        if not _admin_user(request):
            return _deny()
        u = CustUser.objects.filter(openid=openid).first()
        if not u:
            return Response({'code': 404, 'message': '用户不存在', 'data': None}, status=404)
        d = u.to_dict()
        d['recent_orders'] = [o.to_dict() for o in LocalOrder.objects.filter(openid=openid)[:10]]
        return Response({'code': 0, 'message': 'ok', 'data': d})


@method_decorator(csrf_exempt, name='dispatch')
class CustUserActionView(APIView):
    def post(self, request, openid):
        user = _admin_user(request)
        if not user:
            return _deny()
        u = CustUser.objects.filter(openid=openid).first()
        if not u:
            return Response({'code': 404, 'message': '用户不存在', 'data': None}, status=404)
        d = request.data or {}
        action = d.get('action')
        if action == 'block':
            u.is_blocked = True
        elif action == 'unblock':
            u.is_blocked = False
        elif action == 'set_note':
            u.note = (d.get('note') or '').strip()
        else:
            return Response({'code': 400, 'message': '未知操作', 'data': None}, status=400)
        u.save()
        return Response({'code': 0, 'message': 'ok', 'data': u.to_dict()})
