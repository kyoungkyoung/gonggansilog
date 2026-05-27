"""
Klaytn 지갑 생성 명령어
"""
from django.core.management.base import BaseCommand
from blockchain.services import create_wallet


class Command(BaseCommand):
    help = 'Klaytn 블록체인용 새 지갑을 생성합니다'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Klaytn 지갑 생성'))
        self.stdout.write('=' * 60 + '\n')

        wallet = create_wallet()

        self.stdout.write(self.style.WARNING('주의: 개인키는 안전하게 보관하세요!'))
        self.stdout.write(self.style.WARNING('개인키를 분실하면 지갑에 접근할 수 없습니다.\n'))

        self.stdout.write(f"지갑 주소: {self.style.SUCCESS(wallet['address'])}")
        self.stdout.write(f"개인키:    {self.style.WARNING(wallet['private_key'])}")

        self.stdout.write('\n' + '-' * 60)
        self.stdout.write(self.style.NOTICE('다음 단계:'))
        self.stdout.write('-' * 60)
        self.stdout.write('1. .env 파일에 개인키 추가:')
        self.stdout.write(f"   KLAYTN_PRIVATE_KEY={wallet['private_key']}")
        self.stdout.write('')
        self.stdout.write('2. Faucet에서 테스트 KLAY 받기:')
        self.stdout.write('   https://baobab.wallet.klaytn.foundation/faucet')
        self.stdout.write(f"   -> 위 지갑 주소 입력 후 'Run Faucet' 클릭")
        self.stdout.write('')
        self.stdout.write('3. 서버 재시작')
        self.stdout.write('=' * 60 + '\n')
