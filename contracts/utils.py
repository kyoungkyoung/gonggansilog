"""계약서 파일 처리 유틸리티"""
import io
import os
from PIL import Image, ImageDraw
import fitz  # PyMuPDF


# 표준 이미지 크기 (A4 비율: 1:1.414)
STANDARD_WIDTH = 1920
STANDARD_HEIGHT = 2716  # 1920 * 1.414


def standardize_image(image):
    """
    이미지를 표준 크기(A4 비율, 1920x2716)로 변환

    - 이미지를 비율 유지하며 축소
    - 흰색 배경의 A4 캔버스 중앙에 배치

    Args:
        image: PIL Image 객체

    Returns:
        표준화된 PIL Image 객체 (1920x2716, RGB)
    """
    # RGB로 변환 (투명 배경 처리)
    if image.mode in ('RGBA', 'P'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')

    orig_width, orig_height = image.size

    # 비율 계산 (캔버스에 맞게 축소)
    width_ratio = STANDARD_WIDTH / orig_width
    height_ratio = STANDARD_HEIGHT / orig_height
    ratio = min(width_ratio, height_ratio)

    # 새 크기 계산
    new_width = int(orig_width * ratio)
    new_height = int(orig_height * ratio)

    # 이미지 리사이즈 (고품질)
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # 흰색 배경 캔버스 생성
    canvas = Image.new('RGB', (STANDARD_WIDTH, STANDARD_HEIGHT), (255, 255, 255))

    # 중앙에 배치
    x = (STANDARD_WIDTH - new_width) // 2
    y = (STANDARD_HEIGHT - new_height) // 2
    canvas.paste(resized, (x, y))

    return canvas


def is_pdf(file_path):
    """PDF 파일인지 확인"""
    return file_path.lower().endswith('.pdf')


def is_image(file_path):
    """이미지 파일인지 확인"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    return any(file_path.lower().endswith(ext) for ext in image_extensions)


def pdf_to_images(pdf_path):
    """PDF를 이미지 리스트로 변환"""
    doc = fitz.open(pdf_path)
    images = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        # 높은 해상도로 렌더링 (300 DPI)
        pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        images.append(img)

    doc.close()
    return images


def apply_masking_to_image(image, mask_areas):
    """
    이미지에 마스킹 영역 적용

    Args:
        image: PIL Image 객체
        mask_areas: 마스킹 영역 리스트 [{'x': x1, 'y': y1, 'width': w, 'height': h}, ...]

    Returns:
        마스킹된 PIL Image 객체
    """
    # 이미지 복사
    masked_img = image.copy()
    draw = ImageDraw.Draw(masked_img)

    # 각 마스킹 영역에 검은색 박스 그리기
    for area in mask_areas:
        x = area['x']
        y = area['y']
        width = area['width']
        height = area['height']

        # 검은색 사각형 그리기
        draw.rectangle(
            [x, y, x + width, y + height],
            fill='black'
        )

    return masked_img


def images_to_pdf(images, output_path):
    """이미지 리스트를 PDF로 변환"""
    if not images:
        return

    # 첫 번째 이미지를 기준으로 PDF 생성
    first_image = images[0].convert('RGB')
    other_images = [img.convert('RGB') for img in images[1:]]

    first_image.save(
        output_path,
        'PDF',
        save_all=True,
        append_images=other_images,
        resolution=100.0
    )


def process_masked_file(file_path, mask_areas, output_path, standardize=True):
    """
    파일에 마스킹을 적용하고 저장

    Args:
        file_path: 원본 파일 경로
        mask_areas: 마스킹 영역 리스트
        output_path: 출력 파일 경로
        standardize: 표준 크기(1920x2716, A4비율)로 변환 여부 (기본값: True)

    Returns:
        처리 성공 여부
    """
    try:
        if is_pdf(file_path):
            # PDF 처리
            images = pdf_to_images(file_path)

            # 모든 페이지에 마스킹 적용 (현재는 첫 페이지만)
            # TODO: 페이지별 마스킹 영역 구분 필요
            if mask_areas and len(images) > 0:
                images[0] = apply_masking_to_image(images[0], mask_areas)

            # 표준 크기로 변환
            if standardize:
                images = [standardize_image(img) for img in images]

            # 다시 PDF로 저장
            images_to_pdf(images, output_path)

        elif is_image(file_path):
            # 이미지 처리
            img = Image.open(file_path)

            # 마스킹 적용
            if mask_areas:
                img = apply_masking_to_image(img, mask_areas)

            # 표준 크기로 변환
            if standardize:
                img = standardize_image(img)

            # 저장 (JPEG로 저장하여 용량 최적화)
            if output_path.lower().endswith(('.jpg', '.jpeg')):
                img.save(output_path, 'JPEG', quality=90, optimize=True)
            else:
                img.save(output_path)

        else:
            return False

        return True

    except Exception as e:
        print(f"파일 처리 중 오류 발생: {e}")
        return False


def process_uploaded_image(uploaded_file, output_path):
    """
    업로드된 이미지 파일을 표준 크기로 변환하여 저장

    Args:
        uploaded_file: Django UploadedFile 객체 또는 파일 경로
        output_path: 출력 파일 경로

    Returns:
        처리 성공 여부
    """
    try:
        # 파일 열기
        if hasattr(uploaded_file, 'read'):
            img = Image.open(uploaded_file)
        else:
            img = Image.open(uploaded_file)

        # 표준 크기로 변환
        img = standardize_image(img)

        # 저장 (JPEG로 저장하여 용량 최적화)
        if output_path.lower().endswith(('.jpg', '.jpeg')):
            img.save(output_path, 'JPEG', quality=90, optimize=True)
        else:
            img.save(output_path)

        return True

    except Exception as e:
        print(f"이미지 처리 중 오류 발생: {e}")
        return False


def get_file_preview_data(file_path):
    """
    파일을 미리보기용 이미지 데이터로 변환

    Returns:
        {
            'type': 'pdf' or 'image',
            'pages': [base64_image_data, ...],
            'width': int,
            'height': int
        }
    """
    import base64

    result = {
        'type': '',
        'pages': [],
        'width': 0,
        'height': 0
    }

    try:
        if is_pdf(file_path):
            result['type'] = 'pdf'
            images = pdf_to_images(file_path)

            for img in images:
                # 이미지를 base64로 인코딩
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                img_data = base64.b64encode(buffer.getvalue()).decode()
                result['pages'].append(img_data)

            if images:
                result['width'] = images[0].width
                result['height'] = images[0].height

        elif is_image(file_path):
            result['type'] = 'image'
            img = Image.open(file_path)

            # 이미지를 base64로 인코딩
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_data = base64.b64encode(buffer.getvalue()).decode()
            result['pages'].append(img_data)
            result['width'] = img.width
            result['height'] = img.height

    except Exception as e:
        print(f"파일 미리보기 생성 중 오류: {e}")

    return result
