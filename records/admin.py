from django.contrib import admin
from .models import Record, Photo, RecordItemResponse, DefectReport, DefectPhoto, RepairRequest, RepairPhoto, RepairComment, Expense


class PhotoInline(admin.TabularInline):
    """사진 인라인"""
    model = Photo
    extra = 1
    fields = ['image', 'category', 'description']


class RecordItemResponseInline(admin.TabularInline):
    """점검 항목 응답 인라인"""
    model = RecordItemResponse
    extra = 0
    fields = ['template_item', 'condition_status', 'response_value', 'notes']
    readonly_fields = ['created_at']


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    """기록 Admin"""

    list_display = ['contract', 'record_type', 'status', 'upload_deadline', 'created_by', 'created_at']
    list_filter = ['record_type', 'status', 'created_at']
    search_fields = ['contract__address']
    date_hierarchy = 'created_at'
    inlines = [PhotoInline, RecordItemResponseInline]
    readonly_fields = ['submitted_at']

    fieldsets = (
        ('기본 정보', {
            'fields': ('contract', 'record_type', 'created_by')
        }),
        ('상태 관리', {
            'fields': ('status', 'upload_deadline', 'submitted_at')
        }),
        ('승인 정보', {
            'fields': ('landlord_approved_at', 'landlord_comment')
        }),
        ('메모', {
            'fields': ('notes',)
        }),
    )


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    """사진 Admin"""

    list_display = ['record', 'category', 'taken_at', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['record__contract__address', 'description']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('기본 정보', {
            'fields': ('record', 'image', 'category', 'description')
        }),
        ('메타데이터', {
            'fields': ('taken_at', 'latitude', 'longitude', 'device_info')
        }),
    )


@admin.register(RecordItemResponse)
class RecordItemResponseAdmin(admin.ModelAdmin):
    """점검 항목 응답 Admin"""

    list_display = ['record', 'template_item', 'condition_status', 'response_value', 'updated_at']
    list_filter = ['condition_status', 'created_at']
    search_fields = ['record__contract__address', 'template_item__name_ko', 'notes']
    readonly_fields = ['created_at', 'updated_at']


class DefectPhotoInline(admin.TabularInline):
    model = DefectPhoto
    extra = 1
    fields = ['image', 'description']


@admin.register(DefectReport)
class DefectReportAdmin(admin.ModelAdmin):
    """하자 통지 Admin"""

    list_display = ['title', 'contract', 'reported_by', 'severity', 'status', 'created_at']
    list_filter = ['severity', 'status', 'created_at']
    search_fields = ['title', 'description', 'contract__address']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [DefectPhotoInline]


@admin.register(DefectPhoto)
class DefectPhotoAdmin(admin.ModelAdmin):
    """하자 사진 Admin"""

    list_display = ['defect_report', 'created_at']
    search_fields = ['defect_report__title']


class RepairPhotoInline(admin.TabularInline):
    model = RepairPhoto
    extra = 1
    fields = ['image', 'photo_type', 'description']


class RepairCommentInline(admin.TabularInline):
    model = RepairComment
    extra = 0
    fields = ['author', 'message', 'created_at']
    readonly_fields = ['created_at']


@admin.register(RepairRequest)
class RepairRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'contract', 'requested_by', 'status', 'estimated_cost', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'description', 'contract__address']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [RepairPhotoInline, RepairCommentInline]


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'contract', 'category', 'amount', 'paid_by', 'expense_date', 'created_by']
    list_filter = ['category', 'paid_by', 'expense_date']
    search_fields = ['title', 'description', 'contract__address']
