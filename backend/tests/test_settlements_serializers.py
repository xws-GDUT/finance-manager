"""
测试 settlements.serializers - 所有 8 个 Serializer
"""
import pytest
from apps.settlements.serializers import (
    TransactionPairSerializer,
    PairCreateSerializer,
    AAScanSerializer,
    AACreateSerializer,
    SettlementItemSerializer,
    SettlementGroupSerializer,
    SettlementItemCreateSerializer,
    CandidateSearchSerializer,
)
from apps.settlements.models import TransactionPair, SettlementGroup, SettlementItem
from apps.transactions.models import Transaction
from apps.accounts.models import Account
from apps.categories.models import Category


@pytest.mark.django_db
class TestTransactionPairSerializer:
    """TransactionPairSerializer"""

    def test_serialization(self):
        account = Account.objects.create(name='测试账户', account_type='debit')
        expense_tx = Transaction.objects.create(
            trans_date='2024-01-10', amount=100, direction='expense',
            source='alipay', status='confirmed', account=account,
            description='消费', merchant='商户A', unique_key='tp_exp'
        )
        refund_tx = Transaction.objects.create(
            trans_date='2024-01-15', amount=100, direction='income',
            source='alipay', status='confirmed', account=account,
            description='退款', merchant='商户A', unique_key='tp_ref'
        )
        pair = TransactionPair.objects.create(
            expense_tx=expense_tx, refund_tx=refund_tx,
            match_score=80, match_method='auto',
            match_detail={'amount_match': 80, 'date_match': 60}
        )

        serializer = TransactionPairSerializer(pair)
        data = serializer.data
        assert data['expense_tx'] == expense_tx.id
        assert data['refund_tx'] == refund_tx.id
        assert data['expense_date'] == '2024-01-10'
        assert data['refund_date'] == '2024-01-15'
        assert data['expense_amount'] == '100.00'
        assert data['refund_amount'] == '100.00'
        assert data['match_score'] == 80.0
        assert data['match_method'] == 'auto'


class TestPairCreateSerializer:
    """PairCreateSerializer"""

    def test_valid(self):
        serializer = PairCreateSerializer(data={'expense_id': 1, 'refund_id': 2})
        assert serializer.is_valid()
        assert serializer.validated_data['expense_id'] == 1
        assert serializer.validated_data['refund_id'] == 2

    def test_missing_expense_id(self):
        serializer = PairCreateSerializer(data={'refund_id': 2})
        assert not serializer.is_valid()
        assert 'expense_id' in serializer.errors

    def test_missing_refund_id(self):
        serializer = PairCreateSerializer(data={'expense_id': 1})
        assert not serializer.is_valid()
        assert 'refund_id' in serializer.errors


class TestAAScanSerializer:
    """AAScanSerializer"""

    def test_empty(self):
        serializer = AAScanSerializer(data={})
        assert serializer.is_valid()


class TestAACreateSerializer:
    """AACreateSerializer"""

    def test_valid(self):
        serializer = AACreateSerializer(data={
            'receipt_ids': [1, 2, 3],
            'expense_id': 10,
            'group_name': '测试AA',
        })
        assert serializer.is_valid()
        assert serializer.validated_data['receipt_ids'] == [1, 2, 3]
        assert serializer.validated_data['expense_id'] == 10

    def test_default_group_name(self):
        serializer = AACreateSerializer(data={
            'receipt_ids': [1],
            'expense_id': 10,
        })
        assert serializer.is_valid()
        assert serializer.validated_data['group_name'] == 'AA 群收款'

    def test_missing_receipt_ids(self):
        serializer = AACreateSerializer(data={'expense_id': 10})
        assert not serializer.is_valid()

    def test_missing_expense_id(self):
        serializer = AACreateSerializer(data={'receipt_ids': [1]})
        assert not serializer.is_valid()


@pytest.mark.django_db
class TestSettlementItemSerializer:
    """SettlementItemSerializer"""

    def test_serialization(self):
        account = Account.objects.create(name='测试账户', account_type='debit')
        tx = Transaction.objects.create(
            trans_date='2024-01-15', amount=150, direction='expense',
            source='alipay', status='confirmed', account=account,
            description='测试交易', merchant='测试商户', unique_key='si_key'
        )
        group = SettlementGroup.objects.create(name='结算组')
        item = SettlementItem.objects.create(
            settlement=group, transaction=tx, item_type='advance'
        )

        serializer = SettlementItemSerializer(item)
        data = serializer.data
        assert data['transaction'] == tx.id
        assert data['item_type'] == 'advance'
        assert data['trans_date'] == '2024-01-15'
        assert data['amount'] == '150.00'
        assert data['description'] == '测试交易'
        assert data['direction'] == 'expense'


@pytest.mark.django_db
class TestSettlementGroupSerializer:
    """SettlementGroupSerializer"""

    def test_serialization(self):
        group = SettlementGroup.objects.create(
            name='结算组', description='测试',
            total_advance=500, total_reimbursement=300,
            net_amount=200
        )

        serializer = SettlementGroupSerializer(group)
        data = serializer.data
        assert data['name'] == '结算组'
        assert data['description'] == '测试'
        assert data['status'] == 'open'
        assert data['total_advance'] == '500.00'
        assert data['total_reimbursement'] == '300.00'
        assert data['net_amount'] == '200.00'
        assert data['items'] == []

    def test_with_items(self):
        account = Account.objects.create(name='测试账户', account_type='debit')
        tx = Transaction.objects.create(
            trans_date='2024-01-15', amount=150, direction='expense',
            source='alipay', status='confirmed', account=account,
            unique_key='sg_with_items'
        )
        group = SettlementGroup.objects.create(name='结算组')
        SettlementItem.objects.create(
            settlement=group, transaction=tx, item_type='advance'
        )

        serializer = SettlementGroupSerializer(group)
        data = serializer.data
        assert len(data['items']) == 1
        assert data['items'][0]['transaction'] == tx.id


class TestSettlementItemCreateSerializer:
    """SettlementItemCreateSerializer"""

    def test_valid(self):
        serializer = SettlementItemCreateSerializer(data={
            'transaction_id': 1,
            'item_type': 'advance',
        })
        assert serializer.is_valid()

    def test_invalid_item_type(self):
        serializer = SettlementItemCreateSerializer(data={
            'transaction_id': 1,
            'item_type': 'invalid',
        })
        assert not serializer.is_valid()
        assert 'item_type' in serializer.errors

    def test_missing_fields(self):
        serializer = SettlementItemCreateSerializer(data={})
        assert not serializer.is_valid()


class TestCandidateSearchSerializer:
    """CandidateSearchSerializer"""

    def test_valid_empty(self):
        serializer = CandidateSearchSerializer(data={})
        assert serializer.is_valid()
        assert serializer.validated_data['keyword'] == ''
        assert serializer.validated_data['direction'] == ''

    def test_with_params(self):
        serializer = CandidateSearchSerializer(data={
            'keyword': 'test',
            'direction': 'expense',
        })
        assert serializer.is_valid()
        assert serializer.validated_data['keyword'] == 'test'
        assert serializer.validated_data['direction'] == 'expense'
