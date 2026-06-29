"""
统计分析 API — 总览/月度趋势/分类统计/每日趋势
"""
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth, TruncDate
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.transactions.models import Transaction


@api_view(['GET'])
def stats_overview(request):
    """总览统计 — 总支出/总收入/本月支出/收支结余"""
    effective = Transaction.objects.filter(status='confirmed', is_virtual=False)

    total_expense = effective.filter(direction='expense').aggregate(
        total=Sum('amount')
    )['total'] or 0
    total_income = effective.filter(direction='income').aggregate(
        total=Sum('amount')
    )['total'] or 0

    # 本月
    today = date.today()
    month_start = today.replace(day=1)
    month_expense = effective.filter(
        direction='expense', trans_date__gte=month_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    month_income = effective.filter(
        direction='income', trans_date__gte=month_start
    ).aggregate(total=Sum('amount'))['total'] or 0

    # 交易总数
    total_count = Transaction.objects.exclude(status='deleted').count()
    effective_count = effective.count()

    return Response({
        'total_expense': float(total_expense),
        'total_income': float(total_income),
        'balance': float(total_income) - float(total_expense),
        'month_expense': float(month_expense),
        'month_income': float(month_income),
        'month_balance': float(month_income) - float(month_expense),
        'total_count': total_count,
        'effective_count': effective_count,
    })


@api_view(['GET'])
def stats_monthly(request):
    """月度收支趋势（近 12 个月）"""
    today = date.today()
    start_date = today - relativedelta(months=11)
    start_date = start_date.replace(day=1)

    effective = Transaction.objects.filter(
        status='confirmed', is_virtual=False, trans_date__gte=start_date
    )

    # 按月汇总
    monthly = (
        effective
        .annotate(month=TruncMonth('trans_date'))
        .values('month', 'direction')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    # 整理数据
    months = {}
    for item in monthly:
        key = item['month'].strftime('%Y-%m')
        if key not in months:
            months[key] = {'month': key, 'expense': 0, 'income': 0}
        if item['direction'] == 'expense':
            months[key]['expense'] = float(item['total'])
        else:
            months[key]['income'] = float(item['total'])

    # 填充缺失月份
    result = []
    for i in range(12):
        m = (start_date + relativedelta(months=i)).strftime('%Y-%m')
        result.append(months.get(m, {'month': m, 'expense': 0, 'income': 0}))

    return Response(result)


@api_view(['GET'])
def stats_category(request):
    """分类支出统计（Top 8 支出分类 + 笔数）"""
    effective = Transaction.objects.filter(
        status='confirmed', is_virtual=False, direction='expense'
    ).select_related('category')

    # 按父分类汇总
    stats = (
        effective
        .values('category__parent__name', 'category__parent__icon')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')
    )

    result = []
    for item in stats[:8]:
        name = item['category__parent__name'] or item.get('category__name', '未分类')
        icon = item['category__parent__icon'] or ''
        result.append({
            'name': name,
            'icon': icon,
            'amount': float(item['total']),
            'count': item['count'],
        })

    return Response(result)


@api_view(['GET'])
def stats_daily(request):
    """每日支出趋势（近 30 天）"""
    today = date.today()
    start_date = today - timedelta(days=29)

    effective = Transaction.objects.filter(
        status='confirmed', is_virtual=False,
        direction='expense', trans_date__gte=start_date,
    )

    daily = (
        effective
        .annotate(day=TruncDate('trans_date'))
        .values('day')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('day')
    )

    daily_map = {
        item['day'].isoformat(): {'date': item['day'].isoformat(),
                                    'amount': float(item['total']),
                                    'count': item['count']}
        for item in daily
    }

    result = []
    for i in range(30):
        d = (start_date + timedelta(days=i)).isoformat()
        result.append(daily_map.get(d, {'date': d, 'amount': 0, 'count': 0}))

    return Response(result)
