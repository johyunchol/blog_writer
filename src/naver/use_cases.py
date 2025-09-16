# use_cases.py
from typing import List

from domain import PostContent
from interfaces import (
    ContentGeneratorInterface,
    ImageGeneratorInterface,
    PosterInterface,
)


class AutoPostingUseCase:
    """자동 포스팅 전체 워크플로우를 관장하는 핵심 로직"""

    def __init__(
        self,
        content_generator: ContentGeneratorInterface,
        image_generator: ImageGeneratorInterface, # ImageDownloaderInterface -> ImageGeneratorInterface
        poster: PosterInterface,
        image_save_path: str,
    ):
        self.content_generator = content_generator
        self.image_generator = image_generator # image_downloader -> image_generator
        self.poster = poster
        self.image_save_path = image_save_path

    def execute(self, topic: str, secondary_keywords: str, negative_keywords: str, target_url: str, purpose: str, audience: str, style: str, length: str) -> str:
        """주어진 주제로 자동 포스팅을 실행합니다."""
        print("\n--- 자동 포스팅 유스케이스 실행 ---")

        # 1. 콘텐츠 생성
        generated_content = self.content_generator.generate(
            topic=topic,
            secondary_keywords=secondary_keywords,
            negative_keywords=negative_keywords,
            target_url=target_url,
            purpose=purpose,
            audience=audience,
            style=style,
            length=length
        )
        print(f"[UseCase] 생성된 콘텐츠: {generated_content.title}")

        # 2. 콘텐츠 리스트 조합 및 이미지 생성
        final_content_list: List[PostContent] = []
        for item in generated_content.body:
            final_content_list.append(PostContent(type="text", data=item.text))
            if item.image_caption:
                image_path = self.image_generator.generate(
                    item.image_caption, self.image_save_path
                )
                final_content_list.append(PostContent(type="image", data=image_path))

        # 3. 포스팅
        try:
            self.poster.initialize()  # 드라이버 초기화
            self.poster.login()
            # 생성된 제목과 태그를 사용하도록 수정
            post_url = self.poster.post(final_content_list, generated_content.title)
            return post_url
        finally:
            self.poster.close()
