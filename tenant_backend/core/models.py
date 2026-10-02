"""租户版本地订单模型（不含任何天远字段）。"""
import time
import uuid
from django.db import models


def gen_order_no():
    return 'T' + time.strftime('%Y%m%d%H%M%S') + uuid.uuid4().hex[:8].upper()


class LocalOrder(models.Model):
    STATUS_CHOICES = (
        ('unpaid', '待支付'),
        ('paid', '已支付'),
        ('querying', '查询中'),
        ('done', '已完成'),
        ('failed', '失败'),
    )
    order_no = models.CharField(max_length=36, unique=True, default=gen_order_no, editable=False)
    package_id = models.IntegerField(help_text='对应平台 QueryConfig.id')
    package_name = models.CharField(max_length=128, blank=True)
    subject_name = models.CharField(max_length=64, help_text='被查询人姓名')
    subject_id_card = models.CharField(max_length=32, help_text='身份证号')
    subject_phone = models.CharField(max_length=20, blank=True)
    purpose = models.CharField(max_length=255, blank=True, help_text='查询用途（授权书）')
    openid = models.CharField(max_length=64, blank=True, help_text='微信 openid（JSAPI 支付）')
    amount_fen = models.IntegerField(default=0, help_text='客户支付金额（分）')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='unpaid')
    platform_query_id = models.CharField(max_length=64, blank=True)
    report_json = models.JSONField(default=dict, blank=True, help_text='平台返回的报告快照')
    wechat_prepay_id = models.CharField(max_length=64, blank=True)
    err_msg = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    # —— 分销 / 后台扩展（均为可空，不破坏既有下单链路）——
    dist_code = models.CharField(max_length=32, blank=True, default='', help_text='分销商邀请码')
    distributor_id = models.IntegerField(null=True, blank=True, help_text='关联分销商主键')
    commission_fen = models.IntegerField(default=0, help_text='本单应给分销商的佣金（分）')
    refunded_at = models.DateTimeField(null=True, blank=True, help_text='退款时间')
    admin_remark = models.TextField(blank=True, default='', help_text='后台备注')

    class Meta:
        db_table = 'tb_local_order'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_no:
            self.order_no = gen_order_no()
        super().save(*args, **kwargs)

    STATUS_LABEL = {
        'unpaid': '待支付', 'paid': '已支付', 'querying': '查询中',
        'done': '已完成', 'failed': '失败',
    }

    def to_dict(self):
        return {
            'order_no': self.order_no,
            'package_id': self.package_id,
            'package_name': self.package_name,
            'subject_name': self.subject_name,
            'subject_id_card': self.subject_id_card,
            'subject_phone': self.subject_phone,
            'purpose': self.purpose,
            'openid': self.openid,
            'amount_fen': self.amount_fen,
            'amount_yuan': self.amount_fen / 100.0,
            'status': self.status,
            'status_label': self.STATUS_LABEL.get(self.status, self.status),
            'platform_query_id': self.platform_query_id,
            'has_report': bool(self.report_json),
            'wechat_prepay_id': self.wechat_prepay_id,
            'err_msg': self.err_msg,
            'dist_code': self.dist_code,
            'distributor_id': self.distributor_id,
            'commission_fen': self.commission_fen,
            'refunded_at': self.refunded_at.isoformat() if self.refunded_at else None,
            'admin_remark': self.admin_remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
        }
