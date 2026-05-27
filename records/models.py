from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from contracts.models import Contract


class Record(models.Model):
    """입실/퇴실 기록 모델"""

    RECORD_TYPE_CHOICES = [
        ('MOVE_IN', _('입실')),
        ('MOVE_OUT', _('퇴실')),
        ('PRE_MOVE_OUT', _('사전 점검')),
    ]

    # 기존 승인 상태 (호환성 유지)
    APPROVAL_STATUS_CHOICES = [
        ('PENDING', _('대기중')),
        ('APPROVED', _('승인됨')),
        ('REJECTED', _('반려됨')),
    ]

    # 새로운 상태 체계
    STATUS_CHOICES = [
        ('REQUESTED', _('요청됨')),    # 임차인이 임대인에게 기록 등록 요청
        ('OPEN', _('업로드 가능')),     # 임대인이 승인, 사진 업로드 가능
        ('SUBMITTED', _('제출됨')),    # 임차인이 사진 업로드 완료 후 제출
        ('APPROVED', _('승인됨')),     # 임대인 최종 승인
        ('REJECTED', _('반려됨')),     # 임대인 반려
    ]

    # 계약 연결
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name='계약'
    )

    # 기록 타입
    record_type = models.CharField(
        max_length=20,
        choices=RECORD_TYPE_CHOICES,
        verbose_name='기록 타입'
    )

    # 새로운 상태 필드
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='OPEN',
        verbose_name='상태'
    )

    # 업로드 마감일
    upload_deadline = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='업로드 마감일'
    )

    # 생성자 (임대인 또는 임차인)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_records',
        verbose_name='생성자'
    )

    # 제출 일시
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='제출 일시'
    )

    # 승인 정보
    landlord_approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='임대인 승인 일시'
    )
    landlord_comment = models.TextField(
        blank=True,
        verbose_name='임대인 의견'
    )

    # 메모
    notes = models.TextField(
        blank=True,
        verbose_name='메모'
    )

    # 타임스탬프
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='생성일시'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='수정일시'
    )

    # 알림 읽음 처리
    is_read_by_landlord = models.BooleanField(
        default=False,
        verbose_name='임대인 읽음'
    )
    is_read_by_tenant = models.BooleanField(
        default=False,
        verbose_name='임차인 읽음'
    )

    # 템플릿 연결 (신규 - 다국어/동적 템플릿 지원)
    template = models.ForeignKey(
        'templates_engine.InspectionTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='records',
        verbose_name=_('Inspection Template'),
        help_text=_('Selected inspection template for this record. Null for legacy records.')
    )

    class Meta:
        verbose_name = '기록'
        verbose_name_plural = '기록들'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.contract.address} - {self.get_record_type_display()}"

    @property
    def approval_status(self):
        """기존 코드 호환성을 위한 property"""
        if self.status in ['APPROVED', 'REJECTED']:
            return self.status
        elif self.status == 'SUBMITTED':
            return 'PENDING'
        else:
            return 'PENDING'

    def get_approval_status_display(self):
        """기존 코드 호환성을 위한 display 메서드"""
        status_map = {
            'APPROVED': '승인됨',
            'REJECTED': '반려됨',
        }
        return status_map.get(self.status, '대기중')

    def is_deadline_passed(self):
        """마감일 경과 여부"""
        if not self.upload_deadline:
            return False
        return timezone.now() > self.upload_deadline

    def can_upload_photos(self, user):
        """사진 업로드 가능 여부"""
        # 승인 완료된 기록에는 업로드 불가
        if self.status == 'APPROVED':
            return False

        # 마감일이 지났으면 임대인/임차인 모두 업로드 불가
        if self.is_deadline_passed():
            return False

        # 임대인인 경우
        if user == self.contract.landlord:
            return self.status not in ['REQUESTED', 'SUBMITTED']

        # 임차인인 경우
        if user == self.contract.tenant:
            # OPEN 또는 REJECTED 상태에서만 업로드 가능
            if self.status not in ['OPEN', 'REJECTED']:
                return False
            return True

        return False

    def get_deadline_status(self):
        """마감일 상태 반환"""
        if not self.upload_deadline:
            return {'status': 'none', 'message': '마감일 없음'}

        now = timezone.now()
        if now > self.upload_deadline:
            return {'status': 'expired', 'message': '마감일 경과'}

        diff = self.upload_deadline - now
        days = diff.days
        hours = diff.seconds // 3600

        if days > 0:
            return {'status': 'active', 'message': f'{days}일 남음'}
        elif hours > 0:
            return {'status': 'urgent', 'message': f'{hours}시간 남음'}
        else:
            minutes = diff.seconds // 60
            return {'status': 'urgent', 'message': f'{minutes}분 남음'}

    def auto_submit_if_deadline_passed(self):
        """마감일이 지났으면 자동으로 제출 상태로 변경"""
        if self.status == 'OPEN' and self.is_deadline_passed():
            self.status = 'SUBMITTED'
            self.submitted_at = self.upload_deadline  # 마감일 시점으로 제출 시간 설정
            self.save(update_fields=['status', 'submitted_at', 'updated_at'])
            return True
        return False


class Photo(models.Model):
    """사진 모델"""

    CATEGORY_CHOICES = [
        ('WALL_EAST', _('벽면 (동쪽)')),
        ('WALL_WEST', _('벽면 (서쪽)')),
        ('WALL_SOUTH', _('벽면 (남쪽)')),
        ('WALL_NORTH', _('벽면 (북쪽)')),
        ('FLOOR', _('바닥')),
        ('CEILING', _('천장')),
        ('BATHROOM', _('화장실')),
        ('KITCHEN', _('주방/싱크대')),
        ('ELECTRICAL', _('전기/설비')),
        ('SIGNBOARD', _('간판 설치 부위')),
        ('DOOR', _('출입문')),
        ('WINDOW', _('창문')),
        ('OTHER', _('기타')),
    ]

    APPROVAL_STATUS_CHOICES = [
        ('PENDING', _('대기중')),
        ('APPROVED', _('승인됨')),
        ('REJECTED', _('반려됨')),
    ]

    # 기록 연결
    record = models.ForeignKey(
        Record,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name='기록'
    )

    # 승인 상태
    approval_status = models.CharField(
        max_length=10,
        choices=APPROVAL_STATUS_CHOICES,
        default='PENDING',
        verbose_name='승인 상태'
    )
    rejection_reason = models.TextField(
        blank=True,
        verbose_name='반려 사유'
    )

    # 이미지 파일
    image = models.ImageField(
        upload_to='photos/%Y/%m/%d/',
        verbose_name='이미지'
    )

    # 카테고리 (레거시 - 기존 하드코딩 카테고리)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name='카테고리'
    )

    # 템플릿 항목 연결 (신규 - 동적 템플릿 지원)
    template_item = models.ForeignKey(
        'templates_engine.TemplateItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photos',
        verbose_name=_('Template Item'),
        help_text=_('Associated template item. Null for legacy photos using category.')
    )

    # 설명
    description = models.TextField(
        blank=True,
        verbose_name='설명'
    )

    # 메타데이터
    taken_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='촬영 일시'
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='위도'
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='경도'
    )
    device_info = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='촬영 기기 정보'
    )

    # 타임스탬프
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='업로드 일시'
    )

    class Meta:
        verbose_name = '사진'
        verbose_name_plural = '사진들'
        ordering = ['category', 'created_at']


class RecordItemResponse(models.Model):
    """점검 항목 응답 - 모든 템플릿 아이템 타입에 대한 응답 저장"""

    CONDITION_STATUS_CHOICES = [
        ('NORMAL', _('정상')),
        ('DEFECTIVE', _('하자 있음')),
        ('AGED', _('노후')),
        ('NEEDS_REPAIR', _('수리 필요')),
    ]

    record = models.ForeignKey(
        Record,
        on_delete=models.CASCADE,
        related_name='item_responses',
        verbose_name=_('Record')
    )
    template_item = models.ForeignKey(
        'templates_engine.TemplateItem',
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name=_('Template Item')
    )

    # 상태 체크 (모든 항목 공통)
    condition_status = models.CharField(
        max_length=20,
        choices=CONDITION_STATUS_CHOICES,
        default='NORMAL',
        verbose_name=_('Condition Status')
    )

    # 응답 값 (아이템 타입별)
    # PHOTO: 미사용 (Photo 모델에 저장), CHECKBOX: "true"/"false"
    # TEXT: 자유 텍스트, SELECT: 선택된 값, NUMBER: 숫자 문자열
    response_value = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Response Value')
    )

    notes = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Notes')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Record Item Response')
        verbose_name_plural = _('Record Item Responses')
        unique_together = ['record', 'template_item']
        ordering = ['template_item__section__order', 'template_item__order']

    def __str__(self):
        return f"{self.record} - {self.template_item} ({self.get_condition_status_display()})"

    def __str__(self):
        return f"{self.get_category_display()} - {self.record}"


class DefectReport(models.Model):
    """하자 통지 기록"""

    SEVERITY_CHOICES = [
        ('MINOR', _('경미')),
        ('MAJOR', _('중요')),
        ('CRITICAL', _('긴급')),
    ]

    STATUS_CHOICES = [
        ('REPORTED', _('신고됨')),
        ('ACKNOWLEDGED', _('확인됨')),
        ('IN_PROGRESS', _('처리중')),
        ('RESOLVED', _('해결됨')),
    ]

    contract = models.ForeignKey(
        'contracts.Contract',
        on_delete=models.CASCADE,
        related_name='defect_reports',
        verbose_name=_('Contract')
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='defect_reports',
        verbose_name=_('Reported By')
    )

    title = models.CharField(_('Title'), max_length=200)
    description = models.TextField(_('Description'))
    location = models.CharField(_('Location'), max_length=100,
                                help_text=_('e.g., Bathroom, Kitchen, Living Room'))
    severity = models.CharField(
        _('Severity'),
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='MINOR'
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='REPORTED'
    )
    landlord_response = models.TextField(
        _('Landlord Response'),
        blank=True
    )

    acknowledged_at = models.DateTimeField(_('Acknowledged At'), null=True, blank=True)
    resolved_at = models.DateTimeField(_('Resolved At'), null=True, blank=True)

    is_read_by_landlord = models.BooleanField(default=False)
    is_read_by_tenant = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Defect Report')
        verbose_name_plural = _('Defect Reports')
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.title} ({self.get_status_display()})"


class DefectPhoto(models.Model):
    """하자 사진"""

    defect_report = models.ForeignKey(
        DefectReport,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name=_('Defect Report')
    )
    image = models.ImageField(
        _('Image'),
        upload_to='defects/%Y/%m/'
    )
    description = models.TextField(_('Description'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Defect Photo')
        verbose_name_plural = _('Defect Photos')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.defect_report.title} - photo {self.pk}"


class RepairRequest(models.Model):
    """수리 요청"""

    STATUS_CHOICES = [
        ('REQUESTED', _('요청됨')),
        ('QUOTE_PROVIDED', _('견적 제시')),
        ('APPROVED', _('승인됨')),
        ('IN_PROGRESS', _('수리 중')),
        ('COMPLETED', _('완료')),
        ('CANCELLED', _('취소')),
    ]

    contract = models.ForeignKey(
        'contracts.Contract',
        on_delete=models.CASCADE,
        related_name='repair_requests',
        verbose_name=_('Contract')
    )
    defect_report = models.ForeignKey(
        DefectReport,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='repair_requests',
        verbose_name=_('Related Defect')
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='repair_requests',
        verbose_name=_('Requested By')
    )

    title = models.CharField(_('Title'), max_length=200)
    description = models.TextField(_('Description'))
    location = models.CharField(_('Location'), max_length=100, blank=True)

    status = models.CharField(
        _('Status'), max_length=20,
        choices=STATUS_CHOICES, default='REQUESTED'
    )

    estimated_cost = models.DecimalField(
        _('Estimated Cost'), max_digits=12, decimal_places=0,
        null=True, blank=True
    )
    actual_cost = models.DecimalField(
        _('Actual Cost'), max_digits=12, decimal_places=0,
        null=True, blank=True
    )

    approved_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    is_read_by_landlord = models.BooleanField(default=False)
    is_read_by_tenant = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Repair Request')
        verbose_name_plural = _('Repair Requests')
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title}"


class RepairPhoto(models.Model):
    """수리 사진 (문제/시공중/완료)"""

    PHOTO_TYPE_CHOICES = [
        ('ISSUE', _('문제 사진')),
        ('IN_PROGRESS', _('시공 중')),
        ('COMPLETED', _('완료 사진')),
    ]

    repair_request = models.ForeignKey(
        RepairRequest, on_delete=models.CASCADE,
        related_name='photos', verbose_name=_('Repair Request')
    )
    image = models.ImageField(_('Image'), upload_to='repairs/%Y/%m/')
    photo_type = models.CharField(
        _('Photo Type'), max_length=20,
        choices=PHOTO_TYPE_CHOICES, default='ISSUE'
    )
    description = models.TextField(_('Description'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Repair Photo')
        verbose_name_plural = _('Repair Photos')
        ordering = ['created_at']


class RepairComment(models.Model):
    """수리 코멘트 타임라인"""

    repair_request = models.ForeignKey(
        RepairRequest, on_delete=models.CASCADE,
        related_name='comments', verbose_name=_('Repair Request')
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name=_('Author')
    )
    message = models.TextField(_('Message'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Repair Comment')
        verbose_name_plural = _('Repair Comments')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author.username}: {self.message[:30]}"


class Expense(models.Model):
    """수리비/청소비 등 비용 기록"""

    CATEGORY_CHOICES = [
        ('REPAIR', _('수리비')),
        ('CLEANING', _('청소비')),
        ('RESTORATION', _('원상복구비')),
        ('OTHER', _('기타')),
    ]

    PAID_BY_CHOICES = [
        ('TENANT', _('임차인')),
        ('LANDLORD', _('임대인')),
    ]

    contract = models.ForeignKey(
        'contracts.Contract', on_delete=models.CASCADE,
        related_name='expenses', verbose_name=_('Contract')
    )
    repair_request = models.ForeignKey(
        RepairRequest, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='expenses',
        verbose_name=_('Related Repair')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='created_expenses', verbose_name=_('Created By')
    )

    title = models.CharField(_('Title'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    category = models.CharField(
        _('Category'), max_length=20,
        choices=CATEGORY_CHOICES, default='REPAIR'
    )
    amount = models.DecimalField(
        _('Amount'), max_digits=12, decimal_places=0
    )
    paid_by = models.CharField(
        _('Paid By'), max_length=10,
        choices=PAID_BY_CHOICES, default='LANDLORD'
    )
    receipt_image = models.ImageField(
        _('Receipt Image'), upload_to='receipts/%Y/%m/',
        null=True, blank=True
    )
    expense_date = models.DateField(_('Expense Date'))

    is_read_by_landlord = models.BooleanField(default=False)
    is_read_by_tenant = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Expense')
        verbose_name_plural = _('Expenses')
        ordering = ['-expense_date']

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title} ({self.amount})"
