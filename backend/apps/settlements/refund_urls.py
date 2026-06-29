"""退款配对 API 路由"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.settlements.views import RefundPairViewSet

router = DefaultRouter()
router.register('', RefundPairViewSet, basename='refund-pair')

urlpatterns = [
    path('', include(router.urls)),
]
