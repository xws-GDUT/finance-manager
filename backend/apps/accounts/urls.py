"""账户管理 API 路由"""
from django.urls import path
from .views import account_list

urlpatterns = [
    path('', account_list, name='account-list'),
]
