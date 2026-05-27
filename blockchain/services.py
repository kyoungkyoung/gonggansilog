"""
블록체인 앵커링 서비스
- SHA-256 해시 생성
- Klaytn 테스트넷(Baobab)에 직접 트랜잭션 전송
- 파일 무결성 검증
"""
import hashlib
import json
import logging
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Klaytn/Kaia RPC 엔드포인트 (Klaytn이 Kaia로 리브랜딩됨)
KLAYTN_BAOBAB_RPC = 'https://public-en-kairos.node.kaia.io'  # Kairos = 구 Baobab 테스트넷
KLAYTN_MAINNET_RPC = 'https://public-en.node.kaia.io'


def generate_file_hash(file) -> str:
    """파일의 SHA-256 해시 생성

    Args:
        file: Django FileField 또는 ImageField

    Returns:
        str: 64자리 SHA-256 해시값
    """
    sha256_hash = hashlib.sha256()

    # 파일 포인터를 처음으로 이동
    file.seek(0)

    # 청크 단위로 읽어서 해시 계산 (메모리 효율)
    for chunk in iter(lambda: file.read(8192), b''):
        sha256_hash.update(chunk)

    # 파일 포인터를 다시 처음으로 이동 (다른 곳에서 사용할 수 있도록)
    file.seek(0)

    return sha256_hash.hexdigest()


def generate_contract_hash(contract) -> tuple:
    """계약 관련 모든 파일의 최종 해시 생성

    Args:
        contract: Contract 모델 인스턴스

    Returns:
        tuple: (final_hash: str, metadata: dict)
            - final_hash: 모든 해시를 결합한 최종 해시
            - metadata: 각 파일별 해시 정보
    """
    metadata = {
        'contract_id': contract.id,
        'address': contract.address,
        'generated_at': timezone.now().isoformat(),
        'files': {}
    }

    # 해시들을 결합할 리스트
    hash_list = []

    # 1. 계약서 파일 해시
    if contract.contract_file:
        try:
            file_hash = generate_file_hash(contract.contract_file)
            metadata['files']['contract_file'] = {
                'name': contract.contract_file.name,
                'hash': file_hash
            }
            hash_list.append(file_hash)
        except Exception as e:
            logger.error(f"계약서 파일 해시 생성 실패: {e}")

    # 2. 입실/퇴실 기록 사진 해시
    records_data = {}
    for record in contract.records.all():
        record_info = {
            'type': record.record_type,
            'status': record.status,
            'photos': []
        }

        for photo in record.photos.all():
            try:
                photo_hash = generate_file_hash(photo.image)
                photo_info = {
                    'category': photo.category,
                    'hash': photo_hash
                }
                record_info['photos'].append(photo_info)
                hash_list.append(photo_hash)
            except Exception as e:
                logger.error(f"사진 해시 생성 실패 (photo_id={photo.id}): {e}")

        records_data[f'record_{record.id}'] = record_info

    if records_data:
        metadata['files']['records'] = records_data

    # 3. 녹음 파일 해시
    recordings_data = []
    for recording in contract.recordings.all():
        try:
            audio_hash = generate_file_hash(recording.audio_file)
            recording_info = {
                'id': recording.id,
                'title': recording.title,
                'hash': audio_hash
            }
            recordings_data.append(recording_info)
            hash_list.append(audio_hash)
        except Exception as e:
            logger.error(f"녹음 파일 해시 생성 실패 (recording_id={recording.id}): {e}")

    if recordings_data:
        metadata['files']['recordings'] = recordings_data

    # 해시 리스트가 비어있으면 에러
    if not hash_list:
        raise ValueError("해시할 파일이 없습니다.")

    # 모든 해시를 정렬하여 결합 (일관성 보장)
    hash_list.sort()
    combined = ''.join(hash_list)

    # 최종 해시 생성
    final_hash = hashlib.sha256(combined.encode()).hexdigest()

    return final_hash, metadata


def get_web3_instance():
    """Web3 인스턴스 반환"""
    from web3 import Web3

    chain_id = getattr(settings, 'KLAYTN_CHAIN_ID', '1001')

    if chain_id == '8217':  # 메인넷
        rpc_url = KLAYTN_MAINNET_RPC
    else:  # 테스트넷 (Baobab)
        rpc_url = KLAYTN_BAOBAB_RPC

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    return w3


def create_wallet():
    """새 지갑 생성 (개인키, 주소 반환)

    Returns:
        dict: {'private_key': '0x...', 'address': '0x...'}
    """
    from web3 import Web3

    w3 = Web3()
    account = w3.eth.account.create()

    return {
        'private_key': account.key.hex(),
        'address': account.address
    }


def get_wallet_balance(address: str) -> float:
    """지갑 잔액 조회 (KLAY)"""
    w3 = get_web3_instance()

    try:
        balance_wei = w3.eth.get_balance(address)
        balance_klay = w3.from_wei(balance_wei, 'ether')
        return float(balance_klay)
    except Exception as e:
        logger.error(f"잔액 조회 실패: {e}")
        return 0.0


def anchor_to_blockchain(contract_id: int, final_hash: str, max_retries: int = 3) -> dict:
    """Klaytn 블록체인에 해시 기록 (직접 트랜잭션)

    Args:
        contract_id: 계약 ID
        final_hash: 앵커링할 해시값
        max_retries: 최대 재시도 횟수

    Returns:
        dict: {
            'success': True/False,
            'tx_hash': '0x...' (성공시),
            'error': '...' (실패시)
        }
    """
    from web3 import Web3
    import time

    private_key = getattr(settings, 'KLAYTN_PRIVATE_KEY', None)

    if not private_key:
        return {
            'success': False,
            'error': '지갑 개인키가 설정되지 않았습니다. .env 파일의 KLAYTN_PRIVATE_KEY를 확인하세요.'
        }

    try:
        w3 = get_web3_instance()

        # 개인키에서 주소 추출
        account = w3.eth.account.from_key(private_key)
        from_address = account.address

        # 잔액 확인
        balance = get_wallet_balance(from_address)
        if balance < 0.001:
            return {
                'success': False,
                'error': f'잔액이 부족합니다. 현재 잔액: {balance} KLAY. Faucet에서 테스트 KLAY를 받으세요: https://baobab.wallet.klaytn.foundation/faucet'
            }

        # 트랜잭션 데이터 구성
        # input data에 해시와 메타정보 포함
        data_payload = json.dumps({
            'type': 'contract_anchor',
            'contract_id': contract_id,
            'hash': final_hash,
            'timestamp': timezone.now().isoformat()
        })
        data_hex = '0x' + data_payload.encode('utf-8').hex()

        # 재시도 로직
        for attempt in range(max_retries):
            try:
                # nonce 조회
                nonce = w3.eth.get_transaction_count(from_address)

                # 가스 가격 조회
                gas_price = w3.eth.gas_price

                # 트랜잭션 구성 (자기 자신에게 0 KLAY 전송, data에 해시 포함)
                tx = {
                    'nonce': nonce,
                    'to': from_address,  # 자기 자신에게 전송
                    'value': 0,
                    'gas': 100000,  # 충분한 가스
                    'gasPrice': gas_price,
                    'data': data_hex,
                    'chainId': int(getattr(settings, 'KLAYTN_CHAIN_ID', '1001'))
                }

                # 트랜잭션 서명
                signed_tx = w3.eth.account.sign_transaction(tx, private_key)

                # 트랜잭션 전송
                tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                tx_hash_hex = tx_hash.hex()

                # 트랜잭션 확인 대기 (최대 60초)
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

                if receipt['status'] == 1:
                    logger.info(f"블록체인 앵커링 성공: contract_id={contract_id}, tx_hash={tx_hash_hex}")
                    return {
                        'success': True,
                        'tx_hash': tx_hash_hex
                    }
                else:
                    logger.error(f"트랜잭션 실패: receipt={receipt}")
                    return {
                        'success': False,
                        'error': '트랜잭션이 실패했습니다.'
                    }

            except Exception as e:
                logger.warning(f"앵커링 시도 {attempt + 1}/{max_retries} 실패: {e}")

                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 지수 백오프
                else:
                    return {
                        'success': False,
                        'error': str(e)
                    }

    except Exception as e:
        logger.error(f"블록체인 앵커링 오류: {e}")
        return {
            'success': False,
            'error': str(e)
        }

    return {
        'success': False,
        'error': '알 수 없는 오류'
    }


def verify_contract(contract) -> dict:
    """현재 파일 해시 vs DB 저장 해시 비교

    Args:
        contract: Contract 모델 인스턴스

    Returns:
        dict: {
            'is_valid': True/False,
            'current_hash': '...',
            'stored_hash': '...',
            'mismatched_files': [...],
            'details': {...}
        }
    """
    result = {
        'is_valid': False,
        'current_hash': None,
        'stored_hash': contract.blockchain_final_hash,
        'mismatched_files': [],
        'details': {}
    }

    # 블록체인에 앵커링되지 않은 경우
    if not contract.blockchain_final_hash:
        result['error'] = '블록체인에 등록된 해시가 없습니다.'
        return result

    try:
        # 현재 파일들의 해시 재계산
        current_hash, current_metadata = generate_contract_hash(contract)
        result['current_hash'] = current_hash

        # 해시 비교
        if current_hash == contract.blockchain_final_hash:
            result['is_valid'] = True
        else:
            result['is_valid'] = False

            # 개별 파일 해시 비교 (변조된 파일 찾기)
            stored_metadata = contract.blockchain_metadata or {}
            stored_files = stored_metadata.get('files', {})
            current_files = current_metadata.get('files', {})

            # 계약서 파일 비교
            if 'contract_file' in stored_files and 'contract_file' in current_files:
                if stored_files['contract_file']['hash'] != current_files['contract_file']['hash']:
                    result['mismatched_files'].append('계약서 파일')

            # 기록 사진 비교
            if 'records' in stored_files and 'records' in current_files:
                for record_key, stored_record in stored_files['records'].items():
                    current_record = current_files['records'].get(record_key, {})
                    stored_photos = {p['hash'] for p in stored_record.get('photos', [])}
                    current_photos = {p['hash'] for p in current_record.get('photos', [])}

                    if stored_photos != current_photos:
                        result['mismatched_files'].append(f'{record_key} 사진')

            # 녹음 파일 비교
            if 'recordings' in stored_files and 'recordings' in current_files:
                stored_recordings = {r['hash'] for r in stored_files['recordings']}
                current_recordings = {r['hash'] for r in current_files['recordings']}

                if stored_recordings != current_recordings:
                    result['mismatched_files'].append('녹음 파일')

        result['details'] = {
            'anchored_at': contract.blockchain_anchored_at.isoformat() if contract.blockchain_anchored_at else None,
            'tx_hash': contract.blockchain_tx_hash,
            'finalized_at': contract.finalized_at.isoformat() if contract.finalized_at else None
        }

    except Exception as e:
        logger.error(f"계약 검증 실패 (contract_id={contract.id}): {e}")
        result['error'] = str(e)

    return result


def get_klaytn_scope_url(tx_hash: str) -> str:
    """Kaia Scope URL 반환 (Klaytn -> Kaia 리브랜딩)

    Args:
        tx_hash: 트랜잭션 해시

    Returns:
        str: Kaia Scope URL
    """
    chain_id = getattr(settings, 'KLAYTN_CHAIN_ID', '1001')

    # 트랜잭션 해시에 0x 접두사 추가
    if not tx_hash.startswith('0x'):
        tx_hash = f'0x{tx_hash}'

    if chain_id == '8217':  # 메인넷
        return f'https://kaiascan.io/tx/{tx_hash}'
    else:  # 테스트넷 (Kairos, 구 Baobab)
        return f'https://kairos.kaiascan.io/tx/{tx_hash}'


def can_finalize_contract(contract, user) -> tuple:
    """계약 확정 가능 여부 확인

    Args:
        contract: Contract 모델 인스턴스
        user: 현재 사용자

    Returns:
        tuple: (can_finalize: bool, reasons: list)
            - can_finalize: 확정 가능 여부
            - reasons: 확정 불가 사유 목록 (빈 리스트면 확정 가능)
    """
    reasons = []

    # 1. 이미 확정된 경우
    if contract.is_finalized:
        reasons.append('이미 확정된 계약입니다.')
        return False, reasons

    # 2. 임대인만 확정 가능
    if user != contract.landlord:
        reasons.append('임대인만 계약을 확정할 수 있습니다.')

    # 3. 계약서 파일 필수
    if not contract.contract_file:
        reasons.append('계약서 파일이 업로드되지 않았습니다.')

    # 4. 임대인/임차인 모두 연결 필수
    if not contract.tenant:
        reasons.append('임차인이 연결되지 않았습니다.')
    if not contract.landlord:
        reasons.append('임대인이 연결되지 않았습니다.')

    # 5. 입실 기록 존재 + 승인됨
    move_in_record = contract.records.filter(record_type='MOVE_IN').first()
    if not move_in_record:
        reasons.append('입실 기록이 없습니다.')
    elif move_in_record.status != 'APPROVED':
        reasons.append('입실 기록이 최종 승인되지 않았습니다.')

    can_finalize = len(reasons) == 0
    return can_finalize, reasons


def check_wallet_setup() -> dict:
    """지갑 설정 상태 확인

    Returns:
        dict: {
            'is_configured': True/False,
            'address': '0x...',
            'balance': 0.0,
            'error': '...'
        }
    """
    private_key = getattr(settings, 'KLAYTN_PRIVATE_KEY', None)

    if not private_key:
        return {
            'is_configured': False,
            'error': '지갑 개인키가 설정되지 않았습니다.'
        }

    try:
        from web3 import Web3
        w3 = Web3()
        account = w3.eth.account.from_key(private_key)
        address = account.address
        balance = get_wallet_balance(address)

        return {
            'is_configured': True,
            'address': address,
            'balance': balance,
            'has_balance': balance >= 0.001
        }
    except Exception as e:
        return {
            'is_configured': False,
            'error': str(e)
        }
