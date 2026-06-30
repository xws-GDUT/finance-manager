"""
测试所有 Django 模型
"""
from datetime import date
from decimal import Decimal

import pytest
from django.db import IntegrityError
from django.db.utils import IntegrityError as DjangoIntegrityError

from apps.accounts.models import Account
from apps.categories.models import Category
from apps.transactions.models import Transaction
from apps.rules.models import ValidRule, InvalidRule
from apps.imports.models import ImportLog
from apps.settlements.models import TransactionPair, SettlementGroup, SettlementItem


# ============================================================
# Account 模型测试
# ============================================================

class TestAccount:
    """测试 Account 模型"""

    @pytest.mark.django_db
    def test_create_account(self):
        """测试创建账户"""
        account = Account.objects.create(
            name='支付宝',
            account_type=Account.TYPE_PLATFORM,
            owner='张三',
        )
        assert account.id is not None
        assert account.name == '支付宝'
        assert account.account_type == Account.TYPE_PLATFORM
        assert account.owner == '张三'
        assert account.is_active is True
        assert account.bank_name == ''
        assert account.match_keywords == ''
        assert account.created_at is not None

    @pytest.mark.django_db
    def test_account_str(self):
        """测试 __str__ 方法"""
        account = Account.objects.create(name='支付宝')
        assert str(account) == '支付宝'

    @pytest.mark.django_db
    def test_account_type_choices(self):
        """测试所有 TYPE_CHOICES"""
        choices = dict(Account.TYPE_CHOICES)
        assert Account.TYPE_DEBIT in choices
        assert Account.TYPE_CREDIT in choices
        assert Account.TYPE_PLATFORM in choices
        assert choices[Account.TYPE_DEBIT] == '储蓄卡'
        assert choices[Account.TYPE_CREDIT] == '信用卡'
        assert choices[Account.TYPE_PLATFORM] == '支付平台'

    @pytest.mark.django_db
    def test_default_account_type(self):
        """测试默认账户类型为 platform"""
        account = Account.objects.create(name='测试账户')
        assert account.account_type == Account.TYPE_PLATFORM

    @pytest.mark.django_db
    def test_default_is_active(self):
        """测试默认 is_active 为 True"""
        account = Account.objects.create(name='测试账户')
        assert account.is_active is True

    @pytest.mark.django_db
    def test_default_bank_name_empty(self):
        """测试默认 bank_name 为空字符串"""
        account = Account.objects.create(name='测试账户')
        assert account.bank_name == ''

    @pytest.mark.django_db
    def test_default_owner_empty(self):
        """测试默认 owner 为空字符串"""
        account = Account.objects.create(name='测试账户')
        assert account.owner == ''

    @pytest.mark.django_db
    def test_default_match_keywords_empty(self):
        """测试默认 match_keywords 为空字符串"""
        account = Account.objects.create(name='测试账户')
        assert account.match_keywords == ''

    @pytest.mark.django_db
    def test_name_unique_constraint(self):
        """测试 name 字段的唯一约束"""
        Account.objects.create(name='唯一账户')
        with pytest.raises(IntegrityError):
            Account.objects.create(name='唯一账户')

    @pytest.mark.django_db
    def test_name_max_length(self):
        """测试 name 最大长度为 50"""
        account = Account.objects.create(name='A' * 50)
        assert account.name == 'A' * 50

    @pytest.mark.django_db
    def test_bank_name_field(self):
        """测试 bank_name 字段"""
        account = Account.objects.create(
            name='招商银行储蓄卡',
            account_type=Account.TYPE_DEBIT,
            bank_name='招商银行',
        )
        assert account.bank_name == '招商银行'

    @pytest.mark.django_db
    def test_match_keywords_field(self):
        """测试 match_keywords 字段"""
        account = Account.objects.create(
            name='微信支付',
            match_keywords='微信,wechat,零钱',
        )
        assert account.match_keywords == '微信,wechat,零钱'

    @pytest.mark.django_db
    def test_debit_account(self):
        """测试储蓄卡类型账户"""
        account = Account.objects.create(
            name='交通银行储蓄卡',
            account_type=Account.TYPE_DEBIT,
            bank_name='交通银行',
        )
        assert account.account_type == Account.TYPE_DEBIT

    @pytest.mark.django_db
    def test_credit_account(self):
        """测试信用卡类型账户"""
        account = Account.objects.create(
            name='招商银行信用卡',
            account_type=Account.TYPE_CREDIT,
            bank_name='招商银行',
        )
        assert account.account_type == Account.TYPE_CREDIT

    @pytest.mark.django_db
    def test_platform_account(self):
        """测试支付平台类型账户"""
        account = Account.objects.create(
            name='支付宝',
            account_type=Account.TYPE_PLATFORM,
        )
        assert account.account_type == Account.TYPE_PLATFORM

    @pytest.mark.django_db
    def test_is_active_false(self):
        """测试 is_active 可设置为 False"""
        account = Account.objects.create(name='已停用账户', is_active=False)
        assert account.is_active is False

    @pytest.mark.django_db
    def test_ordering(self):
        """测试排序按 id"""
        a1 = Account.objects.create(name='账户A')
        a2 = Account.objects.create(name='账户B')
        accounts = list(Account.objects.all())
        assert accounts[0].id <= accounts[1].id


# ============================================================
# Category 模型测试
# ============================================================

class TestCategory:
    """测试 Category 模型"""

    @pytest.mark.django_db
    def test_create_category(self):
        """测试创建分类"""
        category = Category.objects.create(
            name='餐饮',
            type=Category.TYPE_EXPENSE,
            icon='🍔',
            sort_order=1,
        )
        assert category.id is not None
        assert category.name == '餐饮'
        assert category.type == Category.TYPE_EXPENSE
        assert category.icon == '🍔'
        assert category.sort_order == 1
        assert category.is_active is True
        assert category.parent is None
        assert category.created_at is not None

    @pytest.mark.django_db
    def test_category_str(self):
        """测试 __str__ 方法"""
        category = Category.objects.create(name='餐饮', icon='🍔')
        assert str(category) == '🍔 餐饮'

    @pytest.mark.django_db
    def test_category_str_no_icon(self):
        """测试 __str__ 方法（无图标）"""
        category = Category.objects.create(name='其他')
        assert str(category) == ' 其他'

    @pytest.mark.django_db
    def test_is_parent_property_true(self):
        """测试 is_parent property（父分类）"""
        parent = Category.objects.create(name='餐饮')
        assert parent.is_parent is True

    @pytest.mark.django_db
    def test_is_parent_property_false(self):
        """测试 is_parent property（子分类）"""
        parent = Category.objects.create(name='餐饮')
        child = Category.objects.create(name='午餐', parent=parent)
        assert child.is_parent is False

    @pytest.mark.django_db
    def test_parent_self_reference(self):
        """测试 parent 自引用外键"""
        parent = Category.objects.create(name='餐饮')
        child = Category.objects.create(name='午餐', parent=parent)
        assert child.parent == parent
        assert child.parent_id == parent.id

    @pytest.mark.django_db
    def test_children_related_name(self):
        """测试 children related_name"""
        parent = Category.objects.create(name='餐饮')
        child1 = Category.objects.create(name='午餐', parent=parent)
        child2 = Category.objects.create(name='晚餐', parent=parent)
        children = list(parent.children.all())
        assert len(children) == 2
        assert child1 in children
        assert child2 in children

    @pytest.mark.django_db
    def test_parent_can_be_null(self):
        """测试 parent 可以为 null"""
        category = Category.objects.create(name='顶级分类')
        assert category.parent is None

    @pytest.mark.django_db
    def test_type_choices(self):
        """测试所有 TYPE_CHOICES"""
        choices = dict(Category.TYPE_CHOICES)
        assert Category.TYPE_EXPENSE in choices
        assert Category.TYPE_INCOME in choices
        assert Category.TYPE_TRANSFER in choices
        assert choices[Category.TYPE_EXPENSE] == '支出'
        assert choices[Category.TYPE_INCOME] == '收入'
        assert choices[Category.TYPE_TRANSFER] == '转账'

    @pytest.mark.django_db
    def test_default_type_expense(self):
        """测试默认类型为 expense"""
        category = Category.objects.create(name='测试分类')
        assert category.type == Category.TYPE_EXPENSE

    @pytest.mark.django_db
    def test_default_sort_order_zero(self):
        """测试默认排序为 0"""
        category = Category.objects.create(name='测试分类')
        assert category.sort_order == 0

    @pytest.mark.django_db
    def test_default_is_active_true(self):
        """测试默认 is_active 为 True"""
        category = Category.objects.create(name='测试分类')
        assert category.is_active is True

    @pytest.mark.django_db
    def test_default_icon_empty(self):
        """测试默认 icon 为空字符串"""
        category = Category.objects.create(name='测试分类')
        assert category.icon == ''

    @pytest.mark.django_db
    def test_icon_max_length(self):
        """测试 icon 最大长度为 20"""
        category = Category.objects.create(name='测试', icon='💰' * 10)
        assert len(category.icon) <= 20

    @pytest.mark.django_db
    def test_income_category(self):
        """测试收入类型分类"""
        category = Category.objects.create(name='工资', type=Category.TYPE_INCOME)
        assert category.type == Category.TYPE_INCOME

    @pytest.mark.django_db
    def test_transfer_category(self):
        """测试转账类型分类"""
        category = Category.objects.create(name='转账', type=Category.TYPE_TRANSFER)
        assert category.type == Category.TYPE_TRANSFER

    @pytest.mark.django_db
    def test_is_active_false(self):
        """测试 is_active 可设置为 False"""
        category = Category.objects.create(name='已禁用', is_active=False)
        assert category.is_active is False

    @pytest.mark.django_db
    def test_sort_order_ordering(self):
        """测试按 sort_order 排序"""
        c2 = Category.objects.create(name='B', sort_order=2)
        c1 = Category.objects.create(name='A', sort_order=1)
        categories = list(Category.objects.all())
        assert categories[0].sort_order <= categories[1].sort_order

    @pytest.mark.django_db
    def test_cascade_delete_parent(self):
        """测试删除父分类级联删除子分类"""
        parent = Category.objects.create(name='餐饮')
        child = Category.objects.create(name='午餐', parent=parent)
        child_id = child.id
        parent.delete()
        assert not Category.objects.filter(id=child_id).exists()


# ============================================================
# Transaction 模型测试
# ============================================================

class TestTransaction:
    """测试 Transaction 模型"""

    @pytest.mark.django_db
    def test_create_transaction(self):
        """测试创建交易"""
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 15),
            amount=Decimal('100.50'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            description='午餐消费',
            merchant='测试餐厅',
            unique_key='abc123def4567890',
        )
        assert tx.id is not None
        assert tx.trans_date == date(2024, 1, 15)
        assert tx.amount == Decimal('100.50')
        assert tx.direction == Transaction.DIRECTION_EXPENSE
        assert tx.source == Transaction.SOURCE_ALIPAY
        assert tx.description == '午餐消费'
        assert tx.merchant == '测试餐厅'
        assert tx.unique_key == 'abc123def4567890'
        assert tx.status == Transaction.STATUS_UNKNOWN
        assert tx.is_virtual is False
        assert tx.created_at is not None
        assert tx.updated_at is not None

    @pytest.mark.django_db
    def test_transaction_str(self):
        """测试 __str__ 方法"""
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 15),
            amount=Decimal('100.50'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='abc123def4567890',
        )
        expected = f'{date(2024, 1, 15)} 支出 ¥100.50 (支付宝)'
        assert str(tx) == expected

    @pytest.mark.django_db
    def test_transaction_str_income(self):
        """测试 __str__ 方法（收入）"""
        tx = Transaction.objects.create(
            trans_date=date(2024, 6, 1),
            amount=Decimal('5000'),
            direction=Transaction.DIRECTION_INCOME,
            source=Transaction.SOURCE_CMB_DEBIT,
            unique_key='xyz789ghi0123456',
        )
        expected = f'{date(2024, 6, 1)} 收入 ¥5000 (招商银行储蓄卡)'
        assert str(tx) == expected

    @pytest.mark.django_db
    def test_direction_choices(self):
        """测试所有 DIRECTION_CHOICES"""
        choices = dict(Transaction.DIRECTION_CHOICES)
        assert Transaction.DIRECTION_EXPENSE in choices
        assert Transaction.DIRECTION_INCOME in choices
        assert choices[Transaction.DIRECTION_EXPENSE] == '支出'
        assert choices[Transaction.DIRECTION_INCOME] == '收入'

    @pytest.mark.django_db
    def test_source_choices(self):
        """测试所有 SOURCE_CHOICES（9种来源）"""
        choices = dict(Transaction.SOURCE_CHOICES)
        assert Transaction.SOURCE_ALIPAY in choices
        assert Transaction.SOURCE_JD in choices
        assert Transaction.SOURCE_MEITUAN in choices
        assert Transaction.SOURCE_WECHAT in choices
        assert Transaction.SOURCE_BOCOM_DEBIT in choices
        assert Transaction.SOURCE_CMB_DEBIT in choices
        assert Transaction.SOURCE_CIB_CREDIT in choices
        assert Transaction.SOURCE_CMB_CREDIT in choices
        assert Transaction.SOURCE_DOUYIN in choices
        assert len(choices) == 9

    @pytest.mark.django_db
    def test_status_choices(self):
        """测试所有 STATUS_CHOICES"""
        choices = dict(Transaction.STATUS_CHOICES)
        assert Transaction.STATUS_CONFIRMED in choices
        assert Transaction.STATUS_EXCLUDED in choices
        assert Transaction.STATUS_UNKNOWN in choices
        assert Transaction.STATUS_DELETED in choices
        assert choices[Transaction.STATUS_CONFIRMED] == '有效'
        assert choices[Transaction.STATUS_EXCLUDED] == '无效'
        assert choices[Transaction.STATUS_UNKNOWN] == '未知'
        assert choices[Transaction.STATUS_DELETED] == '已删除'

    @pytest.mark.django_db
    def test_default_status_unknown(self):
        """测试默认状态为 unknown"""
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('10'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='test001',
        )
        assert tx.status == Transaction.STATUS_UNKNOWN

    @pytest.mark.django_db
    def test_unique_key_unique_constraint(self):
        """测试 unique_key 唯一约束"""
        Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('10'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='unique_key_001',
        )
        with pytest.raises(IntegrityError):
            Transaction.objects.create(
                trans_date=date(2024, 1, 2),
                amount=Decimal('20'),
                direction=Transaction.DIRECTION_INCOME,
                source=Transaction.SOURCE_WECHAT,
                unique_key='unique_key_001',
            )

    @pytest.mark.django_db
    def test_unique_key_max_length(self):
        """测试 unique_key 最大长度 32"""
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('10'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='A' * 32,
        )
        assert len(tx.unique_key) == 32

    @pytest.mark.django_db
    def test_category_foreign_key(self):
        """测试 category 外键关联"""
        category = Category.objects.create(name='餐饮', type=Category.TYPE_EXPENSE)
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('50'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='cat_fk_test',
            category=category,
        )
        assert tx.category == category
        assert tx.category_id == category.id

    @pytest.mark.django_db
    def test_category_set_null_on_delete(self):
        """测试删除分类时 category 设为 null"""
        category = Category.objects.create(name='餐饮')
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('50'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='cat_null_test',
            category=category,
        )
        category.delete()
        tx.refresh_from_db()
        assert tx.category is None

    @pytest.mark.django_db
    def test_account_foreign_key(self):
        """测试 account 外键关联"""
        account = Account.objects.create(name='支付宝')
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('50'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='acct_fk_test',
            account=account,
        )
        assert tx.account == account
        assert tx.account_id == account.id

    @pytest.mark.django_db
    def test_account_set_null_on_delete(self):
        """测试删除账户时 account 设为 null"""
        account = Account.objects.create(name='支付宝')
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('50'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='acct_null_test',
            account=account,
        )
        account.delete()
        tx.refresh_from_db()
        assert tx.account is None

    @pytest.mark.django_db
    def test_valid_rule_foreign_key(self):
        """测试 valid_rule 外键关联"""
        rule = ValidRule.objects.create(name='测试有效规则')
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('50'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='vr_fk_test',
            valid_rule=rule,
        )
        assert tx.valid_rule == rule
        assert tx.valid_rule_id == rule.id

    @pytest.mark.django_db
    def test_invalid_rule_foreign_key(self):
        """测试 invalid_rule 外键关联"""
        rule = InvalidRule.objects.create(name='测试无效规则')
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('50'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='ir_fk_test',
            invalid_rule=rule,
        )
        assert tx.invalid_rule == rule
        assert tx.invalid_rule_id == rule.id

    @pytest.mark.django_db
    def test_pair_foreign_key(self):
        """测试 pair（TransactionPair）外键关联"""
        # 需要先创建配对
        tx1 = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='pair_expense',
        )
        tx2 = Transaction.objects.create(
            trans_date=date(2024, 1, 2),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_INCOME,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='pair_refund',
        )
        pair = TransactionPair.objects.create(
            expense_tx=tx1,
            refund_tx=tx2,
        )
        tx1.pair = pair
        tx1.save()
        tx1.refresh_from_db()
        assert tx1.pair == pair

    @pytest.mark.django_db
    def test_settlement_foreign_key(self):
        """测试 settlement（SettlementGroup）外键关联"""
        sg = SettlementGroup.objects.create(name='测试结算组')
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('50'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='settle_fk_test',
            settlement=sg,
        )
        assert tx.settlement == sg
        assert tx.settlement_id == sg.id

    @pytest.mark.django_db
    def test_is_virtual_default_false(self):
        """测试 is_virtual 默认为 False"""
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('10'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='virtual_false',
        )
        assert tx.is_virtual is False

    @pytest.mark.django_db
    def test_is_virtual_true(self):
        """测试 is_virtual 可设置为 True"""
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('10'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='virtual_true',
            is_virtual=True,
        )
        assert tx.is_virtual is True

    @pytest.mark.django_db
    def test_all_source_values(self):
        """测试所有来源值均可创建交易"""
        sources = [
            Transaction.SOURCE_ALIPAY,
            Transaction.SOURCE_JD,
            Transaction.SOURCE_MEITUAN,
            Transaction.SOURCE_WECHAT,
            Transaction.SOURCE_BOCOM_DEBIT,
            Transaction.SOURCE_CMB_DEBIT,
            Transaction.SOURCE_CIB_CREDIT,
            Transaction.SOURCE_CMB_CREDIT,
            Transaction.SOURCE_DOUYIN,
        ]
        for i, source in enumerate(sources):
            tx = Transaction.objects.create(
                trans_date=date(2024, 1, 1),
                amount=Decimal(str(i + 1)),
                direction=Transaction.DIRECTION_EXPENSE,
                source=source,
                unique_key=f'source_test_{i}',
            )
            assert tx.source == source

    @pytest.mark.django_db
    def test_all_status_values(self):
        """测试所有状态值均可创建交易"""
        statuses = [
            Transaction.STATUS_CONFIRMED,
            Transaction.STATUS_EXCLUDED,
            Transaction.STATUS_UNKNOWN,
            Transaction.STATUS_DELETED,
        ]
        for i, status in enumerate(statuses):
            tx = Transaction.objects.create(
                trans_date=date(2024, 1, 1),
                amount=Decimal(str(i + 1)),
                direction=Transaction.DIRECTION_EXPENSE,
                source=Transaction.SOURCE_ALIPAY,
                unique_key=f'status_test_{i}',
                status=status,
            )
            assert tx.status == status

    @pytest.mark.django_db
    def test_optional_fields_default_empty(self):
        """测试可选字段默认值为空字符串"""
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('10'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='optional_test',
        )
        assert tx.trans_type == ''
        assert tx.description == ''
        assert tx.merchant == ''
        assert tx.counterparty == ''
        assert tx.payment_method == ''
        assert tx.payment_channel == ''
        assert tx.remark == ''

    @pytest.mark.django_db
    def test_amount_decimal_precision(self):
        """测试金额精度（max_digits=12, decimal_places=2）"""
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('9999999999.99'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='precision_test',
        )
        assert tx.amount == Decimal('9999999999.99')

    @pytest.mark.django_db
    def test_ordering(self):
        """测试排序按日期降序和id降序"""
        tx1 = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('10'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='order_test_1',
        )
        tx2 = Transaction.objects.create(
            trans_date=date(2024, 6, 1),
            amount=Decimal('10'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='order_test_2',
        )
        txs = list(Transaction.objects.all())
        assert txs[0].trans_date >= txs[1].trans_date

    @pytest.mark.django_db
    def test_db_indexes(self):
        """测试数据库索引存在"""
        indexes = Transaction._meta.indexes
        index_fields = set()
        for idx in indexes:
            index_fields.update(idx.fields)
        assert 'trans_date' in index_fields
        assert 'source' in index_fields
        assert 'status' in index_fields
        assert 'direction' in index_fields
        assert 'unique_key' in index_fields


# ============================================================
# ValidRule 模型测试
# ============================================================

class TestValidRule:
    """测试 ValidRule 模型"""

    @pytest.mark.django_db
    def test_create_valid_rule(self):
        """测试创建有效规则"""
        rule = ValidRule.objects.create(
            name='支付宝餐饮规则',
            priority=80,
            sources='alipay',
            keywords='餐饮,午餐,晚餐',
        )
        assert rule.id is not None
        assert rule.name == '支付宝餐饮规则'
        assert rule.priority == 80
        assert rule.sources == 'alipay'
        assert rule.keywords == '餐饮,午餐,晚餐'
        assert rule.is_active is True
        assert rule.hit_count == 0
        assert rule.created_at is not None
        assert rule.updated_at is not None

    @pytest.mark.django_db
    def test_valid_rule_str(self):
        """测试 __str__ 方法"""
        rule = ValidRule.objects.create(name='测试规则', priority=50)
        assert str(rule) == '[有效] 测试规则 (优先级:50)'

    @pytest.mark.django_db
    def test_valid_rule_str_high_priority(self):
        """测试 __str__ 方法（高优先级）"""
        rule = ValidRule.objects.create(name='高优先级规则', priority=100)
        assert str(rule) == '[有效] 高优先级规则 (优先级:100)'

    @pytest.mark.django_db
    def test_default_priority(self):
        """测试默认优先级为 50"""
        rule = ValidRule.objects.create(name='默认优先级规则')
        assert rule.priority == 50

    @pytest.mark.django_db
    def test_default_is_active(self):
        """测试默认 is_active 为 True"""
        rule = ValidRule.objects.create(name='测试规则')
        assert rule.is_active is True

    @pytest.mark.django_db
    def test_default_hit_count(self):
        """测试默认 hit_count 为 0"""
        rule = ValidRule.objects.create(name='测试规则')
        assert rule.hit_count == 0

    @pytest.mark.django_db
    def test_default_empty_fields(self):
        """测试默认可选字段为空字符串"""
        rule = ValidRule.objects.create(name='测试规则')
        assert rule.sources == ''
        assert rule.trans_types == ''
        assert rule.directions == ''
        assert rule.categories == ''
        assert rule.payment_channels == ''
        assert rule.keywords == ''
        assert rule.keyword_exclude == ''
        assert rule.merchants == ''
        assert rule.amount_min is None
        assert rule.amount_max is None

    @pytest.mark.django_db
    def test_amount_min_max_fields(self):
        """测试金额范围字段"""
        rule = ValidRule.objects.create(
            name='金额范围规则',
            amount_min=Decimal('10.00'),
            amount_max=Decimal('100.00'),
        )
        assert rule.amount_min == Decimal('10.00')
        assert rule.amount_max == Decimal('100.00')

    @pytest.mark.django_db
    def test_amount_min_max_nullable(self):
        """测试金额范围字段可为 null"""
        rule = ValidRule.objects.create(name='无金额限制')
        assert rule.amount_min is None
        assert rule.amount_max is None

    @pytest.mark.django_db
    def test_all_fields_populated(self):
        """测试所有字段填充"""
        rule = ValidRule.objects.create(
            name='完整规则',
            priority=90,
            is_active=True,
            sources='alipay,wechat',
            trans_types='消费,转账',
            directions='expense',
            categories='餐饮,购物',
            payment_channels='余额,银行卡',
            keywords='午餐,晚餐',
            keyword_exclude='报销',
            merchants='美团,饿了么',
            amount_min=Decimal('1'),
            amount_max=Decimal('9999'),
            hit_count=5,
        )
        assert rule.name == '完整规则'
        assert rule.priority == 90
        assert rule.is_active is True
        assert rule.sources == 'alipay,wechat'
        assert rule.trans_types == '消费,转账'
        assert rule.directions == 'expense'
        assert rule.categories == '餐饮,购物'
        assert rule.payment_channels == '余额,银行卡'
        assert rule.keywords == '午餐,晚餐'
        assert rule.keyword_exclude == '报销'
        assert rule.merchants == '美团,饿了么'
        assert rule.amount_min == Decimal('1')
        assert rule.amount_max == Decimal('9999')
        assert rule.hit_count == 5


# ============================================================
# InvalidRule 模型测试
# ============================================================

class TestInvalidRule:
    """测试 InvalidRule 模型"""

    @pytest.mark.django_db
    def test_create_invalid_rule(self):
        """测试创建无效规则"""
        rule = InvalidRule.objects.create(
            name='排除转账',
            priority=100,
            keywords='转账,汇款',
        )
        assert rule.id is not None
        assert rule.name == '排除转账'
        assert rule.priority == 100
        assert rule.keywords == '转账,汇款'
        assert rule.is_active is True
        assert rule.hit_count == 0

    @pytest.mark.django_db
    def test_invalid_rule_str(self):
        """测试 __str__ 方法"""
        rule = InvalidRule.objects.create(name='排除规则', priority=75)
        assert str(rule) == '[无效] 排除规则 (优先级:75)'

    @pytest.mark.django_db
    def test_invalid_rule_str_low_priority(self):
        """测试 __str__ 方法（低优先级）"""
        rule = InvalidRule.objects.create(name='低优规则', priority=10)
        assert str(rule) == '[无效] 低优规则 (优先级:10)'

    @pytest.mark.django_db
    def test_default_priority(self):
        """测试默认优先级为 50"""
        rule = InvalidRule.objects.create(name='默认优先级')
        assert rule.priority == 50

    @pytest.mark.django_db
    def test_counterparties_field(self):
        """测试 counterparties 字段（InvalidRule 独有）"""
        rule = InvalidRule.objects.create(
            name='排除对手方',
            counterparties='某公司,某个人',
        )
        assert rule.counterparties == '某公司,某个人'

    @pytest.mark.django_db
    def test_default_counterparties_empty(self):
        """测试默认 counterparties 为空字符串"""
        rule = InvalidRule.objects.create(name='无对手方规则')
        assert rule.counterparties == ''

    @pytest.mark.django_db
    def test_inherits_base_fields(self):
        """测试继承 RuleBase 的所有字段"""
        rule = InvalidRule.objects.create(
            name='继承测试',
            priority=60,
            sources='wechat',
            trans_types='支付',
            directions='expense',
            categories='娱乐',
            payment_channels='零钱',
            keywords='游戏',
            keyword_exclude='退款',
            merchants='腾讯',
            amount_min=Decimal('0.01'),
            amount_max=Decimal('500'),
        )
        assert rule.sources == 'wechat'
        assert rule.trans_types == '支付'
        assert rule.directions == 'expense'
        assert rule.categories == '娱乐'
        assert rule.payment_channels == '零钱'
        assert rule.keywords == '游戏'
        assert rule.keyword_exclude == '退款'
        assert rule.merchants == '腾讯'
        assert rule.amount_min == Decimal('0.01')
        assert rule.amount_max == Decimal('500')


# ============================================================
# ImportLog 模型测试
# ============================================================

class TestImportLog:
    """测试 ImportLog 模型"""

    @pytest.mark.django_db
    def test_create_import_log(self):
        """测试创建导入日志"""
        log = ImportLog.objects.create(
            source='alipay',
            source_file='支付宝账单_202406.csv',
            file_size=102400,
            total_rows=100,
            imported_rows=95,
            skipped_rows=3,
            error_rows=2,
        )
        assert log.id is not None
        assert log.source == 'alipay'
        assert log.source_file == '支付宝账单_202406.csv'
        assert log.file_size == 102400
        assert log.total_rows == 100
        assert log.imported_rows == 95
        assert log.skipped_rows == 3
        assert log.error_rows == 2
        assert log.status == 'success'
        assert log.error_detail == []
        assert log.created_at is not None

    @pytest.mark.django_db
    def test_import_log_str(self):
        """测试 __str__ 方法"""
        log = ImportLog.objects.create(
            source='alipay',
            source_file='test.csv',
            imported_rows=50,
        )
        result = str(log)
        assert 'test.csv' in result
        assert '50行' in result

    @pytest.mark.django_db
    def test_default_file_size_zero(self):
        """测试默认 file_size 为 0"""
        log = ImportLog.objects.create(source='alipay', source_file='test.csv')
        assert log.file_size == 0

    @pytest.mark.django_db
    def test_default_total_rows_zero(self):
        """测试默认 total_rows 为 0"""
        log = ImportLog.objects.create(source='alipay', source_file='test.csv')
        assert log.total_rows == 0

    @pytest.mark.django_db
    def test_default_imported_rows_zero(self):
        """测试默认 imported_rows 为 0"""
        log = ImportLog.objects.create(source='alipay', source_file='test.csv')
        assert log.imported_rows == 0

    @pytest.mark.django_db
    def test_default_skipped_rows_zero(self):
        """测试默认 skipped_rows 为 0"""
        log = ImportLog.objects.create(source='alipay', source_file='test.csv')
        assert log.skipped_rows == 0

    @pytest.mark.django_db
    def test_default_error_rows_zero(self):
        """测试默认 error_rows 为 0"""
        log = ImportLog.objects.create(source='alipay', source_file='test.csv')
        assert log.error_rows == 0

    @pytest.mark.django_db
    def test_default_status_success(self):
        """测试默认状态为 success"""
        log = ImportLog.objects.create(source='alipay', source_file='test.csv')
        assert log.status == 'success'

    @pytest.mark.django_db
    def test_default_error_detail_empty_list(self):
        """测试默认 error_detail 为空列表"""
        log = ImportLog.objects.create(source='alipay', source_file='test.csv')
        assert log.error_detail == []

    @pytest.mark.django_db
    def test_error_detail_with_data(self):
        """测试 error_detail 存储错误信息"""
        errors = ['行3: 金额格式错误', '行7: 日期解析失败']
        log = ImportLog.objects.create(
            source='alipay',
            source_file='test.csv',
            error_detail=errors,
        )
        assert log.error_detail == errors
        assert len(log.error_detail) == 2

    @pytest.mark.django_db
    def test_status_failed(self):
        """测试 status 为 failed"""
        log = ImportLog.objects.create(
            source='alipay',
            source_file='test.csv',
            status='failed',
            error_rows=10,
        )
        assert log.status == 'failed'

    @pytest.mark.django_db
    def test_large_file_size(self):
        """测试大文件大小"""
        log = ImportLog.objects.create(
            source='alipay',
            source_file='large.csv',
            file_size=10 * 1024 * 1024 * 1024,  # 10GB
        )
        assert log.file_size == 10 * 1024 * 1024 * 1024

    @pytest.mark.django_db
    def test_ordering(self):
        """测试排序按创建时间降序"""
        log1 = ImportLog.objects.create(source='alipay', source_file='a.csv')
        log2 = ImportLog.objects.create(source='wechat', source_file='b.csv')
        logs = list(ImportLog.objects.all())
        assert logs[0].created_at >= logs[1].created_at


# ============================================================
# TransactionPair 模型测试
# ============================================================

class TestTransactionPair:
    """测试 TransactionPair 模型"""

    @pytest.mark.django_db
    def test_create_transaction_pair(self):
        """测试创建退款配对"""
        tx_expense = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='pair_exp_001',
        )
        tx_refund = Transaction.objects.create(
            trans_date=date(2024, 1, 2),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_INCOME,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='pair_ref_001',
        )
        pair = TransactionPair.objects.create(
            expense_tx=tx_expense,
            refund_tx=tx_refund,
            match_score=85.5,
            match_method=TransactionPair.MATCH_AUTO,
            match_detail={'amount': 100, 'date_diff': 1},
        )
        assert pair.id is not None
        assert pair.expense_tx == tx_expense
        assert pair.refund_tx == tx_refund
        assert pair.match_score == 85.5
        assert pair.match_method == TransactionPair.MATCH_AUTO
        assert pair.match_detail == {'amount': 100, 'date_diff': 1}
        assert pair.created_at is not None

    @pytest.mark.django_db
    def test_transaction_pair_str(self):
        """测试 __str__ 方法"""
        tx_expense = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='pair_str_exp',
        )
        tx_refund = Transaction.objects.create(
            trans_date=date(2024, 1, 2),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_INCOME,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='pair_str_ref',
        )
        pair = TransactionPair.objects.create(
            expense_tx=tx_expense,
            refund_tx=tx_refund,
        )
        result = str(pair)
        assert f'配对 #{pair.id}' in result
        assert f'消费#{tx_expense.id}' in result
        assert f'退款#{tx_refund.id}' in result

    @pytest.mark.django_db
    def test_match_method_choices(self):
        """测试 MATCH_METHOD_CHOICES"""
        choices = dict(TransactionPair.MATCH_METHOD_CHOICES)
        assert TransactionPair.MATCH_AUTO in choices
        assert TransactionPair.MATCH_MANUAL in choices
        assert TransactionPair.MATCH_AA in choices
        assert choices[TransactionPair.MATCH_AUTO] == '自动配对'
        assert choices[TransactionPair.MATCH_MANUAL] == '手动配对'
        assert choices[TransactionPair.MATCH_AA] == 'AA群收款'

    @pytest.mark.django_db
    def test_default_match_score_zero(self):
        """测试默认匹配分数为 0"""
        tx_expense = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='score_def_exp',
        )
        tx_refund = Transaction.objects.create(
            trans_date=date(2024, 1, 2),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_INCOME,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='score_def_ref',
        )
        pair = TransactionPair.objects.create(
            expense_tx=tx_expense,
            refund_tx=tx_refund,
        )
        assert pair.match_score == 0

    @pytest.mark.django_db
    def test_default_match_method_auto(self):
        """测试默认配对方式为 auto"""
        tx_expense = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='method_exp',
        )
        tx_refund = Transaction.objects.create(
            trans_date=date(2024, 1, 2),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_INCOME,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='method_ref',
        )
        pair = TransactionPair.objects.create(
            expense_tx=tx_expense,
            refund_tx=tx_refund,
        )
        assert pair.match_method == TransactionPair.MATCH_AUTO

    @pytest.mark.django_db
    def test_default_match_detail_empty_dict(self):
        """测试默认 match_detail 为空字典"""
        tx_expense = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='detail_exp',
        )
        tx_refund = Transaction.objects.create(
            trans_date=date(2024, 1, 2),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_INCOME,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='detail_ref',
        )
        pair = TransactionPair.objects.create(
            expense_tx=tx_expense,
            refund_tx=tx_refund,
        )
        assert pair.match_detail == {}

    @pytest.mark.django_db
    def test_manual_match_method(self):
        """测试手动配对方式"""
        tx_expense = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='manual_exp',
        )
        tx_refund = Transaction.objects.create(
            trans_date=date(2024, 1, 2),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_INCOME,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='manual_ref',
        )
        pair = TransactionPair.objects.create(
            expense_tx=tx_expense,
            refund_tx=tx_refund,
            match_method=TransactionPair.MATCH_MANUAL,
        )
        assert pair.match_method == TransactionPair.MATCH_MANUAL

    @pytest.mark.django_db
    def test_aa_match_method(self):
        """测试 AA 群收款配对方式"""
        tx_expense = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='aa_exp',
        )
        tx_refund = Transaction.objects.create(
            trans_date=date(2024, 1, 2),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_INCOME,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='aa_ref',
        )
        pair = TransactionPair.objects.create(
            expense_tx=tx_expense,
            refund_tx=tx_refund,
            match_method=TransactionPair.MATCH_AA,
        )
        assert pair.match_method == TransactionPair.MATCH_AA

    @pytest.mark.django_db
    def test_related_names(self):
        """测试 related_name 反向关联"""
        tx_expense = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='rel_exp',
        )
        tx_refund = Transaction.objects.create(
            trans_date=date(2024, 1, 2),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_INCOME,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='rel_ref',
        )
        pair = TransactionPair.objects.create(
            expense_tx=tx_expense,
            refund_tx=tx_refund,
        )
        # 通过 related_name 访问
        assert pair in tx_expense.expense_pairs.all()
        assert pair in tx_refund.refund_pairs.all()

    @pytest.mark.django_db
    def test_cascade_delete_expense_tx(self):
        """测试删除消费交易级联删除配对"""
        tx_expense = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='cascade_exp',
        )
        tx_refund = Transaction.objects.create(
            trans_date=date(2024, 1, 2),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_INCOME,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='cascade_ref',
        )
        pair = TransactionPair.objects.create(
            expense_tx=tx_expense,
            refund_tx=tx_refund,
        )
        pair_id = pair.id
        tx_expense.delete()
        assert not TransactionPair.objects.filter(id=pair_id).exists()


# ============================================================
# SettlementGroup 模型测试
# ============================================================

class TestSettlementGroup:
    """测试 SettlementGroup 模型"""

    @pytest.mark.django_db
    def test_create_settlement_group(self):
        """测试创建结算组"""
        sg = SettlementGroup.objects.create(
            name='聚餐结算',
            description='同事聚餐AA',
            total_advance=Decimal('500.00'),
            total_reimbursement=Decimal('300.00'),
            net_amount=Decimal('200.00'),
        )
        assert sg.id is not None
        assert sg.name == '聚餐结算'
        assert sg.description == '同事聚餐AA'
        assert sg.status == SettlementGroup.STATUS_OPEN
        assert sg.total_advance == Decimal('500.00')
        assert sg.total_reimbursement == Decimal('300.00')
        assert sg.net_amount == Decimal('200.00')
        assert sg.is_aa is False
        assert sg.virtual_tx is None
        assert sg.created_at is not None
        assert sg.updated_at is not None

    @pytest.mark.django_db
    def test_settlement_group_str(self):
        """测试 __str__ 方法"""
        sg = SettlementGroup.objects.create(name='聚餐结算')
        result = str(sg)
        assert '聚餐结算' in result
        assert '进行中' in result

    @pytest.mark.django_db
    def test_settlement_group_str_closed(self):
        """测试 __str__ 方法（已结算）"""
        sg = SettlementGroup.objects.create(
            name='已结结算',
            status=SettlementGroup.STATUS_CLOSED,
        )
        result = str(sg)
        assert '已结结算' in result
        assert '已结算' in result

    @pytest.mark.django_db
    def test_status_choices(self):
        """测试 STATUS_CHOICES"""
        choices = dict(SettlementGroup.STATUS_CHOICES)
        assert SettlementGroup.STATUS_OPEN in choices
        assert SettlementGroup.STATUS_CLOSED in choices
        assert choices[SettlementGroup.STATUS_OPEN] == '进行中'
        assert choices[SettlementGroup.STATUS_CLOSED] == '已结算'

    @pytest.mark.django_db
    def test_default_status_open(self):
        """测试默认状态为 open"""
        sg = SettlementGroup.objects.create(name='默认状态')
        assert sg.status == SettlementGroup.STATUS_OPEN

    @pytest.mark.django_db
    def test_default_total_advance_zero(self):
        """测试默认 total_advance 为 0"""
        sg = SettlementGroup.objects.create(name='测试')
        assert sg.total_advance == Decimal('0')

    @pytest.mark.django_db
    def test_default_total_reimbursement_zero(self):
        """测试默认 total_reimbursement 为 0"""
        sg = SettlementGroup.objects.create(name='测试')
        assert sg.total_reimbursement == Decimal('0')

    @pytest.mark.django_db
    def test_default_net_amount_zero(self):
        """测试默认 net_amount 为 0"""
        sg = SettlementGroup.objects.create(name='测试')
        assert sg.net_amount == Decimal('0')

    @pytest.mark.django_db
    def test_default_is_aa_false(self):
        """测试默认 is_aa 为 False"""
        sg = SettlementGroup.objects.create(name='测试')
        assert sg.is_aa is False

    @pytest.mark.django_db
    def test_default_description_empty(self):
        """测试默认 description 为空字符串"""
        sg = SettlementGroup.objects.create(name='测试')
        assert sg.description == ''

    @pytest.mark.django_db
    def test_virtual_tx_foreign_key(self):
        """测试 virtual_tx 外键关联"""
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('200'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='vtx_fk',
            is_virtual=True,
        )
        sg = SettlementGroup.objects.create(
            name='带虚拟交易',
            virtual_tx=tx,
        )
        assert sg.virtual_tx == tx
        assert sg.virtual_tx_id == tx.id

    @pytest.mark.django_db
    def test_virtual_tx_set_null_on_delete(self):
        """测试删除虚拟交易时 virtual_tx 设为 null"""
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('200'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='vtx_null',
            is_virtual=True,
        )
        sg = SettlementGroup.objects.create(name='测试', virtual_tx=tx)
        tx.delete()
        sg.refresh_from_db()
        assert sg.virtual_tx is None

    @pytest.mark.django_db
    def test_is_aa_true(self):
        """测试 is_aa 可设置为 True"""
        sg = SettlementGroup.objects.create(name='AA结算', is_aa=True)
        assert sg.is_aa is True

    @pytest.mark.django_db
    def test_ordering(self):
        """测试排序按创建时间降序"""
        sg1 = SettlementGroup.objects.create(name='组A')
        sg2 = SettlementGroup.objects.create(name='组B')
        groups = list(SettlementGroup.objects.all())
        assert groups[0].created_at >= groups[1].created_at


# ============================================================
# SettlementItem 模型测试
# ============================================================

class TestSettlementItem:
    """测试 SettlementItem 模型"""

    @pytest.mark.django_db
    def test_create_settlement_item(self):
        """测试创建结算明细"""
        sg = SettlementGroup.objects.create(name='测试结算')
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='si_tx',
        )
        item = SettlementItem.objects.create(
            settlement=sg,
            transaction=tx,
            item_type=SettlementItem.ITEM_ADVANCE,
        )
        assert item.id is not None
        assert item.settlement == sg
        assert item.transaction == tx
        assert item.item_type == SettlementItem.ITEM_ADVANCE
        assert item.created_at is not None

    @pytest.mark.django_db
    def test_settlement_item_str(self):
        """测试 __str__ 方法"""
        sg = SettlementGroup.objects.create(name='聚餐')
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='si_str',
        )
        item = SettlementItem.objects.create(
            settlement=sg,
            transaction=tx,
            item_type=SettlementItem.ITEM_ADVANCE,
        )
        result = str(item)
        assert '聚餐' in result
        assert '垫付' in result
        assert f'#{tx.id}' in result

    @pytest.mark.django_db
    def test_item_type_choices(self):
        """测试 ITEM_TYPE_CHOICES"""
        choices = dict(SettlementItem.ITEM_TYPE_CHOICES)
        assert SettlementItem.ITEM_ADVANCE in choices
        assert SettlementItem.ITEM_REIMBURSEMENT in choices
        assert choices[SettlementItem.ITEM_ADVANCE] == '垫付'
        assert choices[SettlementItem.ITEM_REIMBURSEMENT] == '收款'

    @pytest.mark.django_db
    def test_item_type_reimbursement(self):
        """测试收款类型"""
        sg = SettlementGroup.objects.create(name='收款结算')
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('50'),
            direction=Transaction.DIRECTION_INCOME,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='reimb_tx',
        )
        item = SettlementItem.objects.create(
            settlement=sg,
            transaction=tx,
            item_type=SettlementItem.ITEM_REIMBURSEMENT,
        )
        assert item.item_type == SettlementItem.ITEM_REIMBURSEMENT

    @pytest.mark.django_db
    def test_unique_together_constraint(self):
        """测试 (settlement, transaction) 唯一约束"""
        sg = SettlementGroup.objects.create(name='唯一约束测试')
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('10'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='unique_si',
        )
        SettlementItem.objects.create(
            settlement=sg,
            transaction=tx,
            item_type=SettlementItem.ITEM_ADVANCE,
        )
        with pytest.raises(IntegrityError):
            SettlementItem.objects.create(
                settlement=sg,
                transaction=tx,
                item_type=SettlementItem.ITEM_REIMBURSEMENT,
            )

    @pytest.mark.django_db
    def test_related_name_items(self):
        """测试 related_name 'items' 反向关联"""
        sg = SettlementGroup.objects.create(name='关联测试')
        tx1 = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('100'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='items_1',
        )
        tx2 = Transaction.objects.create(
            trans_date=date(2024, 1, 2),
            amount=Decimal('50'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='items_2',
        )
        item1 = SettlementItem.objects.create(
            settlement=sg,
            transaction=tx1,
            item_type=SettlementItem.ITEM_ADVANCE,
        )
        item2 = SettlementItem.objects.create(
            settlement=sg,
            transaction=tx2,
            item_type=SettlementItem.ITEM_ADVANCE,
        )
        items = list(sg.items.all())
        assert len(items) == 2
        assert item1 in items
        assert item2 in items

    @pytest.mark.django_db
    def test_cascade_delete_settlement(self):
        """测试删除结算组级联删除结算明细"""
        sg = SettlementGroup.objects.create(name='级联测试')
        tx = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('10'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='cascade_si',
        )
        item = SettlementItem.objects.create(
            settlement=sg,
            transaction=tx,
            item_type=SettlementItem.ITEM_ADVANCE,
        )
        item_id = item.id
        sg.delete()
        assert not SettlementItem.objects.filter(id=item_id).exists()

    @pytest.mark.django_db
    def test_ordering_by_id(self):
        """测试排序按 id"""
        sg = SettlementGroup.objects.create(name='排序测试')
        tx1 = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('10'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='order_si_1',
        )
        tx2 = Transaction.objects.create(
            trans_date=date(2024, 1, 1),
            amount=Decimal('20'),
            direction=Transaction.DIRECTION_EXPENSE,
            source=Transaction.SOURCE_ALIPAY,
            unique_key='order_si_2',
        )
        SettlementItem.objects.create(
            settlement=sg, transaction=tx1, item_type=SettlementItem.ITEM_ADVANCE,
        )
        SettlementItem.objects.create(
            settlement=sg, transaction=tx2, item_type=SettlementItem.ITEM_ADVANCE,
        )
        items = list(SettlementItem.objects.all())
        assert items[0].id <= items[1].id
