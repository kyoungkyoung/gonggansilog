"""
SusHi Tech Tokyo 데모용 데이터 생성 명령어
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta

from accounts.models import User
from contracts.models import Contract
from records.models import Record
from core.templates_engine.models import InspectionTemplate
from countries.jp.models import ContractJapanExtension


class Command(BaseCommand):
    help = 'Create demo data for SusHi Tech Tokyo presentation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing demo data before creating new',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.clear_demo_data()

        self.create_demo_data()
        self.stdout.write(self.style.SUCCESS('Demo data created successfully!'))

    def clear_demo_data(self):
        """기존 데모 데이터 삭제"""
        self.stdout.write('Clearing existing demo data...')

        # 데모 사용자 삭제 (연관 데이터도 함께 삭제됨)
        User.objects.filter(username__startswith='demo_').delete()

        self.stdout.write(self.style.WARNING('Demo data cleared.'))

    def create_demo_data(self):
        """데모 데이터 생성"""

        # 1. 일본 주거용 템플릿 확인
        jp_residential = InspectionTemplate.objects.filter(
            country='JP', property_type='RESIDENTIAL'
        ).first()

        jp_commercial = InspectionTemplate.objects.filter(
            country='JP', property_type='COMMERCIAL'
        ).first()

        if not jp_residential or not jp_commercial:
            self.stdout.write(self.style.ERROR(
                'Japanese templates not found. Please load templates first.'
            ))
            return

        # 2. 데모 사용자 생성
        self.stdout.write('Creating demo users...')

        # 주거용 - 임대인
        landlord_res, _ = User.objects.get_or_create(
            username='demo_landlord_residential',
            defaults={
                'email': 'landlord.res@demo.jp',
                'first_name': '太郎',
                'last_name': '田中',
                'user_type': 'LANDLORD',
            }
        )
        landlord_res.set_password('demo1234')
        landlord_res.save()

        # 주거용 - 임차인
        tenant_res, _ = User.objects.get_or_create(
            username='demo_tenant_residential',
            defaults={
                'email': 'tenant.res@demo.jp',
                'first_name': '花子',
                'last_name': '鈴木',
                'user_type': 'TENANT',
            }
        )
        tenant_res.set_password('demo1234')
        tenant_res.save()

        # 상가용 - 임대인
        landlord_com, _ = User.objects.get_or_create(
            username='demo_landlord_commercial',
            defaults={
                'email': 'landlord.com@demo.jp',
                'first_name': '一郎',
                'last_name': '山本',
                'user_type': 'LANDLORD',
            }
        )
        landlord_com.set_password('demo1234')
        landlord_com.save()

        # 상가용 - 임차인
        tenant_com, _ = User.objects.get_or_create(
            username='demo_tenant_commercial',
            defaults={
                'email': 'tenant.com@demo.jp',
                'first_name': 'ゆき',
                'last_name': '佐藤',
                'user_type': 'TENANT',
            }
        )
        tenant_com.set_password('demo1234')
        tenant_com.save()

        self.stdout.write(f'  Created 4 demo users (password: demo1234)')

        # 3. 일본 주거용 계약 생성
        self.stdout.write('Creating Japanese residential contract...')

        contract_res, created = Contract.objects.get_or_create(
            address='東京都渋谷区恵比寿1-2-3 恵比寿マンション 505号室',
            defaults={
                'landlord': landlord_res,
                'tenant': tenant_res,
                'landlord_name': '田中太郎',
                'landlord_phone': '03-1234-5678',
                'tenant_name': '鈴木花子',
                'tenant_phone': '090-1234-5678',
                'country': 'JP',
                'contract_date': date.today() - timedelta(days=30),
                'move_in_date': date.today() - timedelta(days=25),
                'status': 'ACTIVE',
                'template': jp_residential,
            }
        )

        if created:
            # 일본 확장 정보 추가
            ContractJapanExtension.objects.create(
                contract=contract_res,
                contract_type='ORDINARY',
                renewal_type='AUTO',
                renewal_fee=150000,
                key_money=300000,
                deposit=300000,
                guarantee_fee=75000,
                management_fee=10000,
                has_special_restoration_clause=False,
                agency_name='ABC不動産株式会社',
                agency_license='東京都知事 (3) 第12345号',
            )
            self.stdout.write(f'  Created residential contract: {contract_res.address}')
        else:
            self.stdout.write(f'  Residential contract already exists')

        # 4. 일본 상가용 계약 생성
        self.stdout.write('Creating Japanese commercial contract...')

        contract_com, created = Contract.objects.get_or_create(
            address='東京都港区六本木3-4-5 六本木ビル 1F',
            defaults={
                'landlord': landlord_com,
                'tenant': tenant_com,
                'landlord_name': '山本一郎',
                'landlord_phone': '03-9876-5432',
                'tenant_name': '佐藤ゆき',
                'tenant_phone': '080-9876-5432',
                'country': 'JP',
                'contract_date': date.today() - timedelta(days=90),
                'move_in_date': date.today() - timedelta(days=85),
                'status': 'ACTIVE',
                'template': jp_commercial,
            }
        )

        if created:
            # 일본 확장 정보 추가 (상가용 특약 포함)
            ContractJapanExtension.objects.create(
                contract=contract_com,
                contract_type='FIXED_TERM',
                renewal_type='NONE',
                key_money=1000000,
                deposit=1500000,
                guarantee_fee=250000,
                management_fee=30000,
                has_special_restoration_clause=True,
                restoration_clause='退去時、テナントは全ての内装・設備を撤去し、スケルトン状態で返還すること。',
                agency_name='六本木商業不動産',
                agency_license='東京都知事 (5) 第98765号',
            )
            self.stdout.write(f'  Created commercial contract: {contract_com.address}')
        else:
            self.stdout.write(f'  Commercial contract already exists')

        # 5. 입실 기록 생성
        self.stdout.write('Creating move-in records...')

        # 주거용 입실 기록
        record_res, created = Record.objects.get_or_create(
            contract=contract_res,
            record_type='MOVE_IN',
            defaults={
                'status': 'APPROVED',
                'created_by': tenant_res,
                'submitted_at': timezone.now() - timedelta(days=24),
                'landlord_approved_at': timezone.now() - timedelta(days=23),
                'notes': '入居時の状態確認。全体的に良好な状態。玄関ドアに小さな傷あり（既存）。',
                'template': jp_residential,
            }
        )
        if created:
            self.stdout.write(f'  Created residential move-in record')

        # 상가용 입실 기록
        record_com, created = Record.objects.get_or_create(
            contract=contract_com,
            record_type='MOVE_IN',
            defaults={
                'status': 'APPROVED',
                'created_by': tenant_com,
                'submitted_at': timezone.now() - timedelta(days=84),
                'landlord_approved_at': timezone.now() - timedelta(days=83),
                'notes': '店舗入居時の状態確認。スケルトン状態での引渡し。床コンクリート、天井配管露出。',
                'template': jp_commercial,
            }
        )
        if created:
            self.stdout.write(f'  Created commercial move-in record')

        # 완료 메시지
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS('Demo data created!'))
        self.stdout.write('')
        self.stdout.write('Demo accounts (password: demo1234):')
        self.stdout.write(f'  - demo_landlord_residential (Landlord - Residential)')
        self.stdout.write(f'  - demo_tenant_residential (Tenant - Residential)')
        self.stdout.write(f'  - demo_landlord_commercial (Landlord - Commercial)')
        self.stdout.write(f'  - demo_tenant_commercial (Tenant - Commercial)')
        self.stdout.write('')
        self.stdout.write('Demo contracts:')
        self.stdout.write(f'  1. Residential: 恵比寿マンション 505号室')
        self.stdout.write(f'  2. Commercial: 六本木ビル 1F')
        self.stdout.write(self.style.SUCCESS('='*50))
