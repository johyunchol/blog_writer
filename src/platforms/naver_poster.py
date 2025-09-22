"""
네이버 블로그 자동 포스팅 모듈
PRD.md 요구사항에 따른 네이버 블로그 포스팅 구현
글과 이미지가 교차되는 전문적인 형식으로 포스팅
"""

import time
import re
import os
import platform
from typing import Optional, List
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

from ..core.base_poster import (
    AbstractPoster,
    BlogPost,
    PostingResult,
    PlatformType,
    LoginError,
    PostingError,
    ContentError
)


class NaverPoster(AbstractPoster):
    """네이버 블로그 포스터"""

    def __init__(self, username: str, password: str, headless: bool = True):
        """
        Args:
            username: 네이버 로그인 아이디
            password: 네이버 로그인 비밀번호
            headless: 헤드리스 모드 여부
        """
        super().__init__(username, password, headless)
        self.blog_url = ""  # 사용자의 블로그 URL (로그인 후 자동 감지)

    def _get_platform_type(self) -> PlatformType:
        """플랫폼 타입 반환"""
        return PlatformType.NAVER

    def _get_login_url(self) -> str:
        """로그인 URL 반환"""
        return "https://nid.naver.com/nidlogin.login"

    def _get_post_create_url(self) -> str:
        """포스트 작성 URL 반환"""
        return f"https://blog.naver.com/{self.username}?Redirect=Write"

    def login(self) -> bool:
        """네이버 계정 로그인 (infrastructure.py 방식 적용)"""
        try:
            self.logger.info("네이버 로그인을 시작합니다...")

            # 드라이버 초기화 (없는 경우에만)
            if not self.driver:
                self.init_driver()

            # 로그인 페이지로 이동
            self.driver.get(self.login_url)
            self.wait.until(EC.presence_of_element_located((By.ID, 'id')))

            # 이미 로그인된 상태 확인
            if "nidlogin.login" not in self.driver.current_url:
                self.logger.info("이미 로그인된 세션입니다.")
                return True

            # 로그인 폼 요소 대기
            id_input = self.wait.until(EC.presence_of_element_located((By.ID, 'id')))
            pw_input = self.wait.until(EC.presence_of_element_located((By.ID, 'pw')))

            # macOS는 Command, 다른 OS는 Ctrl
            import platform
            paste_key = Keys.COMMAND if platform.system() == 'Darwin' else Keys.CONTROL

            # JavaScript를 사용하여 직접 값 설정 (infrastructure.py 방식)
            self.driver.execute_script("arguments[0].value = arguments[1];", id_input, self.username)
            time.sleep(0.3)

            self.driver.execute_script("arguments[0].value = arguments[1];", pw_input, self.password)
            time.sleep(0.3)

            # 로그인 버튼 클릭
            login_button = self.wait.until(EC.element_to_be_clickable((By.ID, 'log.login')))
            login_button.click()

            # 로그인 성공 대기 (URL 변경으로 확인)
            self.wait.until(EC.url_changes("https://nid.naver.com/nidlogin.login"))
            self.logger.info("네이버 로그인 성공!")

            return True

        except (NoSuchElementException, TimeoutException) as e:
            self.logger.error(f"로그인 시간 초과 또는 요소를 찾지 못함: {e}")
            self._save_error_screenshot("login_timeout")
            raise LoginError(f"로그인 자동화 중 요소를 찾지 못했거나 시간 초과: {e}")
        except Exception as e:
            self.logger.error(f"로그인 실패: {e}")
            self._save_error_screenshot("login_error")
            raise LoginError(f"로그인 자동화 중 알 수 없는 오류 발생: {e}")

    def _human_like_typing(self, element, text: str) -> None:
        """사람과 같은 타이핑 시뮬레이션"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(0.1 + (hash(char) % 10) / 100)  # 0.1~0.2초 랜덤 지연

    def _get_blog_url(self) -> None:
        """사용자의 블로그 URL 획득"""
        try:
            # 블로그 메인으로 이동
            self.driver.get("https://blog.naver.com/")
            time.sleep(2)

            # 현재 사용자의 블로그 URL 찾기
            current_url = self.driver.current_url
            if "blog.naver.com" in current_url:
                # URL에서 사용자 ID 추출
                if "/PostList.naver" in current_url:
                    # URL 형태: https://blog.naver.com/PostList.naver?blogId=사용자ID
                    blog_id = current_url.split("blogId=")[1].split("&")[0]
                    self.blog_url = f"https://blog.naver.com/{blog_id}"
                else:
                    # 직접 블로그 URL 사용
                    self.blog_url = current_url

            self.logger.info(f"블로그 URL 설정: {self.blog_url}")

        except Exception as e:
            self.logger.warning(f"블로그 URL 자동 감지 실패: {e}")
            self.blog_url = "https://blog.naver.com/"

    def create_post(self, post: BlogPost) -> PostingResult:
        """포스트 작성 (infrastructure.py 방식 적용)"""
        try:
            self.logger.info(f"네이버 블로그 포스트 작성 시작: {post.title}")

            # 글쓰기 페이지로 이동
            write_page_url = f"https://blog.naver.com/{self.username}?Redirect=Write"
            self.driver.get(write_page_url)

            # iframe으로 전환 (infrastructure.py 방식)
            self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
            time.sleep(0.3)

            # 팝업 처리 (infrastructure.py 방식)
            short_wait = WebDriverWait(self.driver, 1)

            try:
                popup_cancel_button = short_wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.se-popup-button-cancel')))
                popup_cancel_button.click()
                self.logger.info("'다음에' 팝업 닫기 완료.")
            except (TimeoutException, NoSuchElementException):
                self.logger.info("'다음에' 팝업이 나타나지 않아 건너뜁니다.")
                pass

            try:
                help_close_button = short_wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.se-help-panel-close-button')))
                help_close_button.click()
                self.logger.info("'도움말' 팝업 닫기 완료.")
            except (TimeoutException, NoSuchElementException):
                self.logger.info("'도움말' 팝업이 나타나지 않아 건너뜁니다.")
                pass

            # 제목 입력 (infrastructure.py 방식)
            title_input = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".se-section-documentTitle")))
            actions = ActionChains(self.driver)
            actions.click(title_input)
            for char in post.title:
                actions.send_keys(char).pause(0.03)
            actions.perform()
            time.sleep(0.3)

            # 본문 입력 (infrastructure.py 방식으로 간단화)
            self._insert_text_infrastructure_style(post.content)

            return PostingResult(
                success=True,
                message="포스트 작성 완료 (발행 대기)"
            )

        except Exception as e:
            self.logger.error(f"포스트 작성 중 오류: {e}")
            self._save_error_screenshot("create_post_error")
            return PostingResult(
                success=False,
                message=f"포스트 작성 실패: {str(e)}",
                error_code="CREATE_POST_FAILED"
            )

    def _input_title(self, title: str) -> None:
        """제목 입력"""
        try:
            # 네이버 블로그 제목 입력 필드 (다양한 셀렉터 시도)
            title_selectors = [
                "input[placeholder='제목을 입력해 주세요.']",
                "input.se-input-form-input",
                "#title",
                ".title_input input"
            ]

            title_element = None
            for selector in title_selectors:
                try:
                    title_element = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if not title_element:
                raise PostingError("제목 입력 필드를 찾을 수 없습니다")

            # 제목 입력
            title_element.clear()
            title_element.send_keys(title)
            time.sleep(1)

            self.logger.info(f"제목 입력 완료: {title}")

        except Exception as e:
            raise PostingError(f"제목 입력 실패: {e}")

    def _input_content_with_images(self, content: str, images: List[str]) -> None:
        """본문과 이미지를 교차로 배치하여 입력"""
        try:
            # 에디터 프레임 찾기 및 전환
            self._switch_to_editor_frame()

            # 콘텐츠를 단락별로 분할
            paragraphs = self._split_content_to_paragraphs(content)

            # 글과 이미지 교차 배치
            image_index = 0
            for i, paragraph in enumerate(paragraphs):
                if paragraph.strip():
                    # 텍스트 입력
                    self._input_paragraph(paragraph)

                    # 이미지 삽입 (2-3개 단락마다)
                    if images and image_index < len(images) and (i + 1) % 2 == 0:
                        self._insert_image(images[image_index])
                        image_index += 1

                    time.sleep(0.5)

            # 남은 이미지들 마지막에 추가
            while image_index < len(images):
                self._insert_image(images[image_index])
                image_index += 1

            # 메인 프레임으로 돌아가기
            self.driver.switch_to.default_content()

            self.logger.info("본문 및 이미지 입력 완료")

        except Exception as e:
            self.driver.switch_to.default_content()  # 안전장치
            raise PostingError(f"본문 입력 실패: {e}")

    def _switch_to_editor_frame(self) -> None:
        """에디터 iframe으로 전환"""
        try:
            # 네이버 블로그 에디터는 iframe 내부에 있음
            editor_frame_selectors = [
                "iframe#se-2-root",
                "iframe.se-component-content",
                "iframe[title='Rich Text Area']"
            ]

            for selector in editor_frame_selectors:
                try:
                    frame = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    self.driver.switch_to.frame(frame)
                    self.logger.info(f"에디터 프레임 전환 성공: {selector}")
                    return
                except TimeoutException:
                    continue

            # iframe이 없는 경우 메인 에디터 영역 사용
            self.logger.info("iframe 에디터를 찾지 못해 메인 에디터 사용")

        except Exception as e:
            self.logger.warning(f"에디터 프레임 전환 실패: {e}")

    def _split_content_to_paragraphs(self, content: str) -> List[str]:
        """콘텐츠를 단락별로 분할"""
        # HTML 태그 제거 후 단락 분할
        clean_content = re.sub(r'<[^>]+>', '', content)

        # 빈 줄로 단락 구분
        paragraphs = [p.strip() for p in clean_content.split('\n\n') if p.strip()]

        # 너무 긴 단락은 문장별로 분할
        result = []
        for paragraph in paragraphs:
            if len(paragraph) > 500:
                sentences = re.split(r'[.!?]\s+', paragraph)
                result.extend([s.strip() + '.' for s in sentences if s.strip()])
            else:
                result.append(paragraph)

        return result

    def _input_paragraph(self, paragraph: str) -> None:
        """단락 입력"""
        try:
            # 에디터 본문 영역 찾기
            editor_selectors = [
                ".se-component-content",
                ".editor-body",
                "[contenteditable='true']"
            ]

            editor_element = None
            for selector in editor_selectors:
                try:
                    editor_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue

            if editor_element:
                # 기존 방식으로 텍스트 입력
                editor_element.click()
                time.sleep(0.5)
                editor_element.send_keys(paragraph + "\n\n")
            else:
                # JavaScript로 직접 입력
                self.driver.execute_script(f"document.body.innerHTML += '<p>{paragraph}</p>';")

        except Exception as e:
            self.logger.warning(f"단락 입력 실패: {e}")

    def _insert_image(self, image_path: str) -> None:
        """이미지 삽입"""
        try:
            # 메인 프레임으로 돌아가기
            self.driver.switch_to.default_content()

            # 이미지 업로드 버튼 찾기
            image_button_selectors = [
                ".se-toolbar-item-image",
                "button[aria-label='사진']",
                ".photo-upload-btn"
            ]

            image_button = None
            for selector in image_button_selectors:
                try:
                    image_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if image_button:
                self._safe_click(image_button)
                time.sleep(2)

                # 파일 업로드
                self._upload_image_file(image_path)

                # 에디터 프레임으로 다시 전환
                self._switch_to_editor_frame()

        except Exception as e:
            self.logger.warning(f"이미지 삽입 실패: {e}")

    def _upload_image_file(self, image_path: str) -> None:
        """이미지 파일 업로드"""
        try:
            # 파일 업로드 input 찾기
            file_input_selectors = [
                "input[type='file'][accept*='image']",
                "input[type='file']"
            ]

            file_input = None
            for selector in file_input_selectors:
                try:
                    file_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue

            if file_input:
                # 파일 경로 입력
                file_input.send_keys(image_path)
                time.sleep(3)  # 업로드 대기

                self.logger.info(f"이미지 업로드 완료: {image_path}")
            else:
                self.logger.warning("파일 업로드 input을 찾을 수 없습니다")

        except Exception as e:
            self.logger.warning(f"이미지 파일 업로드 실패: {e}")

    def upload_image(self, image_path: str) -> bool:
        """이미지 업로드 (단독 사용)"""
        try:
            self._insert_image(image_path)
            return True
        except Exception as e:
            self.logger.error(f"이미지 업로드 실패: {e}")
            return False

    def _input_tags(self, tags: List[str]) -> None:
        """태그 입력"""
        try:
            # 메인 프레임으로 돌아가기
            self.driver.switch_to.default_content()

            # 태그 입력 필드 찾기
            tag_input_selectors = [
                "input[placeholder*='태그']",
                ".tag-input input",
                "#tag-input"
            ]

            tag_input = None
            for selector in tag_input_selectors:
                try:
                    tag_input = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if tag_input:
                for tag in tags[:10]:  # 네이버는 보통 10개 제한
                    tag_input.clear()
                    tag_input.send_keys(tag)
                    tag_input.send_keys(Keys.ENTER)
                    time.sleep(0.5)

                self.logger.info(f"태그 입력 완료: {tags}")

        except Exception as e:
            self.logger.warning(f"태그 입력 실패: {e}")

    def _set_category(self, category: str) -> None:
        """카테고리 설정"""
        try:
            # 카테고리 드롭다운 또는 버튼 찾기
            category_selectors = [
                ".category-select",
                "select[name='categoryId']",
                ".category-dropdown"
            ]

            for selector in category_selectors:
                try:
                    category_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    category_element.click()
                    time.sleep(1)

                    # 카테고리 옵션 선택 (텍스트 매칭)
                    options = self.driver.find_elements(By.TAG_NAME, "option")
                    for option in options:
                        if category in option.text:
                            option.click()
                            break

                    self.logger.info(f"카테고리 설정: {category}")
                    return

                except NoSuchElementException:
                    continue

        except Exception as e:
            self.logger.warning(f"카테고리 설정 실패: {e}")

    def _set_visibility(self, visibility: str) -> None:
        """공개 설정"""
        try:
            if visibility.lower() in ['private', '비공개']:
                # 비공개 설정
                private_radio = self.driver.find_element(
                    By.CSS_SELECTOR, "input[value='private'], input[value='0']"
                )
                private_radio.click()
            else:
                # 공개 설정 (기본값)
                public_radio = self.driver.find_element(
                    By.CSS_SELECTOR, "input[value='public'], input[value='1']"
                )
                public_radio.click()

            self.logger.info(f"공개 설정: {visibility}")

        except Exception as e:
            self.logger.warning(f"공개 설정 실패: {e}")

    def publish_post(self) -> PostingResult:
        """포스트 발행"""
        try:
            self.logger.info("포스트 발행 시작...")

            # 메인 프레임으로 돌아가기
            self.driver.switch_to.default_content()

            # 발행 버튼 찾기
            publish_selectors = [
                "button[class*='publish']",
                "button.se-button-save",
                "input[value='발행']",
                ".publish-btn"
            ]

            publish_button = None
            for selector in publish_selectors:
                try:
                    publish_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if not publish_button:
                raise PostingError("발행 버튼을 찾을 수 없습니다")

            # 발행 버튼 클릭
            self._safe_click(publish_button)
            time.sleep(3)

            # 발행 완료 확인
            current_url = self.driver.current_url
            if "PostView.naver" in current_url or "blog.naver.com" in current_url:
                self.logger.info("포스트 발행 성공!")

                return PostingResult(
                    success=True,
                    message="포스트 발행 완료",
                    post_url=current_url
                )
            else:
                return PostingResult(
                    success=False,
                    message="발행 완료 확인 실패",
                    error_code="PUBLISH_VERIFICATION_FAILED"
                )

        except Exception as e:
            self.logger.error(f"포스트 발행 실패: {e}")
            self._save_error_screenshot("publish_error")
            return PostingResult(
                success=False,
                message=f"포스트 발행 실패: {str(e)}",
                error_code="PUBLISH_FAILED"
            )

    def _insert_text_infrastructure_style(self, text: str) -> None:
        """HTML 텍스트 삽입 (infrastructure.py 방식)"""
        temp_file_path = os.path.abspath("_temp_render.html")
        original_window = self.driver.current_window_handle
        copy_key = Keys.COMMAND if platform.system() == 'Darwin' else Keys.CONTROL

        try:
            # 1. 임시 HTML 파일 생성 및 작성
            with open(temp_file_path, "w", encoding="utf-8") as f:
                f.write(f'<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"></head><body>{text}</body></html>')

            # 2. 새 탭에서 임시 파일 열기
            self.driver.switch_to.new_window('tab')
            self.driver.get(f"file://{temp_file_path}")
            # 새 탭의 body 요소가 로드될 때까지 명시적으로 대기
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            # 3. 렌더링된 콘텐츠 전체 선택 및 복사
            ActionChains(self.driver).key_down(copy_key).send_keys('a').send_keys('c').key_up(copy_key).perform()
            time.sleep(0.3)

            # 4. 새 탭 닫고 원래 편집기 탭으로 복귀
            self.driver.close()
            self.driver.switch_to.window(original_window)

            # 5. 네이버 에디터 프레임으로 다시 전환하고 포커스 확보
            self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
            time.sleep(0.3)

            # 6. 에디터에 붙여넣기 (더 안정적인 포커스)
            try:
                # body를 한번 클릭하여 프레임 자체에 포커스를 줌
                self.driver.find_element(By.TAG_NAME, "body").click()
                time.sleep(0.3)
            except Exception:
                pass

            # 붙여넣을 컨테이너를 다시 찾아 클릭
            content_div = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".se-section-text")))
            content_div.click()

            # 커서를 문서의 맨 끝으로 이동시켜 붙여넣기 위치를 조정
            ActionChains(self.driver).key_down(copy_key).send_keys('a').key_up(copy_key).perform()
            time.sleep(0.3)

            # 커서를 문서의 맨 끝으로 이동
            ActionChains(self.driver).key_down(Keys.ARROW_RIGHT).key_up(Keys.ARROW_RIGHT).perform()
            time.sleep(0.3)

            # 붙여넣기 실행
            ActionChains(self.driver).key_down(copy_key).send_keys('v').key_up(copy_key).perform()
            time.sleep(0.3)

            # 다음 콘텐츠 입력을 위해 줄바꿈 2번
            ActionChains(self.driver).send_keys(Keys.ENTER).send_keys(Keys.ENTER).perform()
            time.sleep(0.3)

            self.logger.info("HTML 콘텐츠 삽입 완료 (infrastructure.py 방식)")

        finally:
            # 7. 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def _save_error_screenshot(self, error_type: str) -> None:
        """오류 발생 시 스크린샷 저장"""
        try:
            if self.driver:
                screenshot_path = f"naver_error_{error_type}.png"
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
