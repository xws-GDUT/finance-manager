"""
URL 路由配置 — 对应需求文档 43 个 API 端点
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # 流水导入（2 端点）+ 导入历史（1 端点）
    path('api/import/', include('apps.imports.urls')),

    # 交易查询（5 端点）
    path('api/transactions/', include('apps.transactions.urls')),

    # 统计分析（4 端点）
    path('api/', include('apps.transactions.stats_urls')),

    # 有效规则（6 端点）
    # 无效规则（6 端点）
    path('api/', include('apps.rules.urls')),

    # 退款配对（7 端点）
    path('api/refund-pairs/', include('apps.settlements.refund_urls')),

    # 垫付结算（11 端点）
    path('api/settlements/', include('apps.settlements.settlement_urls')),

    # 分类管理（1 端点）
    path('api/categories', include('apps.categories.urls')),

    # 账户管理（1 端点）
    path('api/accounts', include('apps.accounts.urls')),

    # 前端 SPA — 所有非 API/非静态资源路径返回 index.html
    re_path(r'^(?!api/|admin/|static/|assets/|media/).*$', TemplateView.as_view(
        template_name='index.html'
    )),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static('/assets/', document_root=str(settings.STATIC_ROOT / 'assets'))

