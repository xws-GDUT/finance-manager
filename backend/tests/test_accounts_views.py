"""
测试 accounts.views - 账户列表 API
"""
import pytest
from rest_framework.test import APIClient
from apps.accounts.models import Account
from apps.transactions.models import Transaction
from apps.categories.models import Category


@pytest.mark.django_db
class TestAccountList:
    """测试 account_list 视图"""

    def test_empty_list(self):
        """空列表：无账户时返回空数组"""
        client = APIClient()
        resp = client.get('/api/accounts')
        assert resp.status_code == 200
        assert resp.data == []

    def test_account_with_transactions(self):
        """有关联交易：含 expense/income 统计"""
        acc = Account.objects.create(name='测试账户', account_type='debit')
        category = Category.objects.create(name='餐饮', type='expense')
        # 已确认支出
        Transaction.objects.create(
            trans_date='2024-01-01', amount=100, direction='expense',
            source='alipay', status='confirmed', account=acc,
            category=category, unique_key='key1'
        )
        # 已确认收入
        Transaction.objects.create(
            trans_date='2024-01-02', amount=200, direction='income',
            source='alipay', status='confirmed', account=acc,
            category=category, unique_key='key2'
        )
        # 未确认交易（不统计金额）
        Transaction.objects.create(
            trans_date='2024-01-03', amount=50, direction='expense',
            source='alipay', status='unknown', account=acc,
            category=category, unique_key='key3'
        )

        client = APIClient()
        resp = client.get('/api/accounts')
        assert resp.status_code == 200
        assert len(resp.data) == 1
        stats = resp.data[0]['stats']
        assert stats['tx_count'] == 3
        assert stats['total_expense'] == 100.0
        assert stats['total_income'] == 200.0

    def test_sum_none_degradation(self):
        """Sum 返回 None 时降级为 0"""
        acc = Account.objects.create(name='无交易账户', account_type='platform')

        client = APIClient()
        resp = client.get('/api/accounts')
        assert resp.status_code == 200
        assert len(resp.data) == 1
        stats = resp.data[0]['stats']
        assert stats['tx_count'] == 0
        assert stats['total_expense'] == 0.0
        assert stats['total_income'] == 0.0

    def test_soft_deleted_not_counted(self):
        """软删除交易不统计"""
        acc = Account.objects.create(name='测试账户', account_type='debit')
        category = Category.objects.create(name='餐饮', type='expense')
        Transaction.objects.create(
            trans_date='2024-01-01', amount=100, direction='expense',
            source='alipay', status='confirmed', account=acc,
            category=category, unique_key='key_del'
        )
        Transaction.objects.create(
            trans_date='2024-01-02', amount=200, direction='expense',
            source='alipay', status='deleted', account=acc,
            category=category, unique_key='key_del2'
        )

        client = APIClient()
        resp = client.get('/api/accounts')
        assert resp.status_code == 200
        stats = resp.data[0]['stats']
        assert stats['tx_count'] == 1
        assert stats['total_expense'] == 100.0

    def test_non_confirmed_status_not_counted(self):
        """非 confirmed 状态交易不计入统计金额"""
        acc = Account.objects.create(name='测试账户', account_type='debit')
        category = Category.objects.create(name='餐饮', type='expense')
        # excluded 状态
        Transaction.objects.create(
            trans_date='2024-01-01', amount=100, direction='expense',
            source='alipay', status='excluded', account=acc,
            category=category, unique_key='key_exc'
        )
        # unknown 状态
        Transaction.objects.create(
            trans_date='2024-01-02', amount=200, direction='expense',
            source='alipay', status='unknown', account=acc,
            category=category, unique_key='key_unk'
        )

        client = APIClient()
        resp = client.get('/api/accounts')
        assert resp.status_code == 200
        stats = resp.data[0]['stats']
        assert stats['tx_count'] == 2
        # 非 confirmed 状态不计入金额统计
        assert stats['total_expense'] == 0.0

    def test_multiple_accounts(self):
        """多个账户"""
        Account.objects.create(name='账户A', account_type='debit')
        Account.objects.create(name='账户B', account_type='credit')
        Account.objects.create(name='账户C', account_type='platform', is_active=False)

        client = APIClient()
        resp = client.get('/api/accounts')
        assert resp.status_code == 200
        # 只返回活跃账户
        assert len(resp.data) == 2
        names = [a['name'] for a in resp.data]
        assert '账户A' in names
        assert '账户B' in names
        assert '账户C' not in names
