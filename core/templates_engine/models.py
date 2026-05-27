from django.db import models
from django.utils.translation import gettext_lazy as _


class InspectionTemplate(models.Model):
    """
    점검 템플릿 - 국가별/부동산 유형별 점검 항목 템플릿
    Inspection Template - Country/property type specific inspection templates
    """

    class Country(models.TextChoices):
        KOREA = 'KR', _('Korea')
        JAPAN = 'JP', _('Japan')
        GLOBAL = 'GLOBAL', _('Global')

    class PropertyType(models.TextChoices):
        RESIDENTIAL = 'RESIDENTIAL', _('Residential')
        COMMERCIAL = 'COMMERCIAL', _('Commercial')
        OFFICE = 'OFFICE', _('Office')

    # Multi-language names
    name = models.CharField(
        _('Name (Korean)'),
        max_length=200,
        help_text=_('Template name in Korean')
    )
    name_en = models.CharField(
        _('Name (English)'),
        max_length=200,
        blank=True,
        help_text=_('Template name in English')
    )
    name_ja = models.CharField(
        _('Name (Japanese)'),
        max_length=200,
        blank=True,
        help_text=_('Template name in Japanese')
    )

    # Classification
    country = models.CharField(
        _('Country'),
        max_length=10,
        choices=Country.choices,
        default=Country.KOREA
    )
    property_type = models.CharField(
        _('Property Type'),
        max_length=20,
        choices=PropertyType.choices,
        default=PropertyType.COMMERCIAL
    )

    # Metadata
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Description of the template purpose and usage')
    )
    version = models.CharField(
        _('Version'),
        max_length=20,
        default='1.0'
    )
    is_active = models.BooleanField(
        _('Is Active'),
        default=True,
        help_text=_('Only active templates can be selected for new contracts')
    )
    is_default = models.BooleanField(
        _('Is Default'),
        default=False,
        help_text=_('Default template for the country/property type combination')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Inspection Template')
        verbose_name_plural = _('Inspection Templates')
        ordering = ['country', 'property_type', 'name']
        indexes = [
            models.Index(fields=['country', 'property_type', 'is_active']),
        ]

    def __str__(self):
        return f"[{self.get_country_display()}] {self.name} ({self.get_property_type_display()})"

    def get_name_by_language(self, lang='ko'):
        """Get the template name in the specified language."""
        if lang == 'en' and self.name_en:
            return self.name_en
        elif lang == 'ja' and self.name_ja:
            return self.name_ja
        return self.name

    def save(self, *args, **kwargs):
        # Ensure only one default template per country/property_type combination
        if self.is_default:
            InspectionTemplate.objects.filter(
                country=self.country,
                property_type=self.property_type,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class TemplateSection(models.Model):
    """
    템플릿 섹션 - 템플릿 내 점검 영역 분류
    Template Section - Inspection area classification within a template
    """

    template = models.ForeignKey(
        InspectionTemplate,
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name=_('Template')
    )

    # Section code for programmatic access
    code = models.CharField(
        _('Code'),
        max_length=50,
        help_text=_('Unique code within the template (e.g., ENTRANCE, LIVING_ROOM)')
    )

    # Multi-language names
    name_ko = models.CharField(
        _('Name (Korean)'),
        max_length=100
    )
    name_en = models.CharField(
        _('Name (English)'),
        max_length=100,
        blank=True
    )
    name_ja = models.CharField(
        _('Name (Japanese)'),
        max_length=100,
        blank=True
    )

    # Description (optional)
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Additional guidance for this section')
    )

    # Ordering and requirements
    order = models.PositiveIntegerField(
        _('Order'),
        default=0,
        help_text=_('Display order within the template')
    )
    is_required = models.BooleanField(
        _('Is Required'),
        default=True,
        help_text=_('Whether this section must have at least one item completed')
    )

    class Meta:
        verbose_name = _('Template Section')
        verbose_name_plural = _('Template Sections')
        ordering = ['template', 'order', 'code']
        unique_together = ['template', 'code']

    def __str__(self):
        return f"{self.template.name} - {self.name_ko}"

    def get_name_by_language(self, lang='ko'):
        """Get the section name in the specified language."""
        if lang == 'en' and self.name_en:
            return self.name_en
        elif lang == 'ja' and self.name_ja:
            return self.name_ja
        return self.name_ko


class TemplateItem(models.Model):
    """
    템플릿 점검 항목 - 개별 점검 항목
    Template Item - Individual inspection items
    """

    class ItemType(models.TextChoices):
        PHOTO = 'PHOTO', _('Photo')
        CHECKBOX = 'CHECKBOX', _('Checkbox')
        TEXT = 'TEXT', _('Text Input')
        SELECT = 'SELECT', _('Select/Dropdown')
        NUMBER = 'NUMBER', _('Number Input')

    class ResponsibilityHint(models.TextChoices):
        LANDLORD = 'LANDLORD', _('Landlord Responsibility')
        TENANT = 'TENANT', _('Tenant Responsibility')
        NEGOTIABLE = 'NEGOTIABLE', _('Negotiable')

    section = models.ForeignKey(
        TemplateSection,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Section')
    )

    # Item code for programmatic access
    code = models.CharField(
        _('Code'),
        max_length=50,
        help_text=_('Unique code within the section (e.g., FLOOR, WALL_EAST)')
    )

    # Multi-language names
    name_ko = models.CharField(
        _('Name (Korean)'),
        max_length=100
    )
    name_en = models.CharField(
        _('Name (English)'),
        max_length=100,
        blank=True
    )
    name_ja = models.CharField(
        _('Name (Japanese)'),
        max_length=100,
        blank=True
    )

    # Description/guidance
    description_ko = models.TextField(
        _('Description (Korean)'),
        blank=True,
        help_text=_('Guidance or instructions in Korean')
    )
    description_en = models.TextField(
        _('Description (English)'),
        blank=True,
        help_text=_('Guidance or instructions in English')
    )
    description_ja = models.TextField(
        _('Description (Japanese)'),
        blank=True,
        help_text=_('Guidance or instructions in Japanese')
    )

    # Item type and configuration
    item_type = models.CharField(
        _('Item Type'),
        max_length=20,
        choices=ItemType.choices,
        default=ItemType.PHOTO
    )

    # For SELECT type - store options as JSON
    options = models.JSONField(
        _('Options'),
        default=list,
        blank=True,
        help_text=_('Options for SELECT type items (list of {"value": "", "label_ko": "", "label_en": "", "label_ja": ""})')
    )

    # Requirements
    is_required = models.BooleanField(
        _('Is Required'),
        default=False,
        help_text=_('Whether this item must be completed')
    )
    min_photos = models.PositiveIntegerField(
        _('Minimum Photos'),
        default=1,
        help_text=_('Minimum number of photos required (for PHOTO type)')
    )
    max_photos = models.PositiveIntegerField(
        _('Maximum Photos'),
        default=10,
        help_text=_('Maximum number of photos allowed (for PHOTO type)')
    )

    # Responsibility hint
    responsibility_hint = models.CharField(
        _('Responsibility Hint'),
        max_length=20,
        choices=ResponsibilityHint.choices,
        default=ResponsibilityHint.NEGOTIABLE,
        help_text=_('Typical responsibility for restoration (informational only)')
    )

    # Ordering
    order = models.PositiveIntegerField(
        _('Order'),
        default=0,
        help_text=_('Display order within the section')
    )

    class Meta:
        verbose_name = _('Template Item')
        verbose_name_plural = _('Template Items')
        ordering = ['section', 'order', 'code']
        unique_together = ['section', 'code']

    def __str__(self):
        return f"{self.section.name_ko} - {self.name_ko}"

    def get_name_by_language(self, lang='ko'):
        """Get the item name in the specified language."""
        if lang == 'en' and self.name_en:
            return self.name_en
        elif lang == 'ja' and self.name_ja:
            return self.name_ja
        return self.name_ko

    def get_description_by_language(self, lang='ko'):
        """Get the item description in the specified language."""
        if lang == 'en' and self.description_en:
            return self.description_en
        elif lang == 'ja' and self.description_ja:
            return self.description_ja
        return self.description_ko
