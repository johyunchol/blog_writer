"""
블로그 포스팅을 위한 기본 추상 클래스
네이버, 티스토리 등 다양한 플랫폼에서 상속받아 사용
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


class PlatformType(Enum):
    """지원하는 블로그 플랫폼 타입"""
    NAVER = "naver"
    TISTORY = "tistory"


@dataclass
class BlogPost:
    """블로그 포스트 데이터 구조"""
    title: str
    content: str
    tags: List[str]
    category: Optional[str] = None
    images: Optional[List[str]] = None  # 이미지 파일 경로 리스트
    visibility: str = "public"  # public, private, protected
    scheduled_time: Optional[str] = None


@dataclass
class PostingResult:
    """포스팅 결과 데이터 구조"""
    success: bool
    message: str
    post_url: Optional[str] = None
    post_id: Optional[str] = None
    error_code: Optional[str] = None


class BlogPosterError(Exception):
    """블로그 포스터 관련 기본 예외"""
    pass


class LoginError(BlogPosterError):
    """로그인 관련 예외"""
    pass


class PostingError(BlogPosterError):
    """포스팅 관련 예외"""
    pass


class ContentError(BlogPosterError):
    """콘텐츠 관련 예외"""
    pass


class AbstractPoster(ABC):
    """블로그 포스팅을 위한 추상 기본 클래스"""

    def __init__(self, username: str, password: str, headless: bool = True):
        """
        Args:
            username: 로그인 사용자명
            password: 로그인 비밀번호
            headless: 헤드리스 모드 여부
        """
        self.username = username
        self.password = password
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.logger = logging.getLogger(self.__class__.__name__)

        # 플랫폼별 설정
        self.platform_type = self._get_platform_type()
        self.login_url = self._get_login_url()
        self.post_create_url = self._get_post_create_url()

    @abstractmethod
    def _get_platform_type(self) -> PlatformType:
        """플랫폼 타입 반환"""
        pass

    @abstractmethod
    def _get_login_url(self) -> str:
        """로그인 URL 반환"""
        pass

    @abstractmethod
    def _get_post_create_url(self) -> str:
        """포스트 작성 URL 반환"""
        pass

    def init_driver(self) -> None:
        """웹드라이버 초기화"""
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        try:
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 10)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.logger.info("웹드라이버 초기화 완료")
        except Exception as e:
            raise BlogPosterError(f"웹드라이버 초기화 실패: {e}")

    def quit_driver(self) -> None:
        """웹드라이버 종료"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("웹드라이버 종료 완료")
            except Exception as e:
                self.logger.warning(f"웹드라이버 종료 중 오류: {e}")
            finally:
                self.driver = None
                self.wait = None

    @abstractmethod
    def login(self) -> bool:
        """플랫폼별 로그인 구현"""
        pass

    @abstractmethod
    def create_post(self, post: BlogPost) -> PostingResult:
        """플랫폼별 포스트 작성 구현"""
        pass

    @abstractmethod
    def upload_image(self, image_path: str) -> bool:
        """플랫폼별 이미지 업로드 구현"""
        pass

    @abstractmethod
    def publish_post(self) -> PostingResult:
        """플랫폼별 포스트 발행 구현"""
        pass

    def post_article(self, post: BlogPost) -> PostingResult:
        """전체 포스팅 프로세스 실행"""
        try:
            # 1. 웹드라이버 초기화
            self.init_driver()

            # 2. 로그인
            if not self.login():
                return PostingResult(
                    success=False,
                    message="로그인 실패",
                    error_code="LOGIN_FAILED"
                )

            # 3. 포스트 작성
            result = self.create_post(post)
            if not result.success:
                return result

            # 4. 포스트 발행
            return self.publish_post()

        except Exception as e:
            self.logger.error(f"포스팅 프로세스 실행 중 오류: {e}")
            return PostingResult(
                success=False,
                message=f"포스팅 실패: {str(e)}",
                error_code="POSTING_FAILED"
            )
        finally:
            # 5. 리소스 정리
            self.quit_driver()

    def _wait_for_element(self, by: By, value: str, timeout: int = 10):
        """요소 대기 헬퍼 메서드"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.presence_of_element_located((by, value)))
        except TimeoutException:
            raise BlogPosterError(f"요소를 찾을 수 없습니다: {value}")

    def _wait_for_clickable(self, by: By, value: str, timeout: int = 10):
        """클릭 가능한 요소 대기 헬퍼 메서드"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.element_to_be_clickable((by, value)))
        except TimeoutException:
            raise BlogPosterError(f"클릭 가능한 요소를 찾을 수 없습니다: {value}")

    def _safe_click(self, element) -> bool:
        """안전한 클릭 헬퍼 메서드"""
        try:
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except Exception as e:
            self.logger.warning(f"클릭 실패: {e}")
            return False

    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.quit_driver()