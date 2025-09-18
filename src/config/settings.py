"""
통합 블로그 포스팅 시스템 설정 관리
환경변수, 설정 파일, 플랫폼별 설정을 통합 관리
"""

import os
import json
import configparser
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path
from .encryption import PasswordEncryption

from ..core.base_poster import PlatformType


class ConfigSource(Enum):
    """설정 소스 타입"""
    ENVIRONMENT = "environment"
    CONFIG_FILE = "config_file"
    DEFAULT = "default"


@dataclass
class PlatformConfig:
    """플랫폼별 설정"""
    enabled: bool = True
    username: str = ""
    password: str = ""
    additional_settings: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_settings is None:
            self.additional_settings = {}


@dataclass
class AIConfig:
    """AI 서비스 설정"""
    gemini_api_key: str = ""
    model_name: str = "gemini-1.5-flash"
    max_tokens: int = 8192
    temperature: float = 0.7


@dataclass
class ImageConfig:
    """이미지 처리 설정"""
    storage_path: str = "./images"
    max_file_size_mb: int = 2
    default_width: int = 800
    default_height: int = 600
    auto_cleanup_days: int = 7


@dataclass
class EmailConfig:
    """이메일 알림 설정"""
    enabled: bool = False
    sender_email: str = ""
    sender_password: str = ""
    recipient_email: str = ""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587


@dataclass
class AppConfig:
    """전체 앱 설정"""
    # 플랫폼별 설정
    naver: PlatformConfig = None
    tistory: PlatformConfig = None

    # 공통 설정
    ai: AIConfig = None
    image: ImageConfig = None
    email: EmailConfig = None

    # 앱 메타데이터
    version: str = "1.0.0"
    debug: bool = False
    headless: bool = True

    def __post_init__(self):
        if self.naver is None:
            self.naver = PlatformConfig()
        if self.tistory is None:
            self.tistory = PlatformConfig()
        if self.ai is None:
            self.ai = AIConfig()
        if self.image is None:
            self.image = ImageConfig()
        if self.email is None:
            self.email = EmailConfig()


class ConfigManager:
    """설정 관리자"""

    def __init__(self, config_file: str = "config.ini", config_dir: str = "./config"):
        """
        Args:
            config_file: 설정 파일 이름
            config_dir: 설정 파일 디렉토리
        """
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / config_file
        self.logger = logging.getLogger(__name__)

        # 설정 디렉토리 생성
        self.config_dir.mkdir(exist_ok=True)

        # 암호화 시스템 초기화
        self.password_encryption = PasswordEncryption(str(self.config_dir))

        # 설정 로드
        self.config = self._load_config()

    def _load_config(self) -> AppConfig:
        """설정 로드 (환경변수 > 파일 > 기본값 순서)"""
        try:
            # 1. 기본 설정으로 시작
            config = AppConfig()

            # 2. 설정 파일에서 로드
            if self.config_file.exists():
                file_config = self._load_from_file()
                config = self._merge_configs(config, file_config)

            # 3. 환경변수로 오버라이드
            env_config = self._load_from_environment()
            config = self._merge_configs(config, env_config)

            self.logger.info("설정 로드 완료")
            return config

        except Exception as e:
            self.logger.error(f"설정 로드 실패: {e}")
            # 실패 시 기본 설정 반환
            return AppConfig()

    def _load_from_file(self) -> AppConfig:
        """설정 파일에서 로드"""
        try:
            parser = configparser.ConfigParser()
            parser.read(self.config_file, encoding='utf-8')

            config = AppConfig()

            # 네이버 설정
            if parser.has_section('naver'):
                config.naver.enabled = parser.getboolean('naver', 'enabled', fallback=True)
                config.naver.username = parser.get('naver', 'username', fallback='')
                config.naver.password = parser.get('naver', 'password', fallback='')

            # 티스토리 설정
            if parser.has_section('tistory'):
                config.tistory.enabled = parser.getboolean('tistory', 'enabled', fallback=True)
                config.tistory.username = parser.get('tistory', 'username', fallback='')
                config.tistory.password = parser.get('tistory', 'password', fallback='')

                # 티스토리 추가 설정
                config.tistory.additional_settings['blog_name'] = parser.get('tistory', 'blog_name', fallback='')
                config.tistory.additional_settings['category_id'] = parser.getint('tistory', 'category_id', fallback=1532685)

            # AI 설정
            if parser.has_section('ai'):
                config.ai.gemini_api_key = parser.get('ai', 'gemini_api_key', fallback='')
                config.ai.model_name = parser.get('ai', 'model_name', fallback='gemini-1.5-flash')
                config.ai.temperature = parser.getfloat('ai', 'temperature', fallback=0.7)

            # 이미지 설정
            if parser.has_section('image'):
                config.image.storage_path = parser.get('image', 'storage_path', fallback='./images')
                config.image.max_file_size_mb = parser.getint('image', 'max_file_size_mb', fallback=2)

            # 이메일 설정
            if parser.has_section('email'):
                config.email.enabled = parser.getboolean('email', 'enabled', fallback=False)
                config.email.sender_email = parser.get('email', 'sender_email', fallback='')
                config.email.sender_password = parser.get('email', 'sender_password', fallback='')
                config.email.recipient_email = parser.get('email', 'recipient_email', fallback='')

            # 앱 설정
            if parser.has_section('app'):
                config.debug = parser.getboolean('app', 'debug', fallback=False)
                config.headless = parser.getboolean('app', 'headless', fallback=True)

            return config

        except Exception as e:
            self.logger.error(f"설정 파일 로드 실패: {e}")
            return AppConfig()

    def _load_from_environment(self) -> AppConfig:
        """환경변수에서 로드 (환경변수 > 암호화 파일 순서)"""
        config = AppConfig()

        # 네이버 설정 (환경변수 > 암호화 파일 > 기본값)
        config.naver.username = os.getenv('NAVER_ID', config.naver.username)
        naver_pw_env = os.getenv('NAVER_PW')

        # 디버깅 로그 추가
        naver_id_masked = config.naver.username[:3] + "*" * (len(config.naver.username) - 3) if len(config.naver.username) > 3 else "***"
        self.logger.info(f"🔑 환경변수에서 네이버 설정 로드 - 아이디: {naver_id_masked}")

        if naver_pw_env:
            config.naver.password = naver_pw_env
            self.logger.info(f"✅ 네이버 비밀번호를 환경변수에서 로드 완료 (길이: {len(naver_pw_env)}글자)")
        else:
            # 환경변수에 없으면 암호화된 파일에서 시도
            self.logger.info("🔍 환경변수에 네이버 비밀번호가 없어 암호화 파일에서 시도...")
            encrypted_pw = self.password_encryption.get_password('NAVER_PW')
            if encrypted_pw:
                config.naver.password = encrypted_pw
                self.logger.info(f"✅ 네이버 비밀번호를 암호화 파일에서 로드 완료 (길이: {len(encrypted_pw)}글자)")
            else:
                self.logger.warning("⚠️ 네이버 비밀번호를 찾을 수 없습니다.")

        # 티스토리 설정 (환경변수 > 암호화 파일 > 기본값)
        config.tistory.username = os.getenv('TISTORY_ID', config.tistory.username)
        tistory_pw_env = os.getenv('TISTORY_PW')
        if tistory_pw_env:
            config.tistory.password = tistory_pw_env
        else:
            # 환경변수에 없으면 암호화된 파일에서 시도
            encrypted_pw = self.password_encryption.get_password('TISTORY_PW')
            if encrypted_pw:
                config.tistory.password = encrypted_pw

        # 티스토리 추가 설정
        blog_name = os.getenv('TISTORY_BLOG_NAME')
        if blog_name:
            config.tistory.additional_settings['blog_name'] = blog_name

        # AI 설정
        config.ai.gemini_api_key = os.getenv('GEMINI_API_KEY', config.ai.gemini_api_key)

        # 이메일 설정
        config.email.sender_email = os.getenv('SENDER_EMAIL', config.email.sender_email)
        config.email.sender_password = os.getenv('SENDER_PASSWORD', config.email.sender_password)
        config.email.recipient_email = os.getenv('RECIPIENT_EMAIL', config.email.recipient_email)

        # 앱 설정 (환경변수가 있을 때만 오버라이드)
        debug_env = os.getenv('DEBUG')
        if debug_env:
            config.debug = debug_env.lower() in ('true', '1', 'yes', 'on')

        headless_env = os.getenv('HEADLESS')
        if headless_env:
            config.headless = headless_env.lower() in ('true', '1', 'yes', 'on')
        else:
            # 환경변수가 없으면 기본값을 유지하지 않고 None으로 표시
            # _merge_configs에서 파일 설정이 우선되도록 함
            config.headless = None

        return config

    def _merge_configs(self, base: AppConfig, override: AppConfig) -> AppConfig:
        """두 설정을 병합 (override가 우선)"""
        try:
            # 간단한 필드는 직접 오버라이드 (환경변수가 설정된 경우만)
            if hasattr(override, 'debug') and override.debug is not None:
                base.debug = override.debug
            if hasattr(override, 'headless') and override.headless is not None:
                base.headless = override.headless

            # 플랫폼별 설정 병합
            if override.naver.username:
                base.naver.username = override.naver.username
            if override.naver.password:
                base.naver.password = override.naver.password

            if override.tistory.username:
                base.tistory.username = override.tistory.username
            if override.tistory.password:
                base.tistory.password = override.tistory.password
            if override.tistory.additional_settings:
                base.tistory.additional_settings.update(override.tistory.additional_settings)

            # AI 설정 병합
            if override.ai.gemini_api_key:
                base.ai.gemini_api_key = override.ai.gemini_api_key

            # 이메일 설정 병합
            if override.email.sender_email:
                base.email.sender_email = override.email.sender_email
            if override.email.sender_password:
                base.email.sender_password = override.email.sender_password
            if override.email.recipient_email:
                base.email.recipient_email = override.email.recipient_email

            return base

        except Exception as e:
            self.logger.error(f"설정 병합 실패: {e}")
            return base

    def save_to_file(self) -> bool:
        """현재 설정을 파일에 저장"""
        try:
            parser = configparser.ConfigParser()

            # 네이버 설정
            parser.add_section('naver')
            parser.set('naver', 'enabled', str(self.config.naver.enabled))
            parser.set('naver', 'username', self.config.naver.username)
            # 비밀번호는 보안상 저장하지 않음

            # 티스토리 설정
            parser.add_section('tistory')
            parser.set('tistory', 'enabled', str(self.config.tistory.enabled))
            parser.set('tistory', 'username', self.config.tistory.username)
            # 비밀번호는 보안상 저장하지 않음

            blog_name = self.config.tistory.additional_settings.get('blog_name', '')
            if blog_name:
                parser.set('tistory', 'blog_name', blog_name)

            category_id = self.config.tistory.additional_settings.get('category_id', 1532685)
            parser.set('tistory', 'category_id', str(category_id))

            # AI 설정 (API 키는 보안상 저장하지 않음)
            parser.add_section('ai')
            parser.set('ai', 'model_name', self.config.ai.model_name)
            parser.set('ai', 'temperature', str(self.config.ai.temperature))

            # 이미지 설정
            parser.add_section('image')
            parser.set('image', 'storage_path', self.config.image.storage_path)
            parser.set('image', 'max_file_size_mb', str(self.config.image.max_file_size_mb))

            # 이메일 설정 (비밀번호 제외)
            parser.add_section('email')
            parser.set('email', 'enabled', str(self.config.email.enabled))
            parser.set('email', 'sender_email', self.config.email.sender_email)
            parser.set('email', 'recipient_email', self.config.email.recipient_email)

            # 앱 설정
            parser.add_section('app')
            parser.set('app', 'debug', str(self.config.debug))
            parser.set('app', 'headless', str(self.config.headless))

            with open(self.config_file, 'w', encoding='utf-8') as f:
                parser.write(f)

            self.logger.info(f"설정 파일 저장 완료: {self.config_file}")
            return True

        except Exception as e:
            self.logger.error(f"설정 파일 저장 실패: {e}")
            return False

    def create_sample_config(self) -> bool:
        """샘플 설정 파일 생성"""
        try:
            sample_config = """# 통합 블로그 포스팅 시스템 설정 파일
# 보안이 필요한 값들(비밀번호, API 키)은 환경변수를 사용하세요.

[naver]
enabled = true
username = your_naver_id
# password는 환경변수 NAVER_PW로 설정하세요

[tistory]
enabled = true
username = your_tistory_id
blog_name = your_blog_name
category_id = 1532685
# password는 환경변수 TISTORY_PW로 설정하세요

[ai]
model_name = gemini-1.5-flash
temperature = 0.7
# gemini_api_key는 환경변수 GEMINI_API_KEY로 설정하세요

[image]
storage_path = ./images
max_file_size_mb = 2

[email]
enabled = false
sender_email = your_sender@gmail.com
recipient_email = your_recipient@gmail.com
# 이메일 비밀번호는 환경변수 SENDER_PASSWORD로 설정하세요

[app]
debug = false
# headless = true  # 브라우저를 숨김 모드로 실행 (기본값: true)
# headless = false # 브라우저를 화면에 표시 (디버깅용)
headless = true
# 환경변수 HEADLESS=false로 설정하면 브라우저가 화면에 표시됩니다
"""

            sample_file = self.config_dir / "config.sample.ini"
            with open(sample_file, 'w', encoding='utf-8') as f:
                f.write(sample_config)

            self.logger.info(f"샘플 설정 파일 생성 완료: {sample_file}")
            return True

        except Exception as e:
            self.logger.error(f"샘플 설정 파일 생성 실패: {e}")
            return False

    def get_platform_config(self, platform: PlatformType) -> PlatformConfig:
        """플랫폼별 설정 반환"""
        if platform == PlatformType.NAVER:
            return self.config.naver
        elif platform == PlatformType.TISTORY:
            return self.config.tistory
        else:
            raise ValueError(f"지원하지 않는 플랫폼: {platform}")

    def validate_config(self) -> Dict[str, List[str]]:
        """설정 유효성 검증"""
        errors = {}

        # AI 설정 검증
        if not self.config.ai.gemini_api_key:
            errors.setdefault('ai', []).append("Gemini API 키가 설정되지 않았습니다")

        # 플랫폼별 설정 검증
        platforms_to_check = []

        if self.config.naver.enabled:
            platforms_to_check.append(('naver', self.config.naver))
        if self.config.tistory.enabled:
            platforms_to_check.append(('tistory', self.config.tistory))

        for platform_name, platform_config in platforms_to_check:
            if not platform_config.username:
                errors.setdefault(platform_name, []).append("사용자명이 설정되지 않았습니다")
            if not platform_config.password:
                errors.setdefault(platform_name, []).append("비밀번호가 설정되지 않았습니다")

        # 티스토리 특별 검증
        if self.config.tistory.enabled:
            blog_name = self.config.tistory.additional_settings.get('blog_name')
            if not blog_name:
                errors.setdefault('tistory', []).append("블로그 이름이 설정되지 않았습니다")

        return errors

    def is_valid(self) -> bool:
        """설정이 유효한지 확인"""
        errors = self.validate_config()
        return len(errors) == 0

    def get_enabled_platforms(self) -> List[PlatformType]:
        """활성화된 플랫폼 목록 반환"""
        enabled = []
        if self.config.naver.enabled and self.config.naver.username and self.config.naver.password:
            enabled.append(PlatformType.NAVER)
        if self.config.tistory.enabled and self.config.tistory.username and self.config.tistory.password:
            enabled.append(PlatformType.TISTORY)
        return enabled

    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 변환 (비밀번호 제외)"""
        config_dict = asdict(self.config)

        # 보안 정보 제거
        if 'password' in config_dict.get('naver', {}):
            config_dict['naver']['password'] = '***'
        if 'password' in config_dict.get('tistory', {}):
            config_dict['tistory']['password'] = '***'
        if 'gemini_api_key' in config_dict.get('ai', {}):
            config_dict['ai']['gemini_api_key'] = '***'
        if 'sender_password' in config_dict.get('email', {}):
            config_dict['email']['sender_password'] = '***'

        return config_dict

    def save_config_from_gui(self, gui_values: Dict[str, Dict[str, Any]]) -> bool:
        """GUI에서 수정된 설정을 config.ini 파일에 저장"""
        try:
            config_parser = configparser.ConfigParser()

            # 기존 config.ini 파일이 있으면 로드
            if self.config_file.exists():
                config_parser.read(self.config_file, encoding='utf-8')

            # AI 설정 업데이트
            if 'ai' in gui_values:
                if not config_parser.has_section('ai'):
                    config_parser.add_section('ai')

                ai_values = gui_values['ai']
                if 'model_name' in ai_values and ai_values['model_name']:
                    config_parser.set('ai', 'model_name', str(ai_values['model_name']))
                if 'temperature' in ai_values and ai_values['temperature']:
                    config_parser.set('ai', 'temperature', str(ai_values['temperature']))
                # API 키는 환경변수로 관리하므로 config.ini에 저장하지 않음

            # 네이버 설정 업데이트
            if 'naver' in gui_values:
                if not config_parser.has_section('naver'):
                    config_parser.add_section('naver')

                naver_values = gui_values['naver']
                if 'enabled' in naver_values:
                    config_parser.set('naver', 'enabled', str(naver_values['enabled']).lower())
                if 'username' in naver_values and naver_values['username']:
                    config_parser.set('naver', 'username', str(naver_values['username']))
                # 비밀번호는 환경변수 + 암호화 파일로 설정
                if 'password' in naver_values and naver_values['password']:
                    import os
                    password = str(naver_values['password'])
                    # 환경변수 설정 (현재 세션용)
                    os.environ['NAVER_PW'] = password
                    # 암호화 파일 저장 (영구 저장용)
                    self.password_encryption.save_password('NAVER_PW', password)
                    self.logger.info("네이버 비밀번호가 환경변수 및 암호화 파일에 저장되었습니다")

            # 티스토리 설정 업데이트
            if 'tistory' in gui_values:
                if not config_parser.has_section('tistory'):
                    config_parser.add_section('tistory')

                tistory_values = gui_values['tistory']
                if 'enabled' in tistory_values:
                    config_parser.set('tistory', 'enabled', str(tistory_values['enabled']).lower())
                if 'username' in tistory_values and tistory_values['username']:
                    config_parser.set('tistory', 'username', str(tistory_values['username']))
                if 'blog_name' in tistory_values and tistory_values['blog_name']:
                    config_parser.set('tistory', 'blog_name', str(tistory_values['blog_name']))
                if 'category_id' in tistory_values and tistory_values['category_id']:
                    config_parser.set('tistory', 'category_id', str(tistory_values['category_id']))
                # 비밀번호는 환경변수 + 암호화 파일로 설정
                if 'password' in tistory_values and tistory_values['password']:
                    import os
                    password = str(tistory_values['password'])
                    # 환경변수 설정 (현재 세션용)
                    os.environ['TISTORY_PW'] = password
                    # 암호화 파일 저장 (영구 저장용)
                    self.password_encryption.save_password('TISTORY_PW', password)
                    self.logger.info("티스토리 비밀번호가 환경변수 및 암호화 파일에 저장되었습니다")

            # 이미지 설정 업데이트
            if 'image' in gui_values:
                if not config_parser.has_section('image'):
                    config_parser.add_section('image')

                image_values = gui_values['image']
                if 'storage_path' in image_values and image_values['storage_path']:
                    config_parser.set('image', 'storage_path', str(image_values['storage_path']))
                if 'max_file_size_mb' in image_values and image_values['max_file_size_mb']:
                    config_parser.set('image', 'max_file_size_mb', str(image_values['max_file_size_mb']))

            # 앱 설정 업데이트
            if 'app' in gui_values:
                if not config_parser.has_section('app'):
                    config_parser.add_section('app')

                app_values = gui_values['app']
                if 'debug' in app_values:
                    config_parser.set('app', 'debug', str(app_values['debug']).lower())
                if 'headless' in app_values:
                    config_parser.set('app', 'headless', str(app_values['headless']).lower())

            # 파일에 저장
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                config_parser.write(f)

            self.logger.info(f"설정 파일 저장 완료: {self.config_file}")

            # 설정 다시 로드
            self.config = self._load_config()

            return True

        except Exception as e:
            self.logger.error(f"설정 저장 실패: {e}")
            return False

    def backup_config(self) -> bool:
        """현재 설정 파일 백업"""
        try:
            if not self.config_file.exists():
                self.logger.warning("백업할 설정 파일이 없습니다.")
                return False

            backup_file = self.config_dir / f"config.backup.{int(time.time())}.ini"

            import shutil
            shutil.copy2(self.config_file, backup_file)

            self.logger.info(f"설정 파일 백업 완료: {backup_file}")
            return True

        except Exception as e:
            self.logger.error(f"설정 백업 실패: {e}")
            return False

    def restore_config(self, backup_file: Path) -> bool:
        """백업 파일에서 설정 복원"""
        try:
            if not backup_file.exists():
                self.logger.error(f"백업 파일이 존재하지 않습니다: {backup_file}")
                return False

            import shutil
            shutil.copy2(backup_file, self.config_file)

            # 설정 다시 로드
            self._load_config()

            self.logger.info(f"설정 복원 완료: {backup_file} -> {self.config_file}")
            return True

        except Exception as e:
            self.logger.error(f"설정 복원 실패: {e}")
            return False

    def get_backup_files(self) -> List[Path]:
        """백업 파일 목록 반환"""
        backup_files = list(self.config_dir.glob("config.backup.*.ini"))
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return backup_files

    def set_headless_mode(self, headless: bool, save_to_file: bool = True) -> bool:
        """
        헤드리스 모드 설정을 변경하고 선택적으로 파일에 저장

        Args:
            headless: 헤드리스 모드 활성화 여부
            save_to_file: 설정 파일에 저장 여부

        Returns:
            설정 변경 성공 여부
        """
        try:
            # 메모리 설정 변경
            self.config.headless = headless

            # 디버그 모드 로깅
            status = "활성화" if headless else "비활성화"
            self.logger.info(f"🔧 헤드리스 모드 {status}")

            # 파일에 저장
            if save_to_file:
                success = self.save_to_file()
                if success:
                    self.logger.info(f"✅ 헤드리스 모드 설정 저장 완료: {headless}")
                else:
                    self.logger.error("❌ 헤드리스 모드 설정 저장 실패")
                return success

            return True

        except Exception as e:
            self.logger.error(f"헤드리스 모드 설정 변경 실패: {e}")
            return False

    def toggle_headless_mode(self, save_to_file: bool = True) -> bool:
        """
        헤드리스 모드를 토글하고 선택적으로 파일에 저장

        Args:
            save_to_file: 설정 파일에 저장 여부

        Returns:
            설정 변경 성공 여부
        """
        current_mode = self.config.headless
        new_mode = not current_mode

        self.logger.info(f"🔄 헤드리스 모드 토글: {current_mode} → {new_mode}")

        return self.set_headless_mode(new_mode, save_to_file)

    def get_headless_mode(self) -> bool:
        """현재 헤드리스 모드 설정 반환"""
        return self.config.headless