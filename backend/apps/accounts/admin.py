from django.contrib import admin
from .models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_type', 'bank_name', 'owner', 'is_active']
    list_filter = ['account_type', 'is_active']
    list_editable = ['is_active']
    search_fields = ['name', 'bank_name', 'match_keywords']
