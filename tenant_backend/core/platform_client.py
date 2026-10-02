"""平台 OpenAPI 客户端（租户侧唯一对外数据通道）。
🔴 只调平台，绝不直接连天远。
配置来自 TenantConfig（界面可热更新）；env 仅作首次兜底。
本地联调可设 platform_mock=True，返回假报告、不真正打平台（避免花钱）。
"""
import os
import logging

import requests

logger = logging.getLogger(__name__)


def _cfg():
    from console.models import TenantConfig
    return TenantConfig.get()


def _base():
    return (_cfg().platform_api_base or 'https://www.gemidaojia.com/saas/api').rstrip('/')


def _key():
    return _cfg().platform_api_key or ''


def _mock():
    return bool(_cfg().platform_mock)


def _headers():
    return {'X-Api-Key': _key(), 'Content-Type': 'application/json'}


def _fake_report(name, id_card, phone, package_id):
    return {
        'code': 0, 'message': 'ok',
        'data': {
            'query_id': 'MOCK' + os.urandom(6).hex().upper(),
            'status': 'success', 'cost': 0.0, 'cost_type': 'mock',
            'report': {
                'DWBG8B4D': {'success': True, 'data': {'riskScore': 82, 'mock': True}},
                'FLXG7E8F': {'success': True, 'data': {'cases': []}},
                'IVYZ81NC': {'success': True, 'data': {'op_type': 'INR',
                              'op_type_desc': '未查到婚姻登记', 'mock': True}},
                'QCXG9P1C': {'success': True, 'data': {'vehicleCount': 0, 'list': []}},
                'IVYZRAX1': {'success': True, 'data': {'score': 720, 'mock': True}},
            },
        },
    }


def execute_query(package_id, name, id_card, phone='', purpose='', timeout=60):
    """调平台执行一次查询（同步返回报告）。失败返回 code!=0。"""
    if _mock():
        return _fake_report(name, id_card, phone, package_id)
    try:
        r = requests.post(
            f'{_base()}/query/openapi/query/', headers=_headers(),
            json={'query_config_id': package_id, 'name': name, 'id_card': id_card,
                  'phone': phone, 'purpose': purpose}, timeout=timeout)
        try:
            return r.json()
        except Exception:
            return {'code': r.status_code, 'message': '平台返回解析失败', 'data': None}
    except requests.RequestException as e:
        logger.error('platform execute_query error: %s', e)
        return {'code': 502, 'message': f'平台调用失败: {e}', 'data': None}


def get_result(query_id, timeout=30):
    if _mock():
        return {'code': 0, 'message': 'ok',
                'data': {'query_id': query_id, 'status': 'success',
                         'report': {'DWBG8B4D': {'success': True, 'data': {'riskScore': 82, 'mock': True}}}}}
    try:
        r = requests.get(f'{_base()}/query/openapi/result/{query_id}/', headers=_headers(), timeout=timeout)
        try:
            return r.json()
        except Exception:
            return {'code': r.status_code, 'message': '平台返回解析失败', 'data': None}
    except requests.RequestException as e:
        return {'code': 502, 'message': f'平台调用失败: {e}', 'data': None}


def get_balance(timeout=30):
    if _mock():
        return {'code': 0, 'message': 'ok', 'data': {'balance': 999900, 'quota_remain': 1000}}
    try:
        r = requests.get(f'{_base()}/query/openapi/balance/', headers=_headers(), timeout=timeout)
        return r.json()
    except requests.RequestException as e:
        return {'code': 502, 'message': f'平台调用失败: {e}', 'data': None}
