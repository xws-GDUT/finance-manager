"""
退款配对 + 垫付结算 Serializer
"""
from rest_framework import serializers
from apps.settlements.models import TransactionPair, SettlementGroup, SettlementItem


class TransactionPairSerializer(serializers.ModelSerializer):
    """退款配对序列化器"""
    expense_date = serializers.DateField(source='expense_tx.trans_date', read_only=True)
    expense_amount = serializers.DecimalField(source='expense_tx.amount', max_digits=12, decimal_places=2, read_only=True)
    expense_desc = serializers.CharField(source='expense_tx.description', read_only=True)
    expense_merchant = serializers.CharField(source='expense_tx.merchant', read_only=True)

    refund_date = serializers.DateField(source='refund_tx.trans_date', read_only=True)
    refund_amount = serializers.DecimalField(source='refund_tx.amount', max_digits=12, decimal_places=2, read_only=True)
    refund_desc = serializers.CharField(source='refund_tx.description', read_only=True)
    refund_merchant = serializers.CharField(source='refund_tx.merchant', read_only=True)

    class Meta:
        model = TransactionPair
        fields = [
            'id', 'expense_tx', 'refund_tx',
            'expense_date', 'expense_amount', 'expense_desc', 'expense_merchant',
            'refund_date', 'refund_amount', 'refund_desc', 'refund_merchant',
            'match_score', 'match_method', 'match_detail',
            'created_at',
        ]


class PairCreateSerializer(serializers.Serializer):
    """手动配对请求"""
    expense_id = serializers.IntegerField()
    refund_id = serializers.IntegerField()


class AAScanSerializer(serializers.Serializer):
    """AA 扫描请求（无参数，自动扫描）"""
    pass


class AACreateSerializer(serializers.Serializer):
    """AA 创建结算请求"""
    receipt_ids = serializers.ListField(child=serializers.IntegerField())
    expense_id = serializers.IntegerField()
    group_name = serializers.CharField(max_length=100, required=False, default='AA 群收款')


class SettlementItemSerializer(serializers.ModelSerializer):
    """结算明细序列化器"""
    trans_date = serializers.DateField(source='transaction.trans_date', read_only=True)
    amount = serializers.DecimalField(source='transaction.amount', max_digits=12, decimal_places=2, read_only=True)
    description = serializers.CharField(source='transaction.description', read_only=True)
    merchant = serializers.CharField(source='transaction.merchant', read_only=True)
    direction = serializers.CharField(source='transaction.direction', read_only=True)

    class Meta:
        model = SettlementItem
        fields = ['id', 'transaction', 'item_type',
                  'trans_date', 'amount', 'description', 'merchant', 'direction',
                  'created_at']


class SettlementGroupSerializer(serializers.ModelSerializer):
    """垫付结算组序列化器"""
    items = SettlementItemSerializer(many=True, read_only=True)

    class Meta:
        model = SettlementGroup
        fields = [
            'id', 'name', 'description', 'status',
            'total_advance', 'total_reimbursement', 'net_amount',
            'virtual_tx', 'is_aa',
            'items',
            'created_at', 'updated_at',
        ]


class SettlementItemCreateSerializer(serializers.Serializer):
    """添加交易到结算组"""
    transaction_id = serializers.IntegerField()
    item_type = serializers.ChoiceField(choices=[('advance', '垫付'), ('reimbursement', '收款')])


class CandidateSearchSerializer(serializers.Serializer):
    """候选交易搜索"""
    keyword = serializers.CharField(required=False, allow_blank=True, default='')
    direction = serializers.CharField(required=False, allow_blank=True, default='')
