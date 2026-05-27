"""한국어 주소를 영어/일본어로 자동 변환하는 유틸리티"""

# 한국어 초성, 중성, 종성 로마자 변환 테이블 (Revised Romanization)
INITIALS = [
    'g', 'kk', 'n', 'd', 'tt', 'r', 'm', 'b', 'pp',
    's', 'ss', '', 'j', 'jj', 'ch', 'k', 't', 'p', 'h'
]

MEDIALS = [
    'a', 'ae', 'ya', 'yae', 'eo', 'e', 'yeo', 'ye', 'o',
    'wa', 'wae', 'oe', 'yo', 'u', 'wo', 'we', 'wi', 'yu',
    'eu', 'ui', 'i'
]

FINALS = [
    '', 'k', 'k', 'k', 'n', 'n', 'n', 't', 'l',
    'l', 'l', 'l', 'l', 'l', 'l', 'l', 'm', 'p',
    'p', 't', 't', 'ng', 't', 't', 'k', 't', 'p', 't'
]

# 잘 알려진 도시/행정구역 영어 이름
KNOWN_PLACES = {
    '서울': 'Seoul',
    '부산': 'Busan',
    '인천': 'Incheon',
    '대구': 'Daegu',
    '대전': 'Daejeon',
    '광주': 'Gwangju',
    '울산': 'Ulsan',
    '세종': 'Sejong',
    '제주': 'Jeju',
    '수원': 'Suwon',
    '성남': 'Seongnam',
    '고양': 'Goyang',
    '용인': 'Yongin',
    '청주': 'Cheongju',
    '전주': 'Jeonju',
    '천안': 'Cheonan',
    '창원': 'Changwon',
    '포항': 'Pohang',
    '김해': 'Gimhae',
    '안산': 'Ansan',
    '안양': 'Anyang',
    '남양주': 'Namyangju',
    '화성': 'Hwaseong',
    '평택': 'Pyeongtaek',
    '의정부': 'Uijeongbu',
    '파주': 'Paju',
    '시흥': 'Siheung',
    '김포': 'Gimpo',
    '광명': 'Gwangmyeong',
    '하남': 'Hanam',
    '군포': 'Gunpo',
    '오산': 'Osan',
    '이천': 'Icheon',
    '양주': 'Yangju',
    '구리': 'Guri',
    '강남': 'Gangnam',
    '강서': 'Gangseo',
    '강동': 'Gangdong',
    '강북': 'Gangbuk',
    '관악': 'Gwanak',
    '광진': 'Gwangjin',
    '구로': 'Guro',
    '금천': 'Geumcheon',
    '노원': 'Nowon',
    '도봉': 'Dobong',
    '동대문': 'Dongdaemun',
    '동작': 'Dongjak',
    '마포': 'Mapo',
    '서대문': 'Seodaemun',
    '서초': 'Seocho',
    '성동': 'Seongdong',
    '성북': 'Seongbuk',
    '송파': 'Songpa',
    '양천': 'Yangcheon',
    '영등포': 'Yeongdeungpo',
    '용산': 'Yongsan',
    '은평': 'Eunpyeong',
    '종로': 'Jongno',
    '중구': 'Jung-gu',
    '중랑': 'Jungnang',
    '경기': 'Gyeonggi',
    '충북': 'Chungbuk',
    '충남': 'Chungnam',
    '전북': 'Jeonbuk',
    '전남': 'Jeonnam',
    '경북': 'Gyeongbuk',
    '경남': 'Gyeongnam',
    '강원': 'Gangwon',
    '왕십리': 'Wangsimni',
    '테헤란': 'Teheran',
    '을지': 'Euljiro',
    '삼성': 'Samseong',
    '역삼': 'Yeoksam',
    '신사': 'Sinsa',
    '압구정': 'Apgujeong',
    '청담': 'Cheongdam',
    '잠실': 'Jamsil',
    '건대': 'Konkuk Univ.',
    '홍대': 'Hongdae',
    '이태원': 'Itaewon',
    '명동': 'Myeongdong',
    '신촌': 'Sinchon',
    '합정': 'Hapjeong',
    '여의도': 'Yeouido',
}

# 일본어(카타카나) 매핑
KNOWN_PLACES_JA = {
    '서울': 'ソウル',
    '부산': '釜山',
    '인천': '仁川',
    '대구': '大邱',
    '대전': '大田',
    '광주': '光州',
    '울산': '蔚山',
    '세종': '世宗',
    '제주': '済州',
    '강남': 'カンナム',
    '강서': 'カンソ',
    '강동': 'カンドン',
    '강북': 'カンブク',
    '마포': 'マポ',
    '서초': 'ソチョ',
    '성동': 'ソンドン',
    '송파': 'ソンパ',
    '용산': 'ヨンサン',
    '종로': 'チョンノ',
    '영등포': 'ヨンドゥンポ',
    '경기': '京畿',
    '왕십리': 'ワンシムニ',
}

# 행정구역 접미사 변환
SUFFIX_MAP_EN = {
    '특별시': '',
    '광역시': '',
    '특별자치시': '',
    '특별자치도': '-do',
    '도': '-do',
    '시': '-si',
    '군': '-gun',
    '구': '-gu',
    '읍': '-eup',
    '면': '-myeon',
    '동': '-dong',
    '리': '-ri',
    '로': '-ro',
    '길': '-gil',
    '번지': '',
    '번': '',
    '호': '',
    '층': 'F',
}

SUFFIX_MAP_JA = {
    '특별시': '特別市',
    '광역시': '広域市',
    '특별자치시': '特別自治市',
    '특별자치도': '特別自治道',
    '도': '道',
    '시': '市',
    '군': '郡',
    '구': '区',
    '읍': '邑',
    '면': '面',
    '동': '洞',
    '리': '里',
    '로': '路',
    '길': '通り',
    '번지': '番地',
    '번': '番',
    '호': '号',
    '층': '階',
}


def romanize_syllable(char):
    """한글 한 글자를 로마자로 변환"""
    code = ord(char)
    if code < 0xAC00 or code > 0xD7A3:
        return char

    offset = code - 0xAC00
    initial = offset // (21 * 28)
    medial = (offset % (21 * 28)) // 28
    final = offset % 28

    result = INITIALS[initial] + MEDIALS[medial] + FINALS[final]
    return result


def romanize_text(text):
    """한국어 텍스트를 로마자로 변환"""
    result = []
    for char in text:
        if '\uAC00' <= char <= '\uD7A3':
            result.append(romanize_syllable(char))
        else:
            result.append(char)
    return ''.join(result)


def _convert_address_part(part, known_places, suffix_map, romanize=True):
    """주소의 한 부분을 변환"""
    part = part.strip()
    if not part:
        return ''

    # 숫자만 있는 경우 그대로 반환
    if part.replace('-', '').isdigit():
        return part

    # 행정구역 접미사 처리
    for suffix, replacement in sorted(suffix_map.items(), key=lambda x: len(x[0]), reverse=True):
        if part.endswith(suffix):
            base = part[:-len(suffix)]
            if not base:
                continue

            # 알려진 지명 확인
            if base in known_places:
                converted_base = known_places[base]
            elif romanize:
                converted_base = romanize_text(base)
                converted_base = converted_base.capitalize()
            else:
                converted_base = base

            return converted_base + replacement

    # 접미사가 없는 경우
    if part in known_places:
        return known_places[part]
    elif romanize:
        return romanize_text(part).capitalize()
    else:
        return part


def korean_address_to_english(address):
    """
    한국어 주소를 영어로 변환

    예: '서울특별시 성동구 왕십리로 8길 4'
    →   '4, Wangsimni-ro 8-gil, Seongdong-gu, Seoul'
    """
    if not address:
        return ''

    # 한글이 포함되어 있지 않으면 그대로 반환
    if not any('\uAC00' <= c <= '\uD7A3' for c in address):
        return address

    parts = address.split()
    converted_parts = []

    for part in parts:
        converted = _convert_address_part(part, KNOWN_PLACES, SUFFIX_MAP_EN, romanize=True)
        if converted:
            converted_parts.append(converted)

    # 영어 주소 순서: 작은 단위 → 큰 단위 (역순)
    converted_parts.reverse()

    return ', '.join(converted_parts)


def korean_address_to_japanese(address):
    """
    한국어 주소를 일본어로 변환

    예: '서울특별시 성동구 왕십리로 8길 4'
    →   'ソウル特別市 ソンドン区 ワンシムニ路 8通り 4'
    """
    if not address:
        return ''

    # 한글이 포함되어 있지 않으면 그대로 반환
    if not any('\uAC00' <= c <= '\uD7A3' for c in address):
        return address

    parts = address.split()
    converted_parts = []

    for part in parts:
        converted = _convert_address_part(part, KNOWN_PLACES_JA, SUFFIX_MAP_JA, romanize=False)
        if converted:
            # 일본어 매핑에 없으면 로마자로 변환 후 카타카나화하지 않고 로마자 그대로
            if any('\uAC00' <= c <= '\uD7A3' for c in converted):
                # 아직 한글이 남아있으면 로마자로 변환
                converted = _convert_address_part(part, KNOWN_PLACES, SUFFIX_MAP_JA, romanize=True)
            converted_parts.append(converted)

    return ' '.join(converted_parts)


def translate_address(address, language='en'):
    """
    한국어 주소를 지정된 언어로 변환

    Args:
        address: 한국어 주소 문자열
        language: 대상 언어 ('en', 'ja', 'ko')

    Returns:
        변환된 주소 문자열
    """
    if language == 'ko':
        return address
    elif language == 'ja':
        return korean_address_to_japanese(address)
    else:
        return korean_address_to_english(address)
