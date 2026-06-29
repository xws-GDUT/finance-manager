"""
交易流水 Serializer
"""
import hashlib
from rest_framework import serializers
from apps.transactions.models import Transaction


class TransactionListSerializer(serializers.ModelSerializer):
    """交易列表序列化器（含关联对象展开）"""
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    category_icon = serializers.CharField(source='category.icon', read_only=True, default='')
    category_type = serializers.CharField(source='category.type', read_only=True, default='')
    account_name = serializers.CharField(source='account.name', read_only=True, default='')
    valid_rule_name = serializers.CharField(source='valid_rule.name', read_only=True, default='')
    invalid_rule_name = serializers.CharField(source='invalid_rule.name', read_only=True, default='')
    direction_display = serializers.CharField(source='get_direction_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    status_reason = serializers.SerializerMethodField()
    unique_key = serializers.CharField(required=False, allow_blank=True, default='')

    class Meta:
        model = Transaction
        fields = [
            'id', 'trans_date', 'amount', 'direction', 'direction_display',
            'source', 'source_display', 'status', 'status_display',
            'trans_type', 'description', 'merchant', 'counterparty',
            'payment_method', 'payment_channel', 'remark',
            'category', 'category_name', 'category_icon', 'category_type',
            'account', 'account_name',
            'valid_rule', 'valid_rule_name',
            'invalid_rule', 'invalid_rule_name',
            'pair', 'settlement', 'is_virtual',
            'unique_key',
            'status_reason',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_virtual',
                            'valid_rule', 'invalid_rule', 'pair', 'settlement',
                            'status_reason']

    def get_status_reason(self, obj):
        reasons = []
        if obj.is_virtual:
            reasons.append({'type': 'virtual', 'label': '虚拟交易', 'color': 'orange'})
        if obj.settlement_id:
            reasons.append({'type': 'settlement', 'label': '垫付结算', 'color': 'blue'})
        if obj.pair_id:
            reasons.append({'type': 'refund_pair', 'label': '退款配对', 'color': 'purple'})
        if obj.invalid_rule_id:
            name = obj.invalid_rule.name if obj.invalid_rule_id else ''
            reasons.append({'type': 'invalid_rule', 'label': f'无效规则: {name}', 'color': 'red'})
        if obj.valid_rule_id:
            name = obj.valid_rule.name if obj.valid_rule_id else ''
            reasons.append({'type': 'valid_rule', 'label': f'有效规则: {name}', 'color': 'green'})
        return reasons

    def create(self, validated_data):
        """创建交易时自动生成 unique_key"""
        if not validated_data.get('unique_key'):
            raw = (
                f"{validated_data.get('source', '')}|{validated_data.get('trans_date', '')}"
                f"|{validated_data.get('amount', 0)}|{validated_data.get('merchant', '')}"
                f"|{validated_data.get('description', '')[:50]}"
            )
            validated_data['unique_key'] = hashlib.md5(
                raw.encode('utf-8')
            ).hexdigest()[:16] + '_manual'
        return super().create(validated_data)


class TransactionUpdateSerializer(serializers.ModelSerializer):
    """交易更新序列化器（仅允许编辑分类和备注）"""

    class Meta:
        model = Transaction
        fields = ['category', 'remark']
