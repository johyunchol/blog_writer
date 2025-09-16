"""
AI 기반 통합 콘텐츠 생성 모듈
Gemini API를 활용하여 다양한 플랫폼에 맞는 블로그 콘텐츠 생성
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo
import logging

import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

from .base_poster import PlatformType, ContentError


@dataclass
class ContentRequest:
    """콘텐츠 생성 요청 데이터"""
    topic: str  # 주제
    platform: PlatformType  # 대상 플랫폼
    content_type: str = "article"  # article, review, news_analysis
    target_length: int = 2000  # 목표 글자 수
    include_images: bool = True  # 이미지 포함 여부
    writing_style: str = "professional"  # professional, casual, formal
    custom_instructions: Optional[str] = None  # 추가 지시사항


@dataclass
class GeneratedContent:
    """생성된 콘텐츠 데이터"""
    title: str
    content: str
    tags: List[str]
    image_captions: List[str]
    summary: str
    platform_specific_content: Dict[str, str]  # 플랫폼별 특화 콘텐츠


class ContentGenerator:
    """AI 기반 콘텐츠 생성기"""

    def __init__(self, api_key: str):
        """
        Args:
            api_key: Gemini API 키
        """
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.logger.info("Gemini API 초기화 완료")
        except Exception as e:
            raise ContentError(f"Gemini API 초기화 실패: {e}")

    def generate_content(self, request: ContentRequest) -> GeneratedContent:
        """요청에 따른 콘텐츠 생성"""
        try:
            # 1. 플랫폼별 프롬프트 생성
            prompt = self._create_prompt(request)

            # 2. Gemini API 호출
            response = self.model.generate_content(prompt)

            if not response.text:
                raise ContentError("Gemini API에서 응답을 받지 못했습니다")

            # 3. 응답 파싱
            content = self._parse_response(response.text, request.platform)

            self.logger.info(f"콘텐츠 생성 완료: {request.topic}")
            return content

        except Exception as e:
            self.logger.error(f"콘텐츠 생성 실패: {e}")
            raise ContentError(f"콘텐츠 생성 중 오류 발생: {e}")

    def generate_from_news(self, platform: PlatformType, news_date: Optional[str] = None) -> GeneratedContent:
        """뉴스 기반 콘텐츠 생성 (기존 부동산 뉴스 기능)"""
        try:
            if not news_date:
                kst = ZoneInfo("Asia/Seoul")
                news_date = datetime.now(kst).strftime('%Y-%m-%d')

            # 네이버 부동산 뉴스 수집
            news_content = self._fetch_real_estate_news(news_date)

            if not news_content:
                raise ContentError("뉴스 데이터를 가져올 수 없습니다")

            # 뉴스 기반 콘텐츠 요청 생성
            request = ContentRequest(
                topic=f"{news_date} 부동산 뉴스 분석",
                platform=platform,
                content_type="news_analysis",
                target_length=2800,
                include_images=False,
                writing_style="professional"
            )

            # 뉴스 데이터를 포함한 프롬프트 생성
            prompt = self._create_news_analysis_prompt(news_date, news_content, platform)

            # Gemini API 호출
            response = self.model.generate_content(prompt)

            if not response.text:
                raise ContentError("뉴스 분석 콘텐츠 생성 실패")

            return self._parse_response(response.text, platform)

        except Exception as e:
            self.logger.error(f"뉴스 기반 콘텐츠 생성 실패: {e}")
            raise ContentError(f"뉴스 기반 콘텐츠 생성 중 오류: {e}")

    def _create_prompt(self, request: ContentRequest) -> str:
        """요청에 따른 프롬프트 생성"""

        # 플랫폼별 형식 지침
        platform_formats = {
            PlatformType.TISTORY: {
                "format": "HTML 형식 (인라인 CSS 스타일 포함)",
                "structure": "H1 제목, H2 섹션, P 단락, UL/LI 목록",
                "special": "Tistory TinyMCE 에디터 호환"
            },
            PlatformType.NAVER: {
                "format": "마크다운과 HTML 혼합 형식",
                "structure": "제목, 단락, 이미지 교차 배치",
                "special": "네이버 블로그 에디터 호환"
            }
        }

        format_info = platform_formats.get(request.platform, platform_formats[PlatformType.TISTORY])

        # 콘텐츠 타입별 지침
        content_styles = {
            "article": "전문적이고 정보성이 높은 일반 기사",
            "review": "실제 경험을 바탕으로 한 상세한 리뷰",
            "news_analysis": "객관적 데이터 기반의 뉴스 분석"
        }

        style_desc = content_styles.get(request.content_type, content_styles["article"])

        base_prompt = f"""
당신은 {request.platform.value} 플랫폼 전문 블로거입니다.

**주제**: {request.topic}
**콘텐츠 유형**: {style_desc}
**글쓰기 스타일**: {request.writing_style}
**목표 길이**: {request.target_length}자 이상

**형식 요구사항**:
- 형식: {format_info['format']}
- 구조: {format_info['structure']}
- 특별 요구사항: {format_info['special']}

**콘텐츠 구조**:
1. **제목**: 주제를 함축하는 매력적인 제목 (첫 줄에 # 형식)
2. **요약**: 2-3줄 핵심 요약
3. **본문**: 3-5개 섹션으로 구성된 상세 내용
4. **결론**: 실용적인 조언이나 총정리
"""

        if request.include_images:
            base_prompt += f"""
5. **이미지 캡션**: 각 섹션에 어울리는 이미지 캡션 3-5개
   (형식: 이미지캡션::캡션내용)
"""

        base_prompt += f"""
6. **태그**: 관련 태그 5-8개 (형식: 태그::태그1,태그2,태그3)

**작성 지침**:
- {request.writing_style} 어조 유지
- 독자에게 실질적 도움이 되는 내용
- SEO를 고려한 키워드 자연스럽게 포함
- 단락 간 적절한 호흡과 가독성 확보
"""

        if request.custom_instructions:
            base_prompt += f"""
**추가 지시사항**: {request.custom_instructions}
"""

        return base_prompt

    def _create_news_analysis_prompt(self, date: str, news_content: str, platform: PlatformType) -> str:
        """뉴스 분석 전용 프롬프트 생성 (기존 티스토리 로직 활용)"""

        if platform == PlatformType.TISTORY:
            # 기존 티스토리 프롬프트 로직 사용
            from ..tistory.real_estate_posting import create_analysis_prompt
            return create_analysis_prompt(date, news_content)
        else:
            # 네이버용 프롬프트 (향후 개발)
            return self._create_naver_news_prompt(date, news_content)

    def _create_naver_news_prompt(self, date: str, news_content: str) -> str:
        """네이버 블로그용 뉴스 분석 프롬프트"""
        return f"""
당신은 네이버 블로그 부동산 전문가입니다.

**{date} 부동산 뉴스 분석**

다음 뉴스를 바탕으로 네이버 블로그에 적합한 포스트를 작성해주세요:

{news_content}

**네이버 블로그 형식 요구사항**:
- 제목: # 형식으로 시작
- 친근하고 접근하기 쉬운 어조
- 이미지가 들어갈 위치에 [이미지: 설명] 형식 표시
- 단락 구분을 명확히
- 네이버 검색 최적화를 위한 키워드 포함

**구성**:
1. 오늘의 부동산 핫이슈
2. 상세 분석 (3-4개 섹션)
3. 투자자/실수요자를 위한 팁
4. 마무리 정리

전체 분량: 2500자 이상
마지막에 "태그::" 형식으로 태그 5개 이상 포함
"""

    def _parse_response(self, response: str, platform: PlatformType) -> GeneratedContent:
        """Gemini 응답 파싱"""
        try:
            lines = response.split('\n')

            # 제목 추출
            title = ""
            for line in lines:
                if line.strip().startswith('# '):
                    title = line.strip()[2:].strip()
                    break

            if not title:
                title = "생성된 블로그 포스트"

            # 태그 추출
            tags = []
            tag_pattern = r'태그::(.+)'
            for line in lines:
                match = re.search(tag_pattern, line)
                if match:
                    tag_string = match.group(1)
                    tags = [tag.strip() for tag in tag_string.split(',') if tag.strip()]
                    break

            # 이미지 캡션 추출
            image_captions = []
            caption_pattern = r'이미지캡션::(.+)'
            for line in lines:
                match = re.search(caption_pattern, line)
                if match:
                    image_captions.append(match.group(1).strip())

            # 본문 내용 (태그와 이미지 캡션 제거)
            content_lines = []
            for line in lines:
                if not (line.strip().startswith('태그::') or
                       line.strip().startswith('이미지캡션::')):
                    content_lines.append(line)

            content = '\n'.join(content_lines).strip()

            # 요약 생성 (첫 번째 단락 또는 첫 200자)
            summary = self._extract_summary(content)

            # 플랫폼별 특화 콘텐츠
            platform_content = {
                platform.value: content
            }

            return GeneratedContent(
                title=title,
                content=content,
                tags=tags,
                image_captions=image_captions,
                summary=summary,
                platform_specific_content=platform_content
            )

        except Exception as e:
            self.logger.error(f"응답 파싱 실패: {e}")
            raise ContentError(f"응답 파싱 중 오류: {e}")

    def _extract_summary(self, content: str) -> str:
        """콘텐츠에서 요약 추출"""
        # HTML 태그 제거
        clean_content = re.sub(r'<[^>]+>', '', content)

        # 첫 번째 단락 또는 200자 추출
        paragraphs = clean_content.split('\n\n')
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if len(paragraph) > 50:  # 의미있는 길이의 단락
                return paragraph[:200] + ('...' if len(paragraph) > 200 else '')

        # 단락이 없으면 처음 200자
        return clean_content[:200] + ('...' if len(clean_content) > 200 else '')

    def _fetch_real_estate_news(self, date: str) -> str:
        """네이버 부동산 뉴스 수집 (기존 로직 활용)"""
        try:
            news_api_url = f"https://m2.land.naver.com/news/airsList.naver?baseDate={date}&page=1&size=30"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(news_api_url, headers=headers)
            response.raise_for_status()
            news_data = response.json()

            link_urls = [item['linkUrl'] for item in news_data.get('list', [])]

            if not link_urls:
                return ""

            # 기사 내용 수집
            fetched_articles = []
            for url in link_urls[:10]:  # 최대 10개 기사
                try:
                    article_response = requests.get(url, headers=headers, timeout=10)
                    article_response.raise_for_status()
                    soup = BeautifulSoup(article_response.text, 'html.parser')

                    article_body = soup.select_one('#articleBodyContents, #newsct_article')
                    if article_body:
                        # 불필요한 요소 제거
                        for el in article_body.select('script, style, .ad, .promotion'):
                            el.decompose()

                        text = article_body.get_text(separator='\n', strip=True)
                        if len(text) > 100:  # 최소 길이 확인
                            fetched_articles.append(text)

                except Exception as e:
                    self.logger.warning(f"기사 수집 실패: {url}, {e}")
                    continue

            return "\n\n---\n\n".join(fetched_articles)

        except Exception as e:
            self.logger.error(f"뉴스 수집 실패: {e}")
            return ""

    def validate_content(self, content: GeneratedContent) -> bool:
        """생성된 콘텐츠 유효성 검증"""
        try:
            # 기본 필드 검증
            if not content.title or len(content.title) < 5:
                return False

            if not content.content or len(content.content) < 500:
                return False

            # 태그 검증
            if len(content.tags) < 3:
                return False

            return True

        except Exception:
            return False