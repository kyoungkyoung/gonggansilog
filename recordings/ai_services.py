"""
녹음 파일 처리를 위한 AI 서비스
- Whisper API를 사용한 음성-텍스트 변환
- GPT-4o-mini를 사용한 텍스트 요약
"""

from openai import OpenAI
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def transcribe_audio(audio_file_path):
    """
    Whisper API를 사용하여 음성 파일을 텍스트로 변환

    Args:
        audio_file_path: 오디오 파일 경로 (파일 시스템 경로)

    Returns:
        str: 변환된 텍스트, 실패 시 빈 문자열
    """
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # 오디오 파일 열기
        with open(audio_file_path, 'rb') as audio_file:
            # Whisper API 호출
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ko"  # 한국어 지정
            )

        logger.info(f"음성 전사 완료: {audio_file_path}")
        return transcript.text

    except Exception as e:
        logger.error(f"음성 전사 실패: {audio_file_path}, Error: {str(e)}")
        return ""


def summarize_text(transcript):
    """
    GPT-4o-mini를 사용하여 전사본을 요약

    Args:
        transcript: 전사된 텍스트

    Returns:
        str: 요약된 텍스트, 실패 시 빈 문자열
    """
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # GPT-4o-mini API 호출
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """당신은 상가 임대차 계약 전문가입니다.
녹음된 대화 내용을 분석하여 핵심 내용을 요약해주세요.

요약 시 다음 항목을 포함해주세요:
1. 대화 주제 (계약 협의, 원상복구 논의, 시설 점검 등)
2. 주요 논의 사항 (3-5개의 핵심 포인트)
3. 결정된 사항 또는 합의 내용
4. 추후 조치가 필요한 사항

간결하고 명확하게 작성해주세요."""
                },
                {
                    "role": "user",
                    "content": f"다음 대화 내용을 요약해주세요:\n\n{transcript}"
                }
            ],
            temperature=0.3,
            max_completion_tokens=1000
        )

        summary = response.choices[0].message.content
        logger.info(f"텍스트 요약 완료: {len(transcript)} chars -> {len(summary)} chars")
        return summary

    except Exception as e:
        logger.error(f"텍스트 요약 실패: {str(e)}")
        return ""


def translate_title(title, target_lang='en'):
    """
    GPT를 사용하여 녹음 제목을 번역

    Args:
        title: 원본 제목 (한국어)
        target_lang: 대상 언어 ('en' 또는 'ja')

    Returns:
        str: 번역된 제목, 실패 시 빈 문자열
    """
    if not title:
        return ''

    # 한글이 없으면 번역 불필요
    if not any('\uAC00' <= c <= '\uD7A3' for c in title):
        return title

    lang_name = 'English' if target_lang == 'en' else 'Japanese'

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"Translate the following Korean text to {lang_name}. Return ONLY the translation, nothing else. Keep it concise."
                },
                {
                    "role": "user",
                    "content": title
                }
            ],
            temperature=0.1,
            max_tokens=200
        )

        result = response.choices[0].message.content.strip()
        logger.info(f"제목 번역 완료: '{title}' -> '{result}' ({target_lang})")
        return result

    except Exception as e:
        logger.error(f"제목 번역 실패: '{title}', lang={target_lang}, Error: {str(e)}")
        return ''


def process_recording(recording):
    """
    녹음 파일을 전사하고 요약하는 전체 프로세스

    Args:
        recording: Recording 모델 인스턴스

    Returns:
        tuple: (success: bool, transcript: str, summary: str)
    """
    try:
        # 상태를 처리중으로 변경
        recording.processing_status = 'PROCESSING'
        recording.save(update_fields=['processing_status'])

        # 파일 경로 가져오기
        audio_path = recording.audio_file.path

        # 1. 음성을 텍스트로 변환
        logger.info(f"녹음 파일 처리 시작: {recording.id} - {recording.title}")
        transcript = transcribe_audio(audio_path)

        if not transcript:
            recording.processing_status = 'FAILED'
            recording.save(update_fields=['processing_status'])
            return False, "", ""

        # 2. 텍스트 요약
        summary = summarize_text(transcript)

        if not summary:
            recording.processing_status = 'FAILED'
            recording.save(update_fields=['processing_status'])
            return False, transcript, ""

        logger.info(f"녹음 파일 처리 완료: {recording.id}")
        return True, transcript, summary

    except Exception as e:
        logger.error(f"녹음 파일 처리 중 오류 발생: {recording.id}, Error: {str(e)}")
        recording.processing_status = 'FAILED'
        recording.save(update_fields=['processing_status'])
        return False, "", ""
