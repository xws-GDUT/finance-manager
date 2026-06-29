"""
分类模型 — 预置 17 个父分类 + 14 个子分类
"""
from django.db import models


class Category(models.Model):
    """支出/收入/转账分类，支持父子层级"""

    TYPE_EXPENSE = 'expense'
    TYPE_INCOME = 'income'
    TYPE_TRANSFER = 'transfer'
    TYPE_CHOICES = [
        (TYPE_EXPENSE, '支出'),
        (TYPE_INCOME, '收入'),
        (TYPE_TRANSFER, '转账'),
    ]

    name = models.CharField('分类名称', max_length=50)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='children',
        verbose_name='父分类'
    )
    icon = models.CharField('图标', max_length=20, blank=True, default='')
    type = models.CharField('类型', max_length=10, choices=TYPE_CHOICES, default=TYPE_EXPENSE)
    sort_order = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '分类'
        verbose_name_plural = '分类'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'{self.icon} {self.name}'

    @property
    def is_parent(self):
        return self.parent is None
