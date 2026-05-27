from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Recording


@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'get_duration_display', 'get_contract_display', 'get_processing_status_display', 'recorded_at', 'download_mp3_link')
    list_filter = ('recorded_at', 'user', 'processing_status')
    search_fields = ('title', 'description', 'user__username', 'contract__address', 'transcript', 'summary')
    readonly_fields = ('recorded_at', 'processed_at', 'download_mp3_button', 'display_transcript', 'display_summary')

    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'title', 'audio_file', 'duration', 'recorded_at')
        }),
        ('상세 정보', {
            'fields': ('description', 'contract')
        }),
        ('AI 처리 정보', {
            'fields': ('processing_status', 'processed_at', 'display_transcript', 'display_summary'),
            'description': '음성 전사본(원본)과 AI 요약 내용 - 관리자만 볼 수 있습니다'
        }),
        ('다운로드', {
            'fields': ('download_mp3_button',)
        }),
    )

    def get_contract_display(self, obj):
        """계약 표시"""
        if obj.contract:
            return obj.contract.address
        return "-"
    get_contract_display.short_description = '계약'

    def download_mp3_link(self, obj):
        """목록에서 MP3 다운로드 링크"""
        if obj.pk:
            url = reverse('recordings:download_mp3', args=[obj.pk])
            return format_html('<a href="{}" target="_blank">MP3 다운로드</a>', url)
        return '-'
    download_mp3_link.short_description = 'MP3 다운로드'

    def download_mp3_button(self, obj):
        """상세 페이지에서 MP3 다운로드 버튼"""
        if obj.pk:
            url = reverse('recordings:download_mp3', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}" target="_blank" style="padding: 10px 15px; '
                'background-color: #417690; color: white; text-decoration: none; '
                'border-radius: 4px; display: inline-block;">'
                '<strong>🎵 MP3 파일 다운로드</strong></a>',
                url
            )
        return '-'
    download_mp3_button.short_description = 'MP3 다운로드'

    def get_processing_status_display(self, obj):
        """처리 상태를 색상으로 표시"""
        status_colors = {
            'PENDING': '#6c757d',  # 회색
            'PROCESSING': '#ffc107',  # 노란색
            'COMPLETED': '#28a745',  # 초록색
            'FAILED': '#dc3545',  # 빨간색
        }
        status_labels = {
            'PENDING': '대기중',
            'PROCESSING': '처리중',
            'COMPLETED': '완료',
            'FAILED': '실패',
        }
        color = status_colors.get(obj.processing_status, '#6c757d')
        label = status_labels.get(obj.processing_status, obj.processing_status)
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, label
        )
    get_processing_status_display.short_description = '처리 상태'

    def display_transcript(self, obj):
        """전사본 표시 (관리자 전용)"""
        if obj.transcript:
            # 전사본을 보기 좋게 표시
            return format_html(
                '<div style="background-color: #f8f9fa; padding: 15px; border: 1px solid #dee2e6; '
                'border-radius: 5px; max-height: 400px; overflow-y: auto; white-space: pre-wrap; '
                'font-family: monospace; line-height: 1.6;">{}</div>',
                obj.transcript
            )
        elif obj.processing_status == 'COMPLETED':
            return format_html('<span style="color: #dc3545;">전사본이 없습니다.</span>')
        elif obj.processing_status == 'PROCESSING':
            return format_html('<span style="color: #ffc107;">⏳ 처리 중...</span>')
        elif obj.processing_status == 'FAILED':
            return format_html('<span style="color: #dc3545;">❌ 처리 실패</span>')
        else:
            return format_html('<span style="color: #6c757d;">⏸️ 대기중</span>')
    display_transcript.short_description = '📝 전사본 (원본 텍스트)'

    def display_summary(self, obj):
        """요약 표시"""
        if obj.summary:
            return format_html(
                '<div style="background-color: #e7f3ff; padding: 15px; border: 1px solid #b3d9ff; '
                'border-radius: 5px; max-height: 300px; overflow-y: auto; white-space: pre-wrap; '
                'line-height: 1.6;">{}</div>',
                obj.summary
            )
        elif obj.processing_status == 'COMPLETED':
            return format_html('<span style="color: #dc3545;">요약이 없습니다.</span>')
        elif obj.processing_status == 'PROCESSING':
            return format_html('<span style="color: #ffc107;">⏳ 처리 중...</span>')
        elif obj.processing_status == 'FAILED':
            return format_html('<span style="color: #dc3545;">❌ 처리 실패</span>')
        else:
            return format_html('<span style="color: #6c757d;">⏸️ 대기중</span>')
    display_summary.short_description = '✨ AI 요약'
