"""
测试 ImportService 流水导入服务
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from decimal import Decimal
from datetime import date
from apps.imports.services import ImportService, SOURCE_ACCOUNT_MAP


class TestGenerateKey:
    """测试 _generate_key 静态方法"""

    def test_generate_key(self):
        """测试去重key生成"""
        row = {
            'trans_date': '2026-06-20',
            'amount': Decimal('100.50'),
            'merchant': '测试商户',
            'description': '午餐消费',
        }
        key = ImportService._generate_key('alipay', row)
        assert isinstance(key, str)
        assert len(key) == 16

    def test_generate_key_deterministic(self):
        """测试相同输入生成相同key"""
        row = {
            'trans_date': '2026-06-20',
            'amount': Decimal('100'),
            'merchant': '商户A',
            'description': '描述A',
        }
        key1 = ImportService._generate_key('alipay', row)
        key2 = ImportService._generate_key('alipay', row)
        assert key1 == key2

    def test_generate_key_different_source(self):
        """测试不同来源生成不同key"""
        row = {
            'trans_date': '2026-06-20',
            'amount': Decimal('100'),
            'merchant': '商户A',
            'description': '描述A',
        }
        key1 = ImportService._generate_key('alipay', row)
        key2 = ImportService._generate_key('wechat', row)
        assert key1 != key2

    def test_generate_key_different_amount(self):
        """测试不同金额生成不同key"""
        row1 = {
            'trans_date': '2026-06-20',
            'amount': Decimal('100'),
            'merchant': '商户A',
            'description': '描述A',
        }
        row2 = {
            'trans_date': '2026-06-20',
            'amount': Decimal('200'),
            'merchant': '商户A',
            'description': '描述A',
        }
        key1 = ImportService._generate_key('alipay', row1)
        key2 = ImportService._generate_key('alipay', row2)
        assert key1 != key2

    def test_generate_key_long_description_truncated(self):
        """测试超长描述被截断到50字符"""
        long_desc = 'A' * 200
        short_desc = 'A' * 50
        row1 = {
            'trans_date': '2026-06-20',
            'amount': Decimal('100'),
            'merchant': 'M',
            'description': long_desc,
        }
        row2 = {
            'trans_date': '2026-06-20',
            'amount': Decimal('100'),
            'merchant': 'M',
            'description': short_desc,
        }
        key1 = ImportService._generate_key('alipay', row1)
        key2 = ImportService._generate_key('alipay', row2)
        assert key1 == key2

    def test_generate_key_empty_description(self):
        """测试空描述"""
        row = {
            'trans_date': '2026-06-20',
            'amount': Decimal('100'),
            'merchant': '',
            'description': '',
        }
        key = ImportService._generate_key('alipay', row)
        assert isinstance(key, str)
        assert len(key) == 16


@pytest.mark.django_db
class TestMatchOrCreateAccount:
    """测试 _match_or_create_account 方法"""

    def test_known_source_alipay(self):
        """测试已知来源：支付宝"""
        mock_account = MagicMock()
        mock_account_model = MagicMock()
        mock_account_model.objects.get_or_create.return_value = (mock_account, False)

        service = ImportService.__new__(ImportService)
        service.Account = mock_account_model

        result = service._match_or_create_account('alipay')

        assert result == mock_account
        mock_account_model.objects.get_or_create.assert_called_once()
        call_kwargs = mock_account_model.objects.get_or_create.call_args[1]
        assert call_kwargs['name'] == '支付宝'

    def test_known_source_wechat(self):
        """测试已知来源：微信"""
        mock_account = MagicMock()
        mock_account_model = MagicMock()
        mock_account_model.objects.get_or_create.return_value = (mock_account, False)

        service = ImportService.__new__(ImportService)
        service.Account = mock_account_model

        result = service._match_or_create_account('wechat')

        assert result == mock_account
        call_kwargs = mock_account_model.objects.get_or_create.call_args[1]
        assert call_kwargs['name'] == '微信支付'

    def test_unknown_source(self):
        """测试未知来源返回 None"""
        service = ImportService.__new__(ImportService)
        mock_account_model = MagicMock()
        service.Account = mock_account_model

        result = service._match_or_create_account('unknown_source')

        assert result is None
        mock_account_model.objects.get_or_create.assert_not_called()

    def test_create_new_account(self):
        """测试自动创建新账户"""
        mock_account = MagicMock()
        mock_account_model = MagicMock()
        mock_account_model.objects.get_or_create.return_value = (mock_account, True)

        service = ImportService.__new__(ImportService)
        service.Account = mock_account_model

        result = service._match_or_create_account('bocom_debit')

        assert result == mock_account
        call_kwargs = mock_account_model.objects.get_or_create.call_args[1]
        assert call_kwargs['name'] == '交通银行储蓄卡'
        assert call_kwargs['defaults']['account_type'] == 'debit'


@pytest.mark.django_db
class TestCreateTransaction:
    """测试 _create_transaction 方法"""

    def test_new_transaction(self):
        """测试创建新交易"""
        service = ImportService.__new__(ImportService)

        mock_T = MagicMock()
        mock_T.objects.filter.return_value.exists.return_value = False
        service.Transaction = mock_T

        mock_account = MagicMock()
        service._match_or_create_account = MagicMock(return_value=mock_account)
        service._generate_key = MagicMock(return_value='test_key_123456')

        categorizer_mock = MagicMock()
        categorizer_mock.classify.return_value = 5
        service.categorizer = categorizer_mock

        row = {
            'trans_date': '2026-06-20',
            'amount': Decimal('100'),
            'direction': 'expense',
            'trans_type': '餐饮',
            'description': '午餐',
            'merchant': '海底捞',
            'counterparty': '海底捞',
            'payment_method': '支付宝',
            'payment_channel': '支付宝',
        }

        result = {'skipped_rows': 0, 'imported_rows': 0}
        tx = service._create_transaction(row, 'alipay', result)

        assert tx is not None
        assert result.get('imported_rows', 0) == 1

    def test_duplicate_transaction(self):
        """测试重复交易被跳过"""
        service = ImportService.__new__(ImportService)

        mock_T = MagicMock()
        mock_T.objects.filter.return_value.exists.return_value = True
        service.Transaction = mock_T

        service._generate_key = MagicMock(return_value='dup_key_123456')

        row = {
            'trans_date': '2026-06-20',
            'amount': Decimal('100'),
            'direction': 'expense',
        }

        result = {'skipped_rows': 0, 'imported_rows': 0}
        tx = service._create_transaction(row, 'alipay', result)

        assert tx is None
        assert result['skipped_rows'] == 1


@pytest.mark.django_db
class TestApplyRules:
    """测试 _apply_rules 方法"""

    def test_apply_rules_valid_only(self):
        """测试只命中有效规则"""
        service = ImportService.__new__(ImportService)

        mock_valid_engine = MagicMock()
        mock_valid_engine.match.return_value = 1
        service.valid_engine = mock_valid_engine

        mock_invalid_engine = MagicMock()
        mock_invalid_engine.match.return_value = None
        service.invalid_engine = mock_invalid_engine

        tx = MagicMock()
        tx.valid_rule_id = None
        tx.invalid_rule_id = None

        service._apply_rules(tx)

        assert tx.valid_rule_id == 1
        assert tx.status == 'confirmed'
        tx.save.assert_called_once()

    def test_apply_rules_invalid_only(self):
        """测试只命中无效规则"""
        service = ImportService.__new__(ImportService)

        mock_valid_engine = MagicMock()
        mock_valid_engine.match.return_value = None
        service.valid_engine = mock_valid_engine

        mock_invalid_engine = MagicMock()
        mock_invalid_engine.match.return_value = 1
        service.invalid_engine = mock_invalid_engine

        tx = MagicMock()
        tx.valid_rule_id = None
        tx.invalid_rule_id = None

        service._apply_rules(tx)

        assert tx.invalid_rule_id == 1
        assert tx.status == 'excluded'
        tx.save.assert_called_once()

    def test_apply_rules_both_match(self):
        """测试同时命中有效和无效规则（无效覆盖有效）"""
        service = ImportService.__new__(ImportService)

        mock_valid_engine = MagicMock()
        mock_valid_engine.match.return_value = 1
        service.valid_engine = mock_valid_engine

        mock_invalid_engine = MagicMock()
        mock_invalid_engine.match.return_value = 2
        service.invalid_engine = mock_invalid_engine

        tx = MagicMock()
        tx.valid_rule_id = None
        tx.invalid_rule_id = None

        service._apply_rules(tx)

        # 无效规则应覆盖有效规则
        assert tx.valid_rule_id == 1
        assert tx.invalid_rule_id == 2
        assert tx.status == 'excluded'  # 无效优先
        tx.save.assert_called_once()

    def test_apply_rules_neither_match(self):
        """测试都不命中"""
        service = ImportService.__new__(ImportService)

        mock_valid_engine = MagicMock()
        mock_valid_engine.match.return_value = None
        service.valid_engine = mock_valid_engine

        mock_invalid_engine = MagicMock()
        mock_invalid_engine.match.return_value = None
        service.invalid_engine = mock_invalid_engine

        tx = MagicMock()
        tx.valid_rule_id = None
        tx.invalid_rule_id = None

        service._apply_rules(tx)

        # 没有变化，不调用 save
        tx.save.assert_not_called()


@pytest.mark.django_db
class TestApplyRulesBatch:
    """测试 _apply_rules_batch 方法"""

    def test_apply_rules_batch(self):
        """测试批量应用规则"""
        service = ImportService.__new__(ImportService)

        mock_valid_engine = MagicMock()
        mock_valid_engine.match.side_effect = [1, None, 1]
        service.valid_engine = mock_valid_engine

        mock_invalid_engine = MagicMock()
        mock_invalid_engine.match.side_effect = [None, 2, 3]
        service.invalid_engine = mock_invalid_engine

        mock_T = MagicMock()
        service.Transaction = mock_T

        tx1 = MagicMock()
        tx1.valid_rule_id = None
        tx1.invalid_rule_id = None

        tx2 = MagicMock()
        tx2.valid_rule_id = None
        tx2.invalid_rule_id = None

        tx3 = MagicMock()
        tx3.valid_rule_id = None
        tx3.invalid_rule_id = None

        service._apply_rules_batch([tx1, tx2, tx3])

        # tx1: 有效规则命中
        assert tx1.valid_rule_id == 1
        assert tx1.status == 'confirmed'

        # tx2: 无效规则命中
        assert tx2.invalid_rule_id == 2
        assert tx2.status == 'excluded'

        # tx3: 两者都命中，无效覆盖
        assert tx3.valid_rule_id == 1
        assert tx3.invalid_rule_id == 3
        assert tx3.status == 'excluded'

        mock_T.objects.bulk_update.assert_called_once()

    def test_apply_rules_batch_empty(self):
        """测试空列表"""
        service = ImportService.__new__(ImportService)
        mock_T = MagicMock()
        service.Transaction = mock_T

        service._apply_rules_batch([])

        mock_T.objects.bulk_update.assert_not_called()


@pytest.mark.django_db
class TestLogImport:
    """测试 _log_import 方法"""

    def test_log_import_success(self):
        """测试成功导入日志"""
        service = ImportService.__new__(ImportService)

        mock_ImportLog = MagicMock()
        service.ImportLog = mock_ImportLog

        result = {
            'success': True,
            'total_rows': 100,
            'imported_rows': 95,
            'skipped_rows': 5,
            'error_rows': 0,
            'errors': [],
        }

        service._log_import('test.csv', 'alipay', result, 1024)

        mock_ImportLog.objects.create.assert_called_once()
        call_kwargs = mock_ImportLog.objects.create.call_args[1]
        assert call_kwargs['source'] == 'alipay'
        assert call_kwargs['source_file'] == 'test.csv'
        assert call_kwargs['status'] == 'success'

    def test_log_import_partial(self):
        """测试部分成功导入日志"""
        service = ImportService.__new__(ImportService)

        mock_ImportLog = MagicMock()
        service.ImportLog = mock_ImportLog

        result = {
            'success': True,
            'total_rows': 100,
            'imported_rows': 90,
            'skipped_rows': 5,
            'error_rows': 5,
            'errors': ['行处理失败: parse error'],
        }

        service._log_import('test.csv', 'wechat', result, 2048)

        call_kwargs = mock_ImportLog.objects.create.call_args[1]
        assert call_kwargs['status'] == 'partial'
        assert call_kwargs['error_rows'] == 5


@pytest.mark.django_db
class TestImportFile:
    """测试 import_file 完整导入流程"""

    @pytest.fixture
    def service(self):
        """创建带有 mock 依赖的 ImportService"""
        service = ImportService.__new__(ImportService)

        # mock 模型
        service.Transaction = MagicMock()
        service.ValidRule = MagicMock()
        service.InvalidRule = MagicMock()
        service.Category = MagicMock()
        service.Account = MagicMock()
        service.ImportLog = MagicMock()

        # mock 引擎
        service.categorizer = MagicMock()
        service.categorizer.classify.return_value = 1

        service.valid_engine = MagicMock()
        service.valid_engine.match.return_value = None

        service.invalid_engine = MagicMock()
        service.invalid_engine.match.return_value = None

        service.refund_engine = MagicMock()

        # mock 方法
        service._generate_key = MagicMock(return_value='mock_key_123456')
        service._match_or_create_account = MagicMock(return_value=MagicMock())
        service._log_import = MagicMock()
        service._apply_rules_batch = MagicMock()

        return service

    def test_import_file_success(self, service):
        """测试完整导入成功流程"""
        parsed_rows = [
            {
                'trans_date': '2026-06-20',
                'amount': Decimal('100'),
                'direction': 'expense',
                'trans_type': '餐饮',
                'description': '午餐',
                'merchant': '海底捞',
                'counterparty': '海底捞',
                'payment_method': '支付宝',
                'payment_channel': '支付宝',
            },
            {
                'trans_date': '2026-06-20',
                'amount': Decimal('50'),
                'direction': 'expense',
                'trans_type': '交通',
                'description': '地铁',
                'merchant': '地铁',
                'counterparty': '',
                'payment_method': '微信支付',
                'payment_channel': '微信支付',
            },
        ]

        # 每个交易生成不同的唯一key
        service._generate_key.side_effect = ['key_001', 'key_002']

        # 重要：Transaction() 调用需要返回 mock 实例
        mock_tx1 = MagicMock()
        mock_tx2 = MagicMock()
        service.Transaction.side_effect = [mock_tx1, mock_tx2]

        # bulk_create 返回创建的实例
        service.Transaction.objects.bulk_create.return_value = [mock_tx1]
        # 第二次 bulk_create 返回
        service.Transaction.objects.bulk_create.side_effect = [
            [mock_tx1], [mock_tx2]
        ]

        with patch('apps.imports.services.parse_file', return_value=(parsed_rows, 'alipay')), \
             patch('apps.imports.services.os.path.getsize', return_value=1024):
            service.Transaction.objects.filter.return_value.values_list.return_value = []

            result = service.import_file('/fake/path.csv', 'alipay_2026.csv')

        assert result['success'] is True
        assert result['source'] == 'alipay'
        assert result['total_rows'] == 2

    def test_import_file_with_duplicates(self, service):
        """测试导入包含重复交易"""
        parsed_rows = [
            {
                'trans_date': '2026-06-20',
                'amount': Decimal('100'),
                'direction': 'expense',
                'trans_type': '餐饮',
                'description': '午餐',
                'merchant': '海底捞',
                'counterparty': '海底捞',
                'payment_method': '支付宝',
                'payment_channel': '支付宝',
            },
        ]

        with patch('apps.imports.services.parse_file', return_value=(parsed_rows, 'alipay')), \
             patch('apps.imports.services.os.path.getsize', return_value=1024):
            service.Transaction.objects.filter.return_value.values_list.return_value = [
                'mock_key_123456'
            ]

            result = service.import_file('/fake/path.csv', 'alipay_2026.csv')

        assert result['success'] is True
        assert result['total_rows'] == 1
        assert result['skipped_rows'] == 1
        assert result['imported_rows'] == 0

    def test_import_file_parse_error(self, service):
        """测试解析失败"""
        with patch('apps.imports.services.parse_file',
                   side_effect=ValueError('无法识别文件来源')):
            result = service.import_file('/fake/path.csv', 'unknown.csv')

        assert result['success'] is False
        assert len(result['errors']) > 0

    def test_import_file_triggers_refund_pairing(self, service):
        """测试导入成功后触发退款配对"""
        parsed_rows = [
            {
                'trans_date': '2026-06-20',
                'amount': Decimal('100'),
                'direction': 'expense',
                'trans_type': '餐饮',
                'description': '午餐',
                'merchant': '海底捞',
                'counterparty': '海底捞',
                'payment_method': '支付宝',
                'payment_channel': '支付宝',
            },
        ]

        service.refund_engine.auto_pair.return_value = {'paired': 1, 'skipped': 0, 'pairs': []}

        with patch('apps.imports.services.parse_file', return_value=(parsed_rows, 'alipay')), \
             patch('apps.imports.services.os.path.getsize', return_value=1024):
            service.Transaction.objects.filter.return_value.values_list.return_value = []
            service.Transaction.objects.bulk_create = MagicMock(
                side_effect=lambda objs: objs
            )

            result = service.import_file('/fake/path.csv', 'alipay_2026.csv')

        assert 'refund_pairs' in result
        service.refund_engine.auto_pair.assert_called_once()

    def test_import_file_refund_pairing_error_not_fatal(self, service):
        """测试退款配对失败不影响导入"""
        parsed_rows = [
            {
                'trans_date': '2026-06-20',
                'amount': Decimal('100'),
                'direction': 'expense',
                'trans_type': '餐饮',
                'description': '午餐',
                'merchant': '海底捞',
                'counterparty': '海底捞',
                'payment_method': '支付宝',
                'payment_channel': '支付宝',
            },
        ]

        service.refund_engine.auto_pair.side_effect = Exception('配对失败')

        with patch('apps.imports.services.parse_file', return_value=(parsed_rows, 'alipay')), \
             patch('apps.imports.services.os.path.getsize', return_value=1024):
            service.Transaction.objects.filter.return_value.values_list.return_value = []
            service.Transaction.objects.bulk_create = MagicMock(
                side_effect=lambda objs: objs
            )

            result = service.import_file('/fake/path.csv', 'alipay_2026.csv')

        assert result['success'] is True


class TestSourceAccountMap:
    """测试 SOURCE_ACCOUNT_MAP 常量"""

    def test_all_sources_have_mapping(self):
        """测试所有数据来源都有映射"""
        expected_sources = {
            'alipay', 'wechat', 'jd', 'meituan', 'douyin',
            'bocom_debit', 'cmb_debit', 'cib_credit', 'cmb_credit',
        }
        assert set(SOURCE_ACCOUNT_MAP.keys()) == expected_sources

    def test_mapping_has_required_fields(self):
        """测试每个映射包含必要字段"""
        for source, info in SOURCE_ACCOUNT_MAP.items():
            assert 'name' in info
            assert 'account_type' in info
            assert 'bank_name' in info
            assert 'match_keywords' in info
            assert info['account_type'] in ('platform', 'debit', 'credit')
