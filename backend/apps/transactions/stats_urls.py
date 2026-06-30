"""统计分析 API 路由"""
from django.urls import path
from .stats_views import stats_overview, stats_monthly, stats_category, stats_daily

urlpatterns = [
    path('stats/overview/', stats_overview, name='stats-overview'),
    path('stats/monthly/', stats_monthly, name='stats-monthly'),
    path('stats/category/', stats_category, name='stats-category'),
    path('stats/daily/', stats_daily, name='stats-daily'),
]
