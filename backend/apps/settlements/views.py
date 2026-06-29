"""
退款配对 + 垫付结算 API ViewSet
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from apps.settlements.models import TransactionPair, SettlementGroup, SettlementItem
from apps.settlements.serializers import (
    TransactionPairSerializer, PairCreateSerializer,
    AAScanSerializer, AACreateSerializer,
    SettlementGroupSerializer, SettlementItemCreateSerializer,
    CandidateSearchSerializer,
)
from apps.transactions.models import Transaction
from apps.categories.models import Category
from apps.imports.refund_pair import RefundPairEngine
from apps.imports.settlement import SettlementEngine, AAScanner


class RefundPairViewSet(viewsets.ModelViewSet):
    """退款配对管理"""
    queryset = TransactionPair.objects.select_related(
        'expense_tx', 'refund_tx'
    ).all()
    serializer_class = TransactionPairSerializer

    def get_queryset(self):
        return self.queryset

    @action(detail=False, methods=['post'])
    def auto(self, request):
        """自动退款配对"""
        engine = RefundPairEngine(TransactionPair, Transaction)
        result = engine.auto_pair()
        return Response(result)

    @action(detail=False, methods=['post'])
    def manual_pair(self, request):
        """手动创建配对（使用 POST /api/settlements/refund-pairs/ 创建）"""
        return self.create(request)

    def create(self, request, *args, **kwargs):
        """创建手动配对"""
        serializer = PairCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        engine = RefundPairEngine(TransactionPair, Transaction)
        result = engine.manual_pair(
            serializer.validated_data['expense_id'],
            serializer.validated_data['refund_id'],
        )
        if result is None:
            return Response({'error': '配对失败，请检查交易是否存在'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """解除配对"""
        engine = RefundPairEngine(TransactionPair, Transaction)
        success = engine.unpair(int(kwargs['pk']))
        if not success:
            return Response({'error': '配对不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'message': '配对已解除'})

    @action(detail=False, methods=['get'])
    def aa_scan(self, request):
        """AA 群收款扫描"""
        scanner = AAScanner(Transaction)
        results = scanner.scan()
        return Response(results)

    @action(detail=False, methods=['post'])
    def aa_create(self, request):
        """一键创建 AA 结算组"""
        serializer = AACreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        engine = SettlementEngine(SettlementGroup, SettlementItem, Transaction, Category)

        # 创建结算组
        group_id = engine.create_group(
            name=data.get('group_name', 'AA 群收款'),
            description='自动创建的 AA 结算',
            is_aa=True,
        )

        # 添加垫付消费
        engine.add_item(group_id, data['expense_id'], 'advance')

        # 添加群收款
        for rid in data['receipt_ids']:
            engine.add_item(group_id, rid, 'reimbursement')

        # 关闭结算
        virtual_tx_id = engine.close(group_id)

        group = SettlementGroup.objects.get(id=group_id)
        return Response(SettlementGroupSerializer(group).data, status=status.HTTP_201_CREATED)


class SettlementGroupViewSet(viewsets.ModelViewSet):
    """垫付结算组管理"""
    queryset = SettlementGroup.objects.prefetch_related(
        'items__transaction'
    ).all()
    serializer_class = SettlementGroupSerializer

    def create(self, request, *args, **kwargs):
        """创建结算组"""
        name = request.data.get('name', '')
        description = request.data.get('description', '')
        if not name:
            return Response({'error': '名称不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        engine = SettlementEngine(SettlementGroup, SettlementItem, Transaction, Category)
        group_id = engine.create_group(name, description)
        group = SettlementGroup.objects.get(id=group_id)
        return Response(SettlementGroupSerializer(group).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """获取结算组明细"""
        group = self.get_object()
        return Response(SettlementGroupSerializer(group).data)

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """添加交易到结算组"""
        serializer = SettlementItemCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        engine = SettlementEngine(SettlementGroup, SettlementItem, Transaction, Category)
        success = engine.add_item(
            int(pk),
            serializer.validated_data['transaction_id'],
            serializer.validated_data['item_type'],
        )
        if not success:
            return Response({'error': '添加失败'}, status=status.HTTP_400_BAD_REQUEST)

        group = SettlementGroup.objects.get(id=pk)
        return Response(SettlementGroupSerializer(group).data)

    @action(detail=True, methods=['delete'], url_path='items/(?P<item_id>[^/.]+)')
    def remove_item(self, request, pk=None, item_id=None):
        """移除结算明细"""
        engine = SettlementEngine(SettlementGroup, SettlementItem, Transaction, Category)
        success = engine.remove_item(int(pk), int(item_id))
        if not success:
            return Response({'error': '移除失败'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': '已移除'})

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """关闭结算"""
        engine = SettlementEngine(SettlementGroup, SettlementItem, Transaction, Category)
        virtual_tx_id = engine.close(int(pk))
        if virtual_tx_id is None:
            return Response({'error': '关闭失败'}, status=status.HTTP_400_BAD_REQUEST)

        group = SettlementGroup.objects.get(id=pk)
        return Response({
            'message': '结算已关闭',
            'virtual_tx_id': virtual_tx_id,
            'group': SettlementGroupSerializer(group).data,
        })

    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        """重开结算"""
        engine = SettlementEngine(SettlementGroup, SettlementItem, Transaction, Category)
        success = engine.reopen(int(pk))
        if not success:
            return Response({'error': '重开失败'}, status=status.HTTP_400_BAD_REQUEST)

        group = SettlementGroup.objects.get(id=pk)
        return Response({
            'message': '结算已重开',
            'group': SettlementGroupSerializer(group).data,
        })

    @action(detail=False, methods=['get'])
    def candidates(self, request):
        """搜索候选交易"""
        serializer = CandidateSearchSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        engine = SettlementEngine(SettlementGroup, SettlementItem, Transaction, Category)
        results = engine.search_candidates(
            serializer.validated_data.get('keyword', ''),
            serializer.validated_data.get('direction') or None,
        )
        return Response(results)
