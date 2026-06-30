"""
测试 ValidRuleEngine 有效规则引擎（白名单）
"""
import pytest
from unittest.mock import MagicMock, PropertyMock, patch
from decimal import Decimal
from apps.imports.valid_engine import ValidRuleEngine


class TestMatchList:
    """测试 _match_list 静态方法（精确匹配）"""

    def test_exact_match(self):
        """测试精确匹配"""
        assert ValidRuleEngine._match_list('alipay', 'alipay,wechat,bocom_debit') is True

    def test_no_match(self):
        """测试不匹配"""
        assert ValidRuleEngine._match_list('douyin', 'alipay,wechat') is False

    def test_empty_value(self):
        """测试空值返回False"""
        assert ValidRuleEngine._match_list('', 'alipay,wechat') is False

    def test_empty_value_none(self):
        """测试None值返回False"""
        assert ValidRuleEngine._match_list(None, 'alipay,wechat') is False

    def test_whitespace_handling(self):
        """测试逗号分隔值的空格处理"""
        assert ValidRuleEngine._match_list('alipay', ' alipay , wechat ') is True

    def test_empty_rule_field_parts_filtered(self):
        """测试空规则字段部分被过滤"""
        assert ValidRuleEngine._match_list('alipay', 'alipay,,wechat') is True

    def test_single_value_in_list(self):
        """测试列表中只有一个值"""
        assert ValidRuleEngine._match_list('alipay', 'alipay') is True


class TestMatchListContains:
    """测试 _match_list_contains 静态方法（子串匹配）"""

    def test_contains_match(self):
        """测试包含匹配"""
        assert ValidRuleEngine._match_list_contains('快捷支付', '支付,转账') is True

    def test_not_contains(self):
        """测试不包含"""
        assert ValidRuleEngine._match_list_contains('取款', '支付,转账') is False

    def test_empty_value(self):
        """测试空值返回False"""
        assert ValidRuleEngine._match_list_contains('', '支付,转账') is False

    def test_empty_value_none(self):
        """测试None值返回False"""
        assert ValidRuleEngine._match_list_contains(None, '支付,转账') is False

    def test_partial_substring(self):
        """测试部分子串匹配"""
        # '付' 在 '支付' 中
        assert ValidRuleEngine._match_list_contains('支付', '付') is True

    def test_multiple_keywords_one_matches(self):
        """测试多个关键词中有一个匹配"""
        assert ValidRuleEngine._match_list_contains('美团外卖', '饿了么,外卖,星巴克') is True

    def test_whitespace_handling(self):
        """测试逗号分隔值的空格处理"""
        assert ValidRuleEngine._match_list_contains('支付宝支付', ' 支付宝 , 微信 ') is True


class TestMatchRule:
    """测试 _match_rule 方法（10个条件的AND逻辑）"""

    @pytest.fixture
    def engine(self):
        """创建 ValidRuleEngine 实例"""
        mock_valid_rule = MagicMock()
        mock_category = MagicMock()
        return ValidRuleEngine(mock_valid_rule, mock_category)

    def make_rule(self, **kwargs):
        """创建mock规则对象"""
        rule = MagicMock()
        defaults = {
            'sources': '',
            'directions': '',
            'trans_types': '',
            'categories': '',
            'payment_channels': '',
            'keywords': '',
            'keyword_exclude': '',
            'merchants': '',
            'amount_min': None,
            'amount_max': None,
        }
        defaults.update(kwargs)
        for key, val in defaults.items():
            setattr(rule, key, val)
        return rule

    def make_tx(self, **kwargs):
        """创建mock交易对象"""
        tx = MagicMock()
        defaults = {
            'source': 'alipay',
            'direction': 'expense',
            'trans_type': '快捷支付',
            'description': '午餐消费',
            'merchant': '海底捞',
            'counterparty': '海底捞',
            'payment_channel': '支付宝',
            'amount': Decimal('100'),
        }
        defaults.update(kwargs)
        for key, val in defaults.items():
            setattr(tx, key, val)
        # category 需要特殊处理
        if 'category' in defaults:
            tx.category = defaults['category']
        else:
            tx.category = None
        return tx

    # ── sources 条件 ─────────────────────────────────

    def test_sources_match(self, engine):
        """测试 sources 匹配"""
        rule = self.make_rule(sources='alipay,wechat')
        tx = self.make_tx(source='alipay')
        assert engine._match_rule(rule, tx) is True

    def test_sources_no_match(self, engine):
        """测试 sources 不匹配"""
        rule = self.make_rule(sources='wechat')
        tx = self.make_tx(source='alipay')
        assert engine._match_rule(rule, tx) is False

    def test_sources_empty_matches_all(self, engine):
        """测试 sources 为空匹配所有"""
        rule = self.make_rule(sources='')
        tx = self.make_tx(source='alipay')
        assert engine._match_rule(rule, tx) is True

    # ── directions 条件 ──────────────────────────────

    def test_directions_match(self, engine):
        """测试 directions 匹配"""
        rule = self.make_rule(directions='expense')
        tx = self.make_tx(direction='expense')
        assert engine._match_rule(rule, tx) is True

    def test_directions_no_match(self, engine):
        """测试 directions 不匹配"""
        rule = self.make_rule(directions='expense')
        tx = self.make_tx(direction='income')
        assert engine._match_rule(rule, tx) is False

    def test_directions_empty_matches_all(self, engine):
        """测试 directions 为空匹配所有"""
        rule = self.make_rule(directions='')
        tx = self.make_tx(direction='income')
        assert engine._match_rule(rule, tx) is True

    # ── trans_types 条件 ─────────────────────────────

    def test_trans_types_match(self, engine):
        """测试 trans_types 匹配"""
        rule = self.make_rule(trans_types='支付,转账')
        tx = self.make_tx(trans_type='快捷支付')
        assert engine._match_rule(rule, tx) is True

    def test_trans_types_no_match(self, engine):
        """测试 trans_types 不匹配"""
        rule = self.make_rule(trans_types='取款,转账')
        tx = self.make_tx(trans_type='快捷支付')
        assert engine._match_rule(rule, tx) is False

    def test_trans_types_empty_matches_all(self, engine):
        """测试 trans_types 为空匹配所有"""
        rule = self.make_rule(trans_types='')
        tx = self.make_tx(trans_type='任何类型')
        assert engine._match_rule(rule, tx) is True

    # ── categories 条件 ──────────────────────────────

    def test_categories_match(self, engine):
        """测试 categories 匹配"""
        rule = self.make_rule(categories='餐饮,交通')
        cat = MagicMock()
        cat.name = '餐饮美食'
        tx = self.make_tx(category=cat)
        assert engine._match_rule(rule, tx) is True

    def test_categories_no_match(self, engine):
        """测试 categories 不匹配"""
        rule = self.make_rule(categories='交通')
        cat = MagicMock()
        cat.name = '餐饮美食'
        tx = self.make_tx(category=cat)
        assert engine._match_rule(rule, tx) is False

    def test_categories_no_category_on_tx(self, engine):
        """测试交易无分类时跳过分类检查"""
        rule = self.make_rule(categories='餐饮')
        tx = self.make_tx(category=None)
        # 没有分类时，categories 条件不生效
        assert engine._match_rule(rule, tx) is True

    def test_categories_empty_matches_all(self, engine):
        """测试 categories 为空匹配所有"""
        rule = self.make_rule(categories='')
        cat = MagicMock()
        cat.name = '餐饮美食'
        tx = self.make_tx(category=cat)
        assert engine._match_rule(rule, tx) is True

    # ── payment_channels 条件 ────────────────────────

    def test_payment_channels_match(self, engine):
        """测试 payment_channels 匹配"""
        rule = self.make_rule(payment_channels='支付宝,微信')
        tx = self.make_tx(payment_channel='支付宝')
        assert engine._match_rule(rule, tx) is True

    def test_payment_channels_no_match(self, engine):
        """测试 payment_channels 不匹配"""
        rule = self.make_rule(payment_channels='微信支付')
        tx = self.make_tx(payment_channel='支付宝')
        assert engine._match_rule(rule, tx) is False

    def test_payment_channels_empty_matches_all(self, engine):
        """测试 payment_channels 为空匹配所有"""
        rule = self.make_rule(payment_channels='')
        tx = self.make_tx(payment_channel='任何渠道')
        assert engine._match_rule(rule, tx) is True

    # ── keywords 条件 ────────────────────────────────

    def test_keywords_match(self, engine):
        """测试 keywords 匹配（搜索范围含 payment_channel）"""
        rule = self.make_rule(keywords='外卖,星巴克')
        tx = self.make_tx(description='美团外卖', merchant='美团', trans_type='餐饮',
                          counterparty='美团', payment_channel='支付宝')
        assert engine._match_rule(rule, tx) is True

    def test_keywords_match_in_payment_channel(self, engine):
        """测试 keywords 在 payment_channel 中匹配"""
        rule = self.make_rule(keywords='支付宝')
        tx = self.make_tx(description='消费', merchant='商户', trans_type='支付',
                          counterparty='', payment_channel='支付宝支付')
        assert engine._match_rule(rule, tx) is True

    def test_keywords_no_match(self, engine):
        """测试 keywords 不匹配"""
        rule = self.make_rule(keywords='星巴克')
        tx = self.make_tx(description='美团外卖', merchant='美团', trans_type='餐饮',
                          counterparty='美团', payment_channel='支付宝')
        assert engine._match_rule(rule, tx) is False

    def test_keywords_empty_matches_all(self, engine):
        """测试 keywords 为空匹配所有"""
        rule = self.make_rule(keywords='')
        tx = self.make_tx()
        assert engine._match_rule(rule, tx) is True

    # ── keyword_exclude 条件 ─────────────────────────

    def test_keyword_exclude_triggers_exclusion(self, engine):
        """测试 keyword_exclude 命中则排除"""
        rule = self.make_rule(keyword_exclude='还款,转账')
        tx = self.make_tx(description='信用卡还款', merchant='银行', trans_type='还款',
                          counterparty='银行')
        assert engine._match_rule(rule, tx) is False

    def test_keyword_exclude_no_match(self, engine):
        """测试 keyword_exclude 未命中"""
        rule = self.make_rule(keyword_exclude='还款,转账')
        tx = self.make_tx(description='午餐', merchant='海底捞', trans_type='餐饮',
                          counterparty='海底捞')
        assert engine._match_rule(rule, tx) is True

    def test_keyword_exclude_not_search_payment_channel(self, engine):
        """测试 keyword_exclude 不搜索 payment_channel"""
        rule = self.make_rule(keyword_exclude='支付宝')
        tx = self.make_tx(description='消费', merchant='商户', trans_type='支付',
                          counterparty='', payment_channel='支付宝')
        # '支付宝' 只在 payment_channel 中，不应被 keyword_exclude 匹配
        assert engine._match_rule(rule, tx) is True

    def test_keyword_exclude_empty_matches_all(self, engine):
        """测试 keyword_exclude 为空匹配所有"""
        rule = self.make_rule(keyword_exclude='')
        tx = self.make_tx()
        assert engine._match_rule(rule, tx) is True

    # ── merchants 条件 ───────────────────────────────

    def test_merchants_match(self, engine):
        """测试 merchants 匹配"""
        rule = self.make_rule(merchants='海底捞,星巴克')
        tx = self.make_tx(merchant='海底捞火锅')
        assert engine._match_rule(rule, tx) is True

    def test_merchants_no_match(self, engine):
        """测试 merchants 不匹配"""
        rule = self.make_rule(merchants='星巴克')
        tx = self.make_tx(merchant='海底捞')
        assert engine._match_rule(rule, tx) is False

    def test_merchants_empty_matches_all(self, engine):
        """测试 merchants 为空匹配所有"""
        rule = self.make_rule(merchants='')
        tx = self.make_tx()
        assert engine._match_rule(rule, tx) is True

    # ── amount_min/max 条件 ──────────────────────────

    def test_amount_min_pass(self, engine):
        """测试 amount_min 通过"""
        rule = self.make_rule(amount_min=Decimal('50'))
        tx = self.make_tx(amount=Decimal('100'))
        assert engine._match_rule(rule, tx) is True

    def test_amount_min_fail(self, engine):
        """测试 amount_min 不通过"""
        rule = self.make_rule(amount_min=Decimal('50'))
        tx = self.make_tx(amount=Decimal('30'))
        assert engine._match_rule(rule, tx) is False

    def test_amount_max_pass(self, engine):
        """测试 amount_max 通过"""
        rule = self.make_rule(amount_max=Decimal('200'))
        tx = self.make_tx(amount=Decimal('100'))
        assert engine._match_rule(rule, tx) is True

    def test_amount_max_fail(self, engine):
        """测试 amount_max 不通过"""
        rule = self.make_rule(amount_max=Decimal('50'))
        tx = self.make_tx(amount=Decimal('100'))
        assert engine._match_rule(rule, tx) is False

    def test_amount_range_pass(self, engine):
        """测试金额区间通过"""
        rule = self.make_rule(amount_min=Decimal('50'), amount_max=Decimal('200'))
        tx = self.make_tx(amount=Decimal('100'))
        assert engine._match_rule(rule, tx) is True

    def test_amount_range_fail_low(self, engine):
        """测试金额低于区间"""
        rule = self.make_rule(amount_min=Decimal('50'), amount_max=Decimal('200'))
        tx = self.make_tx(amount=Decimal('30'))
        assert engine._match_rule(rule, tx) is False

    def test_amount_range_fail_high(self, engine):
        """测试金额高于区间"""
        rule = self.make_rule(amount_min=Decimal('50'), amount_max=Decimal('200'))
        tx = self.make_tx(amount=Decimal('300'))
        assert engine._match_rule(rule, tx) is False

    def test_amount_min_none_matches_all(self, engine):
        """测试 amount_min=None 匹配所有"""
        rule = self.make_rule(amount_min=None)
        tx = self.make_tx(amount=Decimal('0'))
        assert engine._match_rule(rule, tx) is True

    def test_amount_max_none_matches_all(self, engine):
        """测试 amount_max=None 匹配所有"""
        rule = self.make_rule(amount_max=None)
        tx = self.make_tx(amount=Decimal('999999'))
        assert engine._match_rule(rule, tx) is True

    # ── 复合条件（AND逻辑） ──────────────────────────

    def test_all_conditions_match(self, engine):
        """测试所有条件同时匹配"""
        rule = self.make_rule(
            sources='alipay',
            directions='expense',
            trans_types='支付',
            payment_channels='支付宝',
            keywords='外卖',
            merchants='海底捞',
            amount_min=Decimal('50'),
            amount_max=Decimal('200'),
        )
        tx = self.make_tx(
            source='alipay',
            direction='expense',
            trans_type='快捷支付',
            description='外卖订单',
            merchant='海底捞火锅',
            counterparty='海底捞',
            payment_channel='支付宝',
            amount=Decimal('100'),
        )
        assert engine._match_rule(rule, tx) is True

    def test_one_condition_fails_returns_false(self, engine):
        """测试任一条件不满足则整体不匹配"""
        rule = self.make_rule(
            sources='alipay',
            directions='expense',
            keywords='外卖',
        )
        # direction 不匹配
        tx = self.make_tx(source='alipay', direction='income', description='外卖订单')
        assert engine._match_rule(rule, tx) is False

    def test_empty_rule_matches_all(self, engine):
        """测试全空规则匹配任何交易"""
        rule = self.make_rule()
        tx = self.make_tx()
        assert engine._match_rule(rule, tx) is True


@pytest.mark.django_db
class TestMatch:
    """测试 match 方法（查询数据库规则）"""

    def test_match_finds_rule(self):
        """测试找到匹配的规则"""
        mock_valid_rule = MagicMock()
        mock_category = MagicMock()

        rule1 = MagicMock()
        rule1.id = 1
        rule1.sources = 'alipay'
        rule1.directions = ''
        rule1.trans_types = ''
        rule1.categories = ''
        rule1.payment_channels = ''
        rule1.keywords = ''
        rule1.keyword_exclude = ''
        rule1.merchants = ''
        rule1.amount_min = None
        rule1.amount_max = None

        mock_valid_rule.objects.filter.return_value.order_by.return_value = [rule1]

        engine = ValidRuleEngine(mock_valid_rule, mock_category)

        tx = MagicMock()
        tx.source = 'alipay'
        tx.direction = 'expense'
        tx.trans_type = '支付'
        tx.description = '消费'
        tx.merchant = '商户'
        tx.counterparty = ''
        tx.payment_channel = ''
        tx.amount = Decimal('100')
        tx.category = None

        result = engine.match(tx)
        assert result == 1

    def test_match_no_rule_found(self):
        """测试未找到匹配规则返回None"""
        mock_valid_rule = MagicMock()
        mock_category = MagicMock()

        rule1 = MagicMock()
        rule1.id = 1
        rule1.sources = 'wechat'  # 不匹配
        rule1.directions = ''
        rule1.trans_types = ''
        rule1.categories = ''
        rule1.payment_channels = ''
        rule1.keywords = ''
        rule1.keyword_exclude = ''
        rule1.merchants = ''
        rule1.amount_min = None
        rule1.amount_max = None

        mock_valid_rule.objects.filter.return_value.order_by.return_value = [rule1]

        engine = ValidRuleEngine(mock_valid_rule, mock_category)

        tx = MagicMock()
        tx.source = 'alipay'
        tx.direction = 'expense'
        tx.trans_type = ''
        tx.description = ''
        tx.merchant = ''
        tx.counterparty = ''
        tx.payment_channel = ''
        tx.amount = Decimal('0')
        tx.category = None

        result = engine.match(tx)
        assert result is None

    def test_match_uses_priority_order(self):
        """测试按优先级排序"""
        mock_valid_rule = MagicMock()
        mock_category = MagicMock()

        # 验证 order_by('-priority') 被调用
        mock_valid_rule.objects.filter.return_value.order_by.return_value = []

        engine = ValidRuleEngine(mock_valid_rule, mock_category)

        tx = MagicMock()
        tx.source = 'alipay'
        tx.direction = 'expense'
        tx.trans_type = ''
        tx.description = ''
        tx.merchant = ''
        tx.counterparty = ''
        tx.payment_channel = ''
        tx.amount = Decimal('0')
        tx.category = None

        engine.match(tx)
        mock_valid_rule.objects.filter.assert_called_with(is_active=True)
        mock_valid_rule.objects.filter.return_value.order_by.assert_called_with('-priority')


@pytest.mark.django_db
class TestApplyAll:
    """测试 apply_all 方法"""

    def test_apply_all_new_match(self):
        """测试新命中规则"""
        mock_valid_rule = MagicMock()
        mock_category = MagicMock()

        engine = ValidRuleEngine(mock_valid_rule, mock_category)
        engine.match = MagicMock(return_value=1)

        tx = MagicMock()
        tx.valid_rule_id = None
        tx.status = 'unknown'

        mock_T = MagicMock()
        mock_T.objects.exclude.return_value.select_related.return_value = [tx]
        mock_T.objects.exclude.return_value.filter.return_value.values.return_value.annotate.return_value = []
        mock_valid_rule.objects.all.return_value.update = MagicMock()

        # apply_all 内部 import Transaction，需要 patch 两个位置
        with patch('apps.transactions.models.Transaction', mock_T), \
             patch('apps.imports.valid_engine.Transaction', mock_T, create=True):
            matched, total = engine.apply_all()

        assert total == 1
        assert matched == 1
        assert tx.valid_rule_id == 1
        assert tx.status == 'confirmed'
        tx.save.assert_called()

    def test_apply_all_rule_changed(self):
        """测试规则变更"""
        mock_valid_rule = MagicMock()
        mock_category = MagicMock()

        engine = ValidRuleEngine(mock_valid_rule, mock_category)
        engine.match = MagicMock(return_value=2)

        tx = MagicMock()
        tx.valid_rule_id = 1
        tx.status = 'confirmed'

        mock_T = MagicMock()
        mock_T.objects.exclude.return_value.select_related.return_value = [tx]
        mock_T.objects.exclude.return_value.filter.return_value.values.return_value.annotate.return_value = []
        mock_valid_rule.objects.all.return_value.update = MagicMock()

        with patch('apps.transactions.models.Transaction', mock_T), \
             patch('apps.imports.valid_engine.Transaction', mock_T, create=True):
            matched, total = engine.apply_all()

        assert total == 1
        assert matched == 1
        assert tx.valid_rule_id == 2
        tx.save.assert_called()

    def test_apply_all_rule_removed(self):
        """测试规则被移除（之前有规则，现在无匹配）"""
        mock_valid_rule = MagicMock()
        mock_category = MagicMock()

        engine = ValidRuleEngine(mock_valid_rule, mock_category)
        engine.match = MagicMock(return_value=None)

        tx = MagicMock()
        tx.valid_rule_id = 1

        mock_T = MagicMock()
        mock_T.objects.exclude.return_value.select_related.return_value = [tx]
        mock_T.objects.exclude.return_value.filter.return_value.values.return_value.annotate.return_value = []
        mock_valid_rule.objects.all.return_value.update = MagicMock()

        with patch('apps.transactions.models.Transaction', mock_T), \
             patch('apps.imports.valid_engine.Transaction', mock_T, create=True):
            matched, total = engine.apply_all()

        assert total == 1
        assert matched == 0
        assert tx.valid_rule_id is None
        tx.save.assert_called()

    def test_apply_all_no_change(self):
        """测试无变化"""
        mock_valid_rule = MagicMock()
        mock_category = MagicMock()

        engine = ValidRuleEngine(mock_valid_rule, mock_category)
        engine.match = MagicMock(return_value=1)

        tx = MagicMock()
        tx.valid_rule_id = 1

        mock_T = MagicMock()
        mock_T.objects.exclude.return_value.select_related.return_value = [tx]
        mock_T.objects.exclude.return_value.filter.return_value.values.return_value.annotate.return_value = []
        mock_valid_rule.objects.all.return_value.update = MagicMock()

        with patch('apps.transactions.models.Transaction', mock_T), \
             patch('apps.imports.valid_engine.Transaction', mock_T, create=True):
            matched, total = engine.apply_all()

        assert total == 1
        assert matched == 0
        tx.save.assert_not_called()


@pytest.mark.django_db
class TestTestRule:
    """测试 test_rule 方法"""

    def test_test_rule_count_matches(self):
        """测试规则命中计数"""
        mock_valid_rule = MagicMock()
        mock_category = MagicMock()

        engine = ValidRuleEngine(mock_valid_rule, mock_category)

        call_count = [0]

        def mock_test_match(rule_data, tx):
            call_count[0] += 1
            return call_count[0] <= 2

        engine._test_match = mock_test_match

        mock_T = MagicMock()
        tx1 = MagicMock()
        tx2 = MagicMock()
        tx3 = MagicMock()
        mock_T.objects.exclude.return_value.select_related.return_value = [tx1, tx2, tx3]

        # test_rule 内部 import Transaction
        with patch('apps.transactions.models.Transaction', mock_T), \
             patch('apps.imports.valid_engine.Transaction', mock_T, create=True):
            count = engine.test_rule({'sources': 'alipay'})

        assert count == 2


class TestTestMatch:
    """测试 _test_match 方法（与 _match_rule 相同逻辑但用字典）"""

    @pytest.fixture
    def engine(self):
        mock_valid_rule = MagicMock()
        mock_category = MagicMock()
        return ValidRuleEngine(mock_valid_rule, mock_category)

    def make_tx(self, **kwargs):
        tx = MagicMock()
        defaults = {
            'source': 'alipay',
            'direction': 'expense',
            'trans_type': '快捷支付',
            'description': '午餐',
            'merchant': '海底捞',
            'counterparty': '海底捞',
            'payment_channel': '支付宝',
            'amount': Decimal('100'),
        }
        defaults.update(kwargs)
        for key, val in defaults.items():
            setattr(tx, key, val)
        tx.category = defaults.get('category', None)
        return tx

    def test_test_match_sources(self, engine):
        """测试 sources 条件"""
        assert engine._test_match({'sources': 'alipay'}, self.make_tx(source='alipay')) is True
        assert engine._test_match({'sources': 'wechat'}, self.make_tx(source='alipay')) is False

    def test_test_match_directions(self, engine):
        """测试 directions 条件"""
        assert engine._test_match({'directions': 'expense'}, self.make_tx(direction='expense')) is True
        assert engine._test_match({'directions': 'expense'}, self.make_tx(direction='income')) is False

    def test_test_match_trans_types(self, engine):
        """测试 trans_types 条件"""
        assert engine._test_match({'trans_types': '支付'}, self.make_tx(trans_type='快捷支付')) is True
        assert engine._test_match({'trans_types': '转账'}, self.make_tx(trans_type='快捷支付')) is False

    def test_test_match_categories(self, engine):
        """测试 categories 条件"""
        cat = MagicMock()
        cat.name = '餐饮美食'
        assert engine._test_match({'categories': '餐饮'}, self.make_tx(category=cat)) is True
        assert engine._test_match({'categories': '交通'}, self.make_tx(category=cat)) is False

    def test_test_match_payment_channels(self, engine):
        """测试 payment_channels 条件"""
        assert engine._test_match({'payment_channels': '支付宝'}, self.make_tx(payment_channel='支付宝')) is True
        assert engine._test_match({'payment_channels': '微信'}, self.make_tx(payment_channel='支付宝')) is False

    def test_test_match_keywords(self, engine):
        """测试 keywords 条件"""
        assert engine._test_match({'keywords': '外卖'},
            self.make_tx(description='外卖订单')) is True
        assert engine._test_match({'keywords': '星巴克'},
            self.make_tx(description='外卖')) is False

    def test_test_match_keyword_exclude(self, engine):
        """测试 keyword_exclude 条件"""
        assert engine._test_match({'keyword_exclude': '还款'},
            self.make_tx(description='信用卡还款')) is False
        assert engine._test_match({'keyword_exclude': '还款'},
            self.make_tx(description='午餐')) is True

    def test_test_match_merchants(self, engine):
        """测试 merchants 条件"""
        assert engine._test_match({'merchants': '海底捞'},
            self.make_tx(merchant='海底捞火锅')) is True
        assert engine._test_match({'merchants': '星巴克'},
            self.make_tx(merchant='海底捞')) is False

    def test_test_match_amount(self, engine):
        """测试 amount 条件"""
        assert engine._test_match({'amount_min': Decimal('50')},
            self.make_tx(amount=Decimal('100'))) is True
        assert engine._test_match({'amount_min': Decimal('200')},
            self.make_tx(amount=Decimal('100'))) is False
        assert engine._test_match({'amount_max': Decimal('200')},
            self.make_tx(amount=Decimal('100'))) is True
        assert engine._test_match({'amount_max': Decimal('50')},
            self.make_tx(amount=Decimal('100'))) is False

    def test_test_match_empty_rule_data(self, engine):
        """测试空规则数据匹配所有"""
        assert engine._test_match({}, self.make_tx()) is True
