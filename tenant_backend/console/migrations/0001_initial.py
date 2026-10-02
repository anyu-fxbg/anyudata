from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='AdminUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=64, unique=True)),
                ('password', models.CharField(max_length=128)),
                ('is_superuser', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'tb_admin_user'},
        ),
        migrations.CreateModel(
            name='TenantConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenant_name', models.CharField(default='我的数据查询服务', max_length=128)),
                ('logo_url', models.CharField(blank=True, default='', max_length=512)),
                ('primary_color', models.CharField(default='#6C63FF', max_length=32)),
                ('public_base_url', models.CharField(default='http://localhost:8000', max_length=256)),
                ('platform_api_base', models.CharField(default='https://www.gemidaojia.com/saas/api', max_length=256)),
                ('platform_api_key', models.CharField(blank=True, default='', max_length=256)),
                ('platform_mock', models.BooleanField(default=True)),
                ('wechat_mock', models.BooleanField(default=True)),
                ('wechat_appid', models.CharField(blank=True, default='', max_length=64)),
                ('wechat_mchid', models.CharField(blank=True, default='', max_length=64)),
                ('wechat_apiv3_key', models.CharField(blank=True, default='', max_length=64)),
                ('wechat_serial_no', models.CharField(blank=True, default='', max_length=64)),
                ('wechat_private_key_path', models.CharField(blank=True, default='', max_length=512)),
                ('wechat_cert_dir', models.CharField(default='/certs', max_length=512)),
                ('wechat_notify_url', models.CharField(blank=True, default='', max_length=512)),
            ],
            options={'db_table': 'tb_tenant_config'},
        ),
        migrations.CreateModel(
            name='Package',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query_config_id', models.IntegerField(help_text='对应平台 QueryConfig.id')),
                ('name', models.CharField(max_length=128)),
                ('price_fen', models.IntegerField(default=0, help_text='租户定价（分）')),
                ('desc', models.CharField(blank=True, default='', max_length=256)),
                ('sort', models.IntegerField(default=0)),
                ('enabled', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'tb_package', 'ordering': ['sort', 'id']},
        ),
    ]
