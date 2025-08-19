# 부동산 뉴스 자동 포스팅 블로거

## 📖 프로젝트 설명

이 프로젝트는 Google Gemini API를 활용하여 최신 부동산 뉴스를 기반으로 블로그 게시물을 자동으로 생성하고, 지정된 Tistory 블로그에 포스팅하는 자동화 스크립트입니다. 모든 과정은 GitHub Actions를 통해 설정된 스케줄에 따라 자동으로 실행됩니다.

## ✨ 주요 기능

-   **콘텐츠 자동 생성**: Gemini API를 통해 최신 부동산 뉴스를 검색하고, 이를 바탕으로 전문적인 블로그 글(HTML 형식)을 생성합니다.
-   **자동 로그인 및 포스팅**: Selenium으로 Tistory 블로그에 안전하게 로그인하고, `requests` 라이브러리를 통해 생성된 글을 게시합니다.
-   **결과 알림**: 스크립트 실행 후, 성공 또는 실패 결과를 지정된 이메일로 전송합니다.
-   **스케줄링 실행**: GitHub Actions를 사용하여 원하는 시간(기본: 매일 오전 8시 KST)에 전체 프로세스를 자동으로 실행합니다.

## ⚙️ 동작 방식

1.  **콘텐츠 생성**: `generate_post_with_gemini()` 함수가 Gemini API를 호출하여 네이버 부동산 뉴스 등의 정보를 바탕으로 Tistory 형식에 맞는 글을 작성합니다.
2.  **인증**: `get_tistory_cookies_with_selenium()` 함수가 Selenium을 이용해 Tistory에 로그인하고, 포스팅에 필요한 인증 쿠키를 획득합니다.
3.  **게시**: `post_to_tistory_requests()` 함수가 획득한 쿠키와 생성된 콘텐츠를 사용하여 Tistory의 포스팅 API를 호출하여 글을 게시합니다.
4.  **알림**: `send_email()` 함수가 위 과정의 최종 결과를 설정된 이메일로 발송합니다.

## 🚀 시작하기

### 사전 요구 사항

-   Python 3.10 이상
-   Google Gemini API 키
-   Tistory 블로그 계정
-   이메일 알림을 위한 Gmail 계정 및 앱 비밀번호

### 설치 및 설정

1.  **저장소 복제**
    ```bash
    git clone https://github.com/your-username/your-repository.git
    cd your-repository
    ```

2.  **필요 라이브러리 설치**
    ```bash
    pip install -r requirements.txt
    ```

3.  **환경 변수 설정**
    프로젝트를 실행하려면 아래의 환경 변수들이 필요합니다. 로컬에서 테스트하는 경우 직접 설정하고, GitHub Actions를 사용하는 경우 저장소의 **Secrets**에 아래 변수들을 등록해야 합니다.

    -   `GEMINI_API_KEY`: Google AI Studio에서 발급받은 API 키
    -   `TISTORY_ID`: Tistory 로그인 아이디 (카카오 계정 이메일)
    -   `TISTORY_PW`: Tistory 로그인 비밀번호
    -   `TISTORY_BLOG_NAME`: Tistory 블로그 주소의 서브도메인 (예: `my-blog`)
    -   `SENDER_EMAIL`: 발신자 Gmail 주소 (예: `my-email@gmail.com`)
    -   `SENDER_PASSWORD`: 발신자 Gmail의 **앱 비밀번호** (2단계 인증 사용 시 필요)
    -   `RECIPIENT_EMAIL`: 결과 리포트를 수신할 이메일 주소

## 🛠️ 사용법

환경 변수가 모두 설정되었다면, 다음 명령어로 스크립트를 수동으로 실행할 수 있습니다.

```bash
python real_estate_posting.py
```

## 🤖 자동화

이 프로젝트는 `.github/workflows/auto_post.yml` 파일에 정의된 GitHub Actions 워크플로우를 통해 자동으로 실행됩니다.

-   **스케줄**: 기본적으로 매일 오전 8시(KST)에 실행되도록 설정되어 있습니다. (`cron: '0 23 * * *'`).
-   **수동 실행**: GitHub 저장소의 'Actions' 탭에서 `Blog Auto Posting` 워크플로우를 선택하여 수동으로 실행할 수도 있습니다.
