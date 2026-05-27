from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io

from contracts.models import Contract
from .models import Record, Photo

User = get_user_model()


class RecordModelTest(TestCase):
    """Record 모델 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.tenant = User.objects.create_user(
            username='tenant_test',
            email='tenant@test.com',
            password='testpass123',
            user_type='TENANT'
        )
        self.landlord = User.objects.create_user(
            username='landlord_test',
            email='landlord@test.com',
            password='testpass123',
            user_type='LANDLORD'
        )
        self.contract = Contract.objects.create(
            tenant=self.tenant,
            landlord=self.landlord,
            tenant_name='임차인',
            landlord_name='임대인',
            address='서울시 강남구 테스트로 123',
            contract_date='2025-01-01',
            move_in_date='2025-02-01',
        )

    def test_create_move_in_record(self):
        """입실 기록 생성 테스트"""
        record = Record.objects.create(
            contract=self.contract,
            record_type='MOVE_IN',
            notes='입실 기록 테스트'
        )
        self.assertEqual(record.record_type, 'MOVE_IN')
        self.assertEqual(record.approval_status, 'PENDING')
        self.assertEqual(record.contract, self.contract)
        self.assertEqual(str(record), f'{self.contract.address} - 입실')

    def test_create_move_out_record(self):
        """퇴실 기록 생성 테스트"""
        record = Record.objects.create(
            contract=self.contract,
            record_type='MOVE_OUT',
            notes='퇴실 기록 테스트'
        )
        self.assertEqual(record.record_type, 'MOVE_OUT')
        self.assertEqual(record.get_record_type_display(), '퇴실')


class PhotoModelTest(TestCase):
    """Photo 모델 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.tenant = User.objects.create_user(
            username='tenant_test2',
            email='tenant2@test.com',
            password='testpass123',
            user_type='TENANT'
        )
        self.contract = Contract.objects.create(
            tenant=self.tenant,
            tenant_name='임차인',
            landlord_name='임대인',
            address='서울시 강남구 테스트로 456',
            contract_date='2025-01-01',
            move_in_date='2025-02-01',
        )
        self.record = Record.objects.create(
            contract=self.contract,
            record_type='MOVE_IN'
        )

    def create_test_image(self):
        """테스트용 이미지 생성"""
        image = Image.new('RGB', (100, 100), color='red')
        image_file = io.BytesIO()
        image.save(image_file, 'JPEG')
        image_file.seek(0)
        return SimpleUploadedFile(
            name='test_image.jpg',
            content=image_file.read(),
            content_type='image/jpeg'
        )

    def test_create_photo(self):
        """사진 생성 테스트"""
        photo = Photo.objects.create(
            record=self.record,
            image=self.create_test_image(),
            category='FLOOR',
            description='바닥 사진 테스트'
        )
        self.assertEqual(photo.category, 'FLOOR')
        self.assertEqual(photo.record, self.record)
        self.assertTrue(photo.image)

    def test_photo_categories(self):
        """사진 카테고리 테스트"""
        categories = dict(Photo.CATEGORY_CHOICES)
        self.assertIn('FLOOR', categories)
        self.assertIn('WALL_EAST', categories)
        self.assertIn('BATHROOM', categories)
        self.assertIn('KITCHEN', categories)


class RecordViewTest(TestCase):
    """Record 뷰 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.client = Client()
        self.tenant = User.objects.create_user(
            username='tenant_view',
            email='tenant_view@test.com',
            password='testpass123',
            user_type='TENANT'
        )
        self.landlord = User.objects.create_user(
            username='landlord_view',
            email='landlord_view@test.com',
            password='testpass123',
            user_type='LANDLORD'
        )
        self.other_user = User.objects.create_user(
            username='other_user',
            email='other@test.com',
            password='testpass123',
            user_type='TENANT'
        )
        self.contract = Contract.objects.create(
            tenant=self.tenant,
            landlord=self.landlord,
            tenant_name='임차인',
            landlord_name='임대인',
            address='서울시 강남구 뷰테스트로 789',
            contract_date='2025-01-01',
            move_in_date='2025-02-01',
        )

    def test_record_list_requires_login(self):
        """기록 목록 페이지 로그인 필수 테스트"""
        response = self.client.get(
            reverse('records:list', kwargs={'contract_id': self.contract.pk})
        )
        self.assertEqual(response.status_code, 302)  # 로그인 페이지로 리디렉션

    def test_record_list_access_tenant(self):
        """임차인 기록 목록 접근 테스트"""
        self.client.login(username='tenant_view', password='testpass123')
        response = self.client.get(
            reverse('records:list', kwargs={'contract_id': self.contract.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '입실/퇴실 기록')

    def test_record_list_access_landlord(self):
        """임대인 기록 목록 접근 테스트"""
        self.client.login(username='landlord_view', password='testpass123')
        response = self.client.get(
            reverse('records:list', kwargs={'contract_id': self.contract.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_record_list_access_denied(self):
        """권한 없는 사용자 접근 거부 테스트"""
        self.client.login(username='other_user', password='testpass123')
        response = self.client.get(
            reverse('records:list', kwargs={'contract_id': self.contract.pk})
        )
        self.assertEqual(response.status_code, 302)  # 계약 목록으로 리디렉션

    def test_record_create_page(self):
        """기록 생성 페이지 테스트"""
        self.client.login(username='tenant_view', password='testpass123')
        response = self.client.get(
            reverse('records:create', kwargs={'contract_id': self.contract.pk}) + '?type=MOVE_IN'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '입실 기록 등록')

    def test_record_create_move_in(self):
        """입실 기록 생성 테스트"""
        self.client.login(username='tenant_view', password='testpass123')
        response = self.client.post(
            reverse('records:create', kwargs={'contract_id': self.contract.pk}),
            {
                'record_type': 'MOVE_IN',
                'notes': '테스트 입실 기록',
            }
        )
        # 생성 후 상세 페이지로 리디렉션
        self.assertEqual(response.status_code, 302)

        # 기록이 생성되었는지 확인
        record = Record.objects.filter(contract=self.contract, record_type='MOVE_IN').first()
        self.assertIsNotNone(record)
        self.assertEqual(record.notes, '테스트 입실 기록')

    def test_record_detail_page(self):
        """기록 상세 페이지 테스트"""
        record = Record.objects.create(
            contract=self.contract,
            record_type='MOVE_IN',
            notes='상세 페이지 테스트'
        )
        self.client.login(username='tenant_view', password='testpass123')
        response = self.client.get(
            reverse('records:detail', kwargs={'pk': record.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '입실 기록')
        self.assertContains(response, '상세 페이지 테스트')


class RecordApprovalTest(TestCase):
    """Record 승인 기능 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.client = Client()
        self.tenant = User.objects.create_user(
            username='tenant_approval',
            email='tenant_approval@test.com',
            password='testpass123',
            user_type='TENANT'
        )
        self.landlord = User.objects.create_user(
            username='landlord_approval',
            email='landlord_approval@test.com',
            password='testpass123',
            user_type='LANDLORD'
        )
        self.contract = Contract.objects.create(
            tenant=self.tenant,
            landlord=self.landlord,
            tenant_name='임차인',
            landlord_name='임대인',
            address='서울시 강남구 승인테스트로 111',
            contract_date='2025-01-01',
            move_in_date='2025-02-01',
        )
        self.record = Record.objects.create(
            contract=self.contract,
            record_type='MOVE_IN',
            notes='승인 테스트 기록'
        )

    def test_landlord_can_approve(self):
        """임대인 승인 테스트"""
        self.client.login(username='landlord_approval', password='testpass123')
        response = self.client.post(
            reverse('records:approve', kwargs={'pk': self.record.pk}),
            {
                'approval_status': 'APPROVED',
                'landlord_comment': '승인합니다.'
            }
        )
        self.assertEqual(response.status_code, 302)  # 리디렉션

        self.record.refresh_from_db()
        self.assertEqual(self.record.approval_status, 'APPROVED')
        self.assertEqual(self.record.landlord_comment, '승인합니다.')

    def test_landlord_can_reject(self):
        """임대인 반려 테스트"""
        self.client.login(username='landlord_approval', password='testpass123')
        response = self.client.post(
            reverse('records:approve', kwargs={'pk': self.record.pk}),
            {
                'approval_status': 'REJECTED',
                'landlord_comment': '사진이 부족합니다.'
            }
        )
        self.assertEqual(response.status_code, 302)

        self.record.refresh_from_db()
        self.assertEqual(self.record.approval_status, 'REJECTED')

    def test_tenant_cannot_approve(self):
        """임차인 승인 불가 테스트"""
        self.client.login(username='tenant_approval', password='testpass123')
        response = self.client.post(
            reverse('records:approve', kwargs={'pk': self.record.pk}),
            {
                'approval_status': 'APPROVED',
                'landlord_comment': ''
            }
        )
        # 권한 없음으로 리디렉션
        self.assertEqual(response.status_code, 302)

        self.record.refresh_from_db()
        self.assertEqual(self.record.approval_status, 'PENDING')  # 여전히 대기 중


class RecordCompareTest(TestCase):
    """입실/퇴실 비교 기능 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.client = Client()
        self.tenant = User.objects.create_user(
            username='tenant_compare',
            email='tenant_compare@test.com',
            password='testpass123',
            user_type='TENANT'
        )
        self.contract = Contract.objects.create(
            tenant=self.tenant,
            tenant_name='임차인',
            landlord_name='임대인',
            address='서울시 강남구 비교테스트로 222',
            contract_date='2025-01-01',
            move_in_date='2025-02-01',
        )

    def test_compare_requires_both_records(self):
        """비교 뷰는 입실/퇴실 기록 모두 필요"""
        # 입실 기록만 생성
        Record.objects.create(
            contract=self.contract,
            record_type='MOVE_IN'
        )

        self.client.login(username='tenant_compare', password='testpass123')
        response = self.client.get(
            reverse('records:compare', kwargs={'contract_id': self.contract.pk})
        )
        # 기록이 부족하면 목록으로 리디렉션
        self.assertEqual(response.status_code, 302)

    def test_compare_with_both_records(self):
        """입실/퇴실 기록 모두 있을 때 비교 뷰"""
        Record.objects.create(contract=self.contract, record_type='MOVE_IN')
        Record.objects.create(contract=self.contract, record_type='MOVE_OUT')

        self.client.login(username='tenant_compare', password='testpass123')
        response = self.client.get(
            reverse('records:compare', kwargs={'contract_id': self.contract.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '입실/퇴실 사진 비교')


class URLRoutingTest(TestCase):
    """URL 라우팅 테스트"""

    def test_url_reverse(self):
        """URL reverse 테스트"""
        self.assertEqual(
            reverse('records:list', kwargs={'contract_id': 1}),
            '/records/contract/1/'
        )
        self.assertEqual(
            reverse('records:create', kwargs={'contract_id': 1}),
            '/records/contract/1/create/'
        )
        self.assertEqual(
            reverse('records:detail', kwargs={'pk': 1}),
            '/records/1/'
        )
        self.assertEqual(
            reverse('records:compare', kwargs={'contract_id': 1}),
            '/records/contract/1/compare/'
        )
        self.assertEqual(
            reverse('records:approve', kwargs={'pk': 1}),
            '/records/1/approve/'
        )
        self.assertEqual(
            reverse('records:add_photos', kwargs={'pk': 1}),
            '/records/1/add-photos/'
        )
