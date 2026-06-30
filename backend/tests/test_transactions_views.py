"""
测试 transactions.views - TransactionViewSet
"""
import pytest
from datetime import date
from rest_framework.test import APIClient
from apps.transactions.models import Transaction
from apps.transactions.views import TransactionViewSet
from apps.transactions.serializers import TransactionListSerializer, TransactionUpdateSerializer
from apps.accounts.models import Account
from apps.categories.models import Category


@pytest.mark.django_db
class TestTransactionViewSet:
    """测试 TransactionViewSet CRUD 操作"""

    def test_list(self):
        """分页列表"""
        account = Account.objects.create(name='测试账户', account_type='debit')
        for i in range(5):
            Transaction.objects.create(
                trans_date=f'2024-01-0{i+1}', amount=100 + i * 10,
                direction='expense', source='alipay', status='confirmed',
                account=account, unique_key=f'list_key_{i}'
            )

        client = APIClient()
        resp = client.get('/api/transactions/')
        assert resp.status_code == 200
        # DRF 分页返回
        assert 'results' in resp.data or isinstance(resp.data, list)

    def test_create(self):
        """创建交易"""
        account = Account.objects.create(name='测试账户', account_type='debit')
        category = Category.objects.create(name='餐饮', type='expense')

        client = APIClient()
        data = {
            'trans_date': '2024-01-15',
            'amount': '150.00',
            'direction': 'expense',
            'source': 'alipay',
            'description': '午餐',
            'merchant': '测试餐厅',
            'category': category.id,
            'account': account.id,
        }
        resp = client.post('/api/transactions/', data, format='json')
        assert resp.status_code == 201
        assert resp.data['amount'] == '150.00'
        assert resp.data['description'] == '午餐'

    def test_retrieve(self):
        """获取单个交易"""
        account = Account.objects.create(name='测试账户', account_type='debit')
        tx = Transaction.objects.create(
            trans_date='2024-01-15', amount=150, direction='expense',
            source='alipay', status='confirmed', account=account,
            unique_key='retrieve_key'
        )

        client = APIClient()
        resp = client.get(f'/api/transactions/{tx.id}/')
        assert resp.status_code == 200
        assert resp.data['id'] == tx.id

    def test_update(self):
        """全量更新（使用 TransactionUpdateSerializer）"""
        account = Account.objects.create(name='测试账户', account_type='debit')
        category = Category.objects.create(name='餐饮', type='expense')
        tx = Transaction.objects.create(
            trans_date='2024-01-15', amount=150, direction='expense',
            source='alipay', status='confirmed', account=account,
            unique_key='update_key'
        )

        client = APIClient()
        # TransactionUpdateSerializer 只允许更新 category 和 remark
        data = {'category': category.id, 'remark': '更新备注'}
        resp = client.put(f'/api/transactions/{tx.id}/', data, format='json')
        assert resp.status_code == 200
        assert resp.data['remark'] == '更新备注'

    def test_partial_update(self):
        """部分更新"""
        account = Account.objects.create(name='测试账户', account_type='debit')
        category = Category.objects.create(name='餐饮', type='expense')
        tx = Transaction.objects.create(
            trans_date='2024-01-15', amount=150, direction='expense',
            source='alipay', status='confirmed', account=account,
            unique_key='partial_key'
        )

        client = APIClient()
        data = {'remark': '部分更新备注'}
        resp = client.patch(f'/api/transactions/{tx.id}/', data, format='json')
        assert resp.status_code == 200
        assert resp.data['remark'] == '部分更新备注'

    def test_destroy_soft_delete(self):
        """软删除：status 变为 deleted"""
        account = Account.objects.create(name='测试账户', account_type='debit')
        tx = Transaction.objects.create(
            trans_date='2024-01-15', amount=150, direction='expense',
            source='alipay', status='confirmed', account=account,
            unique_key='delete_key'
        )

        client = APIClient()
        resp = client.delete(f'/api/transactions/{tx.id}/')
        assert resp.status_code == 204

        tx.refresh_from_db()
        assert tx.status == 'deleted'

    def test_filter_values_empty_db(self):
        """filter_values: 空数据库"""
        client = APIClient()
        resp = client.get('/api/transactions/filter_values/')
        assert resp.status_code == 200
        assert resp.data['sources'] == []
        assert resp.data['statuses'] == []
        assert resp.data['directions'] == []
        assert resp.data['trans_types'] == []
        assert resp.data['categories'] == []

    def test_filter_values_with_data(self):
        """filter_values: 有数据"""
        account = Account.objects.create(name='测试账户', account_type='debit')
        category = Category.objects.create(name='餐饮', icon='🍔', type='expense')
        Transaction.objects.create(
            trans_date='2024-01-15', amount=150, direction='expense',
            source='alipay', status='confirmed', trans_type='快捷支付',
            account=account, category=category, unique_key='fv_key1'
        )
        Transaction.objects.create(
            trans_date='2024-01-16', amount=200, direction='income',
            source='bocom_debit', status='unknown', trans_type='转账',
            account=account, category=category, unique_key='fv_key2'
        )

        client = APIClient()
        resp = client.get('/api/transactions/filter_values/')
        assert resp.status_code == 200
        assert len(resp.data['sources']) == 2
        assert len(resp.data['statuses']) == 2
        assert len(resp.data['directions']) == 2
        assert len(resp.data['trans_types']) == 2
        assert len(resp.data['categories']) == 1

    def test_filter_values_trans_type_truncated(self):
        """filter_values: trans_type 截断30"""
        account = Account.objects.create(name='测试账户', account_type='debit')
        for i in range(35):
            Transaction.objects.create(
                trans_date=f'2024-01-{min(i+1, 28):02d}', amount=100 + i,
                direction='expense', source='alipay', status='confirmed',
                trans_type=f'type_{i}', account=account,
                unique_key=f'fv_trunc_{i}'
            )

        client = APIClient()
        resp = client.get('/api/transactions/filter_values/')
        assert resp.status_code == 200
        # trans_types 最多返回 30 条
        assert len(resp.data['trans_types']) == 30

    def test_filter_values_excludes_null_category(self):
        """filter_values: category__isnull 排除"""
        account = Account.objects.create(name='测试账户', account_type='debit')
        category = Category.objects.create(name='餐饮', icon='🍔', type='expense')
        Transaction.objects.create(
            trans_date='2024-01-15', amount=150, direction='expense',
            source='alipay', status='confirmed', account=account,
            category=category, unique_key='fv_cat1'
        )
        # 无分类交易
        Transaction.objects.create(
            trans_date='2024-01-16', amount=200, direction='expense',
            source='alipay', status='confirmed', account=account,
            unique_key='fv_cat2'
        )

        client = APIClient()
        resp = client.get('/api/transactions/filter_values/')
        assert resp.status_code == 200
        # 只有有分类的交易出现在 categories 中
        assert len(resp.data['categories']) == 1

    def test_filter_values_source_dict_fallback(self):
        """filter_values: dict 兜底 - 未知 source 值"""
        account = Account.objects.create(name='测试账户', account_type='debit')
        tx = Transaction(
            trans_date='2024-01-15', amount=150, direction='expense',
            source='alipay', status='confirmed', account=account,
            unique_key='fv_fb1'
        )
        tx.save()

        client = APIClient()
        resp = client.get('/api/transactions/filter_values/')
        assert resp.status_code == 200
        # 应该能正确映射 label
        assert resp.data['sources'][0]['label'] == '支付宝'

    def test_get_serializer_class_update(self):
        """get_serializer_class: update 返回 TransactionUpdateSerializer"""
        view = TransactionViewSet()
        view.action = 'update'
        serializer_class = view.get_serializer_class()
        assert serializer_class == TransactionUpdateSerializer

    def test_get_serializer_class_partial_update(self):
        """get_serializer_class: partial_update 返回 TransactionUpdateSerializer"""
        view = TransactionViewSet()
        view.action = 'partial_update'
        serializer_class = view.get_serializer_class()
        assert serializer_class == TransactionUpdateSerializer

    def test_get_serializer_class_list(self):
        """get_serializer_class: list 返回 TransactionListSerializer"""
        view = TransactionViewSet()
        view.action = 'list'
        serializer_class = view.get_serializer_class()
        assert serializer_class == TransactionListSerializer

    def test_get_serializer_class_create(self):
        """get_serializer_class: create 返回 TransactionListSerializer"""
        view = TransactionViewSet()
        view.action = 'create'
        serializer_class = view.get_serializer_class()
        assert serializer_class == TransactionListSerializer
