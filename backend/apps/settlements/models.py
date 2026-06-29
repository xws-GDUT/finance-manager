"""
退款配对 + 垫付结算模型

- TransactionPair: 消费-退款配对
- SettlementGroup: 垫付结算组
- SettlementItem:  结算明细
"""
from django.db import models


class TransactionPair(models.Model):
    """退款配对 — 消费交易与退款交易的关联"""

    MATCH_AUTO = 'auto'
    MATCH_MANUAL = 'manual'
    MATCH_AA = 'aa'
    MATCH_METHOD_CHOICES = [
        (MATCH_AUTO, '自动配对'),
        (MATCH_MANUAL, '手动配对'),
        (MATCH_AA, 'AA群收款'),
    ]

    expense_tx = models.ForeignKey(
        'transactions.Transaction',
        on_delete=models.CASCADE,
        related_name='expense_pairs',
        verbose_name='消费交易'
    )
    refund_tx = models.ForeignKey(
        'transactions.Transaction',
        on_delete=models.CASCADE,
        related_name='refund_pairs',
        verbose_name='退款交易'
    )
    match_score = models.FloatField('匹配得分', default=0,
                                    help_text='0-100，≥60 自动配对')
    match_method = models.CharField('配对方式', max_length=10, choices=MATCH_METHOD_CHOICES,
                                    default=MATCH_AUTO)
    match_detail = models.JSONField('匹配详情', default=dict, blank=True,
                                    help_text='各维度得分明细')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '退款配对'
        verbose_name_plural = '退款配对'
        ordering = ['-created_at']

    def __str__(self):
        return f'配对 #{self.id}: 消费#{self.expense_tx_id} ↔ 退款#{self.refund_tx_id}'


class SettlementGroup(models.Model):
    """垫付结算组"""

    STATUS_OPEN = 'open'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_OPEN, '进行中'),
        (STATUS_CLOSED, '已结算'),
    ]

    name = models.CharField('结算组名称', max_length=100)
    description = models.TextField('描述', blank=True, default='')
    status = models.CharField('状态', max_length=10, choices=STATUS_CHOICES, default=STATUS_OPEN)

    total_advance = models.DecimalField('垫付总额', max_digits=12, decimal_places=2, default=0)
    total_reimbursement = models.DecimalField('收款总额', max_digits=12, decimal_places=2, default=0)
    net_amount = models.DecimalField('净支出', max_digits=12, decimal_places=2, default=0,
                                     help_text='垫付 - 收款，最低 0')

    # 关闭结算时生成的虚拟交易
    virtual_tx = models.ForeignKey(
        'transactions.Transaction',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='virtual_settlements',
        verbose_name='虚拟交易'
    )

    # AA 群收款关联
    is_aa = models.BooleanField('AA群收款', default=False)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '结算组'
        verbose_name_plural = '结算组'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.get_status_display()})'


class SettlementItem(models.Model):
    """结算明细 — 结算组中的每笔交易"""

    ITEM_ADVANCE = 'advance'
    ITEM_REIMBURSEMENT = 'reimbursement'
    ITEM_TYPE_CHOICES = [
        (ITEM_ADVANCE, '垫付'),
        (ITEM_REIMBURSEMENT, '收款'),
    ]

    settlement = models.ForeignKey(
        SettlementGroup,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='结算组'
    )
    transaction = models.ForeignKey(
        'transactions.Transaction',
        on_delete=models.CASCADE,
        related_name='settlement_items',
        verbose_name='交易'
    )
    item_type = models.CharField('类型', max_length=15, choices=ITEM_TYPE_CHOICES)
    created_at = models.DateTimeField('加入时间', auto_now_add=True)

    class Meta:
        verbose_name = '结算明细'
        verbose_name_plural = '结算明细'
        ordering = ['id']
        unique_together = [('settlement', 'transaction')]

    def __str__(self):
        return f'{self.settlement.name} - {self.get_item_type_display()} #{self.transaction_id}'
