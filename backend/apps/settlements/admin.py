from django.contrib import admin
from .models import TransactionPair, SettlementGroup, SettlementItem


@admin.register(TransactionPair)
class TransactionPairAdmin(admin.ModelAdmin):
    list_display = ['id', 'expense_tx', 'refund_tx', 'match_score', 'match_method']
    list_filter = ['match_method']
    readonly_fields = ['created_at']


class SettlementItemInline(admin.TabularInline):
    model = SettlementItem
    extra = 0
    readonly_fields = ['created_at']


@admin.register(SettlementGroup)
class SettlementGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'total_advance', 'total_reimbursement',
                    'net_amount', 'is_aa']
    list_filter = ['status', 'is_aa']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [SettlementItemInline]
