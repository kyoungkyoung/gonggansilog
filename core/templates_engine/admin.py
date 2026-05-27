from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import InspectionTemplate, TemplateSection, TemplateItem


class TemplateItemInline(admin.TabularInline):
    model = TemplateItem
    extra = 1
    fields = ['code', 'name_ko', 'name_en', 'name_ja', 'item_type', 'is_required', 'responsibility_hint', 'order']
    ordering = ['order', 'code']


class TemplateSectionInline(admin.TabularInline):
    model = TemplateSection
    extra = 1
    fields = ['code', 'name_ko', 'name_en', 'name_ja', 'is_required', 'order']
    ordering = ['order', 'code']
    show_change_link = True


@admin.register(InspectionTemplate)
class InspectionTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'property_type', 'version', 'is_active', 'is_default', 'created_at']
    list_filter = ['country', 'property_type', 'is_active', 'is_default']
    search_fields = ['name', 'name_en', 'name_ja', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [TemplateSectionInline]

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'name_en', 'name_ja', 'description')
        }),
        (_('Classification'), {
            'fields': ('country', 'property_type')
        }),
        (_('Status'), {
            'fields': ('version', 'is_active', 'is_default')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TemplateSection)
class TemplateSectionAdmin(admin.ModelAdmin):
    list_display = ['name_ko', 'template', 'code', 'is_required', 'order']
    list_filter = ['template', 'is_required']
    search_fields = ['name_ko', 'name_en', 'name_ja', 'code']
    ordering = ['template', 'order', 'code']
    inlines = [TemplateItemInline]

    fieldsets = (
        (_('Template'), {
            'fields': ('template',)
        }),
        (_('Section Information'), {
            'fields': ('code', 'name_ko', 'name_en', 'name_ja', 'description')
        }),
        (_('Settings'), {
            'fields': ('order', 'is_required')
        }),
    )


@admin.register(TemplateItem)
class TemplateItemAdmin(admin.ModelAdmin):
    list_display = ['name_ko', 'section', 'code', 'item_type', 'is_required', 'responsibility_hint', 'order']
    list_filter = ['section__template', 'item_type', 'is_required', 'responsibility_hint']
    search_fields = ['name_ko', 'name_en', 'name_ja', 'code']
    ordering = ['section__template', 'section__order', 'order', 'code']

    fieldsets = (
        (_('Section'), {
            'fields': ('section',)
        }),
        (_('Item Information'), {
            'fields': ('code', 'name_ko', 'name_en', 'name_ja')
        }),
        (_('Descriptions'), {
            'fields': ('description_ko', 'description_en', 'description_ja'),
            'classes': ('collapse',)
        }),
        (_('Type Settings'), {
            'fields': ('item_type', 'options')
        }),
        (_('Photo Settings'), {
            'fields': ('min_photos', 'max_photos'),
            'classes': ('collapse',),
            'description': _('Only applicable for PHOTO type items')
        }),
        (_('Requirements'), {
            'fields': ('is_required', 'responsibility_hint', 'order')
        }),
    )
