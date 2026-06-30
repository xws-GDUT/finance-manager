"""
测试 utils/helpers.py — generate_unique_key + detect_source
"""
from decimal import Decimal
import pytest

from utils.helpers import (
    generate_unique_key,
    detect_source,
    SOURCE_FILENAME_PATTERNS,
    PDF_CONTENT_SIGNATURES,
)


class TestGenerateUniqueKey:
    """测试 generate_unique_key 函数"""

    def test_normal_input(self):
        """测试正常输入"""
        result = generate_unique_key(
            source='alipay',
            trans_date='2024-01-15',
            amount=Decimal('100.50'),
            merchant='测试商户',
            description='午餐消费',
        )
        assert isinstance(result, str)
        assert len(result) == 16
        # 相同输入应产生相同输出（确定性）
        result2 = generate_unique_key(
            source='alipay',
            trans_date='2024-01-15',
            amount=Decimal('100.50'),
            merchant='测试商户',
            description='午餐消费',
        )
        assert result == result2

    def test_different_inputs_produce_different_keys(self):
        """测试不同输入产生不同的键"""
        key1 = generate_unique_key('alipay', '2024-01-15', Decimal('100'), '商户A', '描述A')
        key2 = generate_unique_key('wechat', '2024-01-15', Decimal('100'), '商户A', '描述A')
        key3 = generate_unique_key('alipay', '2024-01-16', Decimal('100'), '商户A', '描述A')
        key4 = generate_unique_key('alipay', '2024-01-15', Decimal('200'), '商户A', '描述A')
        key5 = generate_unique_key('alipay', '2024-01-15', Decimal('100'), '商户B', '描述A')
        key6 = generate_unique_key('alipay', '2024-01-15', Decimal('100'), '商户A', '描述B')

        keys = [key1, key2, key3, key4, key5, key6]
        assert len(set(keys)) == 6, '所有不同输入应产生不同的键'

    def test_empty_description(self):
        """测试空描述"""
        result = generate_unique_key(
            source='alipay',
            trans_date='2024-01-15',
            amount=Decimal('50'),
            merchant='商户',
            description='',
        )
        assert isinstance(result, str)
        assert len(result) == 16

    def test_empty_merchant(self):
        """测试空商户名"""
        result = generate_unique_key(
            source='wechat',
            trans_date='2024-06-01',
            amount=Decimal('10'),
            merchant='',
            description='测试',
        )
        assert isinstance(result, str)
        assert len(result) == 16

    def test_long_description_truncated(self):
        """测试超长描述被截断到50字符"""
        long_desc = 'A' * 200
        result = generate_unique_key(
            source='alipay',
            trans_date='2024-01-01',
            amount=Decimal('1'),
            merchant='M',
            description=long_desc,
        )
        # 应该使用前50字符
        short_desc = long_desc[:50]
        expected = generate_unique_key(
            source='alipay',
            trans_date='2024-01-01',
            amount=Decimal('1'),
            merchant='M',
            description=short_desc,
        )
        assert result == expected

    def test_description_exactly_50_chars(self):
        """测试描述恰好50字符"""
        desc_50 = 'A' * 50
        result = generate_unique_key(
            source='alipay',
            trans_date='2024-01-01',
            amount=Decimal('1'),
            merchant='M',
            description=desc_50,
        )
        assert isinstance(result, str)
        assert len(result) == 16

    def test_zero_amount(self):
        """测试金额为0"""
        result = generate_unique_key(
            source='alipay',
            trans_date='2024-01-01',
            amount=Decimal('0'),
            merchant='M',
            description='测试',
        )
        assert isinstance(result, str)
        assert len(result) == 16

    def test_large_amount(self):
        """测试大金额"""
        result = generate_unique_key(
            source='alipay',
            trans_date='2024-01-01',
            amount=Decimal('9999999999.99'),
            merchant='M',
            description='测试',
        )
        assert isinstance(result, str)
        assert len(result) == 16

    def test_special_characters_in_description(self):
        """测试描述中的特殊字符"""
        result = generate_unique_key(
            source='alipay',
            trans_date='2024-01-01',
            amount=Decimal('100'),
            merchant='商户|特殊',
            description='描述|特殊,字符;测试',
        )
        assert isinstance(result, str)
        assert len(result) == 16

    def test_hex_format(self):
        """测试返回的是十六进制字符串"""
        result = generate_unique_key(
            source='test',
            trans_date='2024-01-01',
            amount=Decimal('1'),
            merchant='m',
            description='d',
        )
        # MD5 十六进制只包含 0-9 a-f
        assert all(c in '0123456789abcdef' for c in result)


class TestDetectSource:
    """测试 detect_source 函数"""

    # ── 支付宝 ──────────────────────────────
    def test_detect_alipay_chinese(self):
        """支付宝 - 中文文件名"""
        assert detect_source('支付宝账单_202406.csv') == 'alipay'

    def test_detect_alipay_english(self):
        """支付宝 - 英文文件名"""
        assert detect_source('alipay_record.csv') == 'alipay'

    def test_detect_alipay_yuebao(self):
        """支付宝 - 余额宝"""
        assert detect_source('余额宝收益明细.xlsx') == 'alipay'

    def test_detect_alipay_case_insensitive(self):
        """支付宝 - 大小写不敏感"""
        assert detect_source('Alipay_Record.CSV') == 'alipay'

    # ── 微信 ──────────────────────────────────
    def test_detect_wechat_chinese(self):
        """微信 - 中文文件名"""
        assert detect_source('微信支付账单_202406.csv') == 'wechat'

    def test_detect_wechat_english(self):
        """微信 - 英文文件名"""
        assert detect_source('wechat_bill.csv') == 'wechat'

    def test_detect_wechat_lingqian(self):
        """微信 - 零钱"""
        assert detect_source('零钱明细.csv') == 'wechat'

    # ── 京东 ──────────────────────────────────
    def test_detect_jd_chinese(self):
        """京东 - 中文文件名"""
        assert detect_source('京东订单_2024.csv') == 'jd'

    def test_detect_jd_english(self):
        """京东 - 英文文件名"""
        assert detect_source('jd_orders.xlsx') == 'jd'

    # ── 美团 ─────────────────────────────────
    def test_detect_meituan_chinese(self):
        """美团 - 中文文件名"""
        assert detect_source('美团外卖订单.csv') == 'meituan'

    def test_detect_meituan_english(self):
        """美团 - 英文文件名"""
        assert detect_source('meituan_orders.csv') == 'meituan'

    # ── 抖音 ──────────────────────────────────
    def test_detect_douyin_chinese(self):
        """抖音 - 中文文件名"""
        assert detect_source('抖音月付账单.csv') == 'douyin'

    def test_detect_douyin_english(self):
        """抖音 - 英文文件名"""
        assert detect_source('douyin_payment.csv') == 'douyin'

    # ── 交通银行储蓄卡 ────────────────────────
    def test_detect_bocom_debit_chinese(self):
        """交通银行储蓄卡 - 中文文件名"""
        assert detect_source('交通银行储蓄卡账单.pdf') == 'bocom_debit'

    def test_detect_bocom_debit_short(self):
        """交通银行储蓄卡 - 简称"""
        assert detect_source('交行流水_2024.csv') == 'bocom_debit'

    def test_detect_bocom_debit_english(self):
        """交通银行储蓄卡 - 英文"""
        assert detect_source('bocom_statement.pdf') == 'bocom_debit'

    # ── 招商银行储蓄卡 ────────────────────────
    def test_detect_cmb_debit_chinese(self):
        """招商银行储蓄卡 - 中文文件名"""
        assert detect_source('招商银行储蓄卡流水.csv') == 'cmb_debit'

    def test_detect_cmb_debit_full(self):
        """招商银行储蓄卡 - 招商银行"""
        assert detect_source('招商银行交易明细.xlsx') == 'cmb_debit'

    def test_detect_cmb_debit_short(self):
        """招商银行储蓄卡 - 简称"""
        assert detect_source('招行储蓄流水.csv') == 'cmb_debit'

    # ── 中信信用卡 ────────────────────────────
    def test_detect_cib_credit_chinese(self):
        """中信信用卡 - 中文文件名"""
        assert detect_source('中信信用卡账单.pdf') == 'cib_credit'

    def test_detect_cib_credit_english(self):
        """中信信用卡 - 英文文件名"""
        assert detect_source('cib_credit_statement.csv') == 'cib_credit'

    def test_detect_cib_credit_short(self):
        """中信信用卡 - 中信"""
        assert detect_source('中信账单_2024.csv') == 'cib_credit'

    # ── 招商银行信用卡 ────────────────────────
    def test_detect_cmb_credit_chinese(self):
        """招商银行信用卡 - 中文文件名（需含"信用卡"才能匹配 cmb_credit）"""
        # '招商银行' 会被 cmb_debit 先匹配，所以需要 '招商信用卡' 来匹配 cmb_credit
        assert detect_source('招商信用卡账单.pdf') == 'cmb_credit'

    def test_detect_cmb_credit_short(self):
        """招商银行信用卡 - 简称"""
        assert detect_source('招行信用卡账单.csv') == 'cmb_credit'

    def test_detect_cmb_credit_english(self):
        """招商银行信用卡 - 英文"""
        assert detect_source('cmb_credit_2024.csv') == 'cmb_credit'

    # ── 不匹配 ────────────────────────────────
    def test_no_match_returns_none(self):
        """测试不匹配返回 None"""
        assert detect_source('unknown_bank_statement.csv') is None
        assert detect_source('random_file.xlsx') is None
        assert detect_source('') is None

    def test_no_match_empty_string(self):
        """测试空字符串返回 None"""
        assert detect_source('') is None

    def test_no_match_nonexistent_bank(self):
        """测试不存在的银行"""
        assert detect_source('建设银行账单.csv') is None

    # ── 清理时间戳后匹配 ─────────────────────
    def test_clean_timestamp_suffix(self):
        """测试清理时间戳后缀后匹配"""
        assert detect_source('支付宝_20240629_123456.csv') == 'alipay'
        assert detect_source('微信支付账单-20240629.csv') == 'wechat'
        assert detect_source('京东订单_20240629.csv') == 'jd'

    def test_clean_timestamp_no_seconds(self):
        """测试清理无秒部分的时间戳"""
        assert detect_source('支付宝_20240629.csv') == 'alipay'

    # ── 兜底匹配（原始文件名） ────────────────
    def test_fallback_original_filename(self):
        """测试兜底用原始文件名匹配"""
        # 清理后可能丢失关键词，但原始文件名有
        assert detect_source('20240629_支付宝_账单.csv') == 'alipay'

    def test_fallback_only_original_matches(self):
        """测试清理后不匹配，但原始文件名匹配（命中兜底return source分支）"""
        # 构造文件名：清理后所有关键词被去除，但原始文件名有
        # 使用mock让re.sub返回不含关键词的结果，强制走兜底路径
        import re as _re_module
        from unittest import mock
        # 原始文件名含 'bocom'，mock re.sub 让它清理后变成 'clean.csv'（不含任何关键词）
        with mock.patch('re.sub', return_value='clean.csv'):
            assert detect_source('bocom_data.csv') == 'bocom_debit'

    def test_fallback_second_match_returns_source(self):
        """测试兜底第二次匹配成功时返回source（行59分支）"""
        from unittest import mock
        # mock 清理结果为空，不匹配任何来源
        # 然后原始文件名匹配 'alipay'
        with mock.patch('re.sub', return_value=''):
            assert detect_source('alipay_record.csv') == 'alipay'

    # ── 特殊字符 ──────────────────────────────
    def test_special_characters_in_filename(self):
        """测试文件名含特殊字符"""
        assert detect_source('支付宝（账单）_2024.csv') == 'alipay'
        assert detect_source('wechat-bill (1).csv') == 'wechat'

    # ── SOURCE_FILENAME_PATTERNS 完整性 ───────
    def test_source_filename_patterns_coverage(self):
        """测试所有定义在 SOURCE_FILENAME_PATTERNS 中的来源都可识别"""
        expected_sources = set(SOURCE_FILENAME_PATTERNS.keys())
        assert 'alipay' in expected_sources
        assert 'jd' in expected_sources
        assert 'meituan' in expected_sources
        assert 'wechat' in expected_sources
        assert 'douyin' in expected_sources
        assert 'bocom_debit' in expected_sources
        assert 'cib_credit' in expected_sources
        assert 'cmb_debit' in expected_sources
        assert 'cmb_credit' in expected_sources
        assert len(expected_sources) == 9

    # ── PDF_CONTENT_SIGNATURES 完整性 ─────────
    def test_pdf_content_signatures_coverage(self):
        """测试 PDF_CONTENT_SIGNATURES 定义了5个来源"""
        expected = {'bocom_debit', 'cmb_debit', 'cib_credit', 'cmb_credit', 'douyin'}
        assert set(PDF_CONTENT_SIGNATURES.keys()) == expected

    # ── 优先级测试 ────────────────────────────
    def test_priority_first_match_wins(self):
        """测试字典顺序决定匹配优先级（alipay 在 wechat 之前）"""
        # 文件名同时匹配支付宝和微信时，应返回先遍历到的
        # SOURCE_FILENAME_PATTERNS 中 alipay 在 wechat 之前
        result = detect_source('支付宝微信账单.csv')
        assert result == 'alipay'

    def test_cmb_debit_before_cmb_credit(self):
        """测试招商银行匹配优先级（cmb_debit 在 cmb_credit 之前）"""
        result = detect_source('招商银行账单.pdf')
        # cmb_debit 在 cmb_credit 之前，先匹配到 '招商银行'
        assert result == 'cmb_debit'
