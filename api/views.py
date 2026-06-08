from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Sum

from accounts.models import User
from contracts.models import Contract, ContractChangeRequest, ContractHistory
from records.models import (
    Record, Photo, RecordItemResponse,
    DefectReport, DefectPhoto,
    RepairRequest, RepairPhoto, RepairComment,
    Expense
)
from recordings.models import Recording
from core.reports.models import GeneratedReport
from core.templates_engine.models import InspectionTemplate

from .serializers import *
from .permissions import IsContractParty


# ========== Auth ==========

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def me(request):
    return Response(UserSerializer(request.user).data)


@api_view(['PATCH'])
def update_profile(request):
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ========== Dashboard ==========

@api_view(['GET'])
def dashboard(request):
    """대시보드 알림 데이터"""
    user = request.user
    if user.user_type == 'TENANT':
        contracts = Contract.objects.filter(tenant=user)
    else:
        contracts = Contract.objects.filter(landlord=user)

    data = {
        'contracts_count': contracts.count(),
        'pending_change_requests': ContractChangeRequestSerializer(
            ContractChangeRequest.objects.filter(
                contract__in=contracts, status='PENDING'
            ).exclude(requested_by=user), many=True
        ).data,
        'unread_defects': DefectReport.objects.filter(
            contract__in=contracts,
            **({'is_read_by_landlord': False} if user.user_type == 'LANDLORD' else {'is_read_by_tenant': False, 'reported_by': user})
        ).count(),
        'unread_repairs': RepairRequest.objects.filter(
            contract__in=contracts,
            **({'is_read_by_landlord': False} if user.user_type == 'LANDLORD' else {'is_read_by_tenant': False})
        ).count(),
        'pending_recordings': Recording.objects.filter(
            contract__in=contracts, consent_status='PENDING'
        ).exclude(user=user).count(),
    }
    return Response(data)


# ========== Contracts ==========

class ContractViewSet(viewsets.ModelViewSet):
    serializer_class = ContractListSerializer

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'TENANT':
            return Contract.objects.filter(tenant=user)
        return Contract.objects.filter(landlord=user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ContractDetailSerializer
        if self.action == 'create':
            return ContractCreateSerializer
        return ContractListSerializer

    def perform_create(self, serializer):
        user = self.request.user
        kwargs = {}
        if user.user_type == 'TENANT':
            kwargs['tenant'] = user
        else:
            kwargs['landlord'] = user
            if not serializer.validated_data.get('landlord_name'):
                kwargs['landlord_name'] = user.username
            if not serializer.validated_data.get('landlord_phone'):
                kwargs['landlord_phone'] = user.phone_number or ''
        serializer.save(**kwargs)

    @action(detail=True, methods=['post'])
    def extend(self, request, pk=None):
        contract = self.get_object()
        months = request.data.get('months', 12)
        change_request = ContractChangeRequest.objects.create(
            contract=contract,
            request_type='EXTEND',
            requested_by=request.user,
            extend_months=months,
            note=request.data.get('note', ''),
        )
        return Response({'id': change_request.pk, 'status': 'PENDING'})

    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        contract = self.get_object()
        change_request = ContractChangeRequest.objects.create(
            contract=contract,
            request_type='TERMINATE',
            requested_by=request.user,
            note=request.data.get('note', ''),
        )
        return Response({'id': change_request.pk, 'status': 'PENDING'})

    @action(detail=True)
    def history(self, request, pk=None):
        contract = self.get_object()
        histories = ContractHistory.objects.filter(contract=contract)
        return Response(ContractHistorySerializer(histories, many=True).data)


# ========== Records ==========

class RecordViewSet(viewsets.ModelViewSet):
    serializer_class = RecordListSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        contract_id = self.kwargs.get('contract_id')
        if contract_id:
            return Record.objects.filter(contract_id=contract_id)
        if user.user_type == 'TENANT':
            return Record.objects.filter(contract__tenant=user)
        return Record.objects.filter(contract__landlord=user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RecordDetailSerializer
        return RecordListSerializer

    @action(detail=True, methods=['post'])
    def upload_photos(self, request, pk=None):
        record = self.get_object()
        images = request.FILES.getlist('images')
        template_items = request.data.getlist('template_items', [])
        categories = request.data.getlist('categories', [])

        photos = []
        for i, image in enumerate(images):
            photo = Photo.objects.create(
                record=record,
                image=image,
                category=categories[i] if i < len(categories) else 'OTHER',
                template_item_id=template_items[i] if i < len(template_items) and template_items[i] else None,
            )
            photos.append(photo)

        return Response({
            'count': len(photos),
            'photos': PhotoSerializer(photos, many=True, context={'request': request}).data
        })

    @action(detail=True, methods=['post'])
    def save_responses(self, request, pk=None):
        record = self.get_object()
        responses_data = request.data.get('responses', [])

        for item_data in responses_data:
            RecordItemResponse.objects.update_or_create(
                record=record,
                template_item_id=item_data['template_item'],
                defaults={
                    'condition_status': item_data.get('condition_status', 'NORMAL'),
                    'response_value': item_data.get('response_value', ''),
                    'notes': item_data.get('notes', ''),
                }
            )
        return Response({'status': 'saved'})

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        record = self.get_object()
        if record.status not in ['OPEN', 'REJECTED']:
            return Response({'error': 'Cannot submit in current status'}, status=400)
        record.status = 'SUBMITTED'
        record.submitted_at = timezone.now()
        record.is_read_by_landlord = False
        record.save()
        return Response({'status': 'SUBMITTED'})

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        record = self.get_object()
        action_type = request.data.get('action', 'approve')
        comment = request.data.get('comment', '')

        if action_type == 'approve':
            record.status = 'APPROVED'
        else:
            record.status = 'REJECTED'
        record.landlord_approved_at = timezone.now()
        record.landlord_comment = comment
        record.is_read_by_tenant = False
        record.save()
        return Response({'status': record.status})


# ========== Defects ==========

class DefectViewSet(viewsets.ModelViewSet):
    serializer_class = DefectReportSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        contract_id = self.kwargs.get('contract_id')
        if contract_id:
            return DefectReport.objects.filter(contract_id=contract_id)
        user = self.request.user
        if user.user_type == 'TENANT':
            return DefectReport.objects.filter(contract__tenant=user)
        return DefectReport.objects.filter(contract__landlord=user)

    def perform_create(self, serializer):
        contract_id = self.kwargs.get('contract_id')
        defect = serializer.save(
            contract_id=contract_id,
            reported_by=self.request.user,
        )
        # 사진 첨부
        for image in self.request.FILES.getlist('images'):
            DefectPhoto.objects.create(defect_report=defect, image=image)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        defect = self.get_object()
        action_type = request.data.get('action')
        response_text = request.data.get('response', '')

        if action_type == 'acknowledge':
            defect.status = 'ACKNOWLEDGED'
            defect.acknowledged_at = timezone.now()
        elif action_type == 'in_progress':
            defect.status = 'IN_PROGRESS'
        elif action_type == 'resolve':
            defect.status = 'RESOLVED'
            defect.resolved_at = timezone.now()

        defect.landlord_response = response_text
        defect.is_read_by_tenant = False
        defect.save()
        return Response(DefectReportSerializer(defect).data)


# ========== Repairs ==========

class RepairViewSet(viewsets.ModelViewSet):
    serializer_class = RepairRequestSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        contract_id = self.kwargs.get('contract_id')
        if contract_id:
            return RepairRequest.objects.filter(contract_id=contract_id)
        user = self.request.user
        if user.user_type == 'TENANT':
            return RepairRequest.objects.filter(contract__tenant=user)
        return RepairRequest.objects.filter(contract__landlord=user)

    def perform_create(self, serializer):
        contract_id = self.kwargs.get('contract_id')
        repair = serializer.save(
            contract_id=contract_id,
            requested_by=self.request.user,
        )
        for image in self.request.FILES.getlist('images'):
            RepairPhoto.objects.create(repair_request=repair, image=image, photo_type='ISSUE')

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        repair = self.get_object()
        action_type = request.data.get('action')

        if action_type == 'provide_quote':
            repair.status = 'QUOTE_PROVIDED'
            repair.estimated_cost = request.data.get('estimated_cost')
            repair.is_read_by_tenant = False
        elif action_type == 'approve_quote':
            repair.status = 'APPROVED'
            repair.approved_at = timezone.now()
            repair.is_read_by_landlord = False
        elif action_type == 'start_repair':
            repair.status = 'IN_PROGRESS'
            repair.started_at = timezone.now()
            repair.is_read_by_tenant = False
        elif action_type == 'complete_repair':
            repair.status = 'COMPLETED'
            repair.completed_at = timezone.now()
            repair.actual_cost = request.data.get('actual_cost', repair.estimated_cost)
            repair.is_read_by_tenant = False

        repair.save()

        # 사진 첨부
        photo_type = 'IN_PROGRESS' if action_type == 'start_repair' else 'COMPLETED'
        for image in request.FILES.getlist('images'):
            RepairPhoto.objects.create(repair_request=repair, image=image, photo_type=photo_type)

        return Response(RepairRequestSerializer(repair).data)

    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        repair = self.get_object()
        comment = RepairComment.objects.create(
            repair_request=repair,
            author=request.user,
            message=request.data.get('message', ''),
        )
        if request.user == repair.contract.tenant:
            repair.is_read_by_landlord = False
        else:
            repair.is_read_by_tenant = False
        repair.save(update_fields=['is_read_by_landlord', 'is_read_by_tenant'])
        return Response(RepairCommentSerializer(comment).data)


# ========== Expenses ==========

class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        contract_id = self.kwargs.get('contract_id')
        if contract_id:
            return Expense.objects.filter(contract_id=contract_id)
        user = self.request.user
        if user.user_type == 'TENANT':
            return Expense.objects.filter(contract__tenant=user)
        return Expense.objects.filter(contract__landlord=user)

    def perform_create(self, serializer):
        contract_id = self.kwargs.get('contract_id')
        serializer.save(contract_id=contract_id, created_by=self.request.user)

    @action(detail=False)
    def summary(self, request, contract_id=None):
        expenses = Expense.objects.filter(contract_id=contract_id)
        return Response({
            'total': expenses.aggregate(total=Sum('amount'))['total'] or 0,
            'tenant_total': expenses.filter(paid_by='TENANT').aggregate(total=Sum('amount'))['total'] or 0,
            'landlord_total': expenses.filter(paid_by='LANDLORD').aggregate(total=Sum('amount'))['total'] or 0,
        })


# ========== Recordings ==========

class RecordingViewSet(viewsets.ModelViewSet):
    serializer_class = RecordingSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'TENANT':
            return Recording.objects.filter(
                Q(user=user) | Q(contract__tenant=user)
            ).distinct()
        return Recording.objects.filter(
            Q(user=user) | Q(contract__landlord=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def consent(self, request, pk=None):
        recording = self.get_object()
        action_type = request.data.get('action')

        if action_type == 'approve':
            recording.consent_status = 'APPROVED'
            recording.consented_by = request.user
            recording.consented_at = timezone.now()
        elif action_type == 'reject':
            recording.consent_status = 'REJECTED'
            recording.consented_by = request.user
            recording.consented_at = timezone.now()
            recording.consent_rejected_reason = request.data.get('reason', '')
            recording.contract = None

        recording.save()
        return Response(RecordingSerializer(recording).data)


# ========== Reports ==========

@api_view(['POST'])
def generate_report(request, record_pk):
    """리포트 생성"""
    from core.reports.services import ReportGenerator
    from django.core.files.base import ContentFile

    record = get_object_or_404(Record, pk=record_pk)
    language = request.data.get('language', 'ko')
    report_type = 'MOVE_IN' if record.record_type == 'MOVE_IN' else 'MOVE_OUT'

    generator = ReportGenerator(record.contract, language=language)
    if report_type == 'MOVE_IN':
        result = generator.generate_move_in_report(record)
    else:
        result = generator.generate_move_out_report(record)

    report = GeneratedReport.objects.create(
        contract=record.contract,
        record=record,
        report_type=report_type,
        language=language,
        status='COMPLETED',
        generated_by=request.user,
    )
    report.file.save(result['filename'], ContentFile(result['content']))

    return Response({
        'uuid': str(report.uuid),
        'filename': result['filename'],
        'download_url': request.build_absolute_uri(f'/api/v1/reports/{report.uuid}/download/'),
    })


@api_view(['GET'])
def download_report(request, report_uuid):
    from django.http import FileResponse
    report = get_object_or_404(GeneratedReport, uuid=report_uuid)
    return FileResponse(report.file.open(), content_type='application/pdf')


# ========== Templates ==========

class TemplateViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InspectionTemplateSerializer
    queryset = InspectionTemplate.objects.filter(is_active=True)

    def get_queryset(self):
        qs = super().get_queryset()
        country = self.request.query_params.get('country')
        property_type = self.request.query_params.get('property_type')
        if country:
            qs = qs.filter(country=country)
        if property_type:
            qs = qs.filter(property_type=property_type)
        return qs
