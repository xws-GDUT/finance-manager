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

# 默认规则种子数据
DEFAULT_VALID_RULES = [
    {'name': '日常消费-银行储蓄卡', 'priority': 100, 'sources': 'bocom_debit,cmb_debit', 'directions': 'expense', 'keywords': '快捷支付,网上支付,银联,转账汇款'},
    {'name': '信用卡消费', 'priority': 95, 'sources': 'cib_credit,cmb_credit', 'directions': 'expense', 'keywords': '财付通,支付宝,特约,美团'},
    {'name': '支付宝消费', 'priority': 90, 'sources': 'alipay', 'directions': 'expense'},
    {'name': '京东消费', 'priority': 85, 'sources': 'jd', 'directions': 'expense'},
    {'name': '美团消费', 'priority': 80, 'sources': 'meituan', 'directions': 'expense'},
    {'name': '抖音消费', 'priority': 75, 'sources': 'douyin', 'directions': 'expense', 'keywords': '抖音月付'},
    {'name': '微信支付消费', 'priority': 88, 'sources': 'wechat', 'directions': 'expense'},
    {'name': '工资收入', 'priority': 100, 'sources': 'bocom_debit', 'directions': 'income', 'keywords': '代发工资'},
    {'name': '汇入及退款收入', 'priority': 90, 'directions': 'income', 'keywords': '退税,退款,退票'},
    {'name': '信用卡还款记录', 'priority': 85, 'sources': 'cib_credit,cmb_credit', 'directions': 'income', 'keywords': '还款', 'is_active': False},
    {'name': '消费退款', 'priority': 80, 'directions': 'income', 'keywords': '退款,退货,退票'},
]

DEFAULT_INVALID_RULES = [
    {'name': '银行还款/白条/信贷', 'priority': 90, 'sources': 'bocom_debit,cmb_debit', 'keywords': '还款,白条,信贷,贷款,分期,信用卡还款'},
    {'name': '银行理财/证券/利息', 'priority': 90, 'sources': 'bocom_debit,cmb_debit', 'keywords': '理财,基金,证券,利息,余额宝,朝朝盈,招盈通'},
    {'name': '云闪付转账', 'priority': 85, 'sources': 'bocom_debit,cmb_debit', 'keywords': '云闪付'},
    {'name': '转账给施金变', 'priority': 80, 'sources': 'bocom_debit,cmb_debit', 'counterparties': '施金变'},
    {'name': '转账给许万森', 'priority': 80, 'sources': 'bocom_debit,cmb_debit', 'counterparties': '许万森'},
    {'name': '转账给洗不完', 'priority': 80, 'sources': 'bocom_debit,cmb_debit', 'counterparties': '洗不完'},
    {'name': '招行微信转账', 'priority': 85, 'sources': 'cmb_debit', 'keywords': '微信转账'},
    {'name': '花呗/借呗/网商贷', 'priority': 90, 'sources': 'alipay', 'keywords': '花呗,借呗,网商贷,信用借还,自动还款'},
    {'name': '理财/基金/余额宝', 'priority': 90, 'sources': 'alipay', 'keywords': '理财,基金,余额宝,蚂蚁财富,买入,赎回'},
    {'name': '转账/提现', 'priority': 85, 'sources': 'alipay', 'keywords': '转账,提现,转入,转出'},
    {'name': '信用借还', 'priority': 85, 'sources': 'alipay', 'keywords': '信用借还,借呗还款,花呗还款'},
    {'name': '白条/还款/取现', 'priority': 90, 'sources': 'jd', 'keywords': '白条,还款,取现,分期'},
    {'name': '还款/月付', 'priority': 90, 'sources': 'meituan', 'keywords': '还款,月付,分期'},
    {'name': '还款/提现', 'priority': 90, 'sources': 'wechat', 'keywords': '还款,提现,零钱提现'},
    {'name': '零钱通/理财/基金', 'priority': 90, 'sources': 'wechat', 'keywords': '零钱通,理财,基金,买入,赎回'},
    {'name': '红包/亲属卡', 'priority': 85, 'sources': 'wechat', 'keywords': '红包,亲属卡,群收款'},
    {'name': '汇入排除-内部转账', 'priority': 90, 'directions': 'income', 'counterparties': '许万森,何永丰,同花顺'},
]


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

    @action(detail=False, methods=['post'])
    def create_defaults(self, request):
        """批量创建默认有效规则（跳过已存在的同名规则）"""
        created = 0
        skipped = 0
        for rule_data in DEFAULT_VALID_RULES:
            name = rule_data['name']
            if ValidRule.objects.filter(name=name).exists():
                skipped += 1
                continue
            rule_data.setdefault('is_active', True)
            ValidRule.objects.create(**rule_data)
            created += 1
        return Response({
            'message': f'默认有效规则创建完成',
            'created': created,
            'skipped': skipped,
        })


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

    @action(detail=False, methods=['post'])
    def create_defaults(self, request):
        """批量创建默认无效规则（跳过已存在的同名规则）"""
        created = 0
        skipped = 0
        for rule_data in DEFAULT_INVALID_RULES:
            name = rule_data['name']
            if InvalidRule.objects.filter(name=name).exists():
                skipped += 1
                continue
            rule_data.setdefault('is_active', True)
            InvalidRule.objects.create(**rule_data)
            created += 1
        return Response({
            'message': f'默认无效规则创建完成',
            'created': created,
            'skipped': skipped,
        })
