"""
分类管理 API
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from apps.categories.models import Category


@api_view(['GET'])
def category_list(request):
    """分类列表（树形结构）"""
    parents = Category.objects.filter(parent__isnull=True, is_active=True).order_by('sort_order', 'id')

    data = []
    for p in parents:
        children = Category.objects.filter(parent=p, is_active=True).order_by('id')
        data.append({
            'id': p.id,
            'name': p.name,
            'icon': p.icon,
            'type': p.type,
            'sort_order': p.sort_order,
            'children': [
                {
                    'id': c.id,
                    'name': c.name,
                    'icon': c.icon,
                    'type': c.type,
                }
                for c in children
            ],
        })

    return Response(data)
