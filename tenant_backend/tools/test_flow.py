import os, sys, json, time
sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tenant_backend.settings')
import django
django.setup()
from django.test import Client

c = Client()
print('BRAND', c.get('/api/brand/').json())
print('PACKAGES', c.get('/api/packages/').json())
r = c.post('/api/order/create/', data=json.dumps({
    'package_id': 1, 'name': '张三', 'id_card': '110101199003070011',
    'phone': '13800000000', 'openid': 'oABC'}), content_type='application/json')
j = r.json()
print('CREATE', j)
assert j['code'] == 0, j
no = j['data']['order_no']
c.post('/api/order/%s/mock-pay/' % no)
rep = None
for _ in range(10):
    rep = c.get('/api/order/%s/report/' % no).json()
    if rep['data']['status'] == 'done':
        break
    time.sleep(0.5)
print('STATUS', rep['data']['status'])
print('REPORT_KEYS', list(rep['data']['report'].keys()) if rep['data']['report'] else None)
print('RESULT', 'ALL_OK' if rep['data']['status'] == 'done' else 'FAILED')
