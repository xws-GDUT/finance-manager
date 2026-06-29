"""
垫付结算引擎

功能：
1. 创建/管理结算组
2. 添加垫付/收款交易
3. 自动计算净支出
4. 关闭结算（生成虚拟交易）
5. 重开结算（删除虚拟交易）
6. AA 群收款自动识别与聚类
"""
from decimal import Decimal
from datetime import timedelta
from django.db import transaction as db_transaction
from django.db.models import Sum, Q


class SettlementEngine:
    """垫付结算引擎"""

    def __init__(self, settlement_group_model, settlement_item_model,
                 transaction_model, category_model):
        self.SettlementGroup = settlement_group_model
        self.SettlementItem = settlement_item_model
        self.Transaction = transaction_model
        self.Category = category_model

    def create_group(self, name: str, description: str = '',
                     is_aa: bool = False) -> int:
        """创建结算组，返回 ID"""
        group = self.SettlementGroup.objects.create(
            name=name,
            description=description,
            is_aa=is_aa,
        )
        return group.id

    def add_item(self, settlement_id: int, transaction_id: int,
                 item_type: str) -> bool:
        """
        添加交易到结算组

        Args:
            settlement_id: 结算组 ID
            transaction_id: 交易 ID
            item_type: 'advance'（垫付）或 'reimbursement'（收款）

        Returns:
            是否成功
        """
        try:
            group = self.SettlementGroup.objects.get(id=settlement_id, status='open')
            tx = self.Transaction.objects.get(id=transaction_id)
        except (self.SettlementGroup.DoesNotExist, self.Transaction.DoesNotExist):
            return False

        # 避免重复添加
        if self.SettlementItem.objects.filter(
            settlement=group, transaction=tx
        ).exists():
            return False

        with db_transaction.atomic():
            self.SettlementItem.objects.create(
                settlement=group,
                transaction=tx,
                item_type=item_type,
            )
            self._recalculate(group)

        return True

    def remove_item(self, settlement_id: int, item_id: int) -> bool:
        """从结算组移除交易"""
        try:
            item = self.SettlementItem.objects.get(
                id=item_id, settlement_id=settlement_id
            )
            group = item.settlement
            if group.status != 'open':
                return False
            item.delete()
            self._recalculate(group)
            return True
        except self.SettlementItem.DoesNotExist:
            return False

    def close(self, settlement_id: int) -> int | None:
        """
        关闭结算

        生成虚拟交易（净支出 = 垫付 - 收款，最低 0），
        将所有成员交易标记为无效。

        Returns:
            虚拟交易 ID，失败返回 None
        """
        try:
            group = self.SettlementGroup.objects.get(id=settlement_id, status='open')
        except self.SettlementGroup.DoesNotExist:
            return None

        if group.net_amount <= 0:
            return None

        with db_transaction.atomic():
            # 创建虚拟交易
            default_category = self.Category.objects.filter(name='其他支出').first()

            virtual_tx = self.Transaction.objects.create(
                trans_date=timezone.now().date(),
                amount=group.net_amount,
                direction='expense',
                source='wechat',  # 虚拟交易默认来源
                status='excluded',
                description=f'[结算] {group.name}',
                merchant=group.name,
                trans_type='结算净支出',
                is_virtual=True,
                unique_key=f'virtual_settlement_{group.id}',
                category=default_category,
            )

            # 更新结算组
            group.status = 'closed'
            group.virtual_tx = virtual_tx
            group.save(update_fields=['status', 'virtual_tx'])

            # 标记成员交易为无效
            item_tx_ids = group.items.values_list('transaction_id', flat=True)
            self.Transaction.objects.filter(id__in=item_tx_ids).update(
                status='excluded',
                settlement=group,
            )

        return virtual_tx.id

    def reopen(self, settlement_id: int) -> bool:
        """
        重开结算

        删除虚拟交易，恢复成员交易为有效。
        """
        try:
            group = self.SettlementGroup.objects.get(id=settlement_id, status='closed')
        except self.SettlementGroup.DoesNotExist:
            return False

        with db_transaction.atomic():
            # 删除虚拟交易
            if group.virtual_tx:
                group.virtual_tx.delete()

            # 恢复成员交易
            item_tx_ids = group.items.values_list('transaction_id', flat=True)
            self.Transaction.objects.filter(id__in=item_tx_ids).update(
                status='confirmed',
                settlement=None,
            )

            # 更新结算组
            group.status = 'open'
            group.virtual_tx = None
            group.save(update_fields=['status', 'virtual_tx'])

        return True

    def _recalculate(self, group):
        """重新计算结算组的垫付/收款/净支出"""
        adv = (
            group.items.filter(item_type='advance')
            .aggregate(total=Sum('transaction__amount'))
        )
        reim = (
            group.items.filter(item_type='reimbursement')
            .aggregate(total=Sum('transaction__amount'))
        )

        group.total_advance = adv['total'] or Decimal('0')
        group.total_reimbursement = reim['total'] or Decimal('0')
        group.net_amount = max(group.total_advance - group.total_reimbursement, Decimal('0'))
        group.save(update_fields=['total_advance', 'total_reimbursement', 'net_amount'])

    def search_candidates(self, keyword: str, direction: str | None = None) -> list:
        """
        搜索可加入结算组的候选交易

        Args:
            keyword: 搜索关键词
            direction: 交易方向过滤

        Returns:
            候选交易列表
        """
        qs = self.Transaction.objects.filter(
            status='confirmed',
            is_virtual=False,
        )

        if direction:
            qs = qs.filter(direction=direction)

        if keyword:
            qs = qs.filter(
                Q(description__icontains=keyword) |
                Q(merchant__icontains=keyword) |
                Q(counterparty__icontains=keyword)
            )

        return list(qs.values(
            'id', 'trans_date', 'amount', 'direction',
            'description', 'merchant', 'source',
        )[:50])


class AAScanner:
    """
    AA 群收款扫描器

    算法：
    1. 识别微信群收款（含 AA 关键词的收入交易）
    2. 3 天内群收款归为同一场景
    3. 查找 ±3 天内的大额消费（金额 ≥ 总收款 × 0.3）
    4. 排除还款/信用/白条/月付/花呗/转账/提现类消费
    5. 每笔消费独立匹配（ratio = 总收款 / 消费金额，范围 0.3 ~ 1.05）
    """

    EXCLUDE_KEYWORDS = [
        '还款', '信用', '白条', '月付', '花呗', '转账', '提现',
        '借呗', '网商贷', '理财', '基金', '余额宝', '零钱通',
    ]

    def __init__(self, transaction_model):
        self.Transaction = transaction_model

    def scan(self) -> list[dict]:
        """
        扫描 AA 场景

        Returns:
            list of dict: 每个元素为一个 AA 场景
            {
                'receipts': [...],      # 群收款交易列表
                'total_receipt': Decimal,
                'candidate_expenses': [...],  # 可能的垫付消费
                'suggested_pairs': [...],     # 建议配对
            }
        """
        # 1. 查找所有 AA 群收款（来源为 wechat 的收入交易，含 AA 关键词）
        from apps.imports.refund_pair import AA_KEYWORDS

        q = Q()
        for kw in AA_KEYWORDS:
            q |= Q(description__icontains=kw)
            q |= Q(merchant__icontains=kw)

        receipts = self.Transaction.objects.filter(
            q,
            source='wechat',
            direction='income',
            status__in=['confirmed', 'unknown'],
        ).exclude(status='deleted').order_by('trans_date')

        if not receipts.exists():
            return []

        # 2. 按 3 天窗口聚类
        clusters = self._cluster_by_time(receipts, days=3)

        # 3. 为每个聚类查找对应的垫付消费
        results = []
        for cluster in clusters:
            total_receipt = sum(r.amount for r in cluster)
            min_date = min(r.trans_date for r in cluster) - timedelta(days=3)
            max_date = max(r.trans_date for r in cluster) + timedelta(days=3)

            # 查找 ±3 天内的大额消费
            candidate_expenses = self.Transaction.objects.filter(
                source='wechat',
                direction='expense',
                status__in=['confirmed', 'unknown'],
                trans_date__gte=min_date,
                trans_date__lte=max_date,
                amount__gte=total_receipt * Decimal('0.3'),
            ).exclude(status='deleted')

            # 排除非消费类
            filtered = []
            for exp in candidate_expenses:
                search_text = f"{exp.description} {exp.merchant} {exp.trans_type}"
                if not any(kw in search_text for kw in self.EXCLUDE_KEYWORDS):
                    filtered.append(exp)

            # 匹配
            suggested = []
            for exp in filtered:
                ratio = float(total_receipt / exp.amount) if exp.amount > 0 else 0
                if 0.3 <= ratio <= 1.05:
                    suggested.append({
                        'expense_id': exp.id,
                        'expense_date': exp.trans_date.isoformat(),
                        'expense_amount': str(exp.amount),
                        'expense_desc': exp.description,
                        'receipt_total': str(total_receipt),
                        'ratio': round(ratio, 2),
                    })

            results.append({
                'receipts': [
                    {
                        'id': r.id,
                        'date': r.trans_date.isoformat(),
                        'amount': str(r.amount),
                        'description': r.description,
                    }
                    for r in cluster
                ],
                'total_receipt': str(total_receipt),
                'candidate_expenses': [
                    {
                        'id': e.id,
                        'date': e.trans_date.isoformat(),
                        'amount': str(e.amount),
                        'description': e.description,
                    }
                    for e in filtered
                ],
                'suggested_pairs': suggested,
            })

        return results

    def _cluster_by_time(self, queryset, days: int = 3) -> list[list]:
        """按时间窗口聚类"""
        items = list(queryset)
        if not items:
            return []

        items.sort(key=lambda x: x.trans_date)
        clusters = []
        current = [items[0]]

        for item in items[1:]:
            if (item.trans_date - current[-1].trans_date).days <= days:
                current.append(item)
            else:
                clusters.append(current)
                current = [item]

        clusters.append(current)
        return clusters
