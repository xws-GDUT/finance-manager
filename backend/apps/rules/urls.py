"""规则引擎 API 路由"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.rules.views import ValidRuleViewSet, InvalidRuleViewSet

router = DefaultRouter()
router.register('valid-rules', ValidRuleViewSet, basename='valid-rule')
router.register('invalid-rules', InvalidRuleViewSet, basename='invalid-rule')

urlpatterns = [
    path('', include(router.urls)),
]
