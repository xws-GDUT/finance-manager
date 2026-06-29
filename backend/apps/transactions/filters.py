"""
交易流水 FilterSet — 支持前端多选筛选
"""
import django_filters
from apps.transactions.models import Transaction


class TransactionFilter(django_filters.FilterSet):
    """交易列表筛选器"""

    date_from = django_filters.DateFilter(field_name='trans_date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='trans_date', lookup_expr='lte')
    search = django_filters.CharFilter(method='filter_search')
    direction = django_filters.CharFilter(field_name='direction', lookup_expr='exact')
    source = django_filters.CharFilter(field_name='source', lookup_expr='exact')
    status = django_filters.CharFilter(field_name='status', lookup_expr='exact')
    category = django_filters.NumberFilter(field_name='category_id')
    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')

    # 多选筛选（逗号分隔）
    sources = django_filters.CharFilter(method='filter_multi_source')
    statuses = django_filters.CharFilter(method='filter_multi_status')
    directions = django_filters.CharFilter(method='filter_multi_direction')
    categories = django_filters.CharFilter(method='filter_multi_category')

    class Meta:
        model = Transaction
        fields = []

    def filter_search(self, queryset, name, value):
        """关键词搜索：描述 + 商户 + 对手方 + 交易类型"""
        from django.db.models import Q
        return queryset.filter(
            Q(description__icontains=value) |
            Q(merchant__icontains=value) |
            Q(counterparty__icontains=value) |
            Q(trans_type__icontains=value)
        )

    def filter_multi_source(self, queryset, name, value):
        sources = [s.strip() for s in value.split(',') if s.strip()]
        if sources:
            return queryset.filter(source__in=sources)
        return queryset

    def filter_multi_status(self, queryset, name, value):
        statuses = [s.strip() for s in value.split(',') if s.strip()]
        if statuses:
            return queryset.filter(status__in=statuses)
        return queryset

    def filter_multi_direction(self, queryset, name, value):
        directions = [d.strip() for d in value.split(',') if d.strip()]
        if directions:
            return queryset.filter(direction__in=directions)
        return queryset

    def filter_multi_category(self, queryset, name, value):
        try:
            cat_ids = [int(c.strip()) for c in value.split(',') if c.strip()]
            if cat_ids:
                return queryset.filter(category_id__in=cat_ids)
        except ValueError:
            pass
        return queryset
