"""
测试 transactions.filters - TransactionFilter
"""
import pytest
from datetime import date
from apps.transactions.filters import TransactionFilter
from apps.transactions.models import Transaction
from apps.accounts.models import Account
from apps.categories.models import Category


@pytest.mark.django_db
class TestTransactionFilter:
    """测试 TransactionFilter 各筛选条件"""

    def setup_method(self):
        self.account = Account.objects.create(name='测试账户', account_type='debit')
        self.cat_food = Category.objects.create(name='餐饮', type='expense')
        self.cat_transport = Category.objects.create(name='交通', type='expense')

    def _create_tx(self, **kwargs):
        defaults = {
            'trans_date': '2024-01-15',
            'amount': 100,
            'direction': 'expense',
            'source': 'alipay',
            'status': 'confirmed',
            'account': self.account,
            'unique_key': f'unique_{Transaction.objects.count()}',
        }
        defaults.update(kwargs)
        return Transaction.objects.create(**defaults)

    def test_filter_source(self):
        """source 筛选"""
        self._create_tx(source='alipay', unique_key='fs1')
        self._create_tx(source='bocom_debit', unique_key='fs2')

        f = TransactionFilter(data={'source': 'alipay'})
        qs = f.qs
        assert qs.count() == 1
        assert qs.first().source == 'alipay'

    def test_filter_direction(self):
        """direction 筛选"""
        self._create_tx(direction='expense', unique_key='fd1')
        self._create_tx(direction='income', unique_key='fd2')

        f = TransactionFilter(data={'direction': 'expense'})
        qs = f.qs
        assert qs.count() == 1
        assert qs.first().direction == 'expense'

    def test_filter_status(self):
        """status 筛选"""
        self._create_tx(status='confirmed', unique_key='fst1')
        self._create_tx(status='unknown', unique_key='fst2')

        f = TransactionFilter(data={'status': 'confirmed'})
        qs = f.qs
        assert qs.count() == 1
        assert qs.first().status == 'confirmed'

    def test_filter_date_range(self):
        """date 范围筛选"""
        self._create_tx(trans_date='2024-01-01', unique_key='fdr1')
        self._create_tx(trans_date='2024-06-15', unique_key='fdr2')
        self._create_tx(trans_date='2024-12-31', unique_key='fdr3')

        f = TransactionFilter(data={
            'date_from': '2024-06-01',
            'date_to': '2024-12-31',
        })
        qs = f.qs
        assert qs.count() == 2

    def test_filter_amount_range(self):
        """amount 范围筛选"""
        self._create_tx(amount=50, unique_key='far1')
        self._create_tx(amount=100, unique_key='far2')
        self._create_tx(amount=200, unique_key='far3')

        f = TransactionFilter(data={
            'amount_min': 80,
            'amount_max': 150,
        })
        qs = f.qs
        assert qs.count() == 1
        assert qs.first().amount == 100

    def test_filter_category(self):
        """category 筛选"""
        self._create_tx(category=self.cat_food, unique_key='fc1')
        self._create_tx(category=self.cat_transport, unique_key='fc2')

        f = TransactionFilter(data={'category': self.cat_food.id})
        qs = f.qs
        assert qs.count() == 1
        assert qs.first().category_id == self.cat_food.id

    def test_filter_multi_source(self):
        """多选 source 筛选（逗号分隔）"""
        self._create_tx(source='alipay', unique_key='fms1')
        self._create_tx(source='bocom_debit', unique_key='fms2')
        self._create_tx(source='wechat', unique_key='fms3')

        f = TransactionFilter(data={'sources': 'alipay,wechat'})
        qs = f.qs
        assert qs.count() == 2

    def test_filter_multi_status(self):
        """多选 status 筛选"""
        self._create_tx(status='confirmed', unique_key='fmst1')
        self._create_tx(status='unknown', unique_key='fmst2')
        self._create_tx(status='excluded', unique_key='fmst3')

        f = TransactionFilter(data={'statuses': 'confirmed,excluded'})
        qs = f.qs
        assert qs.count() == 2

    def test_filter_multi_direction(self):
        """多选 direction 筛选"""
        self._create_tx(direction='expense', unique_key='fmd1')
        self._create_tx(direction='income', unique_key='fmd2')
        self._create_tx(direction='expense', unique_key='fmd3')

        f = TransactionFilter(data={'directions': 'expense'})
        qs = f.qs
        assert qs.count() == 2

    def test_filter_multi_category(self):
        """多选 category 筛选"""
        self._create_tx(category=self.cat_food, unique_key='fmc1')
        self._create_tx(category=self.cat_transport, unique_key='fmc2')
        self._create_tx(unique_key='fmc3')

        f = TransactionFilter(data={'categories': f'{self.cat_food.id},{self.cat_transport.id}'})
        qs = f.qs
        assert qs.count() == 2

    def test_filter_multi_category_invalid(self):
        """多选 category 筛选：无效值"""
        self._create_tx(category=self.cat_food, unique_key='fmci1')

        f = TransactionFilter(data={'categories': 'invalid'})
        qs = f.qs
        # 无效值时不筛选，返回全部
        assert qs.count() == 1

    def test_filter_search(self):
        """搜索筛选"""
        self._create_tx(description='午餐外卖', unique_key='fsearch1')
        self._create_tx(merchant='美团', unique_key='fsearch2')
        self._create_tx(counterparty='测试', description='超市', unique_key='fsearch3')

        f = TransactionFilter(data={'search': '午餐'})
        qs = f.qs
        assert qs.count() == 1

    def test_filter_combined(self):
        """组合筛选"""
        self._create_tx(
            source='alipay', direction='expense', status='confirmed',
            amount=100, category=self.cat_food,
            unique_key='fcomb1'
        )
        self._create_tx(
            source='bocom_debit', direction='income', status='confirmed',
            amount=200, category=self.cat_transport,
            unique_key='fcomb2'
        )
        self._create_tx(
            source='alipay', direction='expense', status='unknown',
            amount=300, unique_key='fcomb3'
        )

        f = TransactionFilter(data={
            'source': 'alipay',
            'direction': 'expense',
            'status': 'confirmed',
        })
        qs = f.qs
        assert qs.count() == 1

    def test_filter_multi_source_empty(self):
        """多选 source 筛选：空值返回全部（行46）"""
        self._create_tx(source='alipay', unique_key='fme1')
        f = TransactionFilter(data={'sources': ''})
        qs = f.qs
        assert qs.count() == 1

    def test_filter_multi_status_empty(self):
        """多选 status 筛选：空值返回全部（行52）"""
        self._create_tx(status='confirmed', unique_key='fme2')
        f = TransactionFilter(data={'statuses': ''})
        qs = f.qs
        assert qs.count() == 1

    def test_filter_multi_direction_empty(self):
        """多选 direction 筛选：空值返回全部（行58）"""
        self._create_tx(direction='expense', unique_key='fme3')
        f = TransactionFilter(data={'directions': ''})
        qs = f.qs
        assert qs.count() == 1

    def test_filter_multi_trans_type(self):
        """多选 trans_type 筛选"""
        self._create_tx(trans_type='餐饮', unique_key='fmt1')
        self._create_tx(trans_type='交通', unique_key='fmt2')
        self._create_tx(trans_type='购物', unique_key='fmt3')

        f = TransactionFilter(data={'trans_types': '餐饮,购物'})
        qs = f.qs
        assert qs.count() == 2

    def test_filter_multi_trans_type_empty(self):
        """多选 trans_type 筛选：空值返回全部（行73）"""
        self._create_tx(trans_type='餐饮', unique_key='fme4')
        f = TransactionFilter(data={'trans_types': ''})
        qs = f.qs
        assert qs.count() == 1
