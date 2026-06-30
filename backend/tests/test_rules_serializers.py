"""
测试 rules.serializers
"""
import pytest
from apps.rules.serializers import (
    ValidRuleSerializer, InvalidRuleSerializer, RuleTestSerializer
)
from apps.rules.models import ValidRule, InvalidRule


@pytest.mark.django_db
class TestValidRuleSerializer:
    """测试 ValidRuleSerializer"""

    def test_serialization(self):
        """序列化输出"""
        rule = ValidRule.objects.create(
            name='测试规则', priority=80, sources='alipay,wechat',
            directions='expense', keywords='餐饮,外卖'
        )
        serializer = ValidRuleSerializer(rule)
        data = serializer.data
        assert data['name'] == '测试规则'
        assert data['priority'] == 80
        assert data['sources'] == 'alipay,wechat'
        assert data['hit_count'] == 0

    def test_read_only_fields(self):
        """只读字段不可写"""
        rule = ValidRule.objects.create(name='规则', priority=50, hit_count=10)
        serializer = ValidRuleSerializer(rule, data={'hit_count': 999}, partial=True)
        assert serializer.is_valid()
        # hit_count 是只读字段，即使传入也会被忽略
        instance = serializer.save()
        assert instance.hit_count == 10

    def test_validation_required_name(self):
        """验证必填字段"""
        serializer = ValidRuleSerializer(data={'priority': 50})
        assert not serializer.is_valid()
        assert 'name' in serializer.errors


@pytest.mark.django_db
class TestInvalidRuleSerializer:
    """测试 InvalidRuleSerializer"""

    def test_serialization(self):
        """序列化输出"""
        rule = InvalidRule.objects.create(
            name='无效规则', priority=90, sources='alipay',
            keywords='还款,理财', counterparties='张三'
        )
        serializer = InvalidRuleSerializer(rule)
        data = serializer.data
        assert data['name'] == '无效规则'
        assert data['counterparties'] == '张三'
        assert data['hit_count'] == 0

    def test_read_only_fields(self):
        """只读字段"""
        rule = InvalidRule.objects.create(name='规则', priority=50)
        serializer = InvalidRuleSerializer(rule, data={'hit_count': 100}, partial=True)
        assert serializer.is_valid()
        instance = serializer.save()
        assert instance.hit_count == 0


class TestRuleTestSerializer:
    """测试 RuleTestSerializer"""

    def test_valid_empty(self):
        """空数据验证"""
        serializer = RuleTestSerializer(data={})
        assert serializer.is_valid()

    def test_with_fields(self):
        """带字段验证"""
        data = {
            'sources': 'alipay',
            'directions': 'expense',
            'keywords': '餐饮,外卖',
            'amount_min': '10.00',
            'amount_max': '100.00',
        }
        serializer = RuleTestSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['sources'] == 'alipay'

    def test_invalid_amount_type(self):
        """无效金额类型"""
        serializer = RuleTestSerializer(data={'amount_min': 'not_a_number'})
        assert not serializer.is_valid()
        assert 'amount_min' in serializer.errors
