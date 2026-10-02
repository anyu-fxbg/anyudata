"""初始化租户实例：创建后台管理员 + 写配置 + 导入套餐。

用法：
    python manage.py init_tenant
    ADMIN_PASSWORD=xxx python manage.py init_tenant

- 管理员：用户名 admin，密码取 ADMIN_PASSWORD（默认 123456，务必上线前修改）。
- 配置：用 .env 环境变量覆盖 TenantConfig 单例（仅首次/缺值时）。
- 套餐：若 tb_package 为空，且存在 PACKAGES_JSON 环境变量，则导入。
"""
import os
import json

from django.core.management.base import BaseCommand
from django.db import transaction

from console.models import AdminUser, TenantConfig, Package


class Command(BaseCommand):
    help = '初始化租户后台：管理员 + 配置 + 套餐'

    def handle(self, *args, **options):
        self._init_admin()
        self._init_config()
        self._init_packages()
        self.stdout.write(self.style.SUCCESS('租户初始化完成'))

    def _init_admin(self):
        pw = os.environ.get('ADMIN_PASSWORD', '123456')
        user, created = AdminUser.objects.get_or_create(
            username='admin', defaults={'is_superuser': True})
        user.set_password(pw)
        user.save(update_fields=['password'])
        self.stdout.write(f'管理员账号 admin ({"新建" if created else "已存在，密码已重置"})')

    def _init_config(self):
        c = TenantConfig.get()
        # 仅用环境变量补充“空值”字段，避免覆盖界面已保存的配置
        updates = {}
        mapping = {
            'tenant_name': 'TENANT_NAME', 'logo_url': 'TENANT_LOGO_URL',
            'primary_color': 'PRIMARY_COLOR', 'public_base_url': 'PUBLIC_BASE_URL',
            'platform_api_base': 'PLATFORM_API_BASE', 'platform_api_key': 'PLATFORM_API_KEY',
            'wechat_appid': 'WECHAT_APPID', 'wechat_mchid': 'WECHAT_MCHID',
            'wechat_apiv3_key': 'WECHAT_APIV3_KEY', 'wechat_serial_no': 'WECHAT_SERIAL_NO',
            'wechat_private_key_path': 'WECHAT_PRIVATE_KEY_PATH',
            'wechat_cert_dir': 'WECHAT_CERT_DIR', 'wechat_notify_url': 'WECHAT_NOTIFY_URL',
        }
        for field, env in mapping.items():
            val = os.environ.get(env)
            if val and not getattr(c, field):
                updates[field] = val
        if os.environ.get('PLATFORM_MOCK') and not c.platform_mock:
            pass
        if updates:
            for k, v in updates.items():
                setattr(c, k, v)
            c.save(update_fields=list(updates.keys()))
        self.stdout.write('配置已就绪')

    def _init_packages(self):
        if Package.objects.exists():
            self.stdout.write('套餐已存在，跳过导入')
            return
        raw = os.environ.get('PACKAGES_JSON')
        if not raw:
            self.stdout.write('未配置 PACKAGES_JSON，跳过套餐导入')
            return
        try:
            data = json.loads(raw)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'PACKAGES_JSON 解析失败: {e}'))
            return
        with transaction.atomic():
            for i, p in enumerate(data):
                Package.objects.create(
                    query_config_id=int(p.get('id', 0)),
                    name=p.get('name', f'套餐{i+1}'),
                    price_fen=int(p.get('price', 0)),
                    desc=p.get('desc', ''),
                    sort=i,
                    enabled=True,
                )
        self.stdout.write(self.style.SUCCESS(f'已导入 {len(data)} 个套餐'))
