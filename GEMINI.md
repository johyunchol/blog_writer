**참고: 모든 응답은 한국어로 요청합니다.**

# Gemini 블로그 포스팅 자동화

이 프로젝트는 Gemini API를 활용하여 최신 부동산 뉴스를 기반으로 블로그 포스팅을 자동으로 생성하고, Tistory 블로그에 게시하는 파이썬 스크립트(`api_post.py`)를 중심으로 구성됩니다.

## 1. 전체 자동화 플로우

1.  **블로그 글 생성 (Gemini API)**
    *   `gemini-1.5-flash` 모델을 사용하여 지정된 프롬프트에 따라 최신 부동산 뉴스 기사를 검색하고 요약합니다.
    *   검색된 내용을 바탕으로 Tistory 블로그 형식에 맞는 전문적인 글(HTML)을 생성합니다.

2.  **Tistory 자동 로그인 및 쿠키 획득 (Selenium)**
    *   Selenium을 사용하여 Tistory의 카카오 계정 로그인 페이지에 접속하고, 사용자 ID와 비밀번호로 로그인하여 인증 쿠키를 획득합니다.

3.  **블로그 글 게시 (Requests)**
    *   획득한 인증 쿠키와 Gemini가 생성한 콘텐츠를 사용하여 Tistory 포스팅 API(`manage/post.json`)를 호출합니다.
    *   이 과정에서 제목, 본문, 태그를 분리하고 형식에 맞게 데이터를 가공하여 전송합니다.

4.  **결과 알림 (이메일)**
    *   스크립트 실행 완료 후, 성공 또는 실패 결과를 지정된 이메일 주소로 발송합니다.

5.  **실행 환경 (GitHub Actions)**
    *   스크립트는 GitHub Actions의 Secrets에 저장된 환경 변수(`GEMINI_API_KEY`, `TISTORY_ID` 등)를 사용하여 실행되도록 설계되었습니다.

## 2. `api_post.py` 스크립트 상세 분석

### 주요 함수

-   `send_email(subject, body, sender_email, sender_password, recipient_email)`
    -   **역할**: 스크립트 실행 결과를 이메일로 전송합니다.
    -   **세부 동작**: Gmail의 SMTP 서버를 통해 지정된 수신자에게 성공 또는 실패 메시지를 전달합니다.

-   `generate_post_with_gemini(api_key)`
    -   **역할**: Gemini API를 호출하여 블로그 콘텐츠를 생성합니다.
    -   **프롬프트 주요 내용**:
        -   실시간 부동산 뉴스 검색 및 요약.
        -   Tistory TinyMCE 에디터에 맞는 HTML 형식으로 본문 생성.
        -   제목, 서론, 본론, 결론 구조 및 전문적 어조 사용.
        -   5개 이상의 관련 태그 포함 (`태그::` 형식).
        -   2000자 이상의 분량.

-   `post_to_tistory_requests(blog_name, tistory_id, tistory_pw, content)`
    -   **역할**: 생성된 콘텐츠를 Tistory 블로그에 게시합니다.
    -   **세부 동작**:
        1.  **콘텐츠 파싱**: Gemini가 생성한 텍스트에서 제목(`# `), 태그(`태그::`), 본문을 분리합니다.
        2.  **Selenium 로그인**: `get_tistory_cookies_with_selenium` 내부 함수를 호출하여 Tistory 로그인 후 세션 쿠키를 가져옵니다.
        3.  **API 호출**: `requests` 라이브러리를 사용하여 Tistory 포스팅 API에 `POST` 요청을 보냅니다.
        4.  **Payload 구성**: 제목, HTML로 변환된 본문, 태그, 카테고리 ID 등 포스팅에 필요한 정보를 JSON 형식으로 구성합니다.

### 실행 로직 (`if __name__ == "__main__":`)

-   GitHub Actions의 Secrets 또는 로컬 환경 변수에서 필요한 모든 값(`GEMINI_API_KEY`, `TISTORY_ID`, `SENDER_EMAIL` 등)을 가져옵니다.
-   `generate_post_with_gemini` 함수를 호출하여 글을 생성하고, 성공 시 `post_to_tistory_requests` 함수를 호출하여 포스팅을 완료합니다.
-   모든 과정의 최종 성공 또는 실패 결과를 `send_email` 함수를 통해 이메일로 알립니다.

## 3. 실행 방법

1.  **필요 라이브러리 설치**
    ```bash
    pip install google-generativeai requests selenium
    ```

2.  **환경 변수 설정**
    스크립트를 실행하기 위해 다음 환경 변수를 설정해야 합니다. (GitHub Actions의 경우 Secrets에 등록)
    -   `GEMINI_API_KEY`: Google AI Studio에서 발급받은 API 키
    -   `TISTORY_ID`: Tistory 로그인 아이디 (카카오 계정 이메일)
    -   `TISTORY_PW`: Tistory 로그인 비밀번호
    -   `TISTORY_BLOG_NAME`: Tistory 블로그 주소의 서브도메인 (예: `myblog`)
    -   `SENDER_EMAIL`: 발신자 Gmail 주소 (예: `my-email@gmail.com`)
    -   `SENDER_PASSWORD`: 발신자 Gmail 앱 비밀번호 (2단계 인증 사용 시 필요)
    -   `RECIPIENT_EMAIL`: 수신자 이메일 주소

3.  **스크립트 실행**
    ```bash
    python real_estate_posting.py
    ```
