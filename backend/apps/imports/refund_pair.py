"""
退款配对引擎

功能：
1. 自动识别退款交易（含退款关键词的收入交易）
2. 三维度配对算法（时间 20% + 金额 40% + 商户 40%）
3. 综合得分 ≥ 60 分自动配对
4. 配对后双方标记为无效
"""
from decimal import Decimal
from datetime import timedelta
from django.db import transaction as db_transaction
from django.db.models import Q
from django.utils import timezone


# 退款关键词
REFUND_KEYWORDS = [
    '退款', '退货', '退票', '退差价', '撤销交易', '冲正',
    '返还', '退回', '退订', '退费', '退换', '退款成功',
    '已退款', '快捷退款', '原路退回',
]

# AA 群收款关键词
AA_KEYWORDS = ['群收款', 'aa收款', 'aa收', '分摊', '群收']


class RefundPairEngine:
    """退款配对引擎"""

    def __init__(self, pair_model, transaction_model):
        self.Pair = pair_model
        self.Transaction = transaction_model

    def find_refund_candidates(self) -> list:
        """
        查找所有可能的退款交易

        Returns:
            包含退款关键词的收入交易 queryset
        """
        q = Q()
        for kw in REFUND_KEYWORDS:
            q |= Q(description__icontains=kw)
            q |= Q(merchant__icontains=kw)

        return self.Transaction.objects.filter(
            q,
            direction='income',
            status__in=['confirmed', 'unknown'],
        ).exclude(status='deleted')

    def auto_pair(self) -> dict:
        """
        自动执行退款配对

        算法：
        对每笔退款候选，在同来源的支出交易中找最佳匹配：
        1. 时间维度（权重 20%）：退款在消费后 30 天内
        2. 金额维度（权重 40%）：退款金额 ≤ 消费金额
        3. 商户维度（权重 40%）：商户名相似度

        Returns:
            {'paired': int, 'skipped': int, 'pairs': list}
        """
        refunds = self.find_refund_candidates()
        paired = 0
        skipped = 0
        pairs = []

        for refund in refunds:
            # 查找同来源、30天内的支出交易
            cutoff_date = refund.trans_date - timedelta(days=30)
            candidates = self.Transaction.objects.filter(
                source=refund.source,
                direction='expense',
                status__in=['confirmed', 'unknown'],
                trans_date__gte=cutoff_date,
                trans_date__lte=refund.trans_date,
            ).exclude(status='deleted')

            if not candidates.exists():
                skipped += 1
                continue

            # 计算得分，找最佳匹配
            best_score = 0
            best_candidate = None

            for expense in candidates:
                score = self._calculate_match_score(expense, refund)
                if score > best_score:
                    best_score = score
                    best_candidate = expense

            # 得分 ≥ 60 自动配对
            if best_score >= 60 and best_candidate:
                with db_transaction.atomic():
                    pair = self.Pair.objects.create(
                        expense_tx=best_candidate,
                        refund_tx=refund,
                        match_score=best_score,
                        match_method='auto',
                        match_detail={
                            'time_score': self._time_score(best_candidate, refund),
                            'amount_score': self._amount_score(best_candidate, refund),
                            'merchant_score': self._merchant_score(best_candidate, refund),
                        },
                    )
                    # 标记双方为无效
                    best_candidate.status = 'excluded'
                    best_candidate.pair = pair
                    best_candidate.save(update_fields=['status', 'pair'])
                    refund.status = 'excluded'
                    refund.pair = pair
                    refund.save(update_fields=['status', 'pair'])

                paired += 1
                pairs.append({
                    'pair_id': pair.id,
                    'expense_id': best_candidate.id,
                    'refund_id': refund.id,
                    'score': best_score,
                })
            else:
                skipped += 1

        return {'paired': paired, 'skipped': skipped, 'pairs': pairs}

    def _calculate_match_score(self, expense, refund) -> float:
        """计算消费-退款匹配综合得分（0-100）"""
        time_s = self._time_score(expense, refund) * 0.20
        amount_s = self._amount_score(expense, refund) * 0.40
        merchant_s = self._merchant_score(expense, refund) * 0.40
        return time_s + amount_s + merchant_s

    def _time_score(self, expense, refund) -> float:
        """
        时间维度得分（权重 20%）
        - 同一天：100
        - 30天内线性递减
        - 超过30天：0
        """
        delta = (refund.trans_date - expense.trans_date).days
        if delta < 0:
            return 0
        if delta == 0:
            return 100
        if delta <= 30:
            return 100 * (1 - delta / 30)
        return 0

    def _amount_score(self, expense, refund) -> float:
        """
        金额维度得分（权重 40%）
        - 退款金额 ≤ 消费金额：100 * (退款/消费)
        - 退款金额 > 消费金额：0
        """
        if refund.amount > expense.amount:
            return 0
        if expense.amount == 0:
            return 0
        ratio = float(refund.amount / expense.amount)
        return 100 * ratio

    def _merchant_score(self, expense, refund) -> float:
        """
        商户维度得分（权重 40%）
        - 完全相同：100
        - 一方包含另一方：90
        - 最长公共子串：按比例
        """
        e_name = (expense.merchant + ' ' + expense.description).lower().strip()
        r_name = (refund.merchant + ' ' + refund.description).lower().strip()

        if not e_name or not r_name:
            return 0

        if e_name == r_name:
            return 100

        if e_name in r_name or r_name in e_name:
            return 90

        lcs_len = self._lcs_length(e_name, r_name)
        max_len = max(len(e_name), len(r_name))
        if max_len == 0:
            return 0
        return 100 * lcs_len / max_len

    @staticmethod
    def _lcs_length(a: str, b: str) -> int:
        """最长公共子串长度"""
        m, n = len(a), len(b)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        max_len = 0
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if a[i - 1] == b[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                    max_len = max(max_len, dp[i][j])
        return max_len

    def manual_pair(self, expense_id: int, refund_id: int) -> dict | None:
        """手动创建配对"""
        try:
            expense = self.Transaction.objects.get(id=expense_id, direction='expense')
            refund = self.Transaction.objects.get(id=refund_id, direction='income')
        except self.Transaction.DoesNotExist:
            return None

        score = self._calculate_match_score(expense, refund)

        with db_transaction.atomic():
            pair = self.Pair.objects.create(
                expense_tx=expense,
                refund_tx=refund,
                match_score=score,
                match_method='manual',
            )
            expense.status = 'excluded'
            expense.pair = pair
            expense.save(update_fields=['status', 'pair'])
            refund.status = 'excluded'
            refund.pair = pair
            refund.save(update_fields=['status', 'pair'])

        return {
            'pair_id': pair.id,
            'expense_id': expense.id,
            'refund_id': refund.id,
            'score': score,
        }

    def unpair(self, pair_id: int) -> bool:
        """解除配对，恢复双方为有效状态"""
        try:
            pair = self.Pair.objects.get(id=pair_id)
        except self.Pair.DoesNotExist:
            return False

        with db_transaction.atomic():
            # 恢复交易状态
            expense = pair.expense_tx
            refund = pair.refund_tx
            expense.status = 'confirmed'
            expense.pair = None
            expense.save(update_fields=['status', 'pair'])
            refund.status = 'confirmed'
            refund.pair = None
            refund.save(update_fields=['status', 'pair'])
            pair.delete()

        return True
