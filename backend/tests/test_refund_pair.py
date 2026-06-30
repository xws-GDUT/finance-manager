"""
测试 RefundPairEngine 退款配对引擎
"""
import pytest
from unittest import mock
from unittest.mock import MagicMock, PropertyMock, patch
from decimal import Decimal
from datetime import date, timedelta
from apps.imports.refund_pair import RefundPairEngine, REFUND_KEYWORDS, AA_KEYWORDS


class TestFindRefundCandidates:
    """测试 find_refund_candidates 方法"""

    def test_find_candidates_with_refund_keyword(self):
        """测试找到包含退款关键词的收入交易"""
        mock_pair = MagicMock()
        mock_tx = MagicMock()

        engine = RefundPairEngine(mock_pair, mock_tx)

        # 模拟 queryset
        mock_qs = MagicMock()
        mock_tx.objects.filter.return_value.exclude.return_value = mock_qs

        result = engine.find_refund_candidates()

        # 验证调用了正确的过滤条件
        mock_tx.objects.filter.assert_called_once()
        # 验证 direction='income' 和状态过滤
        filter_kwargs = mock_tx.objects.filter.call_args[1]
        assert filter_kwargs['direction'] == 'income'
        assert 'confirmed' in filter_kwargs['status__in']

    def test_no_candidates(self):
        """测试没有符合条件的退款候选"""
        mock_pair = MagicMock()
        mock_tx = MagicMock()

        mock_qs = MagicMock()
        mock_qs.exists.return_value = False
        mock_tx.objects.filter.return_value.exclude.return_value = mock_qs

        engine = RefundPairEngine(mock_pair, mock_tx)
        result = engine.find_refund_candidates()

        assert result == mock_qs


class TestTimeScore:
    """测试 _time_score 方法"""

    @pytest.fixture
    def engine(self):
        return RefundPairEngine(MagicMock(), MagicMock())

    def test_delta_negative(self, engine):
        """测试 delta < 0（退款在消费之前）返回 0"""
        expense = MagicMock()
        expense.trans_date = date(2026, 6, 20)
        refund = MagicMock()
        refund.trans_date = date(2026, 6, 15)
        assert engine._time_score(expense, refund) == 0

    def test_delta_zero(self, engine):
        """测试同一天返回 100"""
        expense = MagicMock()
        expense.trans_date = date(2026, 6, 20)
        refund = MagicMock()
        refund.trans_date = date(2026, 6, 20)
        assert engine._time_score(expense, refund) == 100

    def test_delta_within_30_days(self, engine):
        """测试 30 天内线性递减"""
        expense = MagicMock()
        expense.trans_date = date(2026, 6, 1)
        refund = MagicMock()
        refund.trans_date = date(2026, 6, 16)  # delta = 15
        score = engine._time_score(expense, refund)
        # 100 * (1 - 15/30) = 50
        assert score == pytest.approx(50.0)

    def test_delta_30_days(self, engine):
        """测试正好 30 天返回 0"""
        expense = MagicMock()
        expense.trans_date = date(2026, 6, 1)
        refund = MagicMock()
        refund.trans_date = date(2026, 7, 1)  # delta = 30
        score = engine._time_score(expense, refund)
        assert score == pytest.approx(0.0)

    def test_delta_greater_than_30(self, engine):
        """测试超过 30 天返回 0"""
        expense = MagicMock()
        expense.trans_date = date(2026, 6, 1)
        refund = MagicMock()
        refund.trans_date = date(2026, 8, 1)  # delta = 61
        assert engine._time_score(expense, refund) == 0


class TestAmountScore:
    """测试 _amount_score 方法"""

    @pytest.fixture
    def engine(self):
        return RefundPairEngine(MagicMock(), MagicMock())

    def test_refund_greater_than_expense(self, engine):
        """测试退款 > 消费返回 0"""
        expense = MagicMock()
        expense.amount = Decimal('100')
        refund = MagicMock()
        refund.amount = Decimal('150')
        assert engine._amount_score(expense, refund) == 0

    def test_expense_zero(self, engine):
        """测试消费金额为 0 返回 0"""
        expense = MagicMock()
        expense.amount = Decimal('0')
        refund = MagicMock()
        refund.amount = Decimal('0')  # refund 也必须为0，否则会被第一个条件拦截
        assert engine._amount_score(expense, refund) == 0

    def test_normal_ratio(self, engine):
        """测试正常比例"""
        expense = MagicMock()
        expense.amount = Decimal('100')
        refund = MagicMock()
        refund.amount = Decimal('80')
        # 100 * (80/100) = 80
        score = engine._amount_score(expense, refund)
        assert score == pytest.approx(80.0)

    def test_full_refund(self, engine):
        """测试全额退款"""
        expense = MagicMock()
        expense.amount = Decimal('100')
        refund = MagicMock()
        refund.amount = Decimal('100')
        score = engine._amount_score(expense, refund)
        assert score == pytest.approx(100.0)

    def test_partial_refund(self, engine):
        """测试部分退款"""
        expense = MagicMock()
        expense.amount = Decimal('200')
        refund = MagicMock()
        refund.amount = Decimal('50')
        # 100 * (50/200) = 25
        score = engine._amount_score(expense, refund)
        assert score == pytest.approx(25.0)


class TestMerchantScore:
    """测试 _merchant_score 方法"""

    @pytest.fixture
    def engine(self):
        return RefundPairEngine(MagicMock(), MagicMock())

    def test_exact_match(self, engine):
        """测试完全相同返回 100"""
        expense = MagicMock()
        expense.merchant = '星巴克'
        expense.description = '咖啡'
        refund = MagicMock()
        refund.merchant = '星巴克'
        refund.description = '咖啡'
        assert engine._merchant_score(expense, refund) == 100

    def test_contains_match(self, engine):
        """测试一方包含另一方返回 90"""
        expense = MagicMock()
        expense.merchant = '星巴克'
        expense.description = '咖啡'
        refund = MagicMock()
        refund.merchant = '星巴克'
        refund.description = '咖啡退款'
        # '星巴克 咖啡退款' 包含 '星巴克 咖啡'
        score = engine._merchant_score(expense, refund)
        assert score == 90

    def test_lcs_match(self, engine):
        """测试最长公共子串得分"""
        expense = MagicMock()
        expense.merchant = '海底捞火锅'
        expense.description = '晚餐'
        refund = MagicMock()
        refund.merchant = '海底捞'
        refund.description = '退款'
        # LCS of '海底捞火锅 晚餐' and '海底捞 退款'
        score = engine._merchant_score(expense, refund)
        assert 0 < score < 90

    def test_empty_names(self, engine):
        """测试空名称返回 0"""
        expense = MagicMock()
        expense.merchant = ''
        expense.description = ''
        refund = MagicMock()
        refund.merchant = ''
        refund.description = ''
        assert engine._merchant_score(expense, refund) == 0

    def test_max_len_zero_branch(self, engine):
        """测试 max_len==0 的分支（行188）"""
        # e_name 和 r_name 都是非空但 max_len==0 的极端情况
        # 通过 mock 绕过前两个条件检查
        expense = MagicMock()
        expense.merchant = 'a'
        expense.description = 'b'
        refund = MagicMock()
        refund.merchant = 'c'
        refund.description = 'd'

        # e_name = 'a b', r_name = 'c d', 都不为空，会跳过第一个检查
        # e_name != r_name，跳过第二个检查
        # lcs_length('a b', 'c d') = 1 (空格)
        # max_len = max(4, 4) = 4，不会触发 max_len==0

        # 用 mock 替换 _lcs_length 和 max 来触发
        with mock.patch.object(engine, '_lcs_length', return_value=0):
            # 模拟 max_len == 0 的情况
            with mock.patch('apps.imports.refund_pair.max', return_value=0):
                score = engine._merchant_score(expense, refund)
                assert score == 0


class TestLcsLength:
    """测试 _lcs_length 静态方法"""

    def test_same_strings(self):
        assert RefundPairEngine._lcs_length('abc', 'abc') == 3

    def test_different_strings(self):
        assert RefundPairEngine._lcs_length('abc', 'def') == 0

    def test_partial_match(self):
        assert RefundPairEngine._lcs_length('abcdef', 'xbcdy') == 3  # 'bcd'

    def test_empty_string_a(self):
        assert RefundPairEngine._lcs_length('', 'abc') == 0

    def test_empty_string_b(self):
        assert RefundPairEngine._lcs_length('abc', '') == 0

    def test_both_empty(self):
        assert RefundPairEngine._lcs_length('', '') == 0

    def test_chinese_characters(self):
        assert RefundPairEngine._lcs_length('海底捞火锅', '海底捞') == 3

    def test_substring_at_end(self):
        assert RefundPairEngine._lcs_length('hello world', 'world') == 5


class TestCalculateMatchScore:
    """测试 _calculate_match_score 方法"""

    @pytest.fixture
    def engine(self):
        eng = RefundPairEngine(MagicMock(), MagicMock())
        eng._time_score = MagicMock(return_value=100.0)
        eng._amount_score = MagicMock(return_value=80.0)
        eng._merchant_score = MagicMock(return_value=90.0)
        return eng

    def test_weighted_calculation(self, engine):
        """测试加权计算"""
        expense = MagicMock()
        refund = MagicMock()
        score = engine._calculate_match_score(expense, refund)
        # 100 * 0.20 + 80 * 0.40 + 90 * 0.40 = 20 + 32 + 36 = 88
        assert score == pytest.approx(88.0)


@pytest.mark.django_db
class TestAutoPair:
    """测试 auto_pair 方法"""

    def test_pair_success(self):
        """测试配对成功"""
        mock_pair = MagicMock()
        mock_tx = MagicMock()

        engine = RefundPairEngine(mock_pair, mock_tx)

        # mock find_refund_candidates
        refund_tx = MagicMock()
        refund_tx.id = 101
        refund_tx.trans_date = date(2026, 6, 20)
        refund_tx.amount = Decimal('100')
        refund_tx.merchant = '星巴克'
        refund_tx.description = '退款'
        refund_tx.source = 'alipay'

        engine.find_refund_candidates = MagicMock(return_value=[refund_tx])

        # mock candidate expenses
        expense_tx = MagicMock()
        expense_tx.id = 1
        expense_tx.trans_date = date(2026, 6, 15)
        expense_tx.amount = Decimal('120')
        expense_tx.merchant = '星巴克'
        expense_tx.description = '咖啡'

        mock_candidates_qs = MagicMock()
        mock_candidates_qs.exists.return_value = True
        mock_candidates_qs.__iter__.return_value = iter([expense_tx])

        mock_tx.objects.filter.return_value.exclude.return_value = mock_candidates_qs

        # mock 得分计算
        engine._calculate_match_score = MagicMock(return_value=75.0)

        # mock pair creation
        mock_pair.objects.create.return_value.id = 1

        result = engine.auto_pair()

        assert result['paired'] == 1
        assert result['skipped'] == 0
        assert len(result['pairs']) == 1
        assert result['pairs'][0]['score'] == 75.0

    def test_no_candidates(self):
        """测试没有候选消费交易"""
        mock_pair = MagicMock()
        mock_tx = MagicMock()

        engine = RefundPairEngine(mock_pair, mock_tx)

        refund_tx = MagicMock()
        refund_tx.source = 'alipay'
        refund_tx.trans_date = date(2026, 6, 20)
        engine.find_refund_candidates = MagicMock(return_value=[refund_tx])

        mock_candidates_qs = MagicMock()
        mock_candidates_qs.exists.return_value = False
        mock_tx.objects.filter.return_value.exclude.return_value = mock_candidates_qs

        result = engine.auto_pair()

        assert result['paired'] == 0
        assert result['skipped'] == 1

    def test_score_too_low(self):
        """测试得分不够（< 60）不配对"""
        mock_pair = MagicMock()
        mock_tx = MagicMock()

        engine = RefundPairEngine(mock_pair, mock_tx)

        refund_tx = MagicMock()
        refund_tx.source = 'alipay'
        refund_tx.trans_date = date(2026, 6, 20)
        engine.find_refund_candidates = MagicMock(return_value=[refund_tx])

        expense_tx = MagicMock()
        mock_candidates_qs = MagicMock()
        mock_candidates_qs.exists.return_value = True
        mock_candidates_qs.__iter__.return_value = iter([expense_tx])
        mock_tx.objects.filter.return_value.exclude.return_value = mock_candidates_qs

        engine._calculate_match_score = MagicMock(return_value=50.0)

        result = engine.auto_pair()

        assert result['paired'] == 0
        assert result['skipped'] == 1


@pytest.mark.django_db
class TestManualPair:
    """测试 manual_pair 方法"""

    def test_manual_pair_success(self):
        """测试手动配对成功"""
        mock_pair = MagicMock()
        mock_tx = MagicMock()

        expense = MagicMock()
        expense.id = 1
        expense.amount = Decimal('100')
        expense.merchant = '商户A'
        expense.description = '消费'
        expense.trans_date = date(2026, 6, 15)

        refund = MagicMock()
        refund.id = 2
        refund.amount = Decimal('100')
        refund.merchant = '商户A'
        refund.description = '退款'
        refund.trans_date = date(2026, 6, 20)

        mock_tx.objects.get.side_effect = [expense, refund]

        engine = RefundPairEngine(mock_pair, mock_tx)
        engine._calculate_match_score = MagicMock(return_value=80.0)

        mock_pair.objects.create.return_value.id = 1

        result = engine.manual_pair(1, 2)

        assert result is not None
        assert result['pair_id'] == 1
        assert result['expense_id'] == 1
        assert result['refund_id'] == 2
        assert result['score'] == 80.0

    def test_manual_pair_transaction_not_found(self):
        """测试交易不存在返回None"""
        mock_pair = MagicMock()
        mock_tx = MagicMock()
        mock_tx.DoesNotExist = Exception
        mock_tx.objects.get.side_effect = mock_tx.DoesNotExist()

        engine = RefundPairEngine(mock_pair, mock_tx)

        result = engine.manual_pair(999, 999)
        assert result is None


@pytest.mark.django_db
class TestUnpair:
    """测试 unpair 方法"""

    def test_unpair_success(self):
        """测试解除配对成功"""
        mock_pair = MagicMock()
        mock_tx = MagicMock()

        engine = RefundPairEngine(mock_pair, mock_tx)

        expense = MagicMock()
        refund = MagicMock()

        pair_obj = MagicMock()
        pair_obj.id = 1
        pair_obj.expense_tx = expense
        pair_obj.refund_tx = refund

        mock_pair.objects.get.return_value = pair_obj

        result = engine.unpair(1)

        assert result is True
        assert expense.status == 'confirmed'
        assert expense.pair is None
        assert refund.status == 'confirmed'
        assert refund.pair is None
        expense.save.assert_called()
        refund.save.assert_called()
        pair_obj.delete.assert_called()

    def test_unpair_pair_not_found(self):
        """测试配对不存在返回False"""
        mock_pair = MagicMock()
        mock_tx = MagicMock()
        mock_pair.DoesNotExist = Exception
        mock_pair.objects.get.side_effect = mock_pair.DoesNotExist()

        engine = RefundPairEngine(mock_pair, mock_tx)

        result = engine.unpair(999)
        assert result is False


class TestRefundKeywords:
    """测试 REFUND_KEYWORDS 常量"""

    def test_contains_expected_keywords(self):
        assert '退款' in REFUND_KEYWORDS
        assert '退货' in REFUND_KEYWORDS
        assert '原路退回' in REFUND_KEYWORDS


class TestAaKeywords:
    """测试 AA_KEYWORDS 常量"""

    def test_contains_expected_keywords(self):
        assert '群收款' in AA_KEYWORDS
        assert 'aa收款' in AA_KEYWORDS
