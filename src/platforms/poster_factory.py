"""
블로그 포스터 팩토리
플랫폼별 포스터 인스턴스 생성 및 관리를 담당
"""

from typing import Dict, Type, Optional
import logging

from ..core.base_poster import AbstractPoster, PlatformType
from ..config.settings import ConfigManager, PlatformConfig
from .tistory_poster import TistoryPoster
from .naver_poster import NaverPoster


class PosterFactory:
    """블로그 포스터 팩토리 클래스"""

    # 플랫폼별 포스터 클래스 등록
    _poster_classes: Dict[PlatformType, Type[AbstractPoster]] = {
        PlatformType.TISTORY: TistoryPoster,
        PlatformType.NAVER: NaverPoster
    }

    def __init__(self, config_manager: ConfigManager):
        """
        Args:
            config_manager: 설정 관리자 인스턴스
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)

    @classmethod
    def register_poster(cls, platform: PlatformType, poster_class: Type[AbstractPoster]):
        """새로운 플랫폼 포스터 클래스 등록"""
        cls._poster_classes[platform] = poster_class

    @classmethod
    def create_poster(cls, platform: str, config_manager: ConfigManager, **kwargs) -> Optional[AbstractPoster]:
        """
        플랫폼별 포스터 인스턴스 생성

        Args:
            platform: 대상 플랫폼 (문자열)
            config_manager: 설정 관리자 인스턴스
            **kwargs: 추가 설정 파라미터

        Returns:
            생성된 포스터 인스턴스 또는 None
        """
        logger = logging.getLogger(__name__)

        try:
            # 문자열을 PlatformType enum으로 변환
            if isinstance(platform, str):
                platform_enum = PlatformType.from_string(platform)
            else:
                platform_enum = platform

            # 플랫폼 지원 여부 확인
            if platform_enum not in cls._poster_classes:
                logger.error(f"지원하지 않는 플랫폼: {platform}")
                return None

            # 플랫폼 설정 가져오기
            platform_config = config_manager.get_platform_config(platform_enum)

            if not platform_config.enabled:
                logger.warning(f"플랫폼이 비활성화됨: {platform}")
                return None

            # 필수 설정 확인
            if not platform_config.username or not platform_config.password:
                logger.error(f"플랫폼 설정이 불완전함: {platform}")
                return None

            # 포스터 클래스 가져오기
            poster_class = cls._poster_classes[platform_enum]

            # 플랫폼별 특수 파라미터 처리
            poster_kwargs = {
                'username': platform_config.username,
                'password': platform_config.password,
                'headless': kwargs.get('headless', config_manager.config.headless),
                **kwargs
            }

            # 플랫폼별 추가 설정
            if platform_enum == PlatformType.TISTORY:
                poster_kwargs.update(cls._get_tistory_specific_kwargs(platform_config, kwargs))
            elif platform_enum == PlatformType.NAVER:
                poster_kwargs.update(cls._get_naver_specific_kwargs(platform_config, kwargs))

            # 포스터 인스턴스 생성
            poster = poster_class(**poster_kwargs)

            logger.info(f"{platform_enum.value} 포스터 생성 완료")
            return poster

        except Exception as e:
            logger.error(f"포스터 생성 실패 ({platform}): {e}")
            return None

    @classmethod
    def _get_tistory_specific_kwargs(cls, config: PlatformConfig, kwargs: dict) -> dict:
        """티스토리 전용 파라미터 생성"""
        tistory_kwargs = {}

        # 블로그 이름 (필수)
        blog_name = kwargs.get('blog_name') or config.additional_settings.get('blog_name')
        if not blog_name:
            raise ValueError("티스토리 블로그 이름이 설정되지 않았습니다")

        tistory_kwargs['blog_name'] = blog_name

        # 카테고리 ID
        category_id = kwargs.get('category_id') or config.additional_settings.get('category_id', 1532685)
        tistory_kwargs['category_id'] = int(category_id)

        return tistory_kwargs

    @classmethod
    def _get_naver_specific_kwargs(cls, config: PlatformConfig, kwargs: dict) -> dict:
        """네이버 전용 파라미터 생성"""
        naver_kwargs = {}

        # 네이버는 현재 추가 파라미터 없음
        # 향후 블로그 URL, 카테고리 등 추가 가능

        return naver_kwargs

    def create_all_available_posters(self, **kwargs) -> Dict[PlatformType, AbstractPoster]:
        """
        설정된 모든 플랫폼의 포스터 생성

        Returns:
            플랫폼별 포스터 인스턴스 딕셔너리
        """
        posters = {}
        enabled_platforms = self.config_manager.get_enabled_platforms()

        for platform in enabled_platforms:
            poster = PosterFactory.create_poster(platform.value, self.config_manager, **kwargs)
            if poster:
                posters[platform] = poster
            else:
                self.logger.warning(f"포스터 생성 실패: {platform}")

        self.logger.info(f"활성 포스터 {len(posters)}개 생성완료: {list(posters.keys())}")
        return posters

    @classmethod
    def get_supported_platforms(cls) -> list:
        """지원하는 플랫폼 목록 반환"""
        return list(cls._poster_classes.keys())

    @classmethod
    def is_platform_supported(cls, platform: PlatformType) -> bool:
        """플랫폼 지원 여부 확인"""
        return platform in cls._poster_classes

    @classmethod
    def validate_platform_config(cls, platform: PlatformType, config_manager: ConfigManager) -> Dict[str, list]:
        """플랫폼 설정 유효성 검증"""
        errors = {}

        try:
            platform_config = config_manager.get_platform_config(platform)

            # 기본 설정 검증
            if not platform_config.username:
                errors.setdefault('basic', []).append("사용자명이 설정되지 않았습니다")

            if not platform_config.password:
                errors.setdefault('basic', []).append("비밀번호가 설정되지 않았습니다")

            # 플랫폼별 특수 설정 검증
            if platform == PlatformType.TISTORY:
                blog_name = platform_config.additional_settings.get('blog_name')
                if not blog_name:
                    errors.setdefault('tistory', []).append("블로그 이름이 설정되지 않았습니다")

            elif platform == PlatformType.NAVER:
                # 네이버 특수 설정 검증 (현재 없음)
                pass

        except Exception as e:
            errors.setdefault('system', []).append(f"설정 검증 중 오류: {e}")

        return errors


class MultiPlatformPoster:
    """다중 플랫폼 동시 포스팅 관리자"""

    def __init__(self, config_manager: ConfigManager):
        """
        Args:
            config_manager: 설정 관리자 인스턴스
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)

    def post_to_all_platforms(self, blog_post, **kwargs) -> Dict[PlatformType, dict]:
        """
        모든 활성화된 플랫폼에 동시 포스팅

        Args:
            blog_post: BlogPost 인스턴스
            **kwargs: 추가 설정

        Returns:
            플랫폼별 포스팅 결과
        """
        results = {}
        posters = self.factory.create_all_available_posters(**kwargs)

        if not posters:
            self.logger.warning("생성된 포스터가 없습니다")
            return results

        self.logger.info(f"{len(posters)}개 플랫폼에 동시 포스팅 시작")

        # 각 플랫폼에 순차적으로 포스팅
        for platform, poster in posters.items():
            try:
                with poster:  # 컨텍스트 매니저 사용으로 자동 리소스 관리
                    result = poster.post_article(blog_post)
                    results[platform] = {
                        'success': result.success,
                        'message': result.message,
                        'post_url': result.post_url,
                        'post_id': result.post_id,
                        'error_code': result.error_code
                    }

                    if result.success:
                        self.logger.info(f"{platform.value} 포스팅 성공: {result.post_url}")
                    else:
                        self.logger.error(f"{platform.value} 포스팅 실패: {result.message}")

            except Exception as e:
                error_msg = f"{platform.value} 포스팅 중 예외 발생: {e}"
                self.logger.error(error_msg)
                results[platform] = {
                    'success': False,
                    'message': error_msg,
                    'error_code': 'EXCEPTION'
                }

        # 결과 요약
        success_count = sum(1 for r in results.values() if r['success'])
        total_count = len(results)

        self.logger.info(f"다중 플랫폼 포스팅 완료: {success_count}/{total_count} 성공")

        return results

    def post_to_specific_platforms(self, blog_post, platforms: list, **kwargs) -> Dict[PlatformType, dict]:
        """
        지정된 플랫폼들에만 포스팅

        Args:
            blog_post: BlogPost 인스턴스
            platforms: 대상 플랫폼 리스트
            **kwargs: 추가 설정

        Returns:
            플랫폼별 포스팅 결과
        """
        results = {}

        for platform in platforms:
            if not isinstance(platform, PlatformType):
                self.logger.error(f"잘못된 플랫폼 타입: {platform}")
                continue

            try:
                poster = PosterFactory.create_poster(platform.value, self.config_manager, **kwargs)
                if not poster:
                    results[platform] = {
                        'success': False,
                        'message': f"포스터 생성 실패: {platform}",
                        'error_code': 'POSTER_CREATE_FAILED'
                    }
                    continue

                with poster:
                    result = poster.post_article(blog_post)
                    results[platform] = {
                        'success': result.success,
                        'message': result.message,
                        'post_url': result.post_url,
                        'post_id': result.post_id,
                        'error_code': result.error_code
                    }

            except Exception as e:
                error_msg = f"{platform.value} 포스팅 중 예외 발생: {e}"
                self.logger.error(error_msg)
                results[platform] = {
                    'success': False,
                    'message': error_msg,
                    'error_code': 'EXCEPTION'
                }

        return results

    def get_platform_status(self) -> Dict[PlatformType, dict]:
        """각 플랫폼의 설정 상태 확인"""
        status = {}
        enabled_platforms = self.config_manager.get_enabled_platforms()

        for platform in PlatformType:
            config_errors = PosterFactory.validate_platform_config(platform, self.config_manager)
            is_enabled = platform in enabled_platforms
            is_configured = len(config_errors) == 0

            status[platform] = {
                'enabled': is_enabled,
                'configured': is_configured,
                'errors': config_errors,
                'ready': is_enabled and is_configured
            }

        return status