"""退款配对 + 垫付结算 API 路由"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RefundPairViewSet, SettlementGroupViewSet

router = DefaultRouter()
router.register('refund-pairs', RefundPairViewSet, basename='refund-pair')
router.register('settlements', SettlementGroupViewSet, basename='settlement')

urlpatterns = [
    path('', include(router.urls)),
]
