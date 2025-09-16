### **네이버 블로그 자동 포스팅 시스템 기능 명세서**

본 문서는 '네이버 블로그 자동 포스팅 시스템'을 구성하는 각 기능의 상세 사양을 정의합니다.

#### **1. 콘텐츠 생성 모듈 (Content Generation Module)**

**1.1. 기능: AI 콘텐츠 생성 (generate_content)**
- **설명:** 주제를 입력받아 Gemini API를 호출하고, 반환된 텍스트에서 (문단, 이미지 캡션) 쌍을 추출하여 리스트로 반환한다. 이미지 캡션은 선택사항이다.
- **입력:**
    - `topic (str)`: 포스팅할 블로그 글의 주제.
- **출력:**
    - `List[Tuple[str, Optional[str]]]`: (문단, 이미지 캡션) 튜플의 리스트. 캡션이 없는 경우 `None`으로 반환된다.
- **예외 처리:**
    - `ContentGenerationError`: API 요청 실패(네트워크 오류, 서버 문제 등) 또는 API 응답 파싱 실패 시 발생한다.

**1.2. 기능: 이미지 준비 (download_images)**
- **설명:** `None`이 아닌 이미지 캡션 리스트를 기반으로 **더미 이미지 URL을 생성하고** 로컬에 다운로드한 뒤 {캡션: 파일 경로} 딕셔너리를 반환한다. **(현재 실제 웹 이미지 검색 기능은 구현되지 않았으며, 더미 이미지를 사용합니다.)**
- **입력:**
    - `captions (List[str])`: 이미지 검색에 사용될 `None`이 아닌 키워드(캡션) 리스트.
    - `save_path (str)`: 다운로드한 이미지를 저장할 로컬 디렉터리 경로.
- **출력:**
    - `Dict[str, str]`: 캡션을 key, 로컬에 저장된 파일 경로를 value로 갖는 딕셔너리.
- **예외 처리:**
    - `ImageDownloadError`: 이미지 다운로드 중 네트워크 연결 오류, 파일 쓰기 권한 부족, 디스크 공간 부족 등 문제가 발생한 경우 발생한다.

**1.3. 기능: 최종 콘텐츠 리스트 조합 (create_content_list)**
- **설명:** `generate_content`의 결과와 `download_images`의 결과를 조합하여, 포스팅 로직이 순차적으로 사용할 최종 콘텐츠 리스트를 생성한다.
- **입력:**
    - `generated_data (List[Tuple[str, Optional[str]]])`: (문단, 캡션) 튜플 리스트.
    - `image_paths (Dict[str, str])`: {캡션: 파일 경로} 딕셔너리.
- **출력:**
    - `List[Dict[str, str]]`: `[{"type": "text", "content": "..."}, {"type": "image", "path": "..."}]` 형식의 최종 딕셔너리 리스트.
- **예외 처리:**
    - `KeyError`: 로직 오류로 `image_paths` 딕셔너리에서 캡션에 해당하는 경로를 찾지 못할 경우 발생할 수 있다. (내부적으로 처리되거나 상위 계층으로 전파될 수 있음)

#### **2. 웹 자동화 모듈 (Web Automation Module)**

**2.1. 기능: 네이버 자동 로그인 (login_naver)**
- **설명:** Selenium WebDriver를 사용하여 네이버 로그인 페이지에 접속하고, 제공된 계정 정보로 로그인을 수행한다.
- **입력:**
    - `user_id (str)`: 네이버 아이디.
    - `user_pw (str)`: 네이버 비밀번호.
- **출력:**
    - `None`: 로그인 성공 시.
- **예외 처리:**
    - `NaverLoginError`: 아이디 또는 비밀번호가 틀렸거나, 캡차(보안문자)가 나타나 로그인이 차단된 경우, 로그인 페이지의 UI 변경으로 아이디/비밀번호 입력 필드나 로그인 버튼을 찾지 못한 경우, 페이지 로딩 시간이 초과된 경우 등 로그인 관련 모든 실패 시 발생한다.

**2.2. 기능: 글쓰기 에디터 제어 (control_editor)**
- **설명:** 최종 조합된 콘텐츠 리스트를 순회하며, 타입에 따라 에디터에 글쓰기 또는 이미지 업로드를 수행한다.
- **입력:**
    - `content_list (List[Dict[str, str]])`: `{"type": "text", "content": "..."}` 또는 `{"type": "image", "path": "..."}` 딕셔너리의 리스트.
- **출력:**
    - `None`
- **예외 처리:**
    - `NaverAutomationError`: 에디터의 HTML 모드 전환 버튼, 사진 추가 버튼 등 핵심 UI 요소를 찾지 못할 경우, 이미지 경로가 잘못되었거나 파일이 존재하지 않아 업로드에 실패한 경우, 페이지의 동적 변화로 인해 이전에 찾은 웹 요소를 더 이상 사용할 수 없게 된 경우 등 에디터 제어 관련 모든 실패 시 발생한다.

#### **3. 포스팅 실행 모듈 (Posting Execution Module)**

**3.1. 기능: 포스트 발행 (publish_post)**
- **설명:** 모든 콘텐츠 입력이 완료된 후, 발행 버튼을 클릭하여 최종적으로 포스트를 블로그에 게시한다.
- **입력:**
    - `None` (내부적으로 WebDriver 객체를 사용)
- **출력:**
    - `str`: 발행이 완료된 포스트의 고유 URL.
- **예외 처리:**
    - `NaverPublishError`: '발행' 버튼을 찾지 못한 경우, 발행 과정에서 알 수 없는 팝업이 발생하거나 오류가 생겨 실패한 경우 등 발행 관련 모든 실패 시 발생한다.

---
#### **전체 실행 워크플로우 (Main Workflow)**

1.  **설정 로드:** `config` 파일에서 API 키, 네이버 계정 정보, 이미지 저장 경로 등 모든 설정을 불러온다. (`main.py`)
2.  **콘텐츠 생성:** `GeminiContentGenerator.generate_content()`를 호출하여 (문단, 캡션) 튜플 리스트를 생성한다. (`use_cases.py`)
3.  **이미지 준비:** 생성된 데이터에서 `None`이 아닌 캡션만 추출하여 `NaverBlogAutomation.download_images()`를 호출, `{캡션: 경로}` 딕셔너리를 받는다. (`use_cases.py`)
4.  **최종 콘텐츠 리스트 조합:** `_create_content_list()`를 호출하여 글과 이미지 경로를 하나의 순차적인 리스트로 조합한다. (`use_cases.py`)
5.  **웹 드라이버 실행 및 로그인:** WebDriver를 초기화하고 `NaverBlogAutomation.login_naver()`를 호출하여 로그인한다. 로그인 실패 시 프로세스를 중단한다. (`use_cases.py`, `main.py`)
6.  **글쓰기 페이지 이동:** 로그인 성공 후 글쓰기 페이지로 이동한다. (`NaverBlogAutomation` 내부)
7.  **콘텐츠 입력:** `NaverBlogAutomation.control_editor()`에 최종 조합된 `content_list`를 전달하여 포스팅을 수행한다. (`use_cases.py`)
8.  **발행:** `NaverBlogAutomation.publish_post()`를 호출하여 포스트를 발행하고 결과 URL을 받는다. (`use_cases.py`)
9.  **종료:** WebDriver를 종료하고, 성공 여부와 결과 URL을 사용자에게 출력한다. (`main.py`)
