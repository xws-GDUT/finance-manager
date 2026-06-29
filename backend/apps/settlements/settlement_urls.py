"""垫付结算 API 路由"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.settlements.views import SettlementGroupViewSet

router = DefaultRouter()
router.register('', SettlementGroupViewSet, basename='settlement')

urlpatterns = [
    path('', include(router.urls)),
]
