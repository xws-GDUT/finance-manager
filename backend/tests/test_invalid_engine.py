"""
测试 InvalidRuleEngine 无效规则引擎（黑名单）
"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from apps.imports.invalid_engine import InvalidRuleEngine


class TestMatchList:
    """测试 _match_list 静态方法（精确匹配）"""

    def test_exact_match(self):
        assert InvalidRuleEngine._match_list('alipay', 'alipay,wechat') is True

    def test_no_match(self):
        assert InvalidRuleEngine._match_list('douyin', 'alipay,wechat') is False

    def test_empty_value(self):
        assert InvalidRuleEngine._match_list('', 'alipay,wechat') is False

    def test_none_value(self):
        assert InvalidRuleEngine._match_list(None, 'alipay,wechat') is False

    def test_whitespace_handling(self):
        assert InvalidRuleEngine._match_list('alipay', ' alipay , wechat ') is True


class TestMatchListContains:
    """测试 _match_list_contains 静态方法（子串匹配）"""

    def test_contains_match(self):
        assert InvalidRuleEngine._match_list_contains('快捷支付', '支付,转账') is True

    def test_not_contains(self):
        assert InvalidRuleEngine._match_list_contains('取款', '支付,转账') is False

    def test_empty_value(self):
        assert InvalidRuleEngine._match_list_contains('', '支付') is False

    def test_none_value(self):
        assert InvalidRuleEngine._match_list_contains(None, '支付') is False

    def test_whitespace_handling(self):
        assert InvalidRuleEngine._match_list_contains('支付宝支付', ' 支付宝 , 微信 ') is True


class TestMatchRule:
    """测试 _match_rule 方法（11个条件的AND逻辑，含counterparties）"""

    @pytest.fixture
    def engine(self):
        mock_invalid_rule = MagicMock()
        mock_category = MagicMock()
        return InvalidRuleEngine(mock_invalid_rule, mock_category)

    def make_rule(self, **kwargs):
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
            'counterparties': '',
            'amount_min': None,
            'amount_max': None,
        }
        defaults.update(kwargs)
        for key, val in defaults.items():
            setattr(rule, key, val)
        return rule

    def make_tx(self, **kwargs):
        tx = MagicMock()
        defaults = {
            'source': 'alipay',
            'direction': 'expense',
            'trans_type': '快捷支付',
            'description': '消费',
            'merchant': '商户A',
            'counterparty': '商户A',
            'payment_channel': '支付宝',
            'amount': Decimal('100'),
        }
        defaults.update(kwargs)
        for key, val in defaults.items():
            setattr(tx, key, val)
        tx.category = defaults.get('category', None)
        return tx

    # ── sources ──────────────────────────────────────

    def test_sources_match(self, engine):
        rule = self.make_rule(sources='alipay,wechat')
        tx = self.make_tx(source='alipay')
        assert engine._match_rule(rule, tx) is True

    def test_sources_no_match(self, engine):
        rule = self.make_rule(sources='wechat')
        tx = self.make_tx(source='alipay')
        assert engine._match_rule(rule, tx) is False

    def test_sources_empty(self, engine):
        rule = self.make_rule(sources='')
        tx = self.make_tx(source='alipay')
        assert engine._match_rule(rule, tx) is True

    # ── directions ───────────────────────────────────

    def test_directions_match(self, engine):
        rule = self.make_rule(directions='expense')
        tx = self.make_tx(direction='expense')
        assert engine._match_rule(rule, tx) is True

    def test_directions_no_match(self, engine):
        rule = self.make_rule(directions='expense')
        tx = self.make_tx(direction='income')
        assert engine._match_rule(rule, tx) is False

    # ── trans_types ──────────────────────────────────

    def test_trans_types_match(self, engine):
        rule = self.make_rule(trans_types='支付')
        tx = self.make_tx(trans_type='快捷支付')
        assert engine._match_rule(rule, tx) is True

    def test_trans_types_no_match(self, engine):
        rule = self.make_rule(trans_types='转账')
        tx = self.make_tx(trans_type='快捷支付')
        assert engine._match_rule(rule, tx) is False

    # ── categories ───────────────────────────────────

    def test_categories_match(self, engine):
        rule = self.make_rule(categories='餐饮')
        cat = MagicMock()
        cat.name = '餐饮美食'
        tx = self.make_tx(category=cat)
        assert engine._match_rule(rule, tx) is True

    def test_categories_no_match(self, engine):
        rule = self.make_rule(categories='交通')
        cat = MagicMock()
        cat.name = '餐饮美食'
        tx = self.make_tx(category=cat)
        assert engine._match_rule(rule, tx) is False

    def test_categories_no_category_on_tx(self, engine):
        rule = self.make_rule(categories='餐饮')
        tx = self.make_tx(category=None)
        assert engine._match_rule(rule, tx) is True

    # ── payment_channels ─────────────────────────────

    def test_payment_channels_match(self, engine):
        rule = self.make_rule(payment_channels='支付宝')
        tx = self.make_tx(payment_channel='支付宝')
        assert engine._match_rule(rule, tx) is True

    def test_payment_channels_no_match(self, engine):
        rule = self.make_rule(payment_channels='微信')
        tx = self.make_tx(payment_channel='支付宝')
        assert engine._match_rule(rule, tx) is False

    # ── keywords ─────────────────────────────────────

    def test_keywords_match(self, engine):
        rule = self.make_rule(keywords='还款')
        tx = self.make_tx(description='信用卡还款', merchant='银行',
                          counterparty='银行', trans_type='还款', payment_channel='支付宝')
        assert engine._match_rule(rule, tx) is True

    def test_keywords_no_match(self, engine):
        rule = self.make_rule(keywords='星巴克')
        tx = self.make_tx(description='午餐', merchant='海底捞')
        assert engine._match_rule(rule, tx) is False

    # ── keyword_exclude ──────────────────────────────

    def test_keyword_exclude_triggers(self, engine):
        rule = self.make_rule(keyword_exclude='还款')
        tx = self.make_tx(description='信用卡还款', merchant='银行',
                          counterparty='银行', trans_type='还款')
        assert engine._match_rule(rule, tx) is False

    def test_keyword_exclude_pass(self, engine):
        rule = self.make_rule(keyword_exclude='还款')
        tx = self.make_tx(description='午餐', merchant='海底捞')
        assert engine._match_rule(rule, tx) is True

    # ── merchants ────────────────────────────────────

    def test_merchants_match(self, engine):
        rule = self.make_rule(merchants='海底捞')
        tx = self.make_tx(merchant='海底捞火锅')
        assert engine._match_rule(rule, tx) is True

    def test_merchants_no_match(self, engine):
        rule = self.make_rule(merchants='星巴克')
        tx = self.make_tx(merchant='海底捞')
        assert engine._match_rule(rule, tx) is False

    # ── counterparties（无效规则特有） ────────────────

    def test_counterparties_match(self, engine):
        """测试对手方精确匹配"""
        rule = self.make_rule(counterparties='张三,李四')
        tx = self.make_tx(counterparty='张三')
        assert engine._match_rule(rule, tx) is True

    def test_counterparties_no_match(self, engine):
        """测试对手方不匹配"""
        rule = self.make_rule(counterparties='张三')
        tx = self.make_tx(counterparty='王五')
        assert engine._match_rule(rule, tx) is False

    def test_counterparties_empty_matches_all(self, engine):
        """测试对手方为空匹配所有"""
        rule = self.make_rule(counterparties='')
        tx = self.make_tx(counterparty='任何人')
        assert engine._match_rule(rule, tx) is True

    # ── amount ───────────────────────────────────────

    def test_amount_min_pass(self, engine):
        rule = self.make_rule(amount_min=Decimal('50'))
        tx = self.make_tx(amount=Decimal('100'))
        assert engine._match_rule(rule, tx) is True

    def test_amount_min_fail(self, engine):
        rule = self.make_rule(amount_min=Decimal('50'))
        tx = self.make_tx(amount=Decimal('30'))
        assert engine._match_rule(rule, tx) is False

    def test_amount_max_pass(self, engine):
        rule = self.make_rule(amount_max=Decimal('200'))
        tx = self.make_tx(amount=Decimal('100'))
        assert engine._match_rule(rule, tx) is True

    def test_amount_max_fail(self, engine):
        rule = self.make_rule(amount_max=Decimal('50'))
        tx = self.make_tx(amount=Decimal('100'))
        assert engine._match_rule(rule, tx) is False

    # ── 复合条件 ─────────────────────────────────────

    def test_all_conditions_match(self, engine):
        """测试11个条件全部匹配"""
        cat = MagicMock()
        cat.name = '餐饮美食'

        rule = self.make_rule(
            sources='alipay',
            directions='expense',
            trans_types='支付',
            categories='餐饮',
            payment_channels='支付宝',
            keywords='外卖',
            keyword_exclude='',
            merchants='海底捞',
            counterparties='海底捞',
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
            category=cat,
        )
        assert engine._match_rule(rule, tx) is True

    def test_one_condition_fails(self, engine):
        """测试任一条不满足则整体不匹配"""
        rule = self.make_rule(sources='alipay', directions='expense')
        tx = self.make_tx(source='alipay', direction='income')
        assert engine._match_rule(rule, tx) is False

    def test_empty_rule_matches_all(self, engine):
        rule = self.make_rule()
        tx = self.make_tx()
        assert engine._match_rule(rule, tx) is True


@pytest.mark.django_db
class TestMatch:
    """测试 match 方法（查询数据库规则）"""

    def test_match_finds_rule(self):
        mock_invalid_rule = MagicMock()
        mock_category = MagicMock()

        rule1 = MagicMock()
        rule1.id = 1
        rule1.sources = 'alipay'
        for field in ['directions', 'trans_types', 'categories', 'payment_channels',
                       'keywords', 'keyword_exclude', 'merchants', 'counterparties']:
            setattr(rule1, field, '')
        rule1.amount_min = None
        rule1.amount_max = None

        mock_invalid_rule.objects.filter.return_value.order_by.return_value = [rule1]

        engine = InvalidRuleEngine(mock_invalid_rule, mock_category)

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
        assert result == 1

    def test_match_no_rule_found(self):
        mock_invalid_rule = MagicMock()
        mock_category = MagicMock()

        rule1 = MagicMock()
        rule1.id = 1
        rule1.sources = 'wechat'
        for field in ['directions', 'trans_types', 'categories', 'payment_channels',
                       'keywords', 'keyword_exclude', 'merchants', 'counterparties']:
            setattr(rule1, field, '')
        rule1.amount_min = None
        rule1.amount_max = None

        mock_invalid_rule.objects.filter.return_value.order_by.return_value = [rule1]

        engine = InvalidRuleEngine(mock_invalid_rule, mock_category)

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


@pytest.mark.django_db
class TestApplyAll:
    """测试 apply_all 方法"""

    def test_apply_all_new_match(self):
        mock_invalid_rule = MagicMock()
        mock_category = MagicMock()

        engine = InvalidRuleEngine(mock_invalid_rule, mock_category)
        engine.match = MagicMock(return_value=1)

        tx = MagicMock()
        tx.invalid_rule_id = None
        tx.status = 'unknown'

        mock_T = MagicMock()
        mock_T.objects.exclude.return_value.select_related.return_value = [tx]
        mock_T.objects.exclude.return_value.filter.return_value.values.return_value.annotate.return_value = []

        mock_invalid_rule.objects.all.return_value.update = MagicMock()

        with patch('apps.transactions.models.Transaction', mock_T), \
             patch('apps.imports.invalid_engine.Transaction', mock_T, create=True):
            matched, total = engine.apply_all()

        assert total == 1
        assert matched == 1
        assert tx.invalid_rule_id == 1
        assert tx.status == 'excluded'
        tx.save.assert_called()

    def test_apply_all_rule_changed(self):
        mock_invalid_rule = MagicMock()
        mock_category = MagicMock()

        engine = InvalidRuleEngine(mock_invalid_rule, mock_category)
        engine.match = MagicMock(return_value=2)

        tx = MagicMock()
        tx.invalid_rule_id = 1
        tx.status = 'excluded'

        mock_T = MagicMock()
        mock_T.objects.exclude.return_value.select_related.return_value = [tx]
        mock_T.objects.exclude.return_value.filter.return_value.values.return_value.annotate.return_value = []

        mock_invalid_rule.objects.all.return_value.update = MagicMock()

        with patch('apps.transactions.models.Transaction', mock_T), \
             patch('apps.imports.invalid_engine.Transaction', mock_T, create=True):
            matched, total = engine.apply_all()

        assert total == 1
        assert matched == 1
        assert tx.invalid_rule_id == 2
        tx.save.assert_called()

    def test_apply_all_rule_removed(self):
        mock_invalid_rule = MagicMock()
        mock_category = MagicMock()

        engine = InvalidRuleEngine(mock_invalid_rule, mock_category)
        engine.match = MagicMock(return_value=None)

        tx = MagicMock()
        tx.invalid_rule_id = 1

        mock_T = MagicMock()
        mock_T.objects.exclude.return_value.select_related.return_value = [tx]
        mock_T.objects.exclude.return_value.filter.return_value.values.return_value.annotate.return_value = []

        mock_invalid_rule.objects.all.return_value.update = MagicMock()

        with patch('apps.transactions.models.Transaction', mock_T), \
             patch('apps.imports.invalid_engine.Transaction', mock_T, create=True):
            matched, total = engine.apply_all()

        assert total == 1
        assert matched == 0
        assert tx.invalid_rule_id is None
        tx.save.assert_called()

    def test_apply_all_no_change(self):
        mock_invalid_rule = MagicMock()
        mock_category = MagicMock()

        engine = InvalidRuleEngine(mock_invalid_rule, mock_category)
        engine.match = MagicMock(return_value=1)

        tx = MagicMock()
        tx.invalid_rule_id = 1

        mock_T = MagicMock()
        mock_T.objects.exclude.return_value.select_related.return_value = [tx]
        mock_T.objects.exclude.return_value.filter.return_value.values.return_value.annotate.return_value = []

        mock_invalid_rule.objects.all.return_value.update = MagicMock()

        with patch('apps.transactions.models.Transaction', mock_T), \
             patch('apps.imports.invalid_engine.Transaction', mock_T, create=True):
            matched, total = engine.apply_all()

        assert total == 1
        assert matched == 0
        tx.save.assert_not_called()


@pytest.mark.django_db
class TestTestRule:
    """测试 test_rule 方法"""

    def test_test_rule_count(self):
        mock_invalid_rule = MagicMock()
        mock_category = MagicMock()

        engine = InvalidRuleEngine(mock_invalid_rule, mock_category)

        call_count = [0]

        def mock_test_match(rule_data, tx):
            call_count[0] += 1
            return call_count[0] <= 2

        engine._test_match = mock_test_match

        mock_T = MagicMock()
        mock_T.objects.exclude.return_value.select_related.return_value = [
            MagicMock(), MagicMock(), MagicMock()
        ]

        with patch('apps.transactions.models.Transaction', mock_T), \
             patch('apps.imports.invalid_engine.Transaction', mock_T, create=True):
            count = engine.test_rule({'sources': 'alipay'})

        assert count == 2


class TestTestMatch:
    """测试 _test_match 方法（11个条件）"""

    @pytest.fixture
    def engine(self):
        mock_invalid_rule = MagicMock()
        mock_category = MagicMock()
        return InvalidRuleEngine(mock_invalid_rule, mock_category)

    def make_tx(self, **kwargs):
        tx = MagicMock()
        defaults = {
            'source': 'alipay',
            'direction': 'expense',
            'trans_type': '快捷支付',
            'description': '消费',
            'merchant': '商户A',
            'counterparty': '商户A',
            'payment_channel': '支付宝',
            'amount': Decimal('100'),
        }
        defaults.update(kwargs)
        for key, val in defaults.items():
            setattr(tx, key, val)
        tx.category = defaults.get('category', None)
        return tx

    def test_sources(self, engine):
        assert engine._test_match({'sources': 'alipay'}, self.make_tx(source='alipay')) is True
        assert engine._test_match({'sources': 'wechat'}, self.make_tx(source='alipay')) is False

    def test_directions(self, engine):
        assert engine._test_match({'directions': 'expense'}, self.make_tx(direction='expense')) is True
        assert engine._test_match({'directions': 'expense'}, self.make_tx(direction='income')) is False

    def test_trans_types(self, engine):
        assert engine._test_match({'trans_types': '支付'}, self.make_tx(trans_type='快捷支付')) is True
        assert engine._test_match({'trans_types': '转账'}, self.make_tx(trans_type='快捷支付')) is False

    def test_categories(self, engine):
        cat = MagicMock()
        cat.name = '餐饮'
        assert engine._test_match({'categories': '餐饮'}, self.make_tx(category=cat)) is True
        assert engine._test_match({'categories': '交通'}, self.make_tx(category=cat)) is False

    def test_payment_channels(self, engine):
        assert engine._test_match({'payment_channels': '支付宝'},
            self.make_tx(payment_channel='支付宝')) is True
        assert engine._test_match({'payment_channels': '微信'},
            self.make_tx(payment_channel='支付宝')) is False

    def test_keywords(self, engine):
        assert engine._test_match({'keywords': '还款'},
            self.make_tx(description='信用卡还款')) is True
        assert engine._test_match({'keywords': '星巴克'},
            self.make_tx(description='外卖')) is False

    def test_keyword_exclude(self, engine):
        assert engine._test_match({'keyword_exclude': '还款'},
            self.make_tx(description='信用卡还款')) is False
        assert engine._test_match({'keyword_exclude': '还款'},
            self.make_tx(description='午餐')) is True

    def test_merchants(self, engine):
        assert engine._test_match({'merchants': '海底捞'},
            self.make_tx(merchant='海底捞火锅')) is True
        assert engine._test_match({'merchants': '星巴克'},
            self.make_tx(merchant='海底捞')) is False

    def test_counterparties(self, engine):
        """测试对手方条件"""
        assert engine._test_match({'counterparties': '张三,李四'},
            self.make_tx(counterparty='张三')) is True
        assert engine._test_match({'counterparties': '张三'},
            self.make_tx(counterparty='王五')) is False

    def test_amount(self, engine):
        assert engine._test_match({'amount_min': Decimal('50')},
            self.make_tx(amount=Decimal('100'))) is True
        assert engine._test_match({'amount_min': Decimal('200')},
            self.make_tx(amount=Decimal('100'))) is False
        assert engine._test_match({'amount_max': Decimal('200')},
            self.make_tx(amount=Decimal('100'))) is True
        assert engine._test_match({'amount_max': Decimal('50')},
            self.make_tx(amount=Decimal('100'))) is False

    def test_empty_rule_data(self, engine):
        assert engine._test_match({}, self.make_tx()) is True
