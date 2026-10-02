from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('console', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Distributor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='邀请码（用户/链接携带）', max_length=32, unique=True)),
                ('name', models.CharField(help_text='分销商名称/渠道名', max_length=128)),
                ('contact', models.CharField(blank=True, default='', help_text='联系方式', max_length=128)),
                ('rate', models.FloatField(help_text='分成比例 0~1（如 0.1=10%）', default=0.1)),
                ('enabled', models.BooleanField(default=True)),
                ('unsettled_fen', models.IntegerField(default=0, help_text='未结算佣金（分）')),
                ('settled_fen', models.IntegerField(default=0, help_text='已结算佣金（分）')),
                ('note', models.CharField(blank=True, default='', max_length=256)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'tb_distributor', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='CustUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('openid', models.CharField(max_length=64, unique=True)),
                ('nickname', models.CharField(blank=True, default='', max_length=128)),
                ('phone', models.CharField(blank=True, default='', max_length=20)),
                ('order_count', models.IntegerField(default=0)),
                ('total_fen', models.IntegerField(default=0, help_text='累计消费（分）')),
                ('last_order_at', models.DateTimeField(blank=True, null=True)),
                ('is_blocked', models.BooleanField(default=False, help_text='拉黑：禁止其继续下单')),
                ('note', models.CharField(blank=True, default='', max_length=256)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'tb_cust_user', 'ordering': ['-last_order_at', '-created_at']},
        ),
        migrations.CreateModel(
            name='DistributorSettlement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_fen', models.IntegerField(default=0, help_text='本次结算金额（分）')),
                ('operator', models.CharField(blank=True, default='', help_text='操作人（后台管理员用户名）', max_length=64)),
                ('note', models.CharField(blank=True, default='', max_length=256)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('distributor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='settlements', to='console.distributor')),
            ],
            options={'db_table': 'tb_distributor_settlement', 'ordering': ['-created_at']},
        ),
    ]
