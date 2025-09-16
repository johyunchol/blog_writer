# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

Gemini API를 활용하여 최신 부동산 뉴스를 기반으로 블로그 포스트를 자동 생성하고 Tistory 블로그에 포스팅하는 자동화 프로젝트입니다. GitHub Actions를 통해 매일 자동으로 실행됩니다.

## 주요 명령어

### 로컬 실행
```bash
# 패키지 설치
pip install -r requirements.txt

# 메인 스크립트 실행 (환경변수 설정 후)
python src/tistory/real_estate_posting.py
```

### GitHub Actions
- **자동 실행**: 매일 KST 08:00 (UTC 23:00)에 자동 실행
- **수동 실행**: GitHub Actions 탭에서 "Blog Auto Posting" 워크플로우를 수동으로 실행 가능

## 아키텍처 구조

### 핵심 워크플로우
1. **콘텐츠 생성**: `generate_post_with_gemini()` - Gemini API로 부동산 뉴스 검색 및 HTML 블로그 포스트 생성
2. **인증**: `get_tistory_cookies_with_selenium()` - Selenium으로 Tistory 카카오 로그인 후 세션 쿠키 획득
3. **포스팅**: `post_to_tistory_requests()` - requests 라이브러리로 Tistory 포스팅 API 호출
4. **알림**: `send_email()` - Gmail SMTP를 통한 성공/실패 결과 이메일 전송

### 뉴스 데이터 처리
- 네이버 부동산 뉴스 API (`https://m2.land.naver.com/news/airsList.naver`)에서 당일 뉴스 목록 수집
- BeautifulSoup으로 각 뉴스 기사의 본문 내용 크롤링
- 수집된 모든 기사 내용을 Gemini에 전달하여 종합 분석 리포트 생성

### Selenium 브라우저 자동화
- Chrome headless 모드 사용
- CI 환경에서는 자동으로 chromedriver PATH 사용
- 로컬 환경에서는 `chromedriver` 바이너리 파일 사용 (`../../chromedriver` 경로)
- 로그인 실패 시 자동으로 스크린샷 저장 (`selenium_error.png`)

### 콘텐츠 포맷팅
- Gemini가 생성한 HTML 콘텐츠를 Tistory TinyMCE 에디터 형식으로 변환
- 제목은 `# 제목` 형식에서 추출
- 태그는 `태그::태그1,태그2,태그3` 형식에서 추출
- HTML 요소에 인라인 CSS 스타일 적용

## 필수 환경변수

GitHub Actions Secrets 또는 로컬 환경에 다음 변수들을 설정해야 합니다:

- `GEMINI_API_KEY`: Google AI Studio API 키
- `TISTORY_ID`: Tistory 카카오 로그인 이메일
- `TISTORY_PW`: Tistory 카카오 로그인 비밀번호
- `TISTORY_BLOG_NAME`: Tistory 블로그 서브도메인 (예: `myblog`)
- `SENDER_EMAIL`: 발신자 Gmail 주소
- `SENDER_PASSWORD`: Gmail 앱 비밀번호 (2단계 인증용)
- `RECIPIENT_EMAIL`: 결과 수신자 이메일

## 기술 스택

- **Python 3.10**: 메인 런타임
- **Selenium + Chrome**: 브라우저 자동화 (Tistory 로그인)
- **Google Generative AI (Gemini)**: 콘텐츠 생성
- **Requests**: HTTP API 호출 (Tistory 포스팅)
- **BeautifulSoup**: HTML 파싱 (뉴스 크롤링)
- **GitHub Actions**: 자동화 스케줄링

## 오류 처리

- 각 단계별로 예외 처리 및 로깅
- Selenium 로그인 실패 시 스크린샷 자동 저장
- GitHub Actions에서 오류 스크린샷 artifact로 업로드
- 모든 오류는 이메일로 알림 전송