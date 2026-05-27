"""
Klaytn 지갑 상태 확인 명령어
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from blockchain.services import check_wallet_setup, get_klaytn_scope_url


class Command(BaseCommand):
    help = 'Klaytn 지갑 설정 및 잔액을 확인합니다'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Klaytn/Kaia 지갑 상태'))
        self.stdout.write('=' * 60 + '\n')

        wallet_info = check_wallet_setup()

        if not wallet_info.get('is_configured'):
            self.stdout.write(self.style.ERROR('지갑이 설정되지 않았습니다.'))
            self.stdout.write(f"오류: {wallet_info.get('error', '알 수 없는 오류')}")
            self.stdout.write('\n설정 방법:')
            self.stdout.write('1. python manage.py create_wallet')
            self.stdout.write('2. .env 파일에 KLAYTN_PRIVATE_KEY 추가')
            self.stdout.write('3. Faucet에서 테스트 KAIA 받기')
            return

        chain_id = getattr(settings, 'KLAYTN_CHAIN_ID', '1001')
        network = '메인넷' if chain_id == '8217' else '테스트넷 (Kairos)'

        balance = wallet_info['balance']
        address = wallet_info['address']

        self.stdout.write(f"네트워크:   {self.style.SUCCESS(network)}")
        self.stdout.write(f"지갑 주소:  {self.style.SUCCESS(address)}")
        self.stdout.write(f"잔액:       {self.style.SUCCESS(f'{balance:.4f} KAIA')}")

        # 잔액 상태
        if wallet_info['balance'] >= 1:
            self.stdout.write(self.style.SUCCESS('\n✓ 잔액 충분 - 블록체인 앵커링 가능'))
            estimated_txs = int(wallet_info['balance'] / 0.001)
            self.stdout.write(f"  예상 가능 트랜잭션: 약 {estimated_txs:,}건")
        elif wallet_info['balance'] >= 0.001:
            self.stdout.write(self.style.WARNING('\n⚠ 잔액 부족 주의 - 곧 충전 필요'))
        else:
            self.stdout.write(self.style.ERROR('\n✗ 잔액 부족 - Faucet에서 KAIA를 받으세요'))
            self.stdout.write('  https://faucet.kaia.io')

        # Kaia Scope 링크
        scope_base = 'https://kaiascan.io' if chain_id == '8217' else 'https://kairos.kaiascan.io'
        self.stdout.write(f"\n지갑 확인:  {scope_base}/account/{wallet_info['address']}")

        self.stdout.write('\n' + '=' * 60 + '\n')
