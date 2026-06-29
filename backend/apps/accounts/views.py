"""
账户管理 API
"""
from django.db.models import Count, Sum, Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from apps.accounts.models import Account
from apps.transactions.models import Transaction


@api_view(['GET'])
def account_list(request):
    """账户列表（含交易统计）"""
    accounts = Account.objects.filter(is_active=True)

    data = []
    for acc in accounts:
        txs = Transaction.objects.filter(account=acc).exclude(status='deleted')

        total_expense = txs.filter(
            direction='expense', status='confirmed'
        ).aggregate(s=Sum('amount'))['s'] or 0
        total_income = txs.filter(
            direction='income', status='confirmed'
        ).aggregate(s=Sum('amount'))['s'] or 0
        tx_count = txs.count()

        data.append({
            'id': acc.id,
            'name': acc.name,
            'account_type': acc.account_type,
            'bank_name': acc.bank_name,
            'owner': acc.owner,
            'match_keywords': acc.match_keywords,
            'is_active': acc.is_active,
            'stats': {
                'tx_count': tx_count,
                'total_expense': float(total_expense),
                'total_income': float(total_income),
            },
        })

    return Response(data)
