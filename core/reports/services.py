"""
PDF 리포트 생성 서비스
ReportLab을 사용하여 입실/퇴실 리포트 및 비교 리포트를 생성
"""
import os
import io
from datetime import datetime
from django.conf import settings
from django.utils.translation import gettext as _, activate, get_language
from django.core.files.base import ContentFile

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .labels import get_labels


class ReportGenerator:
    """리포트 생성기"""

    def __init__(self, contract, language='ko'):
        self.contract = contract
        self.language = language
        self.labels = get_labels(language)
        self._register_fonts()
        self._setup_styles()

    def _register_fonts(self):
        """한글/일본어 폰트 등록"""
        if 'Korean' in pdfmetrics.getRegisteredFontNames():
            return  # 이미 등록됨

        # TTF 폰트 우선 (TTC PostScript 문제 회피)
        font_paths = [
            '/System/Library/Fonts/Supplemental/AppleGothic.ttf',   # macOS (TTF)
            '/Library/Fonts/Arial Unicode.ttf',                      # macOS (유니코드)
            '/System/Library/Fonts/Supplemental/AppleMyungjo.ttf',  # macOS (명조)
            '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',      # Linux (Ubuntu)
            'C:/Windows/Fonts/malgun.ttf',                           # Windows
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('Korean', font_path))
                    return
                except Exception:
                    continue

    def _setup_styles(self):
        """스타일 설정"""
        self.styles = getSampleStyleSheet()

        # 제목 스타일
        self.styles.add(ParagraphStyle(
            name='KoreanTitle',
            fontName='Korean' if 'Korean' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
            fontSize=18,
            leading=22,
            alignment=1,  # Center
            spaceAfter=20,
        ))

        # 섹션 헤더 스타일
        self.styles.add(ParagraphStyle(
            name='KoreanHeading',
            fontName='Korean' if 'Korean' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
            fontSize=14,
            leading=18,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.HexColor('#1a5276'),
        ))

        # 본문 스타일
        self.styles.add(ParagraphStyle(
            name='KoreanBody',
            fontName='Korean' if 'Korean' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
            fontSize=10,
            leading=14,
            spaceAfter=6,
        ))

        # 캡션 스타일
        self.styles.add(ParagraphStyle(
            name='KoreanCaption',
            fontName='Korean' if 'Korean' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
            fontSize=8,
            leading=10,
            textColor=colors.gray,
        ))

    def generate_move_in_report(self, record):
        """입실 리포트 생성"""
        return self._generate_single_report(record, 'MOVE_IN')

    def generate_move_out_report(self, record):
        """퇴실 리포트 생성"""
        return self._generate_single_report(record, 'MOVE_OUT')

    def _generate_single_report(self, record, report_type):
        """개별 리포트 생성 (입실/퇴실)"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        story = []

        # 제목
        if report_type == 'MOVE_IN':
            title = self.labels['move_in_report_title']
        else:
            title = self.labels['move_out_report_title']

        story.append(Paragraph(title, self.styles['KoreanTitle']))
        story.append(Spacer(1, 20))

        # 계약 정보 테이블
        story.append(Paragraph(self.labels['contract_info'], self.styles['KoreanHeading']))
        contract_data = [
            [self.labels['address'], self.contract.address],
            [self.labels['tenant'], self.contract.tenant_name or '-'],
            [self.labels['landlord'], self.contract.landlord_name or '-'],
            [self.labels['contract_date'], str(self.contract.contract_date) if self.contract.contract_date else '-'],
            [self.labels['move_in_date'], str(self.contract.move_in_date) if self.contract.move_in_date else '-'],
        ]

        contract_table = Table(contract_data, colWidths=[4*cm, 12*cm])
        contract_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Korean' if 'Korean' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(contract_table)
        story.append(Spacer(1, 20))

        # 기록 정보
        story.append(Paragraph(self.labels['record_info'], self.styles['KoreanHeading']))
        record_data = [
            [self.labels['record_date'], str(record.created_at.date()) if record.created_at else '-'],
            [self.labels['status'], record.get_status_display()],
            [self.labels['total_photos'], str(record.photos.count())],
        ]

        record_table = Table(record_data, colWidths=[4*cm, 12*cm])
        record_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Korean' if 'Korean' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(record_table)
        story.append(Spacer(1, 20))

        # 사진 섹션
        story.append(Paragraph(self.labels['photos'], self.styles['KoreanHeading']))

        # 템플릿 기반 또는 카테고리 기반 그룹화
        template = record.template or self.contract.template
        has_template_photos = record.photos.filter(template_item__isnull=False).exists()

        if template and has_template_photos:
            # 템플릿 기반 그룹화
            for section in template.sections.all().order_by('order'):
                section_photos = record.photos.filter(
                    template_item__section=section
                ).order_by('template_item__order')

                if section_photos.exists():
                    section_name = section.get_name_by_language(self.language) if hasattr(section, 'get_name_by_language') else section.name_ko
                    story.append(Paragraph(f"• {section_name}", self.styles['KoreanBody']))
                    story.extend(self._create_photo_grid(section_photos))
                    story.append(Spacer(1, 10))
        else:
            # 카테고리 기반 그룹화 (레거시 또는 template_item 미사용)
            from records.models import Photo
            for cat_code, cat_name in Photo.CATEGORY_CHOICES:
                cat_photos = record.photos.filter(category=cat_code)
                if cat_photos.exists():
                    story.append(Paragraph(f"• {cat_name}", self.styles['KoreanBody']))
                    story.extend(self._create_photo_grid(cat_photos))
                    story.append(Spacer(1, 10))

        # 점검 결과 섹션
        story.extend(self._create_inspection_results_section(record))

        # 녹음 기록 섹션
        story.extend(self._create_recordings_section())

        # 생성 정보
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            f"{self.labels['generated_at']}: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            self.styles['KoreanCaption']
        ))

        doc.build(story)

        buffer.seek(0)
        return {
            'content': buffer.getvalue(),
            'filename': f"{report_type.lower()}_report_{self.contract.pk}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        }

    def generate_comparison_report(self, move_in_record, move_out_record):
        """비교 리포트 생성 (Before/After)"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        story = []

        # 제목
        story.append(Paragraph(self.labels['comparison_report_title'], self.styles['KoreanTitle']))
        story.append(Spacer(1, 20))

        # 계약 정보
        story.append(Paragraph(self.labels['contract_info'], self.styles['KoreanHeading']))
        contract_data = [
            [self.labels['address'], self.contract.address],
            [self.labels['tenant'], self.contract.tenant_name or '-'],
            [self.labels['landlord'], self.contract.landlord_name or '-'],
            [self.labels['move_in_date'], str(self.contract.move_in_date) if self.contract.move_in_date else '-'],
            [self.labels['move_out_date'], str(self.contract.move_out_date) if self.contract.move_out_date else '-'],
        ]

        contract_table = Table(contract_data, colWidths=[4*cm, 12*cm])
        contract_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Korean' if 'Korean' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(contract_table)
        story.append(Spacer(1, 20))

        # 비교 섹션
        story.append(Paragraph(self.labels['comparison'], self.styles['KoreanHeading']))

        # 템플릿 기반 또는 카테고리 기반 비교
        template = self.contract.template
        has_template_photos = (
            move_in_record.photos.filter(template_item__isnull=False).exists() or
            move_out_record.photos.filter(template_item__isnull=False).exists()
        )

        if template and has_template_photos:
            for section in template.sections.all().order_by('order'):
                move_in_photos = list(move_in_record.photos.filter(
                    template_item__section=section
                ).order_by('template_item__order'))
                move_out_photos = list(move_out_record.photos.filter(
                    template_item__section=section
                ).order_by('template_item__order'))

                if move_in_photos or move_out_photos:
                    section_name = section.get_name_by_language(self.language) if hasattr(section, 'get_name_by_language') else section.name_ko
                    story.append(Paragraph(f"■ {section_name}", self.styles['KoreanBody']))
                    story.extend(self._create_comparison_grid(move_in_photos, move_out_photos))
                    story.append(Spacer(1, 15))
        else:
            from records.models import Photo
            for cat_code, cat_name in Photo.CATEGORY_CHOICES:
                move_in_photos = list(move_in_record.photos.filter(category=cat_code))
                move_out_photos = list(move_out_record.photos.filter(category=cat_code))

                if move_in_photos or move_out_photos:
                    story.append(Paragraph(f"■ {cat_name}", self.styles['KoreanBody']))
                    story.extend(self._create_comparison_grid(move_in_photos, move_out_photos))
                    story.append(Spacer(1, 15))

        # 생성 정보
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            f"{self.labels['generated_at']}: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            self.styles['KoreanCaption']
        ))

        doc.build(story)

        buffer.seek(0)
        return {
            'content': buffer.getvalue(),
            'filename': f"comparison_report_{self.contract.pk}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        }

    def _create_photo_grid(self, photos, max_width=5*cm, max_height=4*cm):
        """사진 그리드 생성 (사진 + 메모)"""
        elements = []
        font_name = 'Korean' if 'Korean' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
        photos_list = list(photos)

        # 한 줄에 2장씩 (메모 공간 확보)
        for i in range(0, len(photos_list), 2):
            row_photos = photos_list[i:i+2]
            img_row = []
            memo_row = []

            for photo in row_photos:
                # 사진
                try:
                    img_path = photo.image.path
                    if os.path.exists(img_path):
                        img = Image(img_path, width=max_width, height=max_height)
                        img.hAlign = 'CENTER'
                        img_row.append(img)
                    else:
                        img_row.append(Paragraph(self.labels['image_not_found'], self.styles['KoreanCaption']))
                except Exception:
                    img_row.append(Paragraph(self.labels['image_error'], self.styles['KoreanCaption']))

                # 메모
                memo_text = photo.description if photo.description else ''
                if memo_text:
                    memo_row.append(Paragraph(
                        f"<font size=7 color='#555555'>📝 {memo_text}</font>",
                        self.styles['KoreanCaption']
                    ))
                else:
                    memo_row.append('')

            # 빈 셀 채우기
            while len(img_row) < 2:
                img_row.append('')
                memo_row.append('')

            col_width = 8*cm
            table = Table([img_row, memo_row], colWidths=[col_width, col_width])
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                ('ALIGN', (0, 1), (-1, 1), 'LEFT'),
                ('VALIGN', (0, 1), (-1, 1), 'TOP'),
                ('PADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
            ]))
            elements.append(table)

        return elements

    def _create_inspection_results_section(self, record):
        """점검 결과 테이블 생성"""
        elements = []
        font_name = 'Korean' if 'Korean' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'

        responses = record.item_responses.select_related('template_item__section').all()
        if not responses.exists():
            return elements

        elements.append(Spacer(1, 20))
        elements.append(Paragraph(self.labels['inspection_results'], self.styles['KoreanHeading']))

        condition_labels = {
            'NORMAL': self.labels['condition_normal'],
            'DEFECTIVE': self.labels['condition_defective'],
            'AGED': self.labels['condition_aged'],
            'NEEDS_REPAIR': self.labels['condition_needs_repair'],
        }

        condition_colors = {
            'NORMAL': colors.HexColor('#198754'),
            'DEFECTIVE': colors.HexColor('#dc3545'),
            'AGED': colors.HexColor('#0dcaf0'),
            'NEEDS_REPAIR': colors.HexColor('#fd7e14'),
        }

        # Header
        table_data = [[
            self.labels['item_name'],
            self.labels['condition'],
            self.labels['notes'],
        ]]

        for resp in responses:
            item_name = resp.template_item.get_name_by_language(self.language) if hasattr(resp.template_item, 'get_name_by_language') else resp.template_item.name_ko
            condition_text = condition_labels.get(resp.condition_status, resp.condition_status)
            notes_text = resp.notes or '-'

            table_data.append([item_name, condition_text, notes_text])

        table = Table(table_data, colWidths=[6*cm, 3*cm, 7*cm])
        style_cmds = [
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8e8e8')),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]

        # Color-code condition cells
        for i, resp in enumerate(responses, start=1):
            color = condition_colors.get(resp.condition_status)
            if color:
                style_cmds.append(('TEXTCOLOR', (1, i), (1, i), color))

        table.setStyle(TableStyle(style_cmds))
        elements.append(table)

        return elements

    def _create_recordings_section(self):
        """녹음 기록 섹션 생성"""
        elements = []
        font_name = 'Korean' if 'Korean' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'

        recordings = self.contract.recordings.filter(
            processing_status='COMPLETED'
        ).order_by('-recorded_at')

        if not recordings.exists():
            return elements

        elements.append(Spacer(1, 20))
        elements.append(Paragraph(self.labels['recordings'], self.styles['KoreanHeading']))

        for recording in recordings:
            # 녹음 정보 테이블
            title = recording.get_display_title() if hasattr(recording, 'get_display_title') else recording.title
            rec_data = [
                [self.labels['recording_title'], title],
                [self.labels['recording_date'], recording.recorded_at.strftime('%Y-%m-%d %H:%M') if recording.recorded_at else '-'],
                [self.labels['recording_duration'], recording.get_duration_display()],
            ]

            rec_table = Table(rec_data, colWidths=[4*cm, 12*cm])
            rec_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f0ff')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(rec_table)

            # AI 요약
            if recording.summary:
                elements.append(Spacer(1, 5))
                elements.append(Paragraph(
                    f"<b>{self.labels['ai_summary']}</b>",
                    self.styles['KoreanBody']
                ))

                # 요약 내용을 박스 안에 표시
                summary_text = recording.summary.replace('\n', '<br/>')
                summary_style = ParagraphStyle(
                    name=f'Summary_{recording.pk}',
                    parent=self.styles['KoreanBody'],
                    fontSize=9,
                    leading=13,
                    textColor=colors.HexColor('#333333'),
                    leftIndent=10,
                    rightIndent=10,
                )
                summary_para = Paragraph(summary_text, summary_style)

                summary_table = Table([[summary_para]], colWidths=[16*cm])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
                    ('PADDING', (0, 0), (-1, -1), 10),
                ]))
                elements.append(summary_table)

            elements.append(Spacer(1, 15))

        return elements

    def _create_comparison_grid(self, move_in_photos, move_out_photos, max_width=4*cm, max_height=3*cm):
        """비교 사진 그리드 생성 (좌: 입실, 우: 퇴실)"""
        elements = []

        # 헤더
        header = Table(
            [[self.labels['move_in'], self.labels['move_out']]],
            colWidths=[8*cm, 8*cm]
        )
        header.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Korean' if 'Korean' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8e8e8')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(header)

        # 사진 비교 (최대 개수만큼 반복)
        max_count = max(len(move_in_photos), len(move_out_photos))
        for i in range(max_count):
            row_data = []

            # 입실 사진
            if i < len(move_in_photos):
                try:
                    img_path = move_in_photos[i].image.path
                    if os.path.exists(img_path):
                        img = Image(img_path, width=max_width, height=max_height)
                        row_data.append(img)
                    else:
                        row_data.append('')
                except Exception:
                    row_data.append('')
            else:
                row_data.append('')

            # 퇴실 사진
            if i < len(move_out_photos):
                try:
                    img_path = move_out_photos[i].image.path
                    if os.path.exists(img_path):
                        img = Image(img_path, width=max_width, height=max_height)
                        row_data.append(img)
                    else:
                        row_data.append('')
                except Exception:
                    row_data.append('')
            else:
                row_data.append('')

            table = Table([row_data], colWidths=[8*cm, 8*cm])
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('PADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(table)

        return elements
