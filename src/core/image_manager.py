"""
이미지 처리 통합 모듈
더미 이미지 생성, 실제 이미지 검색, 이미지 최적화 등을 담당
"""

import os
import uuid
import hashlib
import logging
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from enum import Enum
import requests
from PIL import Image, ImageDraw, ImageFont
import io
from urllib.parse import quote

from .base_poster import ContentError, PlatformType


class ImageSource(Enum):
    """이미지 소스 타입"""
    DUMMY = "dummy"
    WEB_SEARCH = "web_search"
    LOCAL = "local"
    URL = "url"


@dataclass
class ImageRequest:
    """이미지 요청 데이터"""
    caption: str  # 이미지 캡션/키워드
    width: int = 800  # 이미지 너비
    height: int = 600  # 이미지 높이
    source_type: ImageSource = ImageSource.DUMMY
    platform: Optional[PlatformType] = None


@dataclass
class ProcessedImage:
    """처리된 이미지 데이터"""
    file_path: str  # 로컬 파일 경로
    original_url: Optional[str] = None  # 원본 URL (있을 경우)
    caption: str = ""  # 이미지 캡션
    width: int = 0  # 실제 이미지 너비
    height: int = 0  # 실제 이미지 높이
    file_size: int = 0  # 파일 크기 (바이트)


class ImageManager:
    """이미지 처리 통합 관리자"""

    def __init__(self, storage_path: str = "./images", max_file_size: int = 2 * 1024 * 1024):
        """
        Args:
            storage_path: 이미지 저장 디렉토리
            max_file_size: 최대 파일 크기 (바이트, 기본 2MB)
        """
        self.storage_path = storage_path
        self.max_file_size = max_file_size
        self.logger = logging.getLogger(__name__)

        # 저장 디렉토리 생성
        os.makedirs(storage_path, exist_ok=True)

        # 플랫폼별 이미지 크기 권장사항
        self.platform_sizes = {
            PlatformType.NAVER: (800, 600),
            PlatformType.TISTORY: (700, 500)
        }

    def process_images(self, requests: List[ImageRequest]) -> List[ProcessedImage]:
        """이미지 요청 목록을 처리하여 로컬 이미지 파일 생성"""
        processed_images = []

        for request in requests:
            try:
                processed_image = self._process_single_image(request)
                if processed_image:
                    processed_images.append(processed_image)
                    self.logger.info(f"이미지 처리 완료: {request.caption}")
            except Exception as e:
                self.logger.error(f"이미지 처리 실패: {request.caption}, {e}")
                # 실패 시 기본 더미 이미지 생성 시도
                try:
                    dummy_request = ImageRequest(
                        caption=request.caption,
                        width=request.width,
                        height=request.height,
                        source_type=ImageSource.DUMMY,
                        platform=request.platform
                    )
                    dummy_image = self._create_dummy_image(dummy_request)
                    if dummy_image:
                        processed_images.append(dummy_image)
                except Exception as fallback_error:
                    self.logger.error(f"더미 이미지 생성도 실패: {fallback_error}")

        return processed_images

    def _process_single_image(self, request: ImageRequest) -> Optional[ProcessedImage]:
        """단일 이미지 요청 처리"""
        if request.source_type == ImageSource.DUMMY:
            return self._create_dummy_image(request)
        elif request.source_type == ImageSource.WEB_SEARCH:
            return self._search_and_download_image(request)
        elif request.source_type == ImageSource.URL:
            return self._download_from_url(request)
        elif request.source_type == ImageSource.LOCAL:
            return self._process_local_image(request)
        else:
            raise ContentError(f"지원하지 않는 이미지 소스: {request.source_type}")

    def _create_dummy_image(self, request: ImageRequest) -> ProcessedImage:
        """더미 이미지 생성"""
        try:
            # 플랫폼별 권장 크기 적용
            if request.platform and request.platform in self.platform_sizes:
                width, height = self.platform_sizes[request.platform]
            else:
                width, height = request.width, request.height

            # 이미지 생성
            image = Image.new('RGB', (width, height), color='#f0f0f0')
            draw = ImageDraw.Draw(image)

            # 캡션을 기반으로 색상 생성 (해시 기반)
            caption_hash = hashlib.md5(request.caption.encode()).hexdigest()
            bg_color = f"#{caption_hash[:6]}"

            try:
                # 배경색 적용
                overlay = Image.new('RGB', (width, height), color=bg_color)
                image = Image.blend(image, overlay, 0.3)
                draw = ImageDraw.Draw(image)
            except:
                # 색상 변환 실패 시 기본 색상 사용
                pass

            # 텍스트 추가
            try:
                # 시스템에 설치된 폰트 사용 시도
                font_size = min(width, height) // 20
                font = ImageFont.load_default()

                # 텍스트를 여러 줄로 나누기
                words = request.caption.split()
                lines = []
                current_line = ""

                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    # 간단한 길이 체크 (정확하지 않지만 기본 동작)
                    if len(test_line) * (font_size * 0.6) < width * 0.8:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                            current_line = word
                        else:
                            lines.append(word)

                if current_line:
                    lines.append(current_line)

                # 텍스트 중앙 정렬
                total_height = len(lines) * font_size * 1.2
                start_y = (height - total_height) // 2

                for i, line in enumerate(lines):
                    text_width = len(line) * (font_size * 0.6)  # 대략적 계산
                    text_x = (width - text_width) // 2
                    text_y = start_y + i * font_size * 1.2

                    # 텍스트 그리기 (그림자 효과)
                    draw.text((text_x + 2, text_y + 2), line, fill='#333333', font=font)
                    draw.text((text_x, text_y), line, fill='#ffffff', font=font)

            except Exception as e:
                self.logger.warning(f"텍스트 렌더링 실패: {e}")
                # 기본 텍스트 그리기
                draw.text((50, height//2), request.caption[:20], fill='#333333')

            # 파일 저장
            file_name = f"dummy_{uuid.uuid4().hex[:8]}_{caption_hash[:8]}.jpg"
            file_path = os.path.join(self.storage_path, file_name)

            image.save(file_path, 'JPEG', quality=85, optimize=True)

            # 파일 정보 수집
            file_size = os.path.getsize(file_path)

            return ProcessedImage(
                file_path=file_path,
                caption=request.caption,
                width=width,
                height=height,
                file_size=file_size
            )

        except Exception as e:
            self.logger.error(f"더미 이미지 생성 실패: {e}")
            raise ContentError(f"더미 이미지 생성 실패: {e}")

    def _search_and_download_image(self, request: ImageRequest) -> Optional[ProcessedImage]:
        """웹에서 이미지 검색 및 다운로드 (향후 구현 예정)"""
        self.logger.info(f"웹 이미지 검색 기능은 향후 구현 예정: {request.caption}")

        # 현재는 더미 이미지로 대체
        dummy_request = ImageRequest(
            caption=f"[검색예정] {request.caption}",
            width=request.width,
            height=request.height,
            source_type=ImageSource.DUMMY,
            platform=request.platform
        )
        return self._create_dummy_image(dummy_request)

    def _download_from_url(self, request: ImageRequest) -> Optional[ProcessedImage]:
        """URL에서 이미지 다운로드"""
        # 이 기능은 request.caption을 URL로 간주
        url = request.caption

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10, stream=True)
            response.raise_for_status()

            # 파일 크기 체크
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.max_file_size:
                raise ContentError(f"파일 크기가 너무 큽니다: {content_length} bytes")

            # 이미지 다운로드 및 검증
            image_data = response.content
            if len(image_data) > self.max_file_size:
                raise ContentError(f"다운로드된 파일이 너무 큽니다: {len(image_data)} bytes")

            # PIL로 이미지 유효성 검증
            image = Image.open(io.BytesIO(image_data))

            # 필요시 크기 조정
            if request.platform and request.platform in self.platform_sizes:
                target_width, target_height = self.platform_sizes[request.platform]
                if image.width > target_width or image.height > target_height:
                    image.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)

            # 파일 저장
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            file_extension = self._get_image_extension(image.format)
            file_name = f"downloaded_{url_hash}{file_extension}"
            file_path = os.path.join(self.storage_path, file_name)

            image.save(file_path, optimize=True, quality=85)
            file_size = os.path.getsize(file_path)

            return ProcessedImage(
                file_path=file_path,
                original_url=url,
                caption=f"Downloaded from URL",
                width=image.width,
                height=image.height,
                file_size=file_size
            )

        except Exception as e:
            self.logger.error(f"URL 이미지 다운로드 실패: {url}, {e}")
            raise ContentError(f"URL 이미지 다운로드 실패: {e}")

    def _process_local_image(self, request: ImageRequest) -> Optional[ProcessedImage]:
        """로컬 이미지 파일 처리"""
        local_path = request.caption  # caption을 로컬 파일 경로로 사용

        try:
            if not os.path.exists(local_path):
                raise ContentError(f"로컬 이미지 파일을 찾을 수 없습니다: {local_path}")

            # 이미지 열기 및 검증
            image = Image.open(local_path)

            # 파일을 저장 디렉토리로 복사 (최적화와 함께)
            file_name = f"local_{uuid.uuid4().hex[:8]}{self._get_image_extension(image.format)}"
            file_path = os.path.join(self.storage_path, file_name)

            # 필요시 크기 조정
            if request.platform and request.platform in self.platform_sizes:
                target_width, target_height = self.platform_sizes[request.platform]
                if image.width > target_width or image.height > target_height:
                    image.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)

            image.save(file_path, optimize=True, quality=85)
            file_size = os.path.getsize(file_path)

            return ProcessedImage(
                file_path=file_path,
                caption=os.path.basename(local_path),
                width=image.width,
                height=image.height,
                file_size=file_size
            )

        except Exception as e:
            self.logger.error(f"로컬 이미지 처리 실패: {local_path}, {e}")
            raise ContentError(f"로컬 이미지 처리 실패: {e}")

    def _get_image_extension(self, image_format: str) -> str:
        """이미지 포맷에 따른 확장자 반환"""
        format_map = {
            'JPEG': '.jpg',
            'JPG': '.jpg',
            'PNG': '.png',
            'GIF': '.gif',
            'BMP': '.bmp',
            'WEBP': '.webp'
        }
        return format_map.get(image_format, '.jpg')

    def optimize_image(self, image_path: str, target_size_kb: int = 500) -> str:
        """이미지 최적화 (파일 크기 줄이기)"""
        try:
            image = Image.open(image_path)

            # 다양한 품질로 시도
            for quality in [85, 75, 65, 55, 45]:
                output_buffer = io.BytesIO()
                image.save(output_buffer, format='JPEG', quality=quality, optimize=True)

                if output_buffer.tell() <= target_size_kb * 1024:
                    # 목표 크기 달성
                    optimized_path = image_path.replace('.', f'_optimized.')
                    with open(optimized_path, 'wb') as f:
                        f.write(output_buffer.getvalue())

                    self.logger.info(f"이미지 최적화 완료: {quality}% 품질")
                    return optimized_path

            # 목표 크기를 달성하지 못한 경우 원본 반환
            self.logger.warning(f"목표 크기 달성 실패: {image_path}")
            return image_path

        except Exception as e:
            self.logger.error(f"이미지 최적화 실패: {e}")
            return image_path

    def cleanup_old_images(self, max_age_days: int = 7) -> int:
        """오래된 이미지 파일 정리"""
        try:
            import time
            current_time = time.time()
            deleted_count = 0

            for filename in os.listdir(self.storage_path):
                file_path = os.path.join(self.storage_path, filename)

                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_days * 24 * 3600:  # 초 단위로 변환
                        os.remove(file_path)
                        deleted_count += 1
                        self.logger.info(f"오래된 이미지 파일 삭제: {filename}")

            return deleted_count

        except Exception as e:
            self.logger.error(f"이미지 정리 실패: {e}")
            return 0

    def get_storage_info(self) -> Dict[str, int]:
        """저장소 정보 반환"""
        try:
            total_files = 0
            total_size = 0

            for filename in os.listdir(self.storage_path):
                file_path = os.path.join(self.storage_path, filename)
                if os.path.isfile(file_path):
                    total_files += 1
                    total_size += os.path.getsize(file_path)

            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }

        except Exception as e:
            self.logger.error(f"저장소 정보 수집 실패: {e}")
            return {'total_files': 0, 'total_size_bytes': 0, 'total_size_mb': 0}