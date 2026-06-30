"""
测试 settlements.views - RefundPairViewSet 和 SettlementGroupViewSet
"""
import pytest
from rest_framework.test import APIClient
from apps.settlements.models import TransactionPair, SettlementGroup, SettlementItem
from apps.transactions.models import Transaction
from apps.accounts.models import Account
from apps.categories.models import Category


@pytest.mark.django_db
class TestRefundPairViewSet:
    """测试退款配对 ViewSet"""

    def setup_method(self):
        self.client = APIClient()
        self.account = Account.objects.create(name='测试账户', account_type='debit')
        self.category = Category.objects.create(name='餐饮', type='expense')

    def _create_tx(self, **kwargs):
        defaults = {
            'trans_date': '2024-01-15',
            'amount': 100,
            'direction': 'expense',
            'source': 'alipay',
            'status': 'confirmed',
            'account': self.account,
            'category': self.category,
        }
        defaults.update(kwargs)
        idx = Transaction.objects.count() + 1
        defaults['unique_key'] = kwargs.get('unique_key', f'rp_key_{idx}')
        return Transaction.objects.create(**defaults)

    def test_list(self):
        """列表"""
        resp = self.client.get('/api/refund-pairs/')
        assert resp.status_code == 200

    def test_auto(self, mocker):
        """自动退款配对"""
        mock_engine = mocker.patch('apps.settlements.views.RefundPairEngine')
        mock_instance = mock_engine.return_value
        mock_instance.auto_pair.return_value = {'paired': 3, 'total_scanned': 100}

        resp = self.client.post('/api/refund-pairs/auto/')
        assert resp.status_code == 200
        assert resp.data['paired'] == 3

    def test_create_manual_pair(self, mocker):
        """手动创建配对"""
        expense_tx = self._create_tx(direction='expense', unique_key='rp_exp')
        refund_tx = self._create_tx(direction='income', unique_key='rp_ref')

        mock_engine = mocker.patch('apps.settlements.views.RefundPairEngine')
        mock_instance = mock_engine.return_value
        mock_instance.manual_pair.return_value = {'id': 1, 'expense_tx': expense_tx.id, 'refund_tx': refund_tx.id}

        resp = self.client.post('/api/refund-pairs/manual_pair/', {
            'expense_id': expense_tx.id,
            'refund_id': refund_tx.id,
        }, format='json')
        assert resp.status_code == 201

    def test_create_manual_pair_failure(self, mocker):
        """手动配对失败"""
        mock_engine = mocker.patch('apps.settlements.views.RefundPairEngine')
        mock_instance = mock_engine.return_value
        mock_instance.manual_pair.return_value = None

        resp = self.client.post('/api/refund-pairs/manual_pair/', {
            'expense_id': 999,
            'refund_id': 998,
        }, format='json')
        assert resp.status_code == 400

    def test_create_manual_pair_invalid_serializer(self):
        """手动配对序列化器验证失败（行47）"""
        # 发送无效数据触发serializer.is_valid() = False
        resp = self.client.post('/api/refund-pairs/manual_pair/', {
            'expense_id': 'invalid',  # 应该是整数
            'refund_id': None,
        }, format='json')
        assert resp.status_code == 400

    def test_destroy(self, mocker):
        """解除配对"""
        mock_engine = mocker.patch('apps.settlements.views.RefundPairEngine')
        mock_instance = mock_engine.return_value
        mock_instance.unpair.return_value = True

        resp = self.client.delete('/api/refund-pairs/1/')
        assert resp.status_code == 200
        assert resp.data['message'] == '配对已解除'

    def test_destroy_not_found(self, mocker):
        """解除配对不存在"""
        mock_engine = mocker.patch('apps.settlements.views.RefundPairEngine')
        mock_instance = mock_engine.return_value
        mock_instance.unpair.return_value = False

        resp = self.client.delete('/api/refund-pairs/999/')
        assert resp.status_code == 404

    def test_aa_scan(self, mocker):
        """AA 群收款扫描"""
        mock_scanner = mocker.patch('apps.settlements.views.AAScanner')
        mock_instance = mock_scanner.return_value
        mock_instance.scan.return_value = [{'group': 'test'}]

        resp = self.client.get('/api/refund-pairs/aa_scan/')
        assert resp.status_code == 200
        assert len(resp.data) == 1

    def test_aa_create(self, mocker):
        """一键创建 AA 结算组"""
        expense_tx = self._create_tx(direction='expense', unique_key='aa_exp')
        receipt_tx = self._create_tx(direction='income', unique_key='aa_rec')

        mock_engine = mocker.patch('apps.settlements.views.SettlementEngine')
        mock_instance = mock_engine.return_value
        mock_instance.create_group.return_value = 1
        mock_instance.add_item.return_value = True
        mock_instance.close.return_value = 100

        # Create a real SettlementGroup for serializer
        group = SettlementGroup.objects.create(
            name='AA 群收款', description='自动创建的 AA 结算',
            status='closed', is_aa=True,
        )

        resp = self.client.post('/api/refund-pairs/aa_create/', {
            'receipt_ids': [receipt_tx.id],
            'expense_id': expense_tx.id,
            'group_name': '测试AA',
        }, format='json')
        assert resp.status_code == 201

    def test_aa_create_invalid_serializer(self):
        """AA创建序列化器验证失败（行79）"""
        # 缺少必填字段触发验证失败
        resp = self.client.post('/api/refund-pairs/aa_create/', {
            # receipt_ids 和 expense_id 都是必填
        }, format='json')
        assert resp.status_code == 400


@pytest.mark.django_db
class TestSettlementGroupViewSet:
    """测试垫付结算组 ViewSet"""

    def setup_method(self):
        self.client = APIClient()
        self.account = Account.objects.create(name='测试账户', account_type='debit')
        self.category = Category.objects.create(name='餐饮', type='expense')

    def _create_tx(self, **kwargs):
        defaults = {
            'trans_date': '2024-01-15',
            'amount': 100,
            'direction': 'expense',
            'source': 'alipay',
            'status': 'confirmed',
            'account': self.account,
            'category': self.category,
        }
        defaults.update(kwargs)
        idx = Transaction.objects.count() + 1
        defaults['unique_key'] = kwargs.get('unique_key', f'sg_key_{idx}')
        return Transaction.objects.create(**defaults)

    def test_list(self):
        """列表"""
        resp = self.client.get('/api/settlements/')
        assert resp.status_code == 200

    def test_create(self, mocker):
        """创建结算组"""
        mock_engine = mocker.patch('apps.settlements.views.SettlementEngine')
        mock_instance = mock_engine.return_value
        mock_instance.create_group.return_value = 1

        # Create real group for serializer to use
        group = SettlementGroup.objects.create(
            name='测试结算组', description='测试描述', status='open'
        )

        resp = self.client.post('/api/settlements/', {
            'name': '测试结算组',
            'description': '测试描述',
        }, format='json')
        assert resp.status_code == 201

    def test_create_empty_name(self):
        """创建结算组空名称"""
        resp = self.client.post('/api/settlements/', {
            'name': '',
            'description': '',
        }, format='json')
        assert resp.status_code == 400

    def test_items(self, mocker):
        """获取结算组明细"""
        mock_engine = mocker.patch('apps.settlements.views.SettlementEngine')
        mock_instance = mock_engine.return_value
        mock_instance.create_group.return_value = 1

        group = SettlementGroup.objects.create(name='测试结算组', status='open')

        resp = self.client.get(f'/api/settlements/{group.id}/items/')
        assert resp.status_code == 200

    def test_add_item(self, mocker):
        """添加交易到结算组"""
        tx = self._create_tx(unique_key='sg_add')

        mock_engine = mocker.patch('apps.settlements.views.SettlementEngine')
        mock_instance = mock_engine.return_value
        mock_instance.add_item.return_value = True

        group = SettlementGroup.objects.create(name='测试结算组', status='open')

        resp = self.client.post(f'/api/settlements/{group.id}/add_item/', {
            'transaction_id': tx.id,
            'item_type': 'advance',
        }, format='json')
        assert resp.status_code == 200

    def test_add_item_failure(self, mocker):
        """添加交易失败"""
        mock_engine = mocker.patch('apps.settlements.views.SettlementEngine')
        mock_instance = mock_engine.return_value
        mock_instance.add_item.return_value = False

        resp = self.client.post('/api/settlements/1/add_item/', {
            'transaction_id': 999,
            'item_type': 'advance',
        }, format='json')
        assert resp.status_code == 400

    def test_add_item_invalid_serializer(self):
        """添加交易序列化器验证失败（行135）"""
        # 缺少必填字段
        resp = self.client.post('/api/settlements/1/add_item/', {
            # transaction_id 和 item_type 都是必填
        }, format='json')
        assert resp.status_code == 400

    def test_remove_item(self, mocker):
        """移除结算明细"""
        mock_engine = mocker.patch('apps.settlements.views.SettlementEngine')
        mock_instance = mock_engine.return_value
        mock_instance.remove_item.return_value = True

        resp = self.client.delete('/api/settlements/1/items/5/')
        assert resp.status_code == 200
        assert resp.data['message'] == '已移除'

    def test_remove_item_failure(self, mocker):
        """移除结算明细失败"""
        mock_engine = mocker.patch('apps.settlements.views.SettlementEngine')
        mock_instance = mock_engine.return_value
        mock_instance.remove_item.return_value = False

        resp = self.client.delete('/api/settlements/1/items/5/')
        assert resp.status_code == 400

    def test_close(self, mocker):
        """关闭结算"""
        mock_engine = mocker.patch('apps.settlements.views.SettlementEngine')
        mock_instance = mock_engine.return_value
        mock_instance.close.return_value = 100

        group = SettlementGroup.objects.create(name='测试结算组', status='open')

        resp = self.client.post(f'/api/settlements/{group.id}/close/')
        assert resp.status_code == 200
        assert resp.data['virtual_tx_id'] == 100

    def test_close_failure(self, mocker):
        """关闭结算失败"""
        mock_engine = mocker.patch('apps.settlements.views.SettlementEngine')
        mock_instance = mock_engine.return_value
        mock_instance.close.return_value = None

        resp = self.client.post('/api/settlements/1/close/')
        assert resp.status_code == 400

    def test_reopen(self, mocker):
        """重开结算"""
        mock_engine = mocker.patch('apps.settlements.views.SettlementEngine')
        mock_instance = mock_engine.return_value
        mock_instance.reopen.return_value = True

        group = SettlementGroup.objects.create(name='测试结算组', status='closed')

        resp = self.client.post(f'/api/settlements/{group.id}/reopen/')
        assert resp.status_code == 200
        assert resp.data['message'] == '结算已重开'

    def test_reopen_failure(self, mocker):
        """重开结算失败"""
        mock_engine = mocker.patch('apps.settlements.views.SettlementEngine')
        mock_instance = mock_engine.return_value
        mock_instance.reopen.return_value = False

        resp = self.client.post('/api/settlements/1/reopen/')
        assert resp.status_code == 400

    def test_candidates(self, mocker):
        """搜索候选交易"""
        mock_engine = mocker.patch('apps.settlements.views.SettlementEngine')
        mock_instance = mock_engine.return_value
        mock_instance.search_candidates.return_value = [{'id': 1, 'description': 'test'}]

        resp = self.client.get('/api/settlements/candidates/', {'keyword': 'test'})
        assert resp.status_code == 200
        assert len(resp.data) == 1

    def test_candidates_invalid_serializer(self, mocker):
        """搜索候选交易序列化器验证失败（行192）"""
        # mock serializer.is_valid() 返回 False
        mock_serializer = mocker.patch('apps.settlements.views.CandidateSearchSerializer')
        mock_instance = mock_serializer.return_value
        mock_instance.is_valid.return_value = False
        mock_instance.errors = {'keyword': ['invalid']}

        resp = self.client.get('/api/settlements/candidates/', {'keyword': 'test'})
        assert resp.status_code == 400
