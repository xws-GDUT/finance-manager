"""
导入日志模型 — 记录每次导入的结果
"""
from django.db import models


class ImportLog(models.Model):
    """导入历史日志"""

    source = models.CharField('数据来源', max_length=20)
    source_file = models.CharField('文件名', max_length=255)
    file_size = models.BigIntegerField('文件大小(字节)', default=0)

    total_rows = models.IntegerField('总行数', default=0)
    imported_rows = models.IntegerField('导入行数', default=0)
    skipped_rows = models.IntegerField('跳过行数', default=0)
    error_rows = models.IntegerField('错误行数', default=0)

    # 错误详情（前几条错误的描述）
    error_detail = models.JSONField('错误详情', default=list, blank=True)

    status = models.CharField('状态', max_length=20, default='success')
    created_at = models.DateTimeField('导入时间', auto_now_add=True)

    class Meta:
        verbose_name = '导入日志'
        verbose_name_plural = '导入日志'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.source_file} ({self.imported_rows}行) - {self.created_at:%Y-%m-%d %H:%M}'
