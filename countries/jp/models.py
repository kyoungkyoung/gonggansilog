"""
일본 시장 대응 모델
국토교통성 '原状回復をめぐるトラブルとガイドライン' 기준
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class JapanRestorationItem(models.Model):
    """
    일본 원상회복 항목 (국토교통성 가이드라인 기준)
    通常損耗 (통상손모) vs 故意・過失 (고의/과실) 구분
    """

    CATEGORY_CHOICES = [
        ('FLOOR', _('Floor')),  # 床
        ('WALL_CEILING', _('Wall/Ceiling')),  # 壁・天井
        ('DOOR_WINDOW', _('Door/Window')),  # 建具・窓
        ('EQUIPMENT', _('Equipment')),  # 設備
        ('KITCHEN', _('Kitchen')),  # キッチン
        ('BATHROOM', _('Bathroom')),  # 浴室
        ('TOILET', _('Toilet')),  # トイレ
        ('OTHER', _('Other')),  # その他
    ]

    RESPONSIBILITY_CHOICES = [
        ('LANDLORD', _('Landlord')),  # 貸主負担
        ('TENANT', _('Tenant')),  # 借主負担
        ('NEGOTIABLE', _('Negotiable')),  # 協議
    ]

    PROPERTY_TYPE_CHOICES = [
        ('RESIDENTIAL', _('Residential')),  # 住居用
        ('COMMERCIAL', _('Commercial')),  # 店舗・事務所
        ('BOTH', _('Both')),  # 両方
    ]

    # 기본 정보
    code = models.CharField(
        _('Item Code'),
        max_length=20,
        unique=True,
        help_text=_('Unique code for this restoration item')
    )
    category = models.CharField(
        _('Category'),
        max_length=20,
        choices=CATEGORY_CHOICES
    )
    property_type = models.CharField(
        _('Property Type'),
        max_length=20,
        choices=PROPERTY_TYPE_CHOICES,
        default='BOTH'
    )

    # 다국어 설명
    description_ja = models.TextField(
        _('Description (Japanese)'),
        help_text=_('Japanese description of the item')
    )
    description_en = models.TextField(
        _('Description (English)'),
        blank=True,
        help_text=_('English description of the item')
    )
    description_ko = models.TextField(
        _('Description (Korean)'),
        blank=True,
        help_text=_('Korean description of the item')
    )

    # 책임 구분
    responsibility = models.CharField(
        _('Responsibility'),
        max_length=20,
        choices=RESPONSIBILITY_CHOICES,
        help_text=_('Who is responsible for restoration')
    )

    # 통상손모 여부
    is_normal_wear = models.BooleanField(
        _('Normal Wear and Tear'),
        default=False,
        help_text=_('Is this considered normal wear and tear (通常損耗)?')
    )

    # 비용 관련
    cost_unit = models.CharField(
        _('Cost Unit'),
        max_length=50,
        blank=True,
        help_text=_('Unit for cost calculation (e.g., per sqm, per item)')
    )
    typical_cost_range = models.CharField(
        _('Typical Cost Range'),
        max_length=100,
        blank=True,
        help_text=_('Typical cost range in JPY')
    )

    # 감가상각
    depreciation_years = models.PositiveIntegerField(
        _('Depreciation Years'),
        null=True,
        blank=True,
        help_text=_('Years for depreciation calculation')
    )
    depreciation_method = models.CharField(
        _('Depreciation Method'),
        max_length=50,
        blank=True,
        help_text=_('Method used for depreciation (e.g., straight-line)')
    )

    # 가이드라인 참조
    guideline_reference = models.CharField(
        _('Guideline Reference'),
        max_length=100,
        blank=True,
        help_text=_('Reference to MLIT guideline section')
    )

    # 메타 정보
    order = models.PositiveIntegerField(_('Display Order'), default=0)
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Japan Restoration Item')
        verbose_name_plural = _('Japan Restoration Items')
        ordering = ['category', 'order', 'code']

    def __str__(self):
        return f"[{self.code}] {self.description_ja[:30]}"

    def get_description(self, language='ja'):
        """언어별 설명 반환"""
        if language == 'ja':
            return self.description_ja
        elif language == 'en':
            return self.description_en or self.description_ja
        elif language == 'ko':
            return self.description_ko or self.description_en or self.description_ja
        return self.description_ja


class ContractJapanExtension(models.Model):
    """
    일본 계약 확장 정보
    일본 임대차 계약에 필요한 추가 정보
    """

    CONTRACT_TYPE_CHOICES = [
        ('ORDINARY', _('Ordinary Lease')),  # 普通借家契約
        ('FIXED_TERM', _('Fixed-term Lease')),  # 定期借家契約
    ]

    RENEWAL_TYPE_CHOICES = [
        ('AUTO', _('Auto Renewal')),  # 自動更新
        ('NEGOTIATED', _('Negotiated')),  # 合意更新
        ('NONE', _('No Renewal')),  # 更新なし (定期借家)
    ]

    # 계약 연결
    contract = models.OneToOneField(
        'contracts.Contract',
        on_delete=models.CASCADE,
        related_name='japan_extension',
        verbose_name=_('Contract')
    )

    # 일본 계약 유형
    contract_type = models.CharField(
        _('Contract Type'),
        max_length=20,
        choices=CONTRACT_TYPE_CHOICES,
        default='ORDINARY'
    )

    # 갱신 정보
    renewal_type = models.CharField(
        _('Renewal Type'),
        max_length=20,
        choices=RENEWAL_TYPE_CHOICES,
        default='AUTO'
    )
    renewal_fee = models.DecimalField(
        _('Renewal Fee'),
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        help_text=_('Renewal fee in JPY (更新料)')
    )

    # 초기비용 (일본 특유)
    key_money = models.DecimalField(
        _('Key Money'),
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        help_text=_('Non-refundable key money in JPY (礼金)')
    )
    deposit = models.DecimalField(
        _('Security Deposit'),
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        help_text=_('Refundable security deposit in JPY (敷金)')
    )
    guarantee_fee = models.DecimalField(
        _('Guarantee Fee'),
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        help_text=_('Guarantee company fee in JPY (保証料)')
    )

    # 관리비
    management_fee = models.DecimalField(
        _('Management Fee'),
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        help_text=_('Monthly management fee in JPY (管理費・共益費)')
    )

    # 원상회복 특약
    restoration_clause = models.TextField(
        _('Restoration Clause'),
        blank=True,
        help_text=_('Special restoration clause (原状回復特約)')
    )
    has_special_restoration_clause = models.BooleanField(
        _('Has Special Restoration Clause'),
        default=False,
        help_text=_('Whether contract has special restoration terms')
    )

    # 중개 정보
    agency_name = models.CharField(
        _('Real Estate Agency'),
        max_length=200,
        blank=True,
        help_text=_('Name of real estate agency (不動産会社)')
    )
    agency_license = models.CharField(
        _('Agency License Number'),
        max_length=100,
        blank=True,
        help_text=_('Real estate license number (宅建業者免許番号)')
    )

    # 메타 정보
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Japan Contract Extension')
        verbose_name_plural = _('Japan Contract Extensions')

    def __str__(self):
        return f"JP Extension - {self.contract}"

    @property
    def total_initial_cost(self):
        """초기비용 총액 계산"""
        total = 0
        if self.key_money:
            total += self.key_money
        if self.deposit:
            total += self.deposit
        if self.guarantee_fee:
            total += self.guarantee_fee
        return total


class PhotoRestorationTag(models.Model):
    """
    사진별 원상회복 책임 태그
    사진에 원상회복 항목과 책임 구분을 연결
    """

    RESPONSIBILITY_CHOICES = [
        ('LANDLORD', _('Landlord')),
        ('TENANT', _('Tenant')),
        ('NEGOTIABLE', _('Negotiable')),
        ('PENDING', _('Pending')),  # 미정
    ]

    # 연결
    photo = models.ForeignKey(
        'records.Photo',
        on_delete=models.CASCADE,
        related_name='restoration_tags',
        verbose_name=_('Photo')
    )
    restoration_item = models.ForeignKey(
        JapanRestorationItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photo_tags',
        verbose_name=_('Restoration Item')
    )

    # 책임 구분 (수동 지정 가능)
    responsibility = models.CharField(
        _('Responsibility'),
        max_length=20,
        choices=RESPONSIBILITY_CHOICES,
        default='PENDING'
    )

    # 상세 설명
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Additional description of the damage/condition')
    )

    # 비용 추정
    estimated_cost = models.DecimalField(
        _('Estimated Cost'),
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        help_text=_('Estimated restoration cost in JPY')
    )

    # 메타 정보
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_restoration_tags',
        verbose_name=_('Created By')
    )

    class Meta:
        verbose_name = _('Photo Restoration Tag')
        verbose_name_plural = _('Photo Restoration Tags')

    def __str__(self):
        return f"{self.photo} - {self.get_responsibility_display()}"
