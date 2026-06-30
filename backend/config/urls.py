"""
URL 路由配置 — 对应需求文档 43 个 API 端点
"""
import os
import mimetypes
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import FileResponse, Http404


def serve_frontend_assets(request, path):
    """服务前端构建产物（JS/CSS/图片等静态资源）"""
    full = os.path.normpath(os.path.join(str(settings.STATIC_ROOT), path))
    # 安全检查：确保文件在 STATIC_ROOT 内
    if not full.startswith(str(settings.STATIC_ROOT)):
        raise Http404('Access denied')
    if not os.path.isfile(full):
        raise Http404(f'File not found: {path}')
    content_type, _ = mimetypes.guess_type(full)
    return FileResponse(open(full, 'rb'), content_type=content_type or 'application/octet-stream')


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
    path('api/categories/', include('apps.categories.urls')),

    # 账户管理（1 端点）
    path('api/accounts/', include('apps.accounts.urls')),

    # 前端静态资源（JS/CSS/图片等）
    re_path(r'^assets/(?P<path>.*)$', serve_frontend_assets, name='frontend-assets'),

    # 前端 SPA — 所有非 API/非静态资源路径返回 index.html
    re_path(r'^(?!api/|admin/|static/|assets/|media/).*$', TemplateView.as_view(
        template_name='index.html'
    )),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
