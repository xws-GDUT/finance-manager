"""
规则引擎 API ViewSet — 有效规则 + 无效规则
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.rules.models import ValidRule, InvalidRule
from apps.rules.serializers import (
    ValidRuleSerializer, InvalidRuleSerializer, RuleTestSerializer
)
from apps.categories.models import Category
from apps.imports.valid_engine import ValidRuleEngine
from apps.imports.invalid_engine import InvalidRuleEngine


class ValidRuleViewSet(viewsets.ModelViewSet):
    """有效规则 CRUD"""
    queryset = ValidRule.objects.all()
    serializer_class = ValidRuleSerializer
    pagination_class = None  # 规则数据量小，不需要分页

    @action(detail=False, methods=['post'])
    def apply(self, request):
        """重新应用所有有效规则"""
        engine = ValidRuleEngine(ValidRule, Category)
        matched, total = engine.apply_all()
        return Response({
            'message': f'有效规则已重新应用',
            'matched': matched,
            'total': total,
        })

    @action(detail=False, methods=['post'])
    def test(self, request):
        """测试规则匹配"""
        serializer = RuleTestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        engine = ValidRuleEngine(ValidRule, Category)
        count = engine.test_rule(serializer.validated_data)
        return Response({'matched_count': count})


class InvalidRuleViewSet(viewsets.ModelViewSet):
    """无效规则 CRUD"""
    queryset = InvalidRule.objects.all()
    serializer_class = InvalidRuleSerializer
    pagination_class = None  # 规则数据量小，不需要分页

    @action(detail=False, methods=['post'])
    def apply(self, request):
        """重新应用所有无效规则"""
        engine = InvalidRuleEngine(InvalidRule, Category)
        matched, total = engine.apply_all()
        return Response({
            'message': f'无效规则已重新应用',
            'matched': matched,
            'total': total,
        })

    @action(detail=False, methods=['post'])
    def test(self, request):
        """测试规则匹配"""
        serializer = RuleTestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        engine = InvalidRuleEngine(InvalidRule, Category)
        count = engine.test_rule(serializer.validated_data)
        return Response({'matched_count': count})
