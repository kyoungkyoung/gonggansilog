from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from contracts.models import Contract


class Recording(models.Model):
    """녹음 기록 모델"""

    PROCESSING_STATUS_CHOICES = [
        ('PENDING', _('대기중')),
        ('PROCESSING', _('처리중')),
        ('COMPLETED', _('완료')),
        ('FAILED', _('실패')),
    ]

    CONSENT_STATUS_CHOICES = [
        ('NOT_REQUIRED', _('동의 불필요')),
        ('PENDING', _('동의 대기')),
        ('APPROVED', _('동의 완료')),
        ('REJECTED', _('동의 거절')),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='사용자',
        related_name='recordings'
    )
    title = models.CharField('제목', max_length=200)
    title_en = models.CharField('제목 (영어)', max_length=300, blank=True, default='')
    title_ja = models.CharField('제목 (일본어)', max_length=300, blank=True, default='')
    audio_file = models.FileField('녹음 파일', upload_to='recordings/%Y/%m/')
    duration = models.IntegerField('녹음 시간(초)', default=0)
    recorded_at = models.DateTimeField('녹음 일시', auto_now_add=True)
    description = models.TextField('메모', blank=True)
    contract = models.ForeignKey(
        Contract,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='연결된 계약',
        related_name='recordings'
    )

    # 상호 동의 관련 필드
    consent_status = models.CharField(
        '동의 상태',
        max_length=20,
        choices=CONSENT_STATUS_CHOICES,
        default='NOT_REQUIRED'
    )
    consented_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='동의자',
        related_name='consented_recordings'
    )
    consented_at = models.DateTimeField(
        '동의 일시',
        null=True,
        blank=True
    )
    consent_rejected_reason = models.TextField(
        '동의 거절 사유',
        blank=True
    )

    # AI 처리 관련 필드
    transcript = models.TextField(
        '전사본',
        blank=True,
        help_text='음성을 텍스트로 변환한 원본 (관리자만 표시)'
    )
    summary = models.TextField(
        '요약',
        blank=True,
        help_text='AI가 생성한 요약문'
    )
    processing_status = models.CharField(
        '처리 상태',
        max_length=20,
        choices=PROCESSING_STATUS_CHOICES,
        default='PENDING'
    )
    processed_at = models.DateTimeField(
        '처리 완료 일시',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = '녹음 기록'
        verbose_name_plural = '녹음 기록'
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.title} ({self.user.username})"

    def get_display_title(self):
        """현재 활성 언어에 맞는 제목 반환"""
        from django.utils.translation import get_language
        lang = get_language()
        if lang == 'en' and self.title_en:
            return self.title_en
        elif lang == 'ja' and self.title_ja:
            return self.title_ja
        return self.title

    def get_duration_display(self):
        """녹음 시간을 분:초 형식으로 반환"""
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes}:{seconds:02d}"

    def get_other_party(self, user):
        """상대방 반환 (계약 기준)"""
        if not self.contract:
            return None
        if user == self.contract.tenant:
            return self.contract.landlord
        elif user == self.contract.landlord:
            return self.contract.tenant
        return None

    def is_officially_recognized(self):
        """공식 녹음 기록으로 인정되는지 여부"""
        return self.consent_status in ('APPROVED', 'NOT_REQUIRED')
