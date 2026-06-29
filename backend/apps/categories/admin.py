from django.contrib import admin
from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['icon', 'name', 'parent', 'type', 'sort_order', 'is_active']
    list_filter = ['type', 'is_active']
    list_editable = ['is_active', 'sort_order']
    search_fields = ['name']
