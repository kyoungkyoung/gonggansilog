from rest_framework import serializers
from accounts.models import User
from contracts.models import Contract, ContractChangeRequest, ContractInvitation, ContractHistory
from records.models import (
    Record, Photo, RecordItemResponse,
    DefectReport, DefectPhoto,
    RepairRequest, RepairPhoto, RepairComment,
    Expense
)
from recordings.models import Recording
from core.reports.models import GeneratedReport, ReportShare
from core.templates_engine.models import InspectionTemplate, TemplateSection, TemplateItem


# ========== Auth ==========

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'user_type', 'phone_number']
        read_only_fields = ['id']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'user_type', 'phone_number']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


# ========== Contracts ==========

class ContractListSerializer(serializers.ModelSerializer):
    tenant_username = serializers.CharField(source='tenant.username', read_only=True, default=None)
    landlord_username = serializers.CharField(source='landlord.username', read_only=True, default=None)
    display_address = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = [
            'id', 'address', 'address_en', 'address_ja', 'display_address',
            'contract_date', 'move_in_date', 'move_out_date',
            'status', 'country', 'is_finalized', 'blockchain_status',
            'tenant_username', 'landlord_username',
            'tenant_name', 'landlord_name',
            'created_at',
        ]

    def get_display_address(self, obj):
        return obj.get_display_address()


class ContractDetailSerializer(serializers.ModelSerializer):
    tenant = UserSerializer(read_only=True)
    landlord = UserSerializer(read_only=True)
    display_address = serializers.SerializerMethodField()
    records_count = serializers.SerializerMethodField()
    defects_count = serializers.SerializerMethodField()
    repairs_count = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = '__all__'

    def get_display_address(self, obj):
        return obj.get_display_address()

    def get_records_count(self, obj):
        return obj.records.count()

    def get_defects_count(self, obj):
        return obj.defect_reports.count()

    def get_repairs_count(self, obj):
        return obj.repair_requests.count()


class ContractCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = [
            'address', 'contract_date', 'move_in_date', 'move_out_date',
            'tenant_name', 'tenant_phone', 'landlord_name', 'landlord_phone',
            'country', 'contract_file',
        ]


class ContractChangeRequestSerializer(serializers.ModelSerializer):
    requested_by = UserSerializer(read_only=True)
    responded_by = UserSerializer(read_only=True)

    class Meta:
        model = ContractChangeRequest
        fields = '__all__'
        read_only_fields = ['contract', 'requested_by', 'responded_by', 'responded_at']


class ContractHistorySerializer(serializers.ModelSerializer):
    action_by = UserSerializer(read_only=True)

    class Meta:
        model = ContractHistory
        fields = '__all__'


# ========== Records ==========

class PhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = [
            'id', 'image', 'image_url', 'category', 'template_item',
            'description', 'approval_status', 'rejection_reason',
            'taken_at', 'created_at',
        ]

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class RecordItemResponseSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='template_item.name_ko', read_only=True)

    class Meta:
        model = RecordItemResponse
        fields = [
            'id', 'template_item', 'item_name',
            'condition_status', 'response_value', 'notes',
        ]


class RecordListSerializer(serializers.ModelSerializer):
    photo_count = serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = [
            'id', 'record_type', 'status', 'upload_deadline',
            'submitted_at', 'landlord_approved_at', 'photo_count',
            'created_at',
        ]

    def get_photo_count(self, obj):
        return obj.photos.count()


class RecordDetailSerializer(serializers.ModelSerializer):
    photos = PhotoSerializer(many=True, read_only=True)
    item_responses = RecordItemResponseSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Record
        fields = '__all__'


# ========== Defects ==========

class DefectPhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = DefectPhoto
        fields = ['id', 'image', 'image_url', 'description', 'created_at']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class DefectReportSerializer(serializers.ModelSerializer):
    photos = DefectPhotoSerializer(many=True, read_only=True)
    reported_by = UserSerializer(read_only=True)

    class Meta:
        model = DefectReport
        fields = '__all__'
        read_only_fields = ['reported_by', 'acknowledged_at', 'resolved_at']


# ========== Repairs ==========

class RepairPhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = RepairPhoto
        fields = ['id', 'image', 'image_url', 'photo_type', 'description', 'created_at']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class RepairCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = RepairComment
        fields = ['id', 'author', 'message', 'created_at']
        read_only_fields = ['author']


class RepairRequestSerializer(serializers.ModelSerializer):
    photos = RepairPhotoSerializer(many=True, read_only=True)
    comments = RepairCommentSerializer(many=True, read_only=True)
    requested_by = UserSerializer(read_only=True)

    class Meta:
        model = RepairRequest
        fields = '__all__'
        read_only_fields = ['requested_by', 'approved_at', 'started_at', 'completed_at']


# ========== Expenses ==========

class ExpenseSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    receipt_url = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ['created_by']

    def get_receipt_url(self, obj):
        request = self.context.get('request')
        if obj.receipt_image and request:
            return request.build_absolute_uri(obj.receipt_image.url)
        return None


# ========== Recordings ==========

class RecordingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    display_title = serializers.SerializerMethodField()
    duration_display = serializers.CharField(source='get_duration_display', read_only=True)

    class Meta:
        model = Recording
        fields = [
            'id', 'user', 'title', 'title_en', 'title_ja', 'display_title',
            'audio_file', 'duration', 'duration_display',
            'recorded_at', 'description',
            'contract', 'consent_status', 'consented_by', 'consented_at',
            'consent_rejected_reason',
            'transcript', 'summary', 'processing_status',
        ]
        read_only_fields = ['user', 'transcript', 'summary', 'processing_status']

    def get_display_title(self, obj):
        return obj.get_display_title()


# ========== Reports ==========

class GeneratedReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedReport
        fields = [
            'uuid', 'contract', 'record', 'report_type', 'language',
            'status', 'file', 'generated_by', 'error_message',
            'created_at',
        ]


# ========== Templates ==========

class TemplateItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateItem
        fields = [
            'id', 'code', 'name_ko', 'name_en', 'name_ja',
            'description_ko', 'description_en', 'description_ja',
            'item_type', 'options', 'is_required',
            'min_photos', 'max_photos', 'responsibility_hint', 'order',
        ]


class TemplateSectionSerializer(serializers.ModelSerializer):
    items = TemplateItemSerializer(many=True, read_only=True)

    class Meta:
        model = TemplateSection
        fields = ['id', 'code', 'name_ko', 'name_en', 'name_ja', 'order', 'is_required', 'items']


class InspectionTemplateSerializer(serializers.ModelSerializer):
    sections = TemplateSectionSerializer(many=True, read_only=True)

    class Meta:
        model = InspectionTemplate
        fields = [
            'id', 'name', 'name_en', 'name_ja',
            'country', 'property_type', 'version',
            'is_active', 'is_default', 'sections',
        ]


# ========== Dashboard ==========

class DashboardSerializer(serializers.Serializer):
    """대시보드 알림 데이터"""
    record_notifications = serializers.ListField(child=serializers.DictField())
    recording_notifications = serializers.ListField(child=serializers.DictField())
    defect_notifications = serializers.ListField(child=serializers.DictField())
    repair_notifications = serializers.ListField(child=serializers.DictField())
    pending_requests = ContractChangeRequestSerializer(many=True)
