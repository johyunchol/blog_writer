# domain.py
from dataclasses import dataclass
from typing import Literal, List, Optional

# --- Custom Exceptions ---

class NaverBloggerException(Exception):
    """이 애플리케이션의 최상위 예외 클래스"""
    pass

class ConfigError(NaverBloggerException):
    """설정 파일 관련 오류"""
    pass

class ContentGenerationError(NaverBloggerException):
    """콘텐츠 생성 실패 관련 오류"""
    pass

class ImageGenerationError(NaverBloggerException):
    """이미지 생성 실패 관련 오류"""
    pass

class WebDriverError(NaverBloggerException):
    """웹 드라이버 설정 관련 오류"""
    pass

class LoginError(NaverBloggerException):
    """로그인 실패 관련 오류"""
    pass

class PostingError(NaverBloggerException):
    """포스팅 실패 관련 오류"""
    pass


# --- Domain Models ---

@dataclass(frozen=True)
class PostContent:
    """포스팅될 콘텐츠 조각을 나타내는 데이터 클래스"""
    type: Literal["text", "image"]
    data: str  # 텍스트 내용 또는 이미지 파일 경로

@dataclass(frozen=True)
class GeneratedBody:
    """생성된 포스트의 body 부분을 나타내는 데이터 클래스"""
    text: str
    image_caption: Optional[str]


@dataclass(frozen=True)
class GeneratedContent:
    """생성된 포스트 전체 콘텐츠를 나타내는 데이터 클래스"""
    title: str
    body: List[GeneratedBody]
    tags: List[str]
