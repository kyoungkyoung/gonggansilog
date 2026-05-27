from django.contrib import admin
from django.utils.html import format_html
from django import forms
from django.core.exceptions import ValidationError
from .models import Contract, ContractInvitation, ContractHistory, ContractChangeRequest


class ContractAdminForm(forms.ModelForm):
    """계약 Admin 폼 (수정 시 메모 필수)"""
    admin_note = forms.CharField(
        label='수정 사유',
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 60}),
        required=False,
        help_text='계약 정보를 수정하는 경우 반드시 사유를 입력해주세요.'
    )

    class Meta:
        model = Contract
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 인스턴스 저장 (변경 감지용)
        self.original_instance = None
        if self.instance and self.instance.pk:
            self.original_instance = Contract.objects.get(pk=self.instance.pk)

    def clean(self):
        cleaned_data = super().clean()
        admin_note = cleaned_data.get('admin_note', '').strip()

        # 수정하는 경우에만 검증
        if self.instance.pk and self.original_instance:
            has_changes = False

            # 주요 필드 변경 확인
            if self.original_instance.address != self.instance.address:
                has_changes = True
            if self.original_instance.contract_date != self.instance.contract_date:
                has_changes = True
            if self.original_instance.move_in_date != self.instance.move_in_date:
                has_changes = True
            if self.original_instance.move_out_date != self.instance.move_out_date:
                has_changes = True
            if self.original_instance.status != self.instance.status:
                has_changes = True
            if self.original_instance.tenant != cleaned_data.get('tenant'):
                has_changes = True
            if self.original_instance.landlord != cleaned_data.get('landlord'):
                has_changes = True

            # 변경 사항이 있는데 메모가 없으면 에러
            if has_changes and not admin_note:
                raise ValidationError('계약 정보를 수정하려면 반드시 수정 사유를 입력해야 합니다.')

        return cleaned_data


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    """계약 Admin"""

    form = ContractAdminForm
    list_display = ['address', 'get_tenant_display', 'get_landlord_display', 'contract_date', 'move_in_date', 'move_out_date', 'get_status_display_admin', 'get_blockchain_status_display', 'created_at']
    list_filter = ['status', 'is_finalized', 'blockchain_status', 'created_at', 'contract_date']
    search_fields = ['address', 'tenant__username', 'tenant_name', 'landlord__username', 'landlord_name', 'landlord_phone']
    date_hierarchy = 'contract_date'
    ordering = ['-created_at']
    list_per_page = 20

    fieldsets = (
        ('계약 당사자', {
            'fields': ('tenant', 'tenant_name', 'tenant_phone', 'landlord', 'landlord_name', 'landlord_phone')
        }),
        ('상가 정보', {
            'fields': ('address',)
        }),
        ('계약 날짜', {
            'fields': ('contract_date', 'move_in_date', 'move_out_date')
        }),
        ('계약서', {
            'fields': ('contract_file',)
        }),
        ('상태', {
            'fields': ('status',)
        }),
        ('블록체인 증거화', {
            'fields': ('is_finalized', 'finalized_at', 'blockchain_status', 'blockchain_tx_hash', 'blockchain_final_hash', 'blockchain_anchored_at', 'blockchain_metadata'),
            'description': '블록체인에 기록된 증거화 정보입니다. 이 정보는 자동으로 생성되며 수정할 수 없습니다.'
        }),
        ('수정 사유', {
            'fields': ('admin_note',),
            'description': '계약 정보를 수정하는 경우 반드시 사유를 입력해주세요.'
        }),
        ('타임스탬프', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at', 'is_finalized', 'finalized_at', 'blockchain_status', 'blockchain_tx_hash', 'blockchain_final_hash', 'blockchain_anchored_at', 'blockchain_metadata')

    def get_tenant_display(self, obj):
        """임차인 표시"""
        if obj.tenant:
            return f"{obj.tenant.username} (계정)"
        elif obj.tenant_name:
            return f"{obj.tenant_name} (미연결)"
        return "-"
    get_tenant_display.short_description = '임차인'

    def get_landlord_display(self, obj):
        """임대인 표시"""
        if obj.landlord:
            return f"{obj.landlord.username} (계정)"
        elif obj.landlord_name:
            return f"{obj.landlord_name} (미연결)"
        return "-"
    get_landlord_display.short_description = '임대인'

    def get_status_display_admin(self, obj):
        """계약 상태 표시 (퇴실일 기준 자동 계산)"""
        current_status = obj.get_current_status()
        status_display = obj.get_current_status_display()

        # 색상 설정
        if current_status == 'ACTIVE':
            color = '#28a745'  # 초록색
            icon = '✓'
        else:  # COMPLETED
            color = '#6c757d'  # 회색
            icon = '✕'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, status_display
        )
    get_status_display_admin.short_description = '현재 상태'

    def get_blockchain_status_display(self, obj):
        """블록체인 상태 표시"""
        if obj.is_finalized:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ 확정됨</span>'
            )
        elif obj.blockchain_status == 'PENDING':
            return format_html(
                '<span style="color: #ffc107; font-weight: bold;">⏳ 처리중</span>'
            )
        elif obj.blockchain_status == 'FAILED':
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">✕ 실패</span>'
            )
        else:
            return format_html(
                '<span style="color: #6c757d;">미확정</span>'
            )
    get_blockchain_status_display.short_description = '블록체인'

    def history_view(self, request, object_id, extra_context=None):
        """커스텀 히스토리 뷰 (ContractHistory 포함)"""
        from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
        from django.contrib.contenttypes.models import ContentType
        from django.shortcuts import render

        # 객체 가져오기
        obj = self.get_object(request, object_id)
        if obj is None:
            return self._get_obj_does_not_exist_redirect(request, self.model._meta, object_id)

        # Django admin의 기본 LogEntry
        content_type = ContentType.objects.get_for_model(self.model)
        admin_logs = LogEntry.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).select_related('user').order_by('-action_time')

        # ContractHistory
        contract_histories = obj.histories.all().select_related('action_by').order_by('-created_at')

        # 컨텍스트 설정
        context = {
            **self.admin_site.each_context(request),
            'title': f'{obj}의 변경 이력',
            'subtitle': None,
            'object': obj,
            'admin_logs': admin_logs,
            'contract_histories': contract_histories,
            'opts': self.model._meta,
            'preserved_filters': self.get_preserved_filters(request),
            'app_label': self.model._meta.app_label,
            'module_name': self.model._meta.model_name,
            'object_id': object_id,
            'original': obj,
        }
        if extra_context:
            context.update(extra_context)

        return render(request, 'admin/contracts/contract/object_history.html', context)

    def save_model(self, request, obj, form, change):
        """계약 저장 시 이력 기록"""
        admin_note = form.cleaned_data.get('admin_note', '').strip()

        if change:  # 수정하는 경우
            # 변경 사항 확인
            original = Contract.objects.get(pk=obj.pk)
            has_changes = False
            changes = []

            # 주요 필드 변경 확인
            if original.address != obj.address:
                has_changes = True
                changes.append(f'주소: {original.address} → {obj.address}')
            if original.contract_date != obj.contract_date:
                has_changes = True
                changes.append(f'계약일: {original.contract_date} → {obj.contract_date}')
            if original.move_in_date != obj.move_in_date:
                has_changes = True
                changes.append(f'입실일: {original.move_in_date} → {obj.move_in_date}')
            if original.move_out_date != obj.move_out_date:
                has_changes = True
                changes.append(f'퇴실일: {original.move_out_date} → {obj.move_out_date}')
            if original.status != obj.status:
                has_changes = True
                changes.append(f'상태: {original.get_status_display()} → {obj.get_status_display()}')
            if original.tenant != obj.tenant:
                has_changes = True
                changes.append(f'임차인 변경')
            if original.landlord != obj.landlord:
                has_changes = True
                changes.append(f'임대인 변경')

            # 저장
            super().save_model(request, obj, form, change)

            # 변경 사항이 있으면 이력 생성
            if has_changes and admin_note:
                ContractHistory.objects.create(
                    contract=obj,
                    action_type='MODIFIED',
                    action_by=request.user,
                    previous_move_out_date=original.move_out_date,
                    new_move_out_date=obj.move_out_date,
                    note=f'관리자 수정: {admin_note}\n변경 내용: {", ".join(changes)}'
                )
        else:  # 새로 생성하는 경우
            super().save_model(request, obj, form, change)
            # 생성 이력 기록
            ContractHistory.objects.create(
                contract=obj,
                action_type='CREATED',
                action_by=request.user,
                note='관리자가 계약 등록'
            )


@admin.register(ContractInvitation)
class ContractInvitationAdmin(admin.ModelAdmin):
    """계약 초대 Admin"""

    list_display = ['contract', 'invited_user_type', 'invited_by', 'is_accepted', 'get_accepted_by_display', 'created_at', 'expires_at', 'is_valid_status']
    list_filter = ['is_accepted', 'invited_user_type', 'created_at']
    search_fields = ['contract__address', 'invited_by__username', 'accepted_by__username']
    readonly_fields = ('token', 'created_at')
    ordering = ['-created_at']

    fieldsets = (
        ('초대 정보', {
            'fields': ('contract', 'invited_by', 'invited_user_type')
        }),
        ('토큰', {
            'fields': ('token',)
        }),
        ('수락 정보', {
            'fields': ('is_accepted', 'accepted_by')
        }),
        ('일시', {
            'fields': ('created_at', 'expires_at')
        }),
    )

    def get_accepted_by_display(self, obj):
        """수락한 사람 표시"""
        if obj.accepted_by:
            return obj.accepted_by.username
        return "-"
    get_accepted_by_display.short_description = '수락한 사람'

    def is_valid_status(self, obj):
        """초대 유효성 표시"""
        return obj.is_valid()
    is_valid_status.short_description = '유효 여부'
    is_valid_status.boolean = True


@admin.register(ContractHistory)
class ContractHistoryAdmin(admin.ModelAdmin):
    """계약 이력 Admin"""

    list_display = ['contract', 'get_action_type_display_admin', 'action_by', 'previous_move_out_date', 'new_move_out_date', 'extend_months', 'created_at']
    list_filter = ['action_type', 'created_at']
    search_fields = ['contract__address', 'action_by__username', 'note']
    readonly_fields = ('contract', 'action_type', 'action_by', 'previous_move_out_date', 'new_move_out_date', 'extend_months', 'note', 'created_at')
    ordering = ['-created_at']

    fieldsets = (
        ('계약 정보', {
            'fields': ('contract', 'action_type', 'action_by')
        }),
        ('변경 내용', {
            'fields': ('previous_move_out_date', 'new_move_out_date', 'extend_months', 'note')
        }),
        ('일시', {
            'fields': ('created_at',)
        }),
    )

    def get_action_type_display_admin(self, obj):
        """작업 유형 표시 (색상 포함)"""
        colors = {
            'CREATED': '#007bff',  # 파란색
            'EXTENDED': '#28a745',  # 초록색
            'TERMINATED': '#ffc107',  # 노란색
            'MODIFIED': '#ff6b6b',  # 빨간색
        }
        color = colors.get(obj.action_type, '#6c757d')

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_action_type_display()
        )
    get_action_type_display_admin.short_description = '작업 유형'

    def has_add_permission(self, request):
        """추가 권한 없음 (자동으로만 생성)"""
        return False

    def has_delete_permission(self, request, obj=None):
        """삭제 권한 없음 (이력 보존)"""
        return False


@admin.register(ContractChangeRequest)
class ContractChangeRequestAdmin(admin.ModelAdmin):
    """계약 변경 요청 Admin"""

    list_display = ['contract', 'get_request_type_display_admin', 'requested_by', 'extend_months', 'get_status_display_admin', 'created_at', 'responded_by']
    list_filter = ['request_type', 'status', 'created_at']
    search_fields = ['contract__address', 'requested_by__username', 'responded_by__username']
    readonly_fields = ('contract', 'request_type', 'requested_by', 'extend_months', 'created_at', 'responded_at', 'responded_by', 'note', 'response_note')
    ordering = ['-created_at']

    fieldsets = (
        ('계약 정보', {
            'fields': ('contract', 'request_type', 'requested_by')
        }),
        ('요청 내용', {
            'fields': ('extend_months', 'note')
        }),
        ('처리 정보', {
            'fields': ('status', 'responded_by', 'responded_at', 'response_note')
        }),
        ('일시', {
            'fields': ('created_at',)
        }),
    )

    def get_request_type_display_admin(self, obj):
        """요청 유형 표시 (색상 포함)"""
        colors = {
            'EXTEND': '#28a745',  # 초록색
            'TERMINATE': '#ffc107',  # 노란색
        }
        color = colors.get(obj.request_type, '#6c757d')

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_request_type_display()
        )
    get_request_type_display_admin.short_description = '요청 유형'

    def get_status_display_admin(self, obj):
        """상태 표시 (색상 포함)"""
        colors = {
            'PENDING': '#ffc107',  # 노란색
            'APPROVED': '#28a745',  # 초록색
            'REJECTED': '#dc3545',  # 빨간색
        }
        color = colors.get(obj.status, '#6c757d')

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_display_admin.short_description = '상태'

    def has_add_permission(self, request):
        """추가 권한 없음 (사용자가 요청)"""
        return False


# Django Admin 사이트 설정
admin.site.site_header = '부동산 관리 프로그램(관리자)'
admin.site.site_title = '부동산 관리 프로그램'
admin.site.index_title = '관리자 페이지'
