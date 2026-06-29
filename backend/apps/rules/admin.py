from django.contrib import admin
from .models import ValidRule, InvalidRule


class RuleAdminBase(admin.ModelAdmin):
    list_display = ['name', 'priority', 'is_active', 'hit_count', 'sources', 'directions']
    list_filter = ['is_active']
    search_fields = ['name', 'keywords', 'keyword_exclude', 'merchants']
    list_editable = ['is_active', 'priority']
    readonly_fields = ['hit_count', 'created_at', 'updated_at']


@admin.register(ValidRule)
class ValidRuleAdmin(RuleAdminBase):
    pass


@admin.register(InvalidRule)
class InvalidRuleAdmin(RuleAdminBase):
    list_display = RuleAdminBase.list_display + ['counterparties']
