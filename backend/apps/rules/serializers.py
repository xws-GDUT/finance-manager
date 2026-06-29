"""
规则引擎 Serializer
"""
from rest_framework import serializers
from apps.rules.models import ValidRule, InvalidRule


class RuleBaseSerializer(serializers.ModelSerializer):
    """规则基础序列化器"""
    hit_count = serializers.IntegerField(read_only=True)

    class Meta:
        abstract = True
        fields = '__all__'
        read_only_fields = ['id', 'hit_count', 'created_at', 'updated_at']


class ValidRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValidRule
        fields = '__all__'
        read_only_fields = ['id', 'hit_count', 'created_at', 'updated_at']


class InvalidRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvalidRule
        fields = '__all__'
        read_only_fields = ['id', 'hit_count', 'created_at', 'updated_at']


class RuleTestSerializer(serializers.Serializer):
    """规则测试请求"""
    sources = serializers.CharField(required=False, allow_blank=True, default='')
    directions = serializers.CharField(required=False, allow_blank=True, default='')
    trans_types = serializers.CharField(required=False, allow_blank=True, default='')
    categories = serializers.CharField(required=False, allow_blank=True, default='')
    payment_channels = serializers.CharField(required=False, allow_blank=True, default='')
    keywords = serializers.CharField(required=False, allow_blank=True, default='')
    keyword_exclude = serializers.CharField(required=False, allow_blank=True, default='')
    merchants = serializers.CharField(required=False, allow_blank=True, default='')
    counterparties = serializers.CharField(required=False, allow_blank=True, default='')
    amount_min = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    amount_max = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
