import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from datetime import datetime

# --- 1. 뉴스 데이터 수집 함수 ---
def crawl_real_estate_news():
    """
    주요 뉴스 사이트에서 부동산 관련 최신 뉴스 기사 5개의 제목과 링크를 크롤링합니다.
    이 함수는 특정 웹사이트 구조에 맞춰 수정해야 합니다.
    """
    print("부동산 뉴스 크롤링을 시작합니다...")
    # 예시: 특정 뉴스 사이트의 부동산 섹션 URL
    # 실제로는 대상 사이트의 구조에 맞게 선택자와 로직을 구현해야 합니다.
    url = "https://news.daum.net/economic#1" # 예시 URL입니다.
    
    news_list = []
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # TODO: 실제 사이트의 HTML 구조에 맞게 CSS 선택자를 수정해야 합니다.
        # 아래는 가상의 선택자입니다.
        articles = soup.select('.list_economic > li > a') 

        for article in articles[:5]: # 최대 5개 기사
            title = article.text.strip()
            link = article['href']
            news_list.append({'title': title, 'link': link})
            
        if not news_list:
            print("수집된 뉴스 기사가 없습니다. CSS 선택자를 확인해주세요.")
            return None

        print(f"총 {len(news_list)}개의 뉴스를 수집했습니다.")
        return news_list

    except requests.exceptions.RequestException as e:
        print(f"뉴스 크롤링 중 오류 발생: {e}")
        return None

# --- 2. Gemini를 이용한 블로그 글 생성 함수 ---
def generate_post_with_gemini(api_key, news_items):
    """수집된 뉴스를 바탕으로 Gemini를 통해 블로그 글을 생성합니다."""
    print("Gemini를 통해 블로그 글 생성을 시작합니다...")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    news_summary = ""
    for item in news_items:
        news_summary += f"- 제목: {item['title']}\n  링크: {item['link']}\n\n"

    prompt = f"""
    아래는 오늘 수집된 최신 부동산 뉴스 목록입니다.

    ---
    {news_summary}
    ---

    위 뉴스 기사들의 핵심 내용을 종합하여, 현재 부동산 시장 동향을 분석하는 전문적인 Tistory 블로그 글을 작성해 주세요.

    **다음 지침을 반드시 따라주세요:**
    1.  **마크다운 형식**으로 작성해주세요.
    2.  글의 가장 첫 줄에는 흥미를 유발할 수 있는 **제목**을 `# 제목` 형식으로 넣어주세요.
    3.  서론, 본론, 결론의 구조를 갖추고, 각 뉴스 내용을 자연스럽게 연결하여 설명해주세요.
    4.  독자들이 이해하기 쉽게 친절하고 전문적인 어조를 사용해주세요.
    5.  글의 마지막에는 #부동산 #부동산뉴스 #시장분석 #내집마련 등 관련 **태그**를 5개 이상 추가해주세요.
    """
    
    try:
        response = model.generate_content(prompt)
        print("Gemini 블로그 글 생성 완료!")
        return response.text
    except Exception as e:
        print(f"Gemini API 요청 중 오류 발생: {e}")
        return None

# --- 3. Tistory 블로그 포스팅 함수 ---
def post_to_tistory(access_token, blog_name, content):
    """생성된 글을 Tistory 블로그에 포스팅합니다."""
    print("Tistory 블로그 포스팅을 시작합니다...")
    post_url = "https://www.tistory.com/apis/post/write"

    try:
        # Gemini가 생성한 글의 첫 줄을 제목으로, 나머지를 내용으로 분리
        title = content.split('\n')[0].replace('# ', '').strip()
        post_content = '\n'.join(content.split('\n')[1:]).strip()
    except IndexError:
        print("콘텐츠에서 제목을 분리할 수 없습니다. 기본 제목을 사용합니다.")
        title = f"{datetime.now().strftime('%Y년 %m월 %d일')} 부동산 뉴스 브리핑"
        post_content = content

    params = {
        'access_token': access_token,
        'output': 'json',
        'blogName': blog_name,
        'title': title,
        'content': post_content,
        'visibility': '3',  # 3: 발행
        'category': '0',    # 0: 기본 카테고리
    }

    try:
        response = requests.post(post_url, data=params)
        response.raise_for_status()
        result = response.json()
        
        if result.get('tistory', {}).get('status') == '200':
            print(f"블로그 포스팅 성공! URL: {result['tistory']['url']}")
        else:
            print(f"블로그 포스팅 실패: {result}")
    except requests.exceptions.RequestException as e:
        print(f"Tistory API 요청 중 오류 발생: {e}")

# --- 메인 실행 로직 ---
if __name__ == "__main__":
    # GitHub Actions의 Secrets에서 API 키와 블로그 정보 가져오기
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    tistory_access_token = os.environ.get("TISTORY_ACCESS_TOKEN")
    tistory_blog_name = os.environ.get("TISTORY_BLOG_NAME")

    if not all([gemini_api_key, tistory_access_token, tistory_blog_name]):
        print("오류: 필요한 환경변수가 설정되지 않았습니다.")
        print("GEMINI_API_KEY, TISTORY_ACCESS_TOKEN, TISTORY_BLOG_NAME를 확인해주세요.")
    else:
        # 1. 뉴스 수집
        news_articles = crawl_real_estate_news()
        
        if news_articles:
            # 2. 블로그 글 생성
            blog_post_content = generate_post_with_gemini(gemini_api_key, news_articles)
            
            if blog_post_content:
                # 3. 블로그 포스팅
                post_to_tistory(tistory_access_token, tistory_blog_name, blog_post_content)
