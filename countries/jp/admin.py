from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import JapanRestorationItem, ContractJapanExtension, PhotoRestorationTag


@admin.register(JapanRestorationItem)
class JapanRestorationItemAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'category', 'property_type', 'responsibility',
        'is_normal_wear', 'depreciation_years', 'is_active', 'order'
    ]
    list_filter = ['category', 'property_type', 'responsibility', 'is_normal_wear', 'is_active']
    search_fields = ['code', 'description_ja', 'description_en', 'description_ko']
    ordering = ['category', 'order', 'code']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('code', 'category', 'property_type', 'order', 'is_active')
        }),
        (_('Descriptions'), {
            'fields': ('description_ja', 'description_en', 'description_ko')
        }),
        (_('Responsibility'), {
            'fields': ('responsibility', 'is_normal_wear', 'guideline_reference')
        }),
        (_('Cost Information'), {
            'fields': ('cost_unit', 'typical_cost_range', 'depreciation_years', 'depreciation_method')
        }),
    )


@admin.register(ContractJapanExtension)
class ContractJapanExtensionAdmin(admin.ModelAdmin):
    list_display = [
        'contract', 'contract_type', 'renewal_type',
        'deposit', 'key_money', 'management_fee'
    ]
    list_filter = ['contract_type', 'renewal_type', 'has_special_restoration_clause']
    search_fields = ['contract__address', 'agency_name']
    raw_id_fields = ['contract']

    fieldsets = (
        (_('Contract'), {
            'fields': ('contract', 'contract_type')
        }),
        (_('Renewal'), {
            'fields': ('renewal_type', 'renewal_fee')
        }),
        (_('Initial Costs'), {
            'fields': ('key_money', 'deposit', 'guarantee_fee', 'management_fee')
        }),
        (_('Restoration Clause'), {
            'fields': ('has_special_restoration_clause', 'restoration_clause')
        }),
        (_('Agency Information'), {
            'fields': ('agency_name', 'agency_license')
        }),
    )


@admin.register(PhotoRestorationTag)
class PhotoRestorationTagAdmin(admin.ModelAdmin):
    list_display = [
        'photo', 'restoration_item', 'responsibility',
        'estimated_cost', 'created_by', 'created_at'
    ]
    list_filter = ['responsibility', 'created_at']
    search_fields = ['description', 'photo__record__contract__address']
    raw_id_fields = ['photo', 'restoration_item', 'created_by']
