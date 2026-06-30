"""
测试 Admin 注册 - 所有 Admin 类验证
"""
import pytest
from django.contrib.admin import site
from django.test import override_settings


@pytest.mark.django_db
class TestAdminRegistration:
    """验证所有 Admin 类已正确注册"""

    def test_account_admin_registered(self):
        """AccountAdmin 已注册"""
        from apps.accounts.models import Account
        assert site.is_registered(Account)

    def test_account_admin_config(self):
        """AccountAdmin 配置验证"""
        from apps.accounts.models import Account
        model_admin = site._registry[Account]
        assert 'name' in model_admin.list_display
        assert 'account_type' in model_admin.list_display
        assert 'is_active' in model_admin.list_display
        assert 'account_type' in model_admin.list_filter
        assert 'is_active' in model_admin.list_editable

    def test_category_admin_registered(self):
        """CategoryAdmin 已注册"""
        from apps.categories.models import Category
        assert site.is_registered(Category)

    def test_category_admin_config(self):
        """CategoryAdmin 配置验证"""
        from apps.categories.models import Category
        model_admin = site._registry[Category]
        assert 'name' in model_admin.list_display
        assert 'type' in model_admin.list_display
        assert 'is_active' in model_admin.list_display
        assert 'type' in model_admin.list_filter
        assert 'is_active' in model_admin.list_filter
        assert 'is_active' in model_admin.list_editable
        assert 'sort_order' in model_admin.list_editable

    def test_transaction_admin_registered(self):
        """TransactionAdmin 已注册"""
        from apps.transactions.models import Transaction
        assert site.is_registered(Transaction)

    def test_transaction_admin_config(self):
        """TransactionAdmin 配置验证"""
        from apps.transactions.models import Transaction
        model_admin = site._registry[Transaction]
        assert 'trans_date' in model_admin.list_display
        assert 'amount' in model_admin.list_display
        assert 'direction' in model_admin.list_display
        assert 'source' in model_admin.list_filter
        assert 'status' in model_admin.list_filter
        assert 'direction' in model_admin.list_filter
        assert 'created_at' in model_admin.readonly_fields

    def test_valid_rule_admin_registered(self):
        """ValidRuleAdmin 已注册"""
        from apps.rules.models import ValidRule
        assert site.is_registered(ValidRule)

    def test_valid_rule_admin_config(self):
        """ValidRuleAdmin 配置验证"""
        from apps.rules.models import ValidRule
        model_admin = site._registry[ValidRule]
        assert 'name' in model_admin.list_display
        assert 'priority' in model_admin.list_display
        assert 'is_active' in model_admin.list_display
        assert 'hit_count' in model_admin.list_display
        assert 'is_active' in model_admin.list_filter
        assert 'is_active' in model_admin.list_editable
        assert 'hit_count' in model_admin.readonly_fields

    def test_invalid_rule_admin_registered(self):
        """InvalidRuleAdmin 已注册"""
        from apps.rules.models import InvalidRule
        assert site.is_registered(InvalidRule)

    def test_invalid_rule_admin_config(self):
        """InvalidRuleAdmin 配置验证"""
        from apps.rules.models import InvalidRule
        model_admin = site._registry[InvalidRule]
        assert 'name' in model_admin.list_display
        assert 'counterparties' in model_admin.list_display

    def test_import_log_admin_registered(self):
        """ImportLogAdmin 已注册"""
        from apps.imports.models import ImportLog
        assert site.is_registered(ImportLog)

    def test_import_log_admin_config(self):
        """ImportLogAdmin 配置验证"""
        from apps.imports.models import ImportLog
        model_admin = site._registry[ImportLog]
        assert 'source_file' in model_admin.list_display
        assert 'source' in model_admin.list_display
        assert 'status' in model_admin.list_display
        assert 'source' in model_admin.list_filter
        assert 'status' in model_admin.list_filter

    def test_transaction_pair_admin_registered(self):
        """TransactionPairAdmin 已注册"""
        from apps.settlements.models import TransactionPair
        assert site.is_registered(TransactionPair)

    def test_transaction_pair_admin_config(self):
        """TransactionPairAdmin 配置验证"""
        from apps.settlements.models import TransactionPair
        model_admin = site._registry[TransactionPair]
        assert 'expense_tx' in model_admin.list_display
        assert 'refund_tx' in model_admin.list_display
        assert 'match_score' in model_admin.list_display
        assert 'match_method' in model_admin.list_filter

    def test_settlement_group_admin_registered(self):
        """SettlementGroupAdmin 已注册"""
        from apps.settlements.models import SettlementGroup
        assert site.is_registered(SettlementGroup)

    def test_settlement_group_admin_config(self):
        """SettlementGroupAdmin 配置验证"""
        from apps.settlements.models import SettlementGroup
        model_admin = site._registry[SettlementGroup]
        assert 'name' in model_admin.list_display
        assert 'status' in model_admin.list_display
        assert 'is_aa' in model_admin.list_display
        assert 'status' in model_admin.list_filter
        assert 'is_aa' in model_admin.list_filter
        # 验证 inline
        assert len(model_admin.inlines) == 1
