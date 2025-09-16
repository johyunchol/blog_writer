"""
티스토리 블로그 자동 포스팅 모듈
기존 real_estate_posting.py 코드를 새로운 아키텍처에 맞게 리팩토링
"""

import re
import time
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import requests
import os

from ..core.base_poster import (
    AbstractPoster,
    BlogPost,
    PostingResult,
    PlatformType,
    LoginError,
    PostingError,
    ContentError
)
from ..tistory.real_estate_posting import convert_to_tistory_html


class TistoryPoster(AbstractPoster):
    """티스토리 블로그 포스터"""

    def __init__(self, username: str, password: str, blog_name: str,
                 headless: bool = True, category_id: int = 1532685):
        """
        Args:
            username: 카카오 로그인 아이디 (이메일)
            password: 카카오 로그인 비밀번호
            blog_name: 티스토리 블로그 이름 (subdomain)
            headless: 헤드리스 모드 여부
            category_id: 기본 카테고리 ID
        """
        super().__init__(username, password, headless)
        self.blog_name = blog_name
        self.category_id = category_id
        self.cookies_str: Optional[str] = None

    def _get_platform_type(self) -> PlatformType:
        """플랫폼 타입 반환"""
        return PlatformType.TISTORY

    def _get_login_url(self) -> str:
        """로그인 URL 반환"""
        return ("https://accounts.kakao.com/login/"
                "?continue=https%3A%2F%2Fkauth.kakao.com%2Foauth%2Fauthorize"
                "%3Fclient_id%3D3e6ddd834b023f24221217e370daed18"
                "%26state%3DaHR0cHM6Ly9ra2Vuc3UudGlzdG9yeS5jb20vbWFuYWdlL25ld3Bvc3Qv"
                "%26prompt%3Dselect_account"
                "%26redirect_uri%3Dhttps%253A%252F%252Fwww.tistory.com%252Fauth%252Fkakao%252Fredirect"
                "%26response_type%3Dcode"
                "%26auth_tran_id%3Ddvy6kpj4uxg3e6ddd834b023f24221217e370daed18meh80vuu"
                "%26ka%3Dsdk%252F1.43.6%2520os%252Fjavascript%2520sdk_type%252Fjavascript"
                "%2520lang%252Fko-KR%2520device%252FMacIntel%2520origin%252Fhttps"
                "%25253A%25252F%25252Fwww.tistory.com"
                "%26is_popup%3Dfalse%26through_account%3Dtrue#login")

    def _get_post_create_url(self) -> str:
        """포스트 작성 URL 반환"""
        return f"https://{self.blog_name}.tistory.com/manage/newpost/"

    def login(self) -> bool:
        """카카오 계정으로 티스토리 로그인"""
        try:
            self.logger.info("티스토리 로그인을 시작합니다...")

            # 로그인 페이지로 이동
            self.driver.get(self.login_url)

            # 로그인 폼 요소 대기
            username_field = self._wait_for_element(By.CSS_SELECTOR, "input[name='loginId']")
            password_field = self._wait_for_element(By.CSS_SELECTOR, "input[name='password']")

            # 로그인 정보 입력
            username_field.clear()
            username_field.send_keys(self.username)

            password_field.clear()
            password_field.send_keys(self.password)

            # 로그인 버튼 클릭
            login_button = self._wait_for_clickable(By.CSS_SELECTOR, "button[type='submit']")
            self._safe_click(login_button)

            # 로그인 완료 확인 (관리 페이지로 리다이렉트)
            self.wait.until(EC.url_contains("tistory.com/manage"))

            # 쿠키 문자열 생성
            cookies = self.driver.get_cookies()
            self.cookies_str = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])

            self.logger.info("티스토리 로그인 성공!")
            return True

        except TimeoutException:
            self.logger.error("로그인 시간 초과")
            # 오류 스크린샷 저장
            self._save_error_screenshot("login_timeout")
            raise LoginError("로그인 시간 초과")
        except Exception as e:
            self.logger.error(f"로그인 실패: {e}")
            self._save_error_screenshot("login_error")
            raise LoginError(f"로그인 실패: {e}")

    def create_post(self, post: BlogPost) -> PostingResult:
        """포스트 작성"""
        try:
            if not self.cookies_str:
                raise PostingError("로그인이 되어있지 않습니다")

            self.logger.info(f"포스트 작성 시작: {post.title}")

            # 콘텐츠 전처리
            processed_content = self._preprocess_content(post.content)

            # 제목과 태그 추출
            title, tags, body = self._parse_content(processed_content, post.tags)

            # 티스토리 API 호출
            result = self._post_via_api(title, body, tags, post.category or str(self.category_id))

            if result.success:
                self.logger.info(f"포스트 작성 성공: {title}")
            else:
                self.logger.error(f"포스트 작성 실패: {result.message}")

            return result

        except Exception as e:
            self.logger.error(f"포스트 작성 중 오류: {e}")
            return PostingResult(
                success=False,
                message=f"포스트 작성 실패: {str(e)}",
                error_code="CREATE_POST_FAILED"
            )

    def upload_image(self, image_path: str) -> bool:
        """이미지 업로드 (현재 API 방식에서는 직접 업로드 불필요)"""
        # 티스토리 API는 이미지를 별도로 업로드하지 않고
        # HTML 내에서 외부 URL 참조 방식 사용
        self.logger.info(f"티스토리는 HTML 내 이미지 참조 방식 사용: {image_path}")
        return True

    def publish_post(self) -> PostingResult:
        """포스트 발행 (create_post에서 직접 발행되므로 여기서는 성공 반환)"""
        return PostingResult(
            success=True,
            message="포스트 발행 완료"
        )

    def _preprocess_content(self, content: str) -> str:
        """콘텐츠 전처리"""
        # HTML 코드 블록 제거
        if content.strip().startswith("```html"):
            content = content.strip()[7:].strip()
        if content.strip().endswith("```"):
            content = content.strip()[:-3].strip()

        # body 태그 제거
        content = content.replace("<body>", "").replace("</body>", "").strip()

        return content

    def _parse_content(self, content: str, fallback_tags: list = None) -> tuple:
        """콘텐츠에서 제목, 태그, 본문 추출"""
        lines = content.split('\n')

        # 제목 추출 (첫 번째 # 라인)
        title = ""
        for line in lines:
            if line.strip().startswith('# '):
                title = line.strip()[2:].strip()
                # HTML 태그 제거
                title = re.sub(r'<[^>]+>', '', title).strip()
                break

        if not title:
            title = "자동 생성된 블로그 포스트"

        # 태그 추출 (뒤에서부터 검색)
        extracted_tags = []
        post_body_lines = []
        tag_found = False

        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if not tag_found and '태그::' in line:
                # HTML 태그 제거 후 태그 추출
                cleaned_line = re.sub(r'<[^>]+>', '', line)
                tag_string = cleaned_line.split('::', 1)[-1]
                tags = [tag.strip() for tag in tag_string.split(',') if tag.strip()]
                extracted_tags.extend(tags)
                tag_found = True
            else:
                post_body_lines.insert(0, lines[i])

        # 태그가 없으면 fallback 사용
        if not extracted_tags and fallback_tags:
            extracted_tags = fallback_tags

        # 본문 재구성
        body = '\n'.join(post_body_lines).strip()

        return title, extracted_tags, body

    def _post_via_api(self, title: str, content: str, tags: list, category: str) -> PostingResult:
        """티스토리 API를 통한 포스팅"""
        try:
            # requests 세션 생성
            session = requests.Session()

            # 쿠키 설정
            for cookie_pair in self.cookies_str.split(';'):
                if '=' in cookie_pair:
                    name, value = cookie_pair.split('=', 1)
                    session.cookies.set(name.strip(), value.strip())

            # API URL
            api_url = f"https://{self.blog_name}.tistory.com/manage/post.json"

            # HTML 콘텐츠 변환
            html_content = self._convert_to_tistory_html(content)

            # 제목에서 BMP 문자 제거
            clean_title = self._remove_non_bmp_chars(title)

            # 태그 문자열
            tag_string = ','.join(tags) if tags else ""

            # 요청 페이로드
            payload = {
                "id": "0",
                "title": clean_title,
                "content": html_content,
                "slogan": "",
                "visibility": 20,  # 공개
                "category": int(category) if category.isdigit() else self.category_id,
                "tag": tag_string,
                "published": 1,  # 발행
                "password": "",
                "uselessMarginForEntry": 1,
                "daumLike": "105",
                "cclCommercial": 0,
                "cclDerive": 0,
                "thumbnail": "",
                "type": "post",
                "attachments": [],
                "recaptchaValue": "",
                "draftSequence": None
            }

            # 요청 헤더
            headers = {
                "Host": f"{self.blog_name}.tistory.com",
                "Cookie": self.cookies_str,
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json;charset=UTF-8",
                "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/127.0.6533.100 Safari/537.36"),
                "Origin": f"https://{self.blog_name}.tistory.com",
                "Referer": f"https://{self.blog_name}.tistory.com/manage/newpost/"
            }

            # API 호출
            self.logger.info("티스토리 API 호출 중...")
            response = session.post(api_url, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                response_data = response.json()
                self.logger.info(f"API 응답: {response_data}")

                # 포스트 URL 추출 시도
                post_url = None
                if 'url' in response_data:
                    post_url = response_data['url']
                elif 'postId' in response_data:
                    post_url = f"https://{self.blog_name}.tistory.com/{response_data['postId']}"

                return PostingResult(
                    success=True,
                    message="포스팅 성공",
                    post_url=post_url,
                    post_id=str(response_data.get('postId', ''))
                )
            else:
                error_msg = f"API 호출 실패: 상태코드 {response.status_code}, 응답: {response.text}"
                self.logger.error(error_msg)
                return PostingResult(
                    success=False,
                    message=error_msg,
                    error_code=f"API_ERROR_{response.status_code}"
                )

        except requests.exceptions.Timeout:
            error_msg = "API 요청 시간 초과"
            self.logger.error(error_msg)
            return PostingResult(success=False, message=error_msg, error_code="TIMEOUT")
        except Exception as e:
            error_msg = f"API 호출 중 오류: {e}"
            self.logger.error(error_msg)
            return PostingResult(success=False, message=error_msg, error_code="API_EXCEPTION")

    def _convert_to_tistory_html(self, content: str) -> str:
        """콘텐츠를 티스토리 HTML 형식으로 변환"""
        # 기존 convert_to_tistory_html 함수 사용 또는 간단한 변환
        html_lines = []
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                html_lines.append('<p data-ke-size="size16"><br data-mce-bogus="1"></p>')
            else:
                html_lines.append(f'<p data-ke-size="size16">{line}</p>')

        return '\n'.join(html_lines)

    def _remove_non_bmp_chars(self, text: str) -> str:
        """BMP 범위를 벗어나는 문자 제거"""
        return "".join(c for c in text if c <= '\uFFFF')

    def _save_error_screenshot(self, error_type: str) -> None:
        """오류 발생 시 스크린샷 저장"""
        try:
            if self.driver:
                screenshot_path = f"tistory_error_{error_type}.png"
                self.driver.save_screenshot(screenshot_path)
                self.logger.info(f"오류 스크린샷 저장: {screenshot_path}")
        except Exception as e:
            self.logger.warning(f"스크린샷 저장 실패: {e}")

    def get_post_stats(self) -> dict:
        """포스트 통계 조회 (향후 구현)"""
        return {
            "total_posts": 0,
            "recent_views": 0,
            "comments": 0
        }

    def delete_post(self, post_id: str) -> bool:
        """포스트 삭제 (향후 구현)"""
        self.logger.info(f"포스트 삭제는 향후 구현 예정: {post_id}")
        return False