from django.contrib import admin
from .models import ImportLog


@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = ['source_file', 'source', 'imported_rows', 'skipped_rows',
                    'error_rows', 'status', 'created_at']
    list_filter = ['source', 'status']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
