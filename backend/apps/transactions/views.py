"""
交易流水 API ViewSet
"""
from django.db.models import Q, Count
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.transactions.models import Transaction
from apps.transactions.serializers import TransactionListSerializer, TransactionUpdateSerializer
from apps.transactions.filters import TransactionFilter


class TransactionViewSet(viewsets.ModelViewSet):
    """交易流水 CRUD"""
    queryset = Transaction.objects.select_related(
        'category', 'account', 'valid_rule', 'invalid_rule'
    ).exclude(status='deleted')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TransactionFilter
    ordering_fields = ['trans_date', 'amount', 'created_at']
    ordering = ['-trans_date', '-id']

    def get_serializer_class(self):
        if self.action in ('update', 'partial_update'):
            return TransactionUpdateSerializer
        return TransactionListSerializer

    def perform_destroy(self, instance):
        """软删除"""
        instance.status = 'deleted'
        instance.save(update_fields=['status'])

    @action(detail=False, methods=['get'])
    def filter_values(self, request):
        """
        获取筛选字段的唯一值列表（用于前端表头多选筛选）
        """
        qs = Transaction.objects.exclude(status='deleted')

        sources = list(
            qs.values_list('source', flat=True)
            .distinct().order_by('source')
        )
        statuses = list(
            qs.values_list('status', flat=True)
            .distinct().order_by('status')
        )
        directions = list(
            qs.values_list('direction', flat=True)
            .distinct().order_by('direction')
        )
        trans_types = list(
            qs.exclude(trans_type='')
            .values_list('trans_type', flat=True)
            .distinct().order_by('trans_type')
        )

        # 分类（含子分类）
        categories = list(
            qs.select_related('category')
            .exclude(category__isnull=True)
            .values('category_id', 'category__name', 'category__icon')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        return Response({
            'sources': [
                {'value': s, 'label': dict(Transaction.SOURCE_CHOICES).get(s, s)}
                for s in sources
            ],
            'statuses': [
                {'value': s, 'label': dict(Transaction.STATUS_CHOICES).get(s, s)}
                for s in statuses
            ],
            'directions': [
                {'value': d, 'label': dict(Transaction.DIRECTION_CHOICES).get(d, d)}
                for d in directions
            ],
            'trans_types': [
                {'value': t, 'label': t} for t in trans_types[:30]
            ],
            'categories': [
                {'value': c['category_id'], 'label': f"{c['category__icon']} {c['category__name']}", 'count': c['count']}
                for c in categories
            ],
        })
