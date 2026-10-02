"""租户管理后台数据模型（替代原 .env 静态配置，支持界面热更新）。
- AdminUser：后台管理员（独立账户，不用 Django User）。
- TenantConfig：单例，承接原白标/平台 OpenAPI/微信支付 全部静态项。
- Package：对客套餐列表（替代 PACKAGES_JSON）。
"""
import os

from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class AdminUser(models.Model):
    username = models.CharField(max_length=64, unique=True)
    password = models.CharField(max_length=128)  # 哈希存储
    is_superuser = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tb_admin_user'

    def set_password(self, raw):
        self.password = make_password(raw)

    def verify_password(self, raw):
        return check_password(raw, self.password)

    def to_dict(self):
        return {'username': self.username, 'is_superuser': self.is_superuser}


class TenantConfig(models.Model):
    """单例（pk=1）。首次 get() 用环境变量兜底，之后以界面保存为准。"""
    tenant_name = models.CharField(max_length=128, default='我的数据查询服务')
    logo_url = models.CharField(max_length=512, blank=True, default='')
    primary_color = models.CharField(max_length=32, default='#6C63FF')
    public_base_url = models.CharField(max_length=256, default='http://localhost:8000')

    # 平台 OpenAPI
    platform_api_base = models.CharField(max_length=256, default='https://www.gemidaojia.com/saas/api')
    platform_api_key = models.CharField(max_length=256, blank=True, default='')
    platform_mock = models.BooleanField(default=True)

    # 微信支付 APIv3（租户自己的商户号）
    wechat_mock = models.BooleanField(default=True)
    wechat_appid = models.CharField(max_length=64, blank=True, default='')
    wechat_mchid = models.CharField(max_length=64, blank=True, default='')
    wechat_apiv3_key = models.CharField(max_length=64, blank=True, default='')
    wechat_serial_no = models.CharField(max_length=64, blank=True, default='')
    wechat_private_key_path = models.CharField(max_length=512, blank=True, default='')
    wechat_cert_dir = models.CharField(max_length=512, default='/certs')
    wechat_notify_url = models.CharField(max_length=512, blank=True, default='')

    # 公众号网页授权（OAuth 获取客户 openid，用于 JSAPI 支付）
    wechat_appsecret = models.CharField(max_length=64, blank=True, default='', help_text='公众号 AppSecret（网页授权 code 换 openid 用）')
    oa_scope = models.CharField(max_length=32, default='snsapi_base', help_text='snsapi_base（静默）/ snsapi_userinfo（弹窗授权）')

    class Meta:
        db_table = 'tb_tenant_config'

    @classmethod
    def get(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        if created:
            obj.tenant_name = os.environ.get('TENANT_NAME', '我的数据查询服务')
            obj.logo_url = os.environ.get('TENANT_LOGO_URL', '')
            obj.primary_color = os.environ.get('PRIMARY_COLOR', '#6C63FF')
            obj.public_base_url = os.environ.get('PUBLIC_BASE_URL', 'http://localhost:8000')
            obj.platform_api_base = os.environ.get('PLATFORM_API_BASE', 'https://www.gemidaojia.com/saas/api')
            obj.platform_api_key = os.environ.get('PLATFORM_API_KEY', '')
            obj.platform_mock = os.environ.get('PLATFORM_MOCK', 'True') == 'True'
            obj.wechat_mock = os.environ.get('WECHAT_MOCK', 'True') == 'True'
            obj.wechat_appid = os.environ.get('WECHAT_APPID', '')
            obj.wechat_mchid = os.environ.get('WECHAT_MCHID', '')
            obj.wechat_apiv3_key = os.environ.get('WECHAT_APIV3_KEY', '')
            obj.wechat_serial_no = os.environ.get('WECHAT_SERIAL_NO', '')
            obj.wechat_private_key_path = os.environ.get('WECHAT_PRIVATE_KEY_PATH', '')
            obj.wechat_cert_dir = os.environ.get('WECHAT_CERT_DIR', '/certs')
            obj.wechat_notify_url = os.environ.get('WECHAT_NOTIFY_URL',
                                                  f"{os.environ.get('PUBLIC_BASE_URL', 'http://localhost:8000')}/api/wechat/notify")
            obj.wechat_appsecret = os.environ.get('WECHAT_APPSECRET', '')
            obj.oa_scope = os.environ.get('OA_SCOPE', 'snsapi_base')
            obj.save()
        return obj

    def to_dict(self):
        return {
            'tenant_name': self.tenant_name,
            'logo_url': self.logo_url,
            'primary_color': self.primary_color,
            'public_base_url': self.public_base_url,
            'platform_api_base': self.platform_api_base,
            'platform_api_key': self.platform_api_key,
            'platform_mock': self.platform_mock,
            'wechat_mock': self.wechat_mock,
            'wechat_appid': self.wechat_appid,
            'wechat_mchid': self.wechat_mchid,
            'wechat_apiv3_key': self.wechat_apiv3_key,
            'wechat_serial_no': self.wechat_serial_no,
            'wechat_private_key_path': self.wechat_private_key_path,
            'wechat_cert_dir': self.wechat_cert_dir,
            'wechat_notify_url': self.wechat_notify_url,
            'wechat_appsecret': self.wechat_appsecret,
            'oa_scope': self.oa_scope,
        }


class Package(models.Model):
    """对客套餐：id 对应平台 QueryConfig.id；price_fen 为租户定价（分）。"""
    query_config_id = models.IntegerField(help_text='对应平台 QueryConfig.id')
    name = models.CharField(max_length=128)
    price_fen = models.IntegerField(default=0, help_text='租户定价（分）')
    desc = models.CharField(max_length=256, blank=True, default='')
    sort = models.IntegerField(default=0)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tb_package'
        ordering = ['sort', 'id']

    def to_dict(self):
        return {
            'id': self.id,
            'query_config_id': self.query_config_id,
            'name': self.name,
            'price_fen': self.price_fen,
            'price_yuan': self.price_fen / 100.0,
            'desc': self.desc,
            'sort': self.sort,
            'enabled': self.enabled,
        }


class Distributor(models.Model):
    """分销商：持有邀请码，订单携带该码下单即按 rate 计佣金（未结→已结）。"""
    code = models.CharField(max_length=32, unique=True, help_text='邀请码（用户/链接携带）')
    name = models.CharField(max_length=128, help_text='分销商名称/渠道名')
    contact = models.CharField(max_length=128, blank=True, default='', help_text='联系方式')
    rate = models.FloatField(default=0.1, help_text='分成比例 0~1（如 0.1=10%）')
    enabled = models.BooleanField(default=True)
    unsettled_fen = models.IntegerField(default=0, help_text='未结算佣金（分）')
    settled_fen = models.IntegerField(default=0, help_text='已结算佣金（分）')
    note = models.CharField(max_length=256, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tb_distributor'
        ordering = ['-created_at']

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'contact': self.contact,
            'rate': self.rate,
            'enabled': self.enabled,
            'unsettled_fen': self.unsettled_fen,
            'unsettled_yuan': self.unsettled_fen / 100.0,
            'settled_fen': self.settled_fen,
            'settled_yuan': self.settled_fen / 100.0,
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class DistributorSettlement(models.Model):
    """分销商结算记录。"""
    distributor = models.ForeignKey(Distributor, on_delete=models.CASCADE, related_name='settlements')
    amount_fen = models.IntegerField(default=0, help_text='本次结算金额（分）')
    operator = models.CharField(max_length=64, blank=True, default='', help_text='操作人（后台管理员用户名）')
    note = models.CharField(max_length=256, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tb_distributor_settlement'
        ordering = ['-created_at']

    def to_dict(self):
        return {
            'id': self.id,
            'distributor_id': self.distributor_id,
            'amount_fen': self.amount_fen,
            'amount_yuan': self.amount_fen / 100.0,
            'operator': self.operator,
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class CustUser(models.Model):
    """C 端客户（按微信 openid 唯一标识）。下单时 upsert。"""
    openid = models.CharField(max_length=64, unique=True)
    nickname = models.CharField(max_length=128, blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    order_count = models.IntegerField(default=0)
    total_fen = models.IntegerField(default=0, help_text='累计消费（分）')
    last_order_at = models.DateTimeField(null=True, blank=True)
    is_blocked = models.BooleanField(default=False, help_text='拉黑：禁止其继续下单')
    note = models.CharField(max_length=256, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tb_cust_user'
        ordering = ['-last_order_at', '-created_at']

    def to_dict(self):
        return {
            'openid': self.openid,
            'nickname': self.nickname,
            'phone': self.phone,
            'order_count': self.order_count,
            'total_fen': self.total_fen,
            'total_yuan': self.total_fen / 100.0,
            'last_order_at': self.last_order_at.isoformat() if self.last_order_at else None,
            'is_blocked': self.is_blocked,
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
