from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['trans_date', 'amount', 'direction', 'source', 'status',
                    'merchant', 'category', 'is_virtual']
    list_filter = ['source', 'status', 'direction', 'is_virtual']
    search_fields = ['description', 'merchant', 'counterparty', 'unique_key']
    date_hierarchy = 'trans_date'
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 50
