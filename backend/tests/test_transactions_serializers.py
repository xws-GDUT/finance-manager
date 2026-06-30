"""
测试 transactions.serializers
"""
import pytest
from datetime import date
from apps.transactions.serializers import TransactionListSerializer, TransactionUpdateSerializer
from apps.transactions.models import Transaction
from apps.accounts.models import Account
from apps.categories.models import Category
from apps.rules.models import ValidRule, InvalidRule


@pytest.mark.django_db
class TestTransactionListSerializer:
    """测试 TransactionListSerializer"""

    def test_serialization_output(self):
        """序列化输出验证"""
        account = Account.objects.create(name='测试账户', account_type='debit')
        category = Category.objects.create(name='餐饮', icon='🍔', type='expense')
        tx = Transaction.objects.create(
            trans_date='2024-01-15', amount=150, direction='expense',
            source='alipay', status='confirmed',
            description='午餐', merchant='测试餐厅',
            account=account, category=category,
            unique_key='ser_key1'
        )

        serializer = TransactionListSerializer(tx)
        data = serializer.data
        assert data['amount'] == '150.00'
        assert data['direction'] == 'expense'
        assert data['direction_display'] == '支出'
        assert data['source'] == 'alipay'
        assert data['source_display'] == '支付宝'
        assert data['status'] == 'confirmed'
        assert data['status_display'] == '有效'
        assert data['category_name'] == '餐饮'
        assert data['category_icon'] == '🍔'
        assert data['category_type'] == 'expense'
        assert data['account_name'] == '测试账户'
        assert data['description'] == '午餐'
        assert data['merchant'] == '测试餐厅'

    def test_serialization_with_none_relations(self):
        """序列化：关联字段为 None"""
        tx = Transaction.objects.create(
            trans_date='2024-01-15', amount=150, direction='expense',
            source='alipay', status='confirmed',
            unique_key='ser_key_none'
        )

        serializer = TransactionListSerializer(tx)
        data = serializer.data
        assert data['category_name'] == ''
        assert data['category_icon'] == ''
        assert data['category_type'] == ''
        assert data['account_name'] == ''
        assert data['valid_rule_name'] == ''
        assert data['invalid_rule_name'] == ''

    def test_status_reason_virtual(self):
        """status_reason: is_virtual 虚拟交易"""
        tx = Transaction.objects.create(
            trans_date='2024-01-15', amount=150, direction='expense',
            source='alipay', status='confirmed', is_virtual=True,
            unique_key='ser_virtual'
        )

        serializer = TransactionListSerializer(tx)
        reasons = serializer.data['status_reason']
        assert len(reasons) == 1
        assert reasons[0]['type'] == 'virtual'

    def test_status_reason_valid_rule(self):
        """status_reason: 有效规则"""
        rule = ValidRule.objects.create(name='测试规则', priority=50)
        tx = Transaction.objects.create(
            trans_date='2024-01-15', amount=150, direction='expense',
            source='alipay', status='confirmed', valid_rule=rule,
            unique_key='ser_vrule'
        )

        serializer = TransactionListSerializer(tx)
        reasons = serializer.data['status_reason']
        assert any(r['type'] == 'valid_rule' for r in reasons)

    def test_status_reason_invalid_rule(self):
        """status_reason: 无效规则"""
        rule = InvalidRule.objects.create(name='无效测试', priority=50)
        tx = Transaction.objects.create(
            trans_date='2024-01-15', amount=150, direction='expense',
            source='alipay', status='excluded', invalid_rule=rule,
            unique_key='ser_irule'
        )

        serializer = TransactionListSerializer(tx)
        reasons = serializer.data['status_reason']
        assert any(r['type'] == 'invalid_rule' for r in reasons)

    def test_status_reason_settlement(self):
        """status_reason: 垫付结算（行48）"""
        from apps.settlements.models import SettlementGroup
        group = SettlementGroup.objects.create(name='测试结算', status='open')
        tx = Transaction.objects.create(
            trans_date='2024-01-15', amount=150, direction='expense',
            source='alipay', status='confirmed', settlement=group,
            unique_key='ser_settle'
        )

        serializer = TransactionListSerializer(tx)
        reasons = serializer.data['status_reason']
        assert any(r['type'] == 'settlement' for r in reasons)

    def test_status_reason_refund_pair(self):
        """status_reason: 退款配对（行50）"""
        from apps.settlements.models import TransactionPair
        # 需要先创建两个交易用于配对
        account = Account.objects.create(name='测试账户2', account_type='debit')
        tx_expense = Transaction.objects.create(
            trans_date='2024-01-15', amount=100, direction='expense',
            source='alipay', status='excluded', account=account,
            unique_key='ser_pair_e2'
        )
        tx_refund = Transaction.objects.create(
            trans_date='2024-01-16', amount=100, direction='income',
            source='alipay', status='excluded', account=account,
            unique_key='ser_pair_r2'
        )
        pair = TransactionPair.objects.create(
            expense_tx=tx_expense, refund_tx=tx_refund,
            match_score=100, match_method='auto',
        )
        # 设置 pair 关系到交易
        tx_expense.pair = pair
        tx_expense.save(update_fields=['pair'])

        serializer = TransactionListSerializer(tx_expense)
        reasons = serializer.data['status_reason']
        assert any(r['type'] == 'refund_pair' for r in reasons)

    def test_create_generates_unique_key(self):
        """create 自动生成 unique_key"""
        account = Account.objects.create(name='测试账户', account_type='debit')
        data = {
            'trans_date': '2024-01-15',
            'amount': '150.00',
            'direction': 'expense',
            'source': 'alipay',
            'description': '午餐',
            'merchant': '测试餐厅',
            'account': account.id,
        }
        serializer = TransactionListSerializer(data=data)
        assert serializer.is_valid()
        instance = serializer.save()
        assert instance.unique_key
        assert instance.unique_key.endswith('_manual')

    def test_create_preserves_existing_unique_key(self):
        """create 保留已有的 unique_key"""
        account = Account.objects.create(name='测试账户', account_type='debit')
        data = {
            'trans_date': '2024-01-15',
            'amount': '150.00',
            'direction': 'expense',
            'source': 'alipay',
            'description': '午餐',
            'account': account.id,
            'unique_key': 'my_custom_key',
        }
        serializer = TransactionListSerializer(data=data)
        assert serializer.is_valid()
        instance = serializer.save()
        assert instance.unique_key == 'my_custom_key'


@pytest.mark.django_db
class TestTransactionUpdateSerializer:
    """测试 TransactionUpdateSerializer"""

    def test_partial_update_fields(self):
        """部分更新字段验证：只允许 category 和 remark"""
        serializer = TransactionUpdateSerializer()
        fields = serializer.Meta.fields
        assert 'category' in fields
        assert 'remark' in fields
        assert 'amount' not in fields
        assert 'direction' not in fields

    def test_update_only_category(self):
        """只更新 category"""
        account = Account.objects.create(name='测试账户', account_type='debit')
        category = Category.objects.create(name='交通', type='expense')
        tx = Transaction.objects.create(
            trans_date='2024-01-15', amount=150, direction='expense',
            source='alipay', status='confirmed', account=account,
            unique_key='upd_cat'
        )

        serializer = TransactionUpdateSerializer(tx, data={'category': category.id}, partial=True)
        assert serializer.is_valid()
        updated = serializer.save()
        assert updated.category_id == category.id

    def test_update_only_remark(self):
        """只更新 remark"""
        account = Account.objects.create(name='测试账户', account_type='debit')
        tx = Transaction.objects.create(
            trans_date='2024-01-15', amount=150, direction='expense',
            source='alipay', status='confirmed', account=account,
            unique_key='upd_rem'
        )

        serializer = TransactionUpdateSerializer(tx, data={'remark': '新备注'}, partial=True)
        assert serializer.is_valid()
        updated = serializer.save()
        assert updated.remark == '新备注'

    def test_update_both_fields(self):
        """同时更新 category 和 remark"""
        account = Account.objects.create(name='测试账户', account_type='debit')
        category = Category.objects.create(name='餐饮', type='expense')
        tx = Transaction.objects.create(
            trans_date='2024-01-15', amount=150, direction='expense',
            source='alipay', status='confirmed', account=account,
            unique_key='upd_both'
        )

        serializer = TransactionUpdateSerializer(tx, data={
            'category': category.id, 'remark': '更新备注'
        })
        assert serializer.is_valid()
        updated = serializer.save()
        assert updated.category_id == category.id
        assert updated.remark == '更新备注'
