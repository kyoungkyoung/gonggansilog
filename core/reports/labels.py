"""
다국어 라벨 시스템
리포트에 사용되는 텍스트를 언어별로 정의
"""


LABELS = {
    'ko': {
        # 리포트 제목
        'move_in_report_title': '입실 점검 보고서',
        'move_out_report_title': '퇴실 점검 보고서',
        'comparison_report_title': '입실/퇴실 비교 보고서',

        # 섹션 제목
        'contract_info': '계약 정보',
        'record_info': '기록 정보',
        'photos': '점검 사진',
        'comparison': '비교 사진',

        # 필드 라벨
        'address': '주소',
        'tenant': '임차인',
        'landlord': '임대인',
        'contract_date': '계약일',
        'move_in_date': '입실일',
        'move_out_date': '퇴실일',
        'record_date': '기록 날짜',
        'status': '상태',
        'total_photos': '총 사진 수',
        'move_in': '입실',
        'move_out': '퇴실',

        # 점검 결과
        'inspection_results': '점검 결과',
        'condition': '상태',
        'condition_normal': '정상',
        'condition_defective': '하자 있음',
        'condition_aged': '노후',
        'condition_needs_repair': '수리 필요',
        'item_name': '항목',
        'response': '응답',

        # 메모/녹음
        'memo': '메모',
        'no_memo': '메모 없음',
        'recordings': '녹음 기록',
        'recording_title': '제목',
        'recording_date': '녹음일',
        'recording_duration': '녹음 시간',
        'ai_summary': 'AI 요약',
        'no_recordings': '연결된 녹음 기록이 없습니다.',

        # 기타
        'generated_at': '생성일시',
        'image_not_found': '[이미지 없음]',
        'image_error': '[이미지 로드 오류]',
        'page': '페이지',

        # 책임 구분
        'responsibility_landlord': '임대인 부담',
        'responsibility_tenant': '임차인 부담',
        'responsibility_negotiable': '협의 필요',
    },
    'en': {
        # Report titles
        'move_in_report_title': 'Move-in Inspection Report',
        'move_out_report_title': 'Move-out Inspection Report',
        'comparison_report_title': 'Move-in/Move-out Comparison Report',

        # Section titles
        'contract_info': 'Contract Information',
        'record_info': 'Record Information',
        'photos': 'Inspection Photos',
        'comparison': 'Comparison Photos',

        # Field labels
        'address': 'Address',
        'tenant': 'Tenant',
        'landlord': 'Landlord',
        'contract_date': 'Contract Date',
        'move_in_date': 'Move-in Date',
        'move_out_date': 'Move-out Date',
        'record_date': 'Record Date',
        'status': 'Status',
        'total_photos': 'Total Photos',
        'move_in': 'Move-in',
        'move_out': 'Move-out',

        # Inspection Results
        'inspection_results': 'Inspection Results',
        'condition': 'Condition',
        'condition_normal': 'Normal',
        'condition_defective': 'Defective',
        'condition_aged': 'Aged',
        'condition_needs_repair': 'Needs Repair',
        'item_name': 'Item',
        'response': 'Response',

        # Memo/Recordings
        'memo': 'Memo',
        'no_memo': 'No memo',
        'recordings': 'Recordings',
        'recording_title': 'Title',
        'recording_date': 'Recorded At',
        'recording_duration': 'Duration',
        'ai_summary': 'AI Summary',
        'no_recordings': 'No recordings linked to this contract.',

        # Misc
        'generated_at': 'Generated At',
        'image_not_found': '[Image not found]',
        'image_error': '[Image load error]',
        'page': 'Page',

        # Responsibility
        'responsibility_landlord': 'Landlord Responsibility',
        'responsibility_tenant': 'Tenant Responsibility',
        'responsibility_negotiable': 'Negotiable',
    },
    'ja': {
        # レポートタイトル
        'move_in_report_title': '入居点検報告書',
        'move_out_report_title': '退去点検報告書',
        'comparison_report_title': '入居/退去比較報告書',

        # セクションタイトル
        'contract_info': '契約情報',
        'record_info': '記録情報',
        'photos': '点検写真',
        'comparison': '比較写真',

        # フィールドラベル
        'address': '住所',
        'tenant': '借主',
        'landlord': '貸主',
        'contract_date': '契約日',
        'move_in_date': '入居日',
        'move_out_date': '退去日',
        'record_date': '記録日',
        'status': '状態',
        'total_photos': '写真総数',
        'move_in': '入居',
        'move_out': '退去',

        # 点検結果
        'inspection_results': '点検結果',
        'condition': '状態',
        'condition_normal': '正常',
        'condition_defective': '不具合あり',
        'condition_aged': '経年劣化',
        'condition_needs_repair': '修繕必要',
        'item_name': '項目',
        'response': '回答',

        # メモ/録音
        'memo': 'メモ',
        'no_memo': 'メモなし',
        'recordings': '録音記録',
        'recording_title': 'タイトル',
        'recording_date': '録音日',
        'recording_duration': '録音時間',
        'ai_summary': 'AI要約',
        'no_recordings': 'この契約に連携された録音記録はありません。',

        # その他
        'generated_at': '作成日時',
        'image_not_found': '[画像なし]',
        'image_error': '[画像読み込みエラー]',
        'page': 'ページ',

        # 責任区分
        'responsibility_landlord': '貸主負担',
        'responsibility_tenant': '借主負担',
        'responsibility_negotiable': '協議必要',
    },
}


def get_labels(language='ko'):
    """
    지정된 언어의 라벨을 반환
    지원하지 않는 언어의 경우 영어로 대체
    """
    if language in LABELS:
        return LABELS[language]
    return LABELS.get('en', LABELS['ko'])


def get_label(key, language='ko'):
    """
    특정 라벨 키의 값을 반환
    """
    labels = get_labels(language)
    return labels.get(key, key)
