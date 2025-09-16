# infrastructure.py
import os
import time
import platform

import json
from typing import List, Optional
import pyautogui

import google.generativeai as genai
import requests
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException
from trio import sleep
from webdriver_manager.chrome import ChromeDriverManager

from domain import (
    PostContent, LoginError, PostingError, WebDriverError,
    ContentGenerationError, ImageGenerationError, GeneratedContent, GeneratedBody
)
from interfaces import (
    ContentGeneratorInterface,
    ImageGeneratorInterface,
    PosterInterface,
)


class GeminiContentGenerator(ContentGeneratorInterface):
    """Gemini API를 사용하여 콘텐츠를 생성하는 구현체"""

    PROMPT_TEMPLATE = '''
    당신은 SEO 전문가이자 뛰어난 콘텐츠 기획자이며, 독자가 몰입하고 정보를 쉽게 소화할 수 있도록 글의 가독성과 시각적 흐름을 중요하게 생각하는 블로거입니다.
    다음 키워드들을 포함하여 매력적이고 유익하며 SEO 친화적인 블로그 게시물을 작성해 주세요. 
    글은 최소 800단어 이상이어야 하며, 독자의 흥미를 유발하고 정보 가치가 높으며 검색 엔진에 잘 노출되도록 구성되어야 합니다.
    
    키워드 : {topic}
    보조 키워드 : {secondary_keywords}
    제외 키워드 : {negative_keywords}
    목적 : [{purpose}]
    대상 독자 : [{audience}]
    스타일 : [{style}]
    길이 : [{length}]
    {reference_section}
    
    [블로그 글에 포함되어야 할 요소]
    1 매력적인 제목: 독자의 클릭을 유도하는, 핵심 키워드를 포함한 제목.
    2 도입부: 문제 제기 또는 흥미 유발을 통해 독자의 주의를 사로잡는 부분.
    3 본론:
      - 각 소제목은 H2 태그 형식으로 명시: 예: <h2>소제목 1: 인공지능의 현재와 미래</h2>
      - 각 키워드를 자연스럽게 통합하여 설명.
      - 소제목 내에는 H3 태그 형식의 부제목을 활용: 필요한 경우 <h3>세부 내용과 같이 사용하여 정보 계층화.</h3>
      - 관련성 있는 데이터, 사례, 통계 등을 포함 (필요시 가상 데이터 사용 가능).
      - 독자에게 실질적인 가치를 제공하는 정보.
      - 가독성을 위한 단락 구성:
       1) 한 단락은 3~5줄을 넘지 않도록 짧게 구성.
       2) 문장은 간결하고 명확하게 작성.
      - 강조 문구 (Highlighting): 중요한 핵심 문장이나 키워드는 볼드체 또는 이탤릭체로 강조하여 시선을 끌도록 요청.
      - 목록 활용 (List): 정보 나열 시 불릿 포인트 또는 숫자 목록을 적극적으로 활용하여 시각적 분리 및 쉬운 이해 유도.
      - 예)
      - 항목 1
      - 항목 2
      - 첫 번째 단계
      - 두 번째 단계
      - 인용구 (Quote Block) 삽입: 중요한 주장이나 인용할 내용이 있을 경우, 별도의 인용구 블록으로 표시.
      - 예:
      - "미래는 이미 와 있다. 단지 널리 퍼져 있지 않을 뿐이다." - 윌리엄 깁슨
      - 결론: 본론 내용을 요약하고, 핵심 메시지를 다시 강조하며, 독자에게 행동을 유도하거나 생각할 거리를 제공하는 부분. 여기에도 강조 문구 및 요약 목록 활용.
      - 메타 설명 (Meta Description): 검색 엔진 결과 페이지에 표시될 150-160자 내외의 요약.
      - 행동 유도 (Call to Action - CTA): 독자가 다음으로 무엇을 할 수 있는지 명확하게 제시 (예: 댓글, 공유, 관련 글 읽기).

    [결과는 반드시 아래 규칙을 엄격하게 따라야 합니다]
    - 결과는 JSON 형식으로 구성되어야 합니다. {{'title': '제목', 'body': [ {{ 'text': '문단1', 'image': '이미지 설명1' }}, {{ 'text': '문단2', 'image': '이미지 설명2' }}, ... ]], 'tags':['태그1', '태그2']}} 형태로 작성해주세요.
    - body 에 들어가는 text 는 html tag 형식 이어야 합니다. 강조가 필요한 경우 <strong>과 같은 태그를 사용하고, 문단 구분은 <p> 태그로 해주세요. 인용구 태그를 사용해서 가독성을 높일 수 있도록 합니다.
    - 이미지가 없어도 되는경우에는 image 은 null 로 채워주세요.
    - image 는 간결하고 일반적인 이미지 설명을 포함해야 합니다. (예: '도시 풍경', '행복한 사람들')
    - image 는 1~3단어의 매우 짧고 간단한 키워드여야 합니다. (예: '기술', '미래', '혁신')
    - 포스트는 여러 개의 문단으로 구성되어야 합니다.
    '''

    def __init__(self, api_key: str):
        self.api_key = api_key
        try:
            genai.configure(api_key=self.api_key)
        except Exception as e:
            raise ContentGenerationError(f"Gemini API 키 설정에 실패했습니다: {e}") from e
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate(self, topic: str, secondary_keywords: str, negative_keywords: str, target_url: str, purpose: str, audience: str, style: str, length: str) -> GeneratedContent:
        print(f"[Infrastructure] Gemini API로 '{topic}' 콘텐츠 생성 중...")

        reference_section = ""
        if target_url:
            try:
                fetched_content = google_web_search(query=f"summarize: {target_url}")
                reference_section = f"\n[참고 자료]\n{fetched_content}\n"
            except Exception as e:
                print(f"[Infrastructure] 참고 URL 콘텐츠를 가져오는 데 실패했습니다: {e}")

        prompt = self.PROMPT_TEMPLATE.format(
            topic=topic,
            secondary_keywords=secondary_keywords,
            negative_keywords=negative_keywords,
            purpose=purpose,
            audience=audience,
            style=style,
            length=length,
            reference_section=reference_section
        )

        try:
            response = self.model.generate_content(prompt)
            # Gemini 응답에서 JSON 부분만 추출
            json_text = response.text.strip().replace('```json', '').replace('```', '').strip()
            return self._parse_response(json_text)
        except Exception as e:
            raise ContentGenerationError(f"Gemini API 호출 중 오류 발생: {e}") from e

    def _parse_response(self, text: str) -> GeneratedContent:
        try:
            data = json.loads(text)
            body_items = [GeneratedBody(text=item['text'], image_caption=item.get('image')) for item in data['body']]

            if not body_items:
                raise ContentGenerationError("API 응답에 유효한 'body' 콘텐츠가 없습니다.")

            return GeneratedContent(
                title=data['title'],
                body=body_items,
                tags=data.get('tags', [])
            )
        except (json.JSONDecodeError, KeyError) as e:
            raise ContentGenerationError(f"API 응답 JSON 파싱 실패: {e}") from e


class PixabayImageSearchGenerator(ImageGeneratorInterface):
    """Pixabay API를 사용하여 이미지를 검색하고 다운로드하는 구현체"""

    PIXABAY_API_URL = "https://pixabay.com/api/"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.run_id = int(time.time())
        self.sequence = 0

    def generate(self, caption: str, save_path: str) -> str:
        print(f"[Infrastructure] Pixabay에서 '{caption}' 이미지 검색 중...")
        self.sequence += 1

        try:
            params = {
                "key": self.api_key,
                "q": caption,
                "image_type": "photo",
                "orientation": "horizontal",
                "per_page": 3,  # Get a few results
                "safesearch": True,
            }
            response = requests.get(self.PIXABAY_API_URL, params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors

            data = response.json()

            if not data["hits"]:
                raise ImageGenerationError(f"Pixabay에서 '{caption}'에 대한 이미지를 찾을 수 없습니다.")

            # Get the URL of the large image from the first hit
            image_url = data["hits"][0]["largeImageURL"]

            # Download the image
            image_response = requests.get(image_url)
            image_response.raise_for_status()

            # Save the image
            file_name = f"temp_image_{self.run_id}_{self.sequence}.png"
            full_path = os.path.join(save_path, file_name)

            os.makedirs(save_path, exist_ok=True)

            with open(full_path, 'wb') as f:
                f.write(image_response.content)

            print(f"-> 이미지 검색 및 저장 완료: {full_path}")
            return full_path

        except requests.exceptions.RequestException as e:
            raise ImageGenerationError(f"Pixabay API 호출 또는 이미지 다운로드 중 오류 발생: {e}") from e
        except Exception as e:
            raise ImageGenerationError(f"Pixabay 이미지 검색 중 알 수 없는 오류 발생: {e}") from e


class SeleniumNaverPoster(PosterInterface):
    """Selenium을 사용하여 네이버 블로그에 포스팅하는 구현체"""

    def __init__(self, user_id: str, user_pw: str):
        self.user_id = user_id
        self.user_pw = user_pw
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None

    def initialize(self):
        """웹 드라이버를 초기화합니다."""
        if self.driver is not None:
            print("[Infrastructure] 드라이버가 이미 초기화되었습니다.")
            return

        print("[Infrastructure] Selenium 드라이버를 초기화합니다...")
        try:
            options = Options()
            user_data_dir = os.path.join(os.path.expanduser("~"), ".naver-blogger-session")
            options.add_argument(f"user-data-dir={user_data_dir}")
            options.add_argument("--start-maximized")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.implicitly_wait(5)
            self.wait = WebDriverWait(self.driver, 20)
        except Exception as e:
            raise WebDriverError(f"웹 드라이버 초기화 중 오류 발생: {e}") from e

    def login(self) -> None:
        if not self.driver or not self.wait:
            raise WebDriverError("드라이버가 초기화되지 않았습니다. login() 전에 initialize()를 호출해야 합니다.")

        print(f"[Infrastructure] 네이버 로그인 페이지로 이동합니다...")
        self.driver.get("https://nid.naver.com/nidlogin.login")
        self.wait.until(EC.presence_of_element_located((By.ID, 'id')))

        if "nidlogin.login" not in self.driver.current_url:
            print("[Infrastructure] 이미 로그인된 세션입니다.")
            return

        try:
            id_input = self.wait.until(EC.presence_of_element_located((By.ID, 'id')))
            pw_input = self.wait.until(EC.presence_of_element_located((By.ID, 'pw')))

            paste_key = Keys.COMMAND if platform.system() == 'Darwin' else Keys.CONTROL

            self.driver.execute_script("arguments[0].value = arguments[1];", id_input, self.user_id)
            time.sleep(0.3)  # Give time for script to register

            self.driver.execute_script("arguments[0].value = arguments[1];", pw_input, self.user_pw)
            time.sleep(0.3)  # Give time for script to register

            login_button = self.wait.until(EC.element_to_be_clickable((By.ID, 'log.login')))
            login_button.click()

            self.wait.until(EC.url_changes("https://nid.naver.com/nidlogin.login"))
            print("[Infrastructure] 로그인 성공.")

        except (NoSuchElementException, TimeoutException) as e:
            raise LoginError(f"로그인 자동화 중 요소를 찾지 못했거나 시간 초과: {e}") from e
        except Exception as e:
            raise LoginError(f"로그인 자동화 중 알 수 없는 오류 발생: {e}") from e

    def post(self, content_list: List[PostContent], title: str) -> str:
        if not self.driver or not self.wait:
            raise WebDriverError("드라이버가 초기화되지 않았습니다. post() 전에 initialize()를 호출해야 합니다.")
        print(f"[Infrastructure] Selenium으로 포스팅 시작: {title}")
        try:
            write_page_url = f"https://blog.naver.com/{self.user_id}?Redirect=Write"
            self.driver.get(write_page_url)
            self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
            time.sleep(0.3)

            # Optional popups might not appear. Use a much shorter wait time for them
            # to avoid a long delay when they are absent.
            short_wait = WebDriverWait(self.driver, 1)  # 3-second wait

            try:
                popup_cancel_button = short_wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.se-popup-button-cancel')))
                popup_cancel_button.click()
                print("[Infrastructure] '다음에' 팝업 닫기 완료.")
            except (TimeoutException, NoSuchElementException):
                print("[Infrastructure] '다음에' 팝업이 나타나지 않아 건너뜁니다.")
                pass

            try:
                help_close_button = short_wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.se-help-panel-close-button')))
                help_close_button.click()
                print("[Infrastructure] '도움말' 팝업 닫기 완료.")
            except (TimeoutException, NoSuchElementException):
                print("[Infrastructure] '도움말' 팝업이 나타나지 않아 건너뜁니다.")
                pass

            title_input = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".se-section-documentTitle")))
            actions = ActionChains(self.driver)
            actions.click(title_input)
            for char in title:
                actions.send_keys(char).pause(0.03)
            actions.perform()
            time.sleep(0.3)  # 제목 입력 후 안정화 대기

            for content in content_list:
                if content.type == "text":
                    self._insert_text(content.data)
                elif content.type == "image":
                    self._insert_image(content.data)
                time.sleep(0.3)

            # 첫 번째 발행 버튼 클릭
            publish_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-click-area="tpb.publish"]'))
            )
            publish_button.click()

            # 두 번째 발행 버튼 클릭 (확인 팝업 등)
            final_publish_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-click-area="tpb*i.publish"]'))
            )
            final_publish_button.click()

            # URL이 'PostView.naver'를 포함하도록 변경될 때까지 명시적으로 대기
            self.wait.until(EC.url_contains(f"https://blog.naver.com/{self.user_id}"))
            time.sleep(2)
            post_url = self.driver.current_url
            return post_url
        except ElementNotInteractableException as e:
            raise PostingError(f"요소와 상호작용할 수 없습니다: {e}") from e
        except Exception as e:
            raise PostingError(f"포스팅 중 오류 발생: {e}") from e

    def _insert_text(self, text: str):
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
            time.sleep(0.3)  # Increased sleep

            # 4. 새 탭 닫고 원래 편집기 탭으로 복귀
            self.driver.close()
            self.driver.switch_to.window(original_window)

            # 5. 네이버 에디터 프레임으로 다시 전환하고 포커스 확보
            self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
            time.sleep(0.3)  # 프레임 전환 후 안정화 대기

            # 6. 에디터에 붙여넣기 (더 안정적인 포커스)
            try:
                # body를 한번 클릭하여 프레임 자체에 포커스를 줌
                self.driver.find_element(By.TAG_NAME, "body").click()
                time.sleep(0.3)
            except Exception:
                pass  # 실패해도 계속 진행

            # 붙여넣을 컨테이너를 다시 찾아 클릭
            content_div = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".se-section-text")))
            content_div.click()

            # 커서를 문서의 맨 끝으로 이동시켜 붙여넣기 위치를 조정합니다.
            ActionChains(self.driver).key_down(copy_key).send_keys('a').key_up(copy_key).perform()
            time.sleep(0.3)

            # 커서를 문서의 맨 끝으로 이동시켜 붙여넣기 위치를 조정합니다.
            ActionChains(self.driver).key_down(Keys.ARROW_RIGHT).key_up(Keys.ARROW_RIGHT).perform()
            time.sleep(0.3)

            # 붙여넣기 실행
            ActionChains(self.driver).key_down(copy_key).send_keys('v').key_up(copy_key).perform()
            time.sleep(0.3)  # 붙여넣기 후 에디터가 처리할 시간 대기

            # 다음 콘텐츠 입력을 위해 줄바꿈 2번
            ActionChains(self.driver).send_keys(Keys.ENTER).send_keys(Keys.ENTER).perform()
            time.sleep(0.3)

        finally:
            # 7. 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def _insert_image(self, image_path: str):
        # '사진' 버튼을 클릭하여 파일 선택 대화상자를 엽니다.
        # data-name="image" 속성을 사용하여 버튼을 안정적으로 찾습니다.
        try:
            image_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-name="image"]'))
            )
            image_button.click()
            time.sleep(0.3)  # 파일 선택창이 완전히 나타날 때까지 잠시 대기합니다.
        except TimeoutException:
            raise PostingError("이미지 추가 버튼을 찾을 수 없습니다.")

        # 파일 input 요소에 이미지의 절대 경로를 전송합니다.
        # 이 input 요소는 일반적으로 숨겨져 있으므로, send_keys를 사용해 직접 값을 설정합니다.
        try:
            abs_image_path = os.path.abspath(image_path)
            # input[type="file"] 요소가 나타날 때까지 기다립니다.
            file_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
            )
            file_input.send_keys(abs_image_path)
            time.sleep(0.5)
            pyautogui.press('esc')  # Added to close potential native file dialog

            # 이미지 업로드가 완료될 때까지 대기합니다.
            # 로딩 표시기가 사라지는 것을 기준으로 삼습니다.
            self.wait.until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".se-media-loading-indicator"))
            )
            # 에디터에 이미지가 완전히 렌더링될 시간을 추가로 확보합니다.
            time.sleep(2)

            # 다음 콘텐츠 입력을 위해 줄바꿈 2번
            ActionChains(self.driver).send_keys(Keys.END).send_keys(Keys.ENTER).send_keys(Keys.ENTER).perform()
            time.sleep(0.3)

        except TimeoutException:
            raise PostingError("이미지 업로드 중 오류가 발생했습니다 (타임아웃).")

    def close(self) -> None:
        print("[Infrastructure] Selenium 드라이버를 종료합니다.")
        if self.driver:
            self.driver.quit()
            self.driver = None # 드라이버 종료 후 None으로 설정
