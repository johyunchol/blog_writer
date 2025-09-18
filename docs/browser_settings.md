# 브라우저 설정 가이드

블로그 포스팅 시 브라우저 표시/숨김 모드를 제어하는 방법을 설명합니다.

## 브라우저 헤드리스 모드란?

- **헤드리스 모드 (headless=true)**: 브라우저가 백그라운드에서 실행되며 화면에 표시되지 않음 (기본값)
- **표시 모드 (headless=false)**: 브라우저 창이 화면에 표시되어 동작을 확인할 수 있음 (디버깅용)

## 설정 방법

### 1. 환경변수로 설정 (권장)

```bash
# 브라우저를 화면에 표시
export HEADLESS=false

# 브라우저를 숨김 모드로 실행 (기본값)
export HEADLESS=true
```

### 2. 설정 파일로 설정

`config/config.ini` 파일에 다음과 같이 설정:

```ini
[app]
debug = false
headless = true   # 브라우저 숨김 모드 (기본값)
# headless = false  # 브라우저 화면에 표시 (디버깅용)
```

### 3. 프로그래밍 방식으로 설정

```python
from src.platforms.poster_factory import PosterFactory
from src.config.settings import ConfigManager

config = ConfigManager()

# 브라우저를 화면에 표시
poster = PosterFactory.create_poster('naver', config, headless=False)

# 브라우저를 숨김 모드로 실행 (설정값 사용)
poster = PosterFactory.create_poster('naver', config)
```

## 사용 예시

### 디버깅 시 브라우저 표시

```bash
# 환경변수 설정
export HEADLESS=false

# 스크립트 실행
python your_posting_script.py
```

### 자동화 시 브라우저 숨김 (기본값)

```bash
# 환경변수 설정 (선택사항, 기본값이 true)
export HEADLESS=true

# 스크립트 실행
python your_posting_script.py
```

### 일회성으로 브라우저 표시

```bash
# 명령어와 함께 환경변수 설정
HEADLESS=false python your_posting_script.py
```

## 설정 우선순위

1. 코드에서 직접 지정한 `headless` 매개변수
2. 환경변수 `HEADLESS`
3. 설정 파일의 `[app] headless` 값
4. 기본값 (true - 숨김 모드)

## 주의사항

- **프로덕션 환경**에서는 `headless=true`를 사용하여 리소스를 절약하세요
- **디버깅/테스트**할 때만 `headless=false`를 사용하세요
- **CI/CD 환경**에서는 항상 헤드리스 모드를 사용해야 합니다
- 브라우저가 화면에 표시될 때는 포스팅 과정을 방해하지 마세요

## 동적 헤드리스 모드 변경

### 편의 스크립트 사용

프로젝트에 포함된 `scripts/toggle_headless.py` 스크립트를 사용하여 간편하게 헤드리스 모드를 변경할 수 있습니다:

```bash
# 대화형 모드로 헤드리스 설정 변경
python scripts/toggle_headless.py

# 또는 직접 실행
./scripts/toggle_headless.py
```

스크립트 실행 시 다음 옵션들을 선택할 수 있습니다:
- 헤드리스 모드 토글 (현재 상태 반전)
- 헤드리스 모드 활성화 (브라우저 숨김)
- 헤드리스 모드 비활성화 (브라우저 표시)
- 현재 상태 확인

### 프로그래밍 방식으로 변경

```python
from src.config.settings import ConfigManager

config = ConfigManager()

# 헤드리스 모드 비활성화 (브라우저 표시)
config.set_headless_mode(False)

# 헤드리스 모드 활성화 (브라우저 숨김)
config.set_headless_mode(True)

# 헤드리스 모드 토글
config.toggle_headless_mode()

# 현재 상태 확인
current_mode = config.get_headless_mode()
print(f"헤드리스 모드: {current_mode}")
```

## 트러블슈팅

### 브라우저가 화면에 나타나지 않을 때

```bash
# 환경변수 확인
echo $HEADLESS

# 설정 파일 확인
cat config/config.ini | grep headless

# 편의 스크립트로 브라우저 표시 모드로 변경
python scripts/toggle_headless.py

# 또는 강제로 표시 모드로 실행
HEADLESS=false python your_script.py
```

### 헤드리스 모드에서 오류가 발생할 때

```bash
# 편의 스크립트로 브라우저 표시 모드로 변경
python scripts/toggle_headless.py

# 또는 브라우저를 표시하여 어떤 문제가 있는지 확인
HEADLESS=false python your_script.py
```

### 설정이 저장되지 않을 때

```bash
# 설정 파일 권한 확인
ls -la config/config.ini

# 설정 파일이 존재하는지 확인
test -f config/config.ini && echo "설정 파일 존재" || echo "설정 파일 없음"

# 편의 스크립트로 설정 확인 및 변경
python scripts/toggle_headless.py
```