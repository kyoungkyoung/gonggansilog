from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid
from datetime import timedelta


class Contract(models.Model):
    """계약 정보 모델"""

    STATUS_CHOICES = [
        ('ACTIVE', _('진행중')),
        ('COMPLETED', _('종료')),
    ]

    BLOCKCHAIN_STATUS_CHOICES = [
        ('NONE', _('미등록')),
        ('PENDING', _('처리중')),
        ('ANCHORED', _('등록됨')),
        ('FAILED', _('실패')),
    ]

    # 계약 당사자
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tenant_contracts',
        null=True,
        blank=True,
        verbose_name='임차인'
    )
    tenant_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='임차인 이름'
    )
    tenant_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='임차인 연락처'
    )
    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='landlord_contracts',
        null=True,
        blank=True,
        verbose_name='임대인'
    )
    landlord_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='임대인 이름'
    )
    landlord_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='임대인 연락처'
    )

    # 상가 정보
    address = models.CharField(
        max_length=500,
        verbose_name=_('주소')
    )
    address_en = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='주소 (영어)'
    )
    address_ja = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='주소 (일본어)'
    )

    # 계약 날짜
    contract_date = models.DateField(
        verbose_name='계약일'
    )
    move_in_date = models.DateField(
        verbose_name='입실일'
    )
    move_out_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='퇴실 예정일'
    )

    # 계약서 파일
    contract_file = models.FileField(
        upload_to='contracts/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='계약서 파일'
    )

    # 계약 상태
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        verbose_name='계약 상태'
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

    # 블록체인 관련 필드
    blockchain_tx_hash = models.CharField(
        max_length=66,
        null=True,
        blank=True,
        verbose_name='트랜잭션 해시'
    )
    blockchain_anchored_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='블록체인 앵커링 시점'
    )
    blockchain_final_hash = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name='최종 해시'
    )
    blockchain_metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='파일별 해시 메타데이터'
    )
    blockchain_status = models.CharField(
        max_length=10,
        choices=BLOCKCHAIN_STATUS_CHOICES,
        default='NONE',
        verbose_name='블록체인 상태'
    )
    is_finalized = models.BooleanField(
        default=False,
        verbose_name='계약 확정 여부'
    )
    finalized_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='계약 확정 시점'
    )

    # 국가 및 템플릿 설정 (신규 - 다국어/동적 템플릿 지원)
    country = models.CharField(
        _('Country'),
        max_length=10,
        default='KR',
        help_text=_('Country code for this contract (KR, JP, etc.)')
    )
    template = models.ForeignKey(
        'templates_engine.InspectionTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contracts',
        verbose_name=_('Inspection Template'),
        help_text=_('Default inspection template for records in this contract')
    )

    class Meta:
        verbose_name = '계약'
        verbose_name_plural = '계약들'
        ordering = ['-created_at']

    def __str__(self):
        if self.tenant:
            return f"{self.address} - {self.tenant.username}"
        elif self.tenant_name:
            return f"{self.address} - {self.tenant_name}"
        else:
            return f"{self.address}"

    def save(self, *args, **kwargs):
        # 주소가 변경되었을 때 번역 주소 자동 생성
        if self.address:
            from core.address_utils import korean_address_to_english, korean_address_to_japanese
            if not self.address_en or self._address_changed():
                self.address_en = korean_address_to_english(self.address)
            if not self.address_ja or self._address_changed():
                self.address_ja = korean_address_to_japanese(self.address)
        super().save(*args, **kwargs)

    def _address_changed(self):
        if not self.pk:
            return True
        try:
            old = Contract.objects.get(pk=self.pk)
            return old.address != self.address
        except Contract.DoesNotExist:
            return True

    def get_display_address(self):
        """현재 활성 언어에 맞는 주소 반환"""
        from django.utils.translation import get_language
        lang = get_language()
        if lang == 'en' and self.address_en:
            return self.address_en
        elif lang == 'ja' and self.address_ja:
            return self.address_ja
        return self.address

    def get_current_status(self):
        """현재 계약 상태 반환 (퇴실일 기준 자동 계산)"""
        from datetime import date

        # 퇴실 예정일이 있고, 현재 날짜가 퇴실일을 지났으면 '종료'
        if self.move_out_date and date.today() > self.move_out_date:
            return 'COMPLETED'

        # 그 외에는 DB에 저장된 상태 반환
        return self.status

    def get_current_status_display(self):
        """현재 계약 상태 한글 표시"""
        status = self.get_current_status()
        status_dict = dict(self.STATUS_CHOICES)
        return status_dict.get(status, '알 수 없음')


class ContractChangeRequest(models.Model):
    """계약 변경 요청 모델 (연장/해지 요청)"""

    REQUEST_TYPE_CHOICES = [
        ('EXTEND', _('계약 연장')),
        ('TERMINATE', _('계약 해지')),
    ]

    STATUS_CHOICES = [
        ('PENDING', _('승인 대기')),
        ('APPROVED', _('승인됨')),
        ('REJECTED', _('거절됨')),
    ]

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='change_requests',
        verbose_name='계약'
    )
    request_type = models.CharField(
        max_length=20,
        choices=REQUEST_TYPE_CHOICES,
        verbose_name='요청 유형'
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='contract_change_requests',
        verbose_name='요청자'
    )
    extend_months = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='연장 개월 수'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name='상태'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='요청 일시'
    )
    responded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='응답 일시'
    )
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contract_change_responses',
        verbose_name='응답자'
    )
    note = models.TextField(
        blank=True,
        verbose_name='메모'
    )
    response_note = models.TextField(
        blank=True,
        verbose_name='응답 메모 (승인/거절 사유)'
    )
    is_read_by_requester = models.BooleanField(
        default=False,
        verbose_name='요청자 읽음 여부'
    )

    class Meta:
        verbose_name = '계약 변경 요청'
        verbose_name_plural = '계약 변경 요청들'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.contract.address} - {self.get_request_type_display()} ({self.get_status_display()})"

    def get_other_party(self):
        """상대방 반환"""
        if self.requested_by == self.contract.tenant:
            return self.contract.landlord
        elif self.requested_by == self.contract.landlord:
            return self.contract.tenant
        return None


class ContractHistory(models.Model):
    """계약 이력 모델 (연장/해지 등)"""

    ACTION_TYPE_CHOICES = [
        ('CREATED', _('계약 등록')),
        ('EXTENDED', _('계약 연장')),
        ('TERMINATED', _('계약 해지')),
        ('MODIFIED', _('관리자 수정')),
    ]

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='histories',
        verbose_name='계약'
    )
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPE_CHOICES,
        verbose_name='작업 유형'
    )
    action_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='실행자'
    )
    previous_move_out_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='이전 퇴실 예정일'
    )
    new_move_out_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='새 퇴실 예정일'
    )
    extend_months = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='연장 개월 수'
    )
    note = models.TextField(
        blank=True,
        verbose_name='메모'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='기록 일시'
    )

    class Meta:
        verbose_name = '계약 이력'
        verbose_name_plural = '계약 이력들'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.contract.address} - {self.get_action_type_display()} ({self.created_at.strftime('%Y-%m-%d')})"


class ContractInvitation(models.Model):
    """계약 초대 모델"""

    USER_TYPE_CHOICES = [
        ('TENANT', _('임차인')),
        ('LANDLORD', _('임대인')),
    ]

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name='계약'
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
        verbose_name='초대한 사람'
    )
    invited_user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        verbose_name='초대받는 사람 유형'
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='초대 토큰'
    )
    is_accepted = models.BooleanField(
        default=False,
        verbose_name='수락 여부'
    )
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_invitations',
        verbose_name='수락한 사람'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='생성일시'
    )
    expires_at = models.DateTimeField(
        verbose_name='만료일시'
    )

    class Meta:
        verbose_name = '계약 초대'
        verbose_name_plural = '계약 초대들'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.contract.address} - {self.get_invited_user_type_display()} 초대"

    def save(self, *args, **kwargs):
        # expires_at이 설정되지 않은 경우 7일 후로 설정
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def is_valid(self):
        """초대가 유효한지 확인"""
        return not self.is_accepted and timezone.now() < self.expires_at
