#!/usr/bin/env python
"""租户版后端入口（独立部署，绝不包含天远凭证）。"""
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tenant_backend.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
