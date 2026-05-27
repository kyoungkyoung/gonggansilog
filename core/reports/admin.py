from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import GeneratedReport


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'contract', 'report_type', 'language', 'status', 'generated_by', 'created_at']
    list_filter = ['report_type', 'language', 'status', 'created_at']
    search_fields = ['uuid', 'contract__address', 'generated_by__username']
    readonly_fields = ['uuid', 'created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        (_('Report Information'), {
            'fields': ('uuid', 'contract', 'record', 'report_type', 'language')
        }),
        (_('Status'), {
            'fields': ('status', 'error_message')
        }),
        (_('File'), {
            'fields': ('file',)
        }),
        (_('Metadata'), {
            'fields': ('generated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
