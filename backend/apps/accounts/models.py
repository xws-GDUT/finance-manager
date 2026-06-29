"""
账户模型 — 预置 8 个账户
"""
from django.db import models


class Account(models.Model):
    """支付账户（银行卡、支付平台、信用账户）"""

    TYPE_DEBIT = 'debit'
    TYPE_CREDIT = 'credit'
    TYPE_PLATFORM = 'platform'
    TYPE_CHOICES = [
        (TYPE_DEBIT, '储蓄卡'),
        (TYPE_CREDIT, '信用卡'),
        (TYPE_PLATFORM, '支付平台'),
    ]

    name = models.CharField('账户名称', max_length=50, unique=True)
    account_type = models.CharField('账户类型', max_length=10, choices=TYPE_CHOICES, default=TYPE_PLATFORM)
    bank_name = models.CharField('银行名称', max_length=50, blank=True, default='')
    owner = models.CharField('持有人', max_length=50, blank=True, default='')
    # 用于导入时自动匹配（payment_method 字段的值）
    match_keywords = models.CharField('匹配关键词', max_length=200, blank=True, default='',
                                      help_text='逗号分隔，用于导入时自动匹配账户')
    is_active = models.BooleanField('启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '账户'
        verbose_name_plural = '账户'
        ordering = ['id']

    def __str__(self):
        return self.name
