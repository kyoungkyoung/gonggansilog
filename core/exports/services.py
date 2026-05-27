"""
Export 서비스 모듈
- JSON Export: 계약 전체 데이터 + 메타데이터
- 이미지 ZIP Export: 계약별 모든 사진 압축
- 통합 패키지 Export: JSON + 이미지 + PDF
"""
import json
import hashlib
import zipfile
from io import BytesIO
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.utils import timezone


class ContractExportService:
    """계약 데이터 Export 서비스"""

    def __init__(self, contract):
        self.contract = contract

    def _calculate_file_hash(self, file_field):
        """파일의 SHA-256 해시 계산"""
        if not file_field:
            return None
        try:
            file_field.seek(0)
            hash_sha256 = hashlib.sha256()
            for chunk in iter(lambda: file_field.read(4096), b''):
                hash_sha256.update(chunk)
            file_field.seek(0)
            return hash_sha256.hexdigest()
        except Exception:
            return None

    def _format_datetime(self, dt):
        """datetime을 ISO 형식 문자열로 변환"""
        if dt is None:
            return None
        if timezone.is_aware(dt):
            return dt.isoformat()
        return timezone.make_aware(dt).isoformat()

    def _format_date(self, d):
        """date를 ISO 형식 문자열로 변환"""
        if d is None:
            return None
        return d.isoformat()

    def export_json(self) -> dict:
        """
        계약 전체 데이터를 JSON으로 변환

        Returns:
            dict: 계약 데이터 딕셔너리
        """
        contract = self.contract

        # 기본 계약 정보
        data = {
            "export_info": {
                "version": "1.0",
                "exported_at": self._format_datetime(timezone.now()),
                "service": "공간실록 (Space Chronicle)",
            },
            "contract": {
                "id": contract.id,
                "address": contract.address,
                "country": contract.country,
                "status": contract.status,
                "contract_date": self._format_date(contract.contract_date),
                "move_in_date": self._format_date(contract.move_in_date),
                "move_out_date": self._format_date(contract.move_out_date),
                "created_at": self._format_datetime(contract.created_at),
                "updated_at": self._format_datetime(contract.updated_at),
            },
            "parties": {
                "landlord": {
                    "name": contract.landlord_name,
                    "phone": contract.landlord_phone,
                    "username": contract.landlord.username if contract.landlord else None,
                },
                "tenant": {
                    "name": contract.tenant_name,
                    "phone": contract.tenant_phone,
                    "username": contract.tenant.username if contract.tenant else None,
                },
            },
            "blockchain": {
                "status": contract.blockchain_status,
                "is_finalized": contract.is_finalized,
                "finalized_at": self._format_datetime(contract.finalized_at),
                "tx_hash": contract.blockchain_tx_hash,
                "final_hash": contract.blockchain_final_hash,
                "anchored_at": self._format_datetime(contract.blockchain_anchored_at),
            },
            "template": None,
            "records": [],
            "recordings": [],
            "japan_extension": None,
            "files": {
                "contract_file": None,
            },
        }

        # 템플릿 정보
        if contract.template:
            data["template"] = {
                "id": contract.template.id,
                "name": contract.template.name,
                "country": contract.template.country,
                "property_type": contract.template.property_type,
            }

        # 계약서 파일 해시
        if contract.contract_file:
            data["files"]["contract_file"] = {
                "name": Path(contract.contract_file.name).name,
                "path": contract.contract_file.name,
                "hash": self._calculate_file_hash(contract.contract_file),
            }

        # 입실/퇴실 기록
        for record in contract.records.all().prefetch_related('photos'):
            record_data = {
                "id": record.id,
                "type": record.record_type,
                "status": record.status,
                "notes": record.notes,
                "created_at": self._format_datetime(record.created_at),
                "submitted_at": self._format_datetime(record.submitted_at),
                "landlord_approved_at": self._format_datetime(record.landlord_approved_at),
                "landlord_comment": record.landlord_comment,
                "photos": [],
            }

            # 사진 정보
            for photo in record.photos.all():
                photo_data = {
                    "id": photo.id,
                    "category": photo.category,
                    "category_display": photo.get_category_display(),
                    "description": photo.description,
                    "filename": Path(photo.image.name).name if photo.image else None,
                    "path": photo.image.name if photo.image else None,
                    "hash": self._calculate_file_hash(photo.image) if photo.image else None,
                    "taken_at": self._format_datetime(photo.taken_at),
                    "latitude": str(photo.latitude) if photo.latitude else None,
                    "longitude": str(photo.longitude) if photo.longitude else None,
                    "device_info": photo.device_info,
                    "created_at": self._format_datetime(photo.created_at),
                    "approval_status": photo.approval_status,
                }
                record_data["photos"].append(photo_data)

            data["records"].append(record_data)

        # 녹음 정보
        for recording in contract.recordings.all():
            recording_data = {
                "id": recording.id,
                "title": recording.title,
                "duration": recording.duration,
                "duration_display": recording.get_duration_display(),
                "description": recording.description,
                "filename": Path(recording.audio_file.name).name if recording.audio_file else None,
                "path": recording.audio_file.name if recording.audio_file else None,
                "hash": self._calculate_file_hash(recording.audio_file) if recording.audio_file else None,
                "recorded_at": self._format_datetime(recording.recorded_at),
                "processing_status": recording.processing_status,
                "summary": recording.summary,
            }
            data["recordings"].append(recording_data)

        # 일본 계약 확장 정보
        if hasattr(contract, 'japan_extension') and contract.japan_extension:
            ext = contract.japan_extension
            data["japan_extension"] = {
                "contract_type": ext.contract_type,
                "renewal_type": ext.renewal_type,
                "renewal_fee": int(ext.renewal_fee) if ext.renewal_fee else None,
                "key_money": int(ext.key_money) if ext.key_money else None,
                "deposit": int(ext.deposit) if ext.deposit else None,
                "guarantee_fee": int(ext.guarantee_fee) if ext.guarantee_fee else None,
                "management_fee": int(ext.management_fee) if ext.management_fee else None,
                "has_special_restoration_clause": ext.has_special_restoration_clause,
                "restoration_clause": ext.restoration_clause,
                "agency_name": ext.agency_name,
                "agency_license": ext.agency_license,
            }

        return data

    def export_images_zip(self) -> BytesIO:
        """
        계약 관련 모든 이미지를 ZIP 압축하여 반환

        Returns:
            BytesIO: ZIP 파일 바이너리 스트림
        """
        buffer = BytesIO()

        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 계약서 파일 추가
            if self.contract.contract_file:
                try:
                    filename = Path(self.contract.contract_file.name).name
                    zf.writestr(
                        f"contract/{filename}",
                        self.contract.contract_file.read()
                    )
                    self.contract.contract_file.seek(0)
                except Exception:
                    pass

            # 입실/퇴실 기록별 사진 추가
            for record in self.contract.records.all().prefetch_related('photos'):
                record_type = record.record_type.lower()
                record_folder = f"{record_type}_{record.id}"

                for photo in record.photos.all():
                    if not photo.image:
                        continue
                    try:
                        filename = Path(photo.image.name).name
                        category = photo.category.lower()
                        zf.writestr(
                            f"records/{record_folder}/{category}/{filename}",
                            photo.image.read()
                        )
                        photo.image.seek(0)
                    except Exception:
                        pass

            # 녹음 파일 추가
            for recording in self.contract.recordings.all():
                if not recording.audio_file:
                    continue
                try:
                    filename = Path(recording.audio_file.name).name
                    zf.writestr(
                        f"recordings/{filename}",
                        recording.audio_file.read()
                    )
                    recording.audio_file.seek(0)
                except Exception:
                    pass

            # 메타데이터 JSON 추가
            metadata = self.export_json()
            zf.writestr(
                "metadata.json",
                json.dumps(metadata, ensure_ascii=False, indent=2)
            )

        buffer.seek(0)
        return buffer

    def export_full_package(self, include_pdf=True) -> BytesIO:
        """
        JSON + 이미지 + PDF 통합 패키지 생성

        Args:
            include_pdf: PDF 리포트 포함 여부

        Returns:
            BytesIO: ZIP 파일 바이너리 스트림
        """
        buffer = BytesIO()

        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. JSON 메타데이터
            metadata = self.export_json()
            zf.writestr(
                "data/contract_data.json",
                json.dumps(metadata, ensure_ascii=False, indent=2)
            )

            # 2. 계약서 파일
            if self.contract.contract_file:
                try:
                    filename = Path(self.contract.contract_file.name).name
                    zf.writestr(
                        f"documents/contract/{filename}",
                        self.contract.contract_file.read()
                    )
                    self.contract.contract_file.seek(0)
                except Exception:
                    pass

            # 3. 입실/퇴실 기록 사진
            for record in self.contract.records.all().prefetch_related('photos'):
                record_type = record.record_type.lower()
                record_folder = f"{record_type}_{record.id}"

                for photo in record.photos.all():
                    if not photo.image:
                        continue
                    try:
                        filename = Path(photo.image.name).name
                        category = photo.category.lower()
                        zf.writestr(
                            f"images/{record_folder}/{category}/{filename}",
                            photo.image.read()
                        )
                        photo.image.seek(0)
                    except Exception:
                        pass

            # 4. 녹음 파일
            for recording in self.contract.recordings.all():
                if not recording.audio_file:
                    continue
                try:
                    filename = Path(recording.audio_file.name).name
                    zf.writestr(
                        f"audio/{filename}",
                        recording.audio_file.read()
                    )
                    recording.audio_file.seek(0)
                except Exception:
                    pass

            # 5. PDF 리포트 (있는 경우)
            if include_pdf:
                from core.reports.models import GeneratedReport
                reports = GeneratedReport.objects.filter(
                    contract=self.contract,
                    status='COMPLETED'
                ).order_by('-created_at')

                for report in reports:
                    if report.file:
                        try:
                            filename = Path(report.file.name).name
                            report_type = report.report_type.lower()
                            zf.writestr(
                                f"reports/{report_type}_{report.language}_{filename}",
                                report.file.read()
                            )
                            report.file.seek(0)
                        except Exception:
                            pass

            # 6. README 파일 추가
            readme_content = self._generate_readme()
            zf.writestr("README.txt", readme_content)

        buffer.seek(0)
        return buffer

    def _generate_readme(self) -> str:
        """README 파일 내용 생성"""
        contract = self.contract
        now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""공간실록 (Space Chronicle) - Export Package
============================================

Export Date: {now}
Contract Address: {contract.address}
Contract ID: {contract.id}

Package Contents:
-----------------
/data/
  - contract_data.json : Complete contract data with file hashes

/documents/
  - contract/ : Contract document files

/images/
  - move_in_*/ : Move-in record photos by category
  - move_out_*/ : Move-out record photos by category

/audio/
  - Recording files

/reports/
  - PDF reports (move-in, move-out, comparison)

Data Integrity:
---------------
Each file includes SHA-256 hash in metadata.json for verification.
Blockchain anchoring status: {contract.blockchain_status}
"""
        if contract.blockchain_tx_hash:
            content += f"Transaction Hash: {contract.blockchain_tx_hash}\n"

        content += """
For verification, compare file hashes in contract_data.json.

---
Generated by 공간실록 (Space Chronicle)
https://github.com/space-chronicle
"""
        return content
