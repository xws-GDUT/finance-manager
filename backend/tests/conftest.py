"""
测试配置
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 在 pytest 加载前设置测试模式
os.environ['DJANGO_DEBUG'] = 'False'

django.setup()
