"""
规则引擎模型 — 有效规则（白名单）+ 无效规则（黑名单）

匹配条件（所有条件为 AND 关系）：
- sources         精确匹配，逗号分隔
- trans_types     子串匹配
- directions      expense / income
- categories      子串匹配
- payment_channels 子串匹配
- keywords        搜索范围：description + merchant + counterparty + trans_type + payment_channel
- keyword_exclude 搜索范围：description + merchant + counterparty + trans_type（不含 payment_channel）
- merchants       子串匹配
- amount_min/max  数值区间

无效规则额外支持：
- counterparties  对手方精确匹配
"""
from django.db import models


class RuleBase(models.Model):
    """规则基类 — 有效/无效规则共享的字段"""

    name = models.CharField('规则名称', max_length=100)
    priority = models.IntegerField('优先级', default=50,
                                   help_text='数值越大优先级越高')
    is_active = models.BooleanField('启用', default=True)

    # ── 匹配条件 ──────────────────────────────────
    sources = models.CharField('来源', max_length=200, blank=True, default='',
                               help_text='逗号分隔，精确匹配。如 alipay,bocom_debit')
    trans_types = models.CharField('交易类型', max_length=200, blank=True, default='',
                                   help_text='逗号分隔，子串匹配')
    directions = models.CharField('收支方向', max_length=50, blank=True, default='',
                                  help_text='逗号分隔：expense / income')
    categories = models.CharField('分类', max_length=200, blank=True, default='',
                                  help_text='逗号分隔，子串匹配分类名')
    payment_channels = models.CharField('支付渠道', max_length=200, blank=True, default='',
                                        help_text='逗号分隔，子串匹配')
    keywords = models.TextField('关键词', blank=True, default='',
                                help_text='逗号分隔。搜索范围：description+merchant+counterparty+trans_type+payment_channel')
    keyword_exclude = models.TextField('排除关键词', blank=True, default='',
                                       help_text='逗号分隔。搜索范围同上但不含 payment_channel')
    merchants = models.TextField('商户', blank=True, default='',
                                 help_text='逗号分隔，子串匹配')
    amount_min = models.DecimalField('最小金额', max_digits=12, decimal_places=2,
                                     null=True, blank=True)
    amount_max = models.DecimalField('最大金额', max_digits=12, decimal_places=2,
                                     null=True, blank=True)

    # ── 统计 ──────────────────────────────────────
    hit_count = models.IntegerField('命中次数', default=0)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-priority', 'id']


class ValidRule(RuleBase):
    """有效规则（白名单）— 命中则标记交易为有效"""

    class Meta:
        verbose_name = '有效规则'
        verbose_name_plural = '有效规则'

    def __str__(self):
        return f'[有效] {self.name} (优先级:{self.priority})'


class InvalidRule(RuleBase):
    """无效规则（黑名单）— 命中则标记交易为无效（覆盖有效规则）"""

    # 无效规则额外支持的匹配条件
    counterparties = models.TextField('对手方', blank=True, default='',
                                      help_text='逗号分隔，精确匹配 counterparty 字段')

    class Meta:
        verbose_name = '无效规则'
        verbose_name_plural = '无效规则'

    def __str__(self):
        return f'[无效] {self.name} (优先级:{self.priority})'
