"""流水导入 API 路由"""
from django.urls import path
from .views import import_file, import_batch, import_history

urlpatterns = [
    path('upload', import_file, name='import-file'),
    path('batch', import_batch, name='import-batch'),
    path('history', import_history, name='import-history'),
]
