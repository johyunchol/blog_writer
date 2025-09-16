#!/usr/bin/env python3
"""
통합 블로그 포스팅 시스템 메인 스크립트
네이버와 티스토리 블로그에 동시 포스팅 가능한 통합 시스템
"""

import sys
import os
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core import (
    ContentGenerator, ContentRequest, GeneratedContent,
    ImageManager, ImageRequest, ImageSource,
    BlogPost, PlatformType
)
from src.config import ConfigManager
from src.platforms import PosterFactory, MultiPlatformPoster


def setup_logging(debug: bool = False) -> None:
    """로깅 설정"""
    log_level = logging.DEBUG if debug else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('blog_poster.log', encoding='utf-8')
        ]
    )


def print_banner():
    """시작 배너 출력"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║              통합 블로그 포스팅 시스템 v1.0                 ║
║                                                              ║
║  • 네이버 블로그 & 티스토리 동시 포스팅                     ║
║  • Gemini AI 기반 자동 콘텐츠 생성                          ║
║  • 이미지 자동 삽입 및 최적화                               ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_platform_status(config_manager: ConfigManager, factory: PosterFactory):
    """플랫폼 상태 출력"""
    print("\n📋 플랫폼 설정 상태:")
    print("-" * 50)

    multi_poster = MultiPlatformPoster(config_manager)
    status = multi_poster.get_platform_status()

    for platform, info in status.items():
        status_icon = "✅" if info['ready'] else "❌"
        enabled_text = "활성화" if info['enabled'] else "비활성화"
        configured_text = "설정완료" if info['configured'] else "설정필요"

        print(f"{status_icon} {platform.value.upper():<8} - {enabled_text} | {configured_text}")

        if info['errors']:
            for category, errors in info['errors'].items():
                for error in errors:
                    print(f"    ⚠️  {error}")

    ready_count = sum(1 for info in status.values() if info['ready'])
    print(f"\n사용 가능한 플랫폼: {ready_count}/{len(status)}개")


def generate_content_interactive(content_generator: ContentGenerator) -> GeneratedContent:
    """대화형 콘텐츠 생성"""
    print("\n📝 콘텐츠 생성 옵션:")
    print("1. 자유 주제로 글 작성")
    print("2. 부동산 뉴스 분석 (기본)")

    choice = input("선택 (1-2, 기본값: 2): ").strip() or "2"

    if choice == "1":
        # 자유 주제 입력
        topic = input("\n주제를 입력하세요: ").strip()
        if not topic:
            print("주제가 입력되지 않았습니다. 기본 주제를 사용합니다.")
            topic = "유용한 생활 정보 및 팁"

        platform_input = input("대상 플랫폼 (naver/tistory/all, 기본값: all): ").strip() or "all"

        if platform_input.lower() == "naver":
            platform = PlatformType.NAVER
        elif platform_input.lower() == "tistory":
            platform = PlatformType.TISTORY
        else:
            platform = PlatformType.TISTORY  # 기본값

        request = ContentRequest(
            topic=topic,
            platform=platform,
            content_type="article",
            target_length=2500,
            include_images=True,
            writing_style="professional"
        )

        return content_generator.generate_content(request)

    else:
        # 부동산 뉴스 분석 (기본)
        print("부동산 뉴스를 수집하고 분석합니다...")
        platform = PlatformType.TISTORY  # 뉴스 분석은 티스토리 최적화
        return content_generator.generate_from_news(platform)


def process_images(content: GeneratedContent, image_manager: ImageManager) -> list:
    """이미지 처리"""
    if not content.image_captions:
        print("이미지 캡션이 없어 이미지 처리를 건너뜁니다.")
        return []

    print(f"\n🖼️  {len(content.image_captions)}개 이미지 처리 중...")

    image_requests = []
    for caption in content.image_captions:
        request = ImageRequest(
            caption=caption,
            width=800,
            height=600,
            source_type=ImageSource.DUMMY,  # 현재는 더미 이미지만 지원
            platform=PlatformType.TISTORY
        )
        image_requests.append(request)

    processed_images = image_manager.process_images(image_requests)
    image_paths = [img.file_path for img in processed_images]

    print(f"✅ {len(image_paths)}개 이미지 처리 완료")

    return image_paths


def create_blog_post(content: GeneratedContent, image_paths: list) -> BlogPost:
    """BlogPost 객체 생성"""
    return BlogPost(
        title=content.title,
        content=content.content,
        tags=content.tags,
        images=image_paths,
        visibility="public"
    )


def post_to_platforms(blog_post: BlogPost, config_manager: ConfigManager) -> dict:
    """플랫폼별 포스팅 실행"""
    print("\n🚀 블로그 포스팅 시작...")

    multi_poster = MultiPlatformPoster(config_manager)
    results = multi_poster.post_to_all_platforms(blog_post)

    print("\n📊 포스팅 결과:")
    print("-" * 50)

    for platform, result in results.items():
        status_icon = "✅" if result['success'] else "❌"
        print(f"{status_icon} {platform.value.upper()}: {result['message']}")

        if result['success'] and result.get('post_url'):
            print(f"   🔗 URL: {result['post_url']}")
        elif not result['success'] and result.get('error_code'):
            print(f"   ⚠️  오류 코드: {result['error_code']}")

    return results


def send_email_notification(results: dict, config_manager: ConfigManager):
    """이메일 알림 발송"""
    if not config_manager.config.email.enabled:
        return

    success_count = sum(1 for r in results.values() if r['success'])
    total_count = len(results)

    subject = f"블로그 포스팅 결과: {success_count}/{total_count} 성공"

    body_lines = ["블로그 포스팅 결과 리포트\n"]
    body_lines.append("=" * 40)

    for platform, result in results.items():
        status = "성공" if result['success'] else "실패"
        body_lines.append(f"\n{platform.value.upper()}: {status}")
        body_lines.append(f"메시지: {result['message']}")

        if result.get('post_url'):
            body_lines.append(f"URL: {result['post_url']}")

    body = "\n".join(body_lines)

    try:
        # 이메일 전송 로직 (기존 티스토리 코드의 send_email 함수 활용)
        from src.tistory.real_estate_posting import send_email

        send_email(
            subject=subject,
            body=body,
            sender_email=config_manager.config.email.sender_email,
            sender_password=config_manager.config.email.sender_password,
            recipient_email=config_manager.config.email.recipient_email
        )
        print("✅ 이메일 알림 발송 완료")

    except Exception as e:
        print(f"⚠️  이메일 알림 발송 실패: {e}")


def main():
    """메인 실행 함수"""
    try:
        # 설정 로드
        config_manager = ConfigManager()
        setup_logging(config_manager.config.debug)

        logger = logging.getLogger(__name__)
        logger.info("통합 블로그 포스팅 시스템 시작")

        # 배너 출력
        print_banner()

        # 설정 검증
        config_errors = config_manager.validate_config()
        if config_errors:
            print("⚠️  설정 오류가 발견되었습니다:")
            for category, errors in config_errors.items():
                for error in errors:
                    print(f"   - {error}")

            response = input("\n계속 진행하시겠습니까? (y/N): ").strip().lower()
            if response != 'y':
                print("프로그램을 종료합니다.")
                return

        # 포스터 팩토리 초기화
        factory = PosterFactory(config_manager)

        # 플랫폼 상태 표시
        print_platform_status(config_manager, factory)

        # 사용 가능한 플랫폼 확인
        enabled_platforms = config_manager.get_enabled_platforms()
        if not enabled_platforms:
            print("\n❌ 설정된 플랫폼이 없습니다. 설정을 확인해주세요.")
            return

        # 컴포넌트 초기화
        content_generator = ContentGenerator(config_manager.config.ai.gemini_api_key)
        image_manager = ImageManager(
            storage_path=config_manager.config.image.storage_path,
            max_file_size=config_manager.config.image.max_file_size_mb * 1024 * 1024
        )

        # 콘텐츠 생성
        content = generate_content_interactive(content_generator)

        if not content or not content_generator.validate_content(content):
            print("❌ 유효한 콘텐츠를 생성하지 못했습니다.")
            return

        print(f"\n✅ 콘텐츠 생성 완료:")
        print(f"   제목: {content.title}")
        print(f"   길이: {len(content.content)}자")
        print(f"   태그: {', '.join(content.tags)}")

        # 이미지 처리
        image_paths = process_images(content, image_manager)

        # BlogPost 객체 생성
        blog_post = create_blog_post(content, image_paths)

        # 최종 확인
        print(f"\n📋 포스팅 준비 완료:")
        print(f"   제목: {blog_post.title}")
        print(f"   대상 플랫폼: {', '.join(p.value for p in enabled_platforms)}")
        print(f"   이미지: {len(blog_post.images or [])}개")

        response = input("\n포스팅을 시작하시겠습니까? (Y/n): ").strip().lower()
        if response == 'n':
            print("포스팅을 취소했습니다.")
            return

        # 포스팅 실행
        results = post_to_platforms(blog_post, config_manager)

        # 이메일 알림
        send_email_notification(results, config_manager)

        # 마무리
        success_count = sum(1 for r in results.values() if r['success'])
        if success_count > 0:
            print(f"\n🎉 {success_count}개 플랫폼에 성공적으로 포스팅되었습니다!")
        else:
            print("\n😞 모든 플랫폼에서 포스팅이 실패했습니다.")

        logger.info("통합 블로그 포스팅 시스템 종료")

    except KeyboardInterrupt:
        print("\n\n⏹️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류 발생: {e}")
        logging.exception("메인 실행 중 오류 발생")


if __name__ == "__main__":
    main()