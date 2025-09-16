# interfaces.py
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional

from domain import PostContent, GeneratedContent


class ContentGeneratorInterface(ABC):
    """콘텐츠 생성에 대한 인터페이스"""

    @abstractmethod
    def generate(self, topic: str) -> GeneratedContent:
        """주제를 기반으로 콘텐츠 데이터 객체를 생성합니다."""
        pass


class ImageGeneratorInterface(ABC):
    """이미지 생성에 대한 인터페이스"""

    @abstractmethod
    def generate(self, caption: str, save_path: str) -> str:
        """캡션을 기반으로 이미지를 생성하고 저장된 경로를 반환합니다."""
        pass


class PosterInterface(ABC):
    """블로그 포스팅에 대한 인터페이스"""

    @abstractmethod
    def initialize(self) -> None:
        """포스팅을 위한 리소스를 초기화합니다. (예: 웹 드라이버)"""
        pass

    @abstractmethod
    def login(self) -> None:
        """블로그에 로그인합니다."""
        pass

    @abstractmethod
    def post(self, content_list: List[PostContent], title: str) -> str:
        """주어진 콘텐츠 리스트와 제목으로 포스팅을 수행하고 결과 URL을 반환합니다."""
        pass

    @abstractmethod
    def close(self) -> None:
        """사용한 리소스를 정리합니다."""
        pass
