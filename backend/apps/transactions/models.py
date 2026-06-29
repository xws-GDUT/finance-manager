"""
交易流水模型 — 核心数据表

关键约定：
- 金额统一存储绝对值，direction 字段表达方向（expense/income）
- unique_key 用于导入去重（MD5 前 16 位）
- 软删除：status='deleted' 而非物理删除
- 虚拟交易：is_virtual=True 用于结算生成的净支出
"""
from django.db import models


class Transaction(models.Model):
    """交易流水"""

    # 方向
    DIRECTION_EXPENSE = 'expense'
    DIRECTION_INCOME = 'income'
    DIRECTION_CHOICES = [
        (DIRECTION_EXPENSE, '支出'),
        (DIRECTION_INCOME, '收入'),
    ]

    # 来源（9 种数据源）
    SOURCE_ALIPAY = 'alipay'
    SOURCE_JD = 'jd'
    SOURCE_MEITUAN = 'meituan'
    SOURCE_WECHAT = 'wechat'
    SOURCE_BOCOM_DEBIT = 'bocom_debit'
    SOURCE_CMB_DEBIT = 'cmb_debit'
    SOURCE_CIB_CREDIT = 'cib_credit'
    SOURCE_CMB_CREDIT = 'cmb_credit'
    SOURCE_DOUYIN = 'douyin'
    SOURCE_CHOICES = [
        (SOURCE_ALIPAY, '支付宝'),
        (SOURCE_JD, '京东'),
        (SOURCE_MEITUAN, '美团'),
        (SOURCE_WECHAT, '微信支付'),
        (SOURCE_BOCOM_DEBIT, '交通银行储蓄卡'),
        (SOURCE_CMB_DEBIT, '招商银行储蓄卡'),
        (SOURCE_CIB_CREDIT, '中信信用卡'),
        (SOURCE_CMB_CREDIT, '招商银行信用卡'),
        (SOURCE_DOUYIN, '抖音月付'),
    ]

    # 状态（三态 + 已删除）
    STATUS_CONFIRMED = 'confirmed'
    STATUS_EXCLUDED = 'excluded'
    STATUS_UNKNOWN = 'unknown'
    STATUS_DELETED = 'deleted'
    STATUS_CHOICES = [
        (STATUS_CONFIRMED, '有效'),
        (STATUS_EXCLUDED, '无效'),
        (STATUS_UNKNOWN, '未知'),
        (STATUS_DELETED, '已删除'),
    ]

    # ── 基础字段 ──────────────────────────────────
    trans_date = models.DateField('交易日期')
    amount = models.DecimalField('金额', max_digits=12, decimal_places=2,
                                 help_text='绝对值，方向由 direction 决定')
    direction = models.CharField('收支方向', max_length=10, choices=DIRECTION_CHOICES)
    source = models.CharField('数据来源', max_length=20, choices=SOURCE_CHOICES)
    status = models.CharField('状态', max_length=10, choices=STATUS_CHOICES, default=STATUS_UNKNOWN)

    # ── 交易详情 ──────────────────────────────────
    trans_type = models.CharField('交易类型', max_length=100, blank=True, default='')
    description = models.TextField('交易描述', blank=True, default='')
    merchant = models.CharField('商户名', max_length=200, blank=True, default='')
    counterparty = models.CharField('对手方', max_length=200, blank=True, default='')
    payment_method = models.CharField('支付方式', max_length=100, blank=True, default='')
    payment_channel = models.CharField('支付渠道', max_length=100, blank=True, default='')
    remark = models.TextField('备注', blank=True, default='')

    # ── 分类与账户 ────────────────────────────────
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='分类'
    )
    account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='账户'
    )

    # ── 规则关联 ──────────────────────────────────
    valid_rule = models.ForeignKey(
        'rules.ValidRule',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='命中的有效规则'
    )
    invalid_rule = models.ForeignKey(
        'rules.InvalidRule',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='命中的无效规则'
    )

    # ── 配对与结算 ────────────────────────────────
    pair = models.ForeignKey(
        'settlements.TransactionPair',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='退款配对'
    )
    settlement = models.ForeignKey(
        'settlements.SettlementGroup',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='所属结算组'
    )

    # ── 特殊标记 ──────────────────────────────────
    is_virtual = models.BooleanField('虚拟交易', default=False,
                                     help_text='结算关闭时生成的净支出虚拟交易')
    unique_key = models.CharField('唯一键', max_length=32, unique=True,
                                  help_text='MD5 前 16 位，用于导入去重')

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '交易'
        verbose_name_plural = '交易'
        ordering = ['-trans_date', '-id']
        indexes = [
            models.Index(fields=['trans_date']),
            models.Index(fields=['source']),
            models.Index(fields=['status']),
            models.Index(fields=['direction']),
            models.Index(fields=['unique_key']),
        ]

    def __str__(self):
        return f'{self.trans_date} {self.get_direction_display()} ¥{self.amount} ({self.get_source_display()})'
