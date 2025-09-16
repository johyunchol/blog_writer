# 🚀 통합 블로그 포스팅 시스템

네이버 블로그와 티스토리에 동시 포스팅이 가능한 AI 기반 자동 포스팅 시스템

## 📖 프로젝트 설명

Google Gemini API를 활용하여 AI 콘텐츠 생성과 다중 플랫폼 블로그 포스팅을 제공하는 통합 시스템입니다. GUI와 CLI 모드를 모두 지원하며, 네이버 블로그와 티스토리에 동시 포스팅이 가능합니다.

## ✨ 주요 기능

- 🤖 **Gemini AI 콘텐츠 생성**: 부동산 뉴스 분석 및 자유 주제 글 작성
- 📝 **다중 플랫폼 포스팅**: 네이버 블로그 + 티스토리 동시 포스팅
- 🖼️ **이미지 자동 삽입**: AI 생성 이미지 캡션 기반 자동 이미지 처리
- 🖥️ **GUI + CLI 지원**: 직관적인 GUI 인터페이스와 자동화용 CLI 모드
- ⚙️ **설정 관리**: 간편한 설정 파일 및 환경변수 관리

## 🎯 사용 방법

### GUI 모드 (추천)
```bash
python3 blog_poster_gui.py
```

### CLI 모드 (자동화)
```bash
python3 unified_blog_poster.py
```

## 📦 설치 및 설정

### 1. 환경변수 설정
```bash
export GEMINI_API_KEY="your_gemini_api_key"
export NAVER_PW="your_naver_password"
export TISTORY_PW="your_tistory_password"
export SENDER_PASSWORD="your_email_password"  # 선택사항
```

### 2. 설정 파일 생성
```bash
cp config/config.sample.ini config/config.ini
# config.ini 편집하여 계정 정보 입력
```

### 3. 의존성 설치
```bash
pip install selenium google-generativeai requests pillow
# Chrome 브라우저 및 ChromeDriver 필요
```

## 🏗️ 프로젝트 구조

```
blog_writer/
├── blog_poster_gui.py          # GUI 실행 스크립트
├── unified_blog_poster.py      # CLI 실행 스크립트
├── config/
│   ├── config.sample.ini       # 설정 파일 샘플
│   └── config.ini              # 실제 설정 파일
├── src/
│   ├── core/                   # 핵심 모듈
│   │   ├── base_poster.py      # 추상 기본 클래스
│   │   ├── content_generator.py # AI 콘텐츠 생성
│   │   └── image_manager.py    # 이미지 처리
│   ├── platforms/              # 플랫폼별 구현
│   │   ├── tistory_poster.py   # 티스토리 포스터
│   │   ├── naver_poster.py     # 네이버 포스터
│   │   └── poster_factory.py   # 팩토리 패턴
│   ├── config/                 # 설정 관리
│   │   └── settings.py         # 설정 매니저
│   └── gui/                    # GUI 모듈
│       ├── main_window.py      # 메인 윈도우
│       └── widgets.py          # 커스텀 위젯
└── claudedocs/                 # 개발 문서
```

## 🎨 GUI 인터페이스

### 메인 포스팅 화면
- 플랫폼 선택 (네이버/티스토리)
- 콘텐츠 생성 설정 (뉴스 분석/자유 주제)
- 실시간 진행률 표시
- 결과 로그 및 미리보기

### 설정 화면
- AI 설정 (Gemini API, 모델 선택)
- 플랫폼별 계정 설정
- 이미지 및 기타 옵션 설정

## 📊 지원 플랫폼

| 플랫폼 | 상태 | 인증 방식 | 주요 기능 |
|--------|------|-----------|-----------|
| **티스토리** | ✅ 완료 | Selenium + API | HTML 포스팅, 이미지 업로드 |
| **네이버 블로그** | ✅ 완료 | Selenium | 텍스트/이미지 교대 배치 |

## 🚦 개발 단계

### ✅ Phase 1 완료: 공통 모듈
- 추상 클래스 및 인터페이스 정의
- 설정 관리 시스템
- AI 콘텐츠 생성 엔진
- 이미지 처리 시스템

### ✅ Phase 2 완료: 플랫폼 구현
- 티스토리 포스터 리팩토링
- 네이버 포스터 구현
- 팩토리 패턴 적용
- 통합 테스트 스크립트

### ✅ Phase 3 완료: GUI 개발
- tkinter 기반 현대적 GUI
- 실시간 진행률 표시
- 설정 관리 인터페이스
- 백엔드 완전 연동

## 🔧 개발 가이드

### 아키텍처 패턴
- **Abstract Factory Pattern**: 플랫폼별 포스터 생성
- **Strategy Pattern**: 콘텐츠 생성 전략 선택
- **Observer Pattern**: GUI 상태 업데이트
- **MVC Pattern**: GUI와 비즈니스 로직 분리

### 주요 클래스
- `AbstractPoster`: 모든 플랫폼 포스터의 기본 클래스
- `ContentGenerator`: Gemini AI 기반 콘텐츠 생성
- `ConfigManager`: 설정 파일 및 환경변수 관리
- `BlogPosterGUI`: tkinter 기반 메인 GUI

## 📝 사용 예시

### 1. GUI에서 부동산 뉴스 포스팅
1. GUI 실행 → 네이버/티스토리 선택
2. "부동산 뉴스 분석" 선택
3. "콘텐츠 생성" → "블로그 포스팅"

### 2. CLI에서 자동화
```bash
# 환경변수 설정 후
python3 unified_blog_poster.py
# 대화형 메뉴에서 옵션 선택
```

## 🔍 테스트 결과

- ✅ 모든 모듈 import 테스트 통과
- ✅ 플랫폼별 포스터 정상 작동
- ✅ GUI와 백엔드 연동 완료
- ✅ 설정 관리 시스템 검증
- ✅ 에러 처리 및 안정성 확보

## 🤝 기여 방법

1. 이슈 생성 또는 기능 제안
2. Fork 후 기능 개발
3. 테스트 코드 작성
4. Pull Request 제출

## 📄 라이선스

MIT License

## 📞 지원

- 버그 리포트: GitHub Issues
- 기능 제안: GitHub Discussions
- 문서: `claudedocs/` 디렉토리 참조

---

**개발 완료**: Phase 3 GUI 개발까지 완료 ✅
**다음 단계**: 사용자 피드백 수집 및 기능 개선