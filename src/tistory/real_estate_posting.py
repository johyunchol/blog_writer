import json
import os
import re
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

import google.generativeai as genai
import requests
from bs4 import BeautifulSoup


# --- Helper function for BMP filtering ---
def remove_non_bmp_chars(s):
    return "".join(c for c in s if c <= '\uFFFF')


# --- HTML 콘텐츠 변환 함수 ---
def convert_to_tistory_html(content):
    """Gemini가 생성한 콘텐츠를 Tistory 형식의 HTML로 변환합니다."""
    styles = get_html_styles()
    html_content = ""

    lines = content.split('\n')
    in_list = False

    for line in lines:
        line = line.strip()

        if not line:
            # 빈 줄 처리
            html_content += '<p data-ke-size="size16"><br data-mce-bogus="1"></p>\n'

        elif line.startswith('<h1'):
            # H1 제목
            html_content += f'{line}\n'

        elif line.startswith('<h2'):
            # H2 섹션 제목
            if in_list:
                html_content += '</ul>\n'
                in_list = False
            html_content += f'{line}\n'

        elif line.startswith('<h3'):
            # H3 소제목
            if in_list:
                html_content += '</ul>\n'
                in_list = False
            html_content += f'{line}\n'

        elif line.startswith('<ul>'):
            # 목록 시작
            html_content += f'<ul style="{styles["ul"]}" data-ke-list-type="disc">\n'
            in_list = True

        elif line.startswith('<li>'):
            # 목록 항목
            html_content += f'<li style="{styles["li"]}" data-ke-list-type="disc">{line[4:-5]}</li>\n'

        elif line.startswith('</ul>'):
            # 목록 끝
            html_content += '</ul>\n'
            in_list = False

        elif line.startswith('<p'):
            # 기존 p 태그가 있는 경우
            if in_list:
                html_content += '</ul>\n'
                in_list = False
            html_content += f'{line}\n'

        else:
            # 일반 텍스트 줄
            if in_list:
                html_content += '</ul>\n'
                in_list = False

            # strong 태그 처리
            if '<strong>' in line:
                line = line.replace('<strong>', f'<strong style="{styles["strong"]}">')

            html_content += f'<p style="{styles["p"]}" data-ke-size="size16">{line}</p>\n'

    # 목록이 열려있으면 닫기
    if in_list:
        html_content += '</ul>\n'

    return html_content.strip()


# --- HTML 스타일링 함수 ---
def get_html_styles():
    """Tistory 블로그용 HTML 스타일을 반환합니다."""
    return {
        'h1': "font-family: 'Noto Sans KR', sans-serif; font-size: 26px; font-weight: bold; margin-bottom: 25px; color: #2c3e50; text-align: center;",
        'h2': "font-family: 'Noto Sans KR', sans-serif; font-size: 22px; font-weight: bold; margin-top: 30px; margin-bottom: 18px; border-bottom: 3px solid #3498db; padding-bottom: 8px; color: #2c3e50;",
        'h3': "font-family: 'Noto Sans KR', sans-serif; font-size: 18px; font-weight: bold; margin-top: 25px; margin-bottom: 15px; color: #34495e;",
        'p': "font-family: 'Noto Sans KR', sans-serif; line-height: 1.8; margin: 12px 0; color: #2c3e50; font-size: 16px;",
        'ul': "font-family: 'Noto Sans KR', sans-serif; line-height: 1.7; margin: 15px 0; padding-left: 20px;",
        'li': "margin-bottom: 8px; color: #2c3e50;",
        'strong': "color: #e74c3c; font-weight: bold;",
        'highlight_box': "background-color: #f8f9fa; border-left: 4px solid #3498db; padding: 15px; margin: 20px 0; border-radius: 5px;"
    }


# --- 프롬프트 템플릿 함수 ---
def create_analysis_prompt(today_date, fetched_articles_text):
    """부동산 분석 보고서 생성을 위한 최적화된 프롬프트를 생성합니다."""
    styles = get_html_styles()

    system_role = """
당신은 15년 경력의 부동산 시장 분석 전문가입니다.
주요 역할:
- 부동산 시장 트렌드 분석 및 예측
- 정책 변화가 시장에 미치는 영향 분석
- 투자자와 실수요자를 위한 실용적 인사이트 제공
"""

    content_framework = """
다음 분석 프레임워크를 활용하여 보고서를 작성하세요:

1. **정책 및 제도 변화**: 금리, 대출규제, 세제 변화 등
2. **시장 동향 분석**: 가격 변동, 거래량, 지역별 특징
3. **수급 균형**: 공급물량, 수요 패턴, 미분양 현황
4. **투자 환경**: 수익률, 리스크 요소, 기회 영역
"""

    target_audience = """
독자 타겟:
- 부동산 투자를 검토하는 개인 투자자 (30-50대)
- 내집 마련을 준비하는 실수요자 (20-40대)
- 부동산 시장 동향에 관심 있는 일반인
"""

    output_structure = f"""
보고서 구조 (각 HTML 요소에 인라인 스타일 적용):
1. **제목**: <h1 style="{styles['h1']}">{today_date} 부동산 시장 분석 리포트</h1> (# 형식으로 시작)
2. **핵심 요약**: <div style="{styles['highlight_box']}">3-4줄 핵심 내용</div>
3. **주요 동향 분석**: <h2 style="{styles['h2']}">섹션 제목</h2>으로 구분
   - 정책/제도 변화와 시장 영향
   - 지역별/유형별 시장 동향
   - 주목할 만한 거래 패턴
4. **시장 전망**: <h2 style="{styles['h2']}">향후 3-6개월 예상 시나리오</h2>
5. **실용 가이드**: <h3 style="{styles['h3']}">투자자별/실수요자별 구체적 행동 지침</h3>
"""

    writing_guidelines = """
작성 지침:
- 객관적 데이터와 사실 중심, 구체적 수치 활용
- 전문 용어 사용 시 (용어 설명) 병행
- 감정적 표현 완전 배제, 분석적 어조 유지
- "투자 기회", "매수 타이밍" 등 실행 가능한 구체적 제언
- 위험 요소와 기회 요소 균형 있게 제시
"""

    format_instructions = f"""
필수 형식 요구사항:
- 제목: # 형식으로 시작 (마크다운)
- HTML 요소별 인라인 CSS 스타일:
  * H1: style="{styles['h1']}"
  * H2: style="{styles['h2']}"
  * H3: style="{styles['h3']}"
  * P: style="{styles['p']}"
  * Strong: style="{styles['strong']}"
  * UL: style="{styles['ul']}"
- 핵심 포인트는 <ul>, <li> 태그로 목록화
- 중요 내용은 <strong> 태그로 강조
- 하이라이트 박스: <div style="{styles['highlight_box']}">내용</div>
- 마지막에 '태그::부동산분석,시장동향,투자전략,정책변화,지역별분석' 형식 (5개 이상)
- 전체 분량: 2800자 이상
"""

    prompt = f"""
{system_role}

{target_audience}

**분석 대상**: {today_date} 부동산 뉴스

**뉴스 원문**:
{fetched_articles_text}

{content_framework}

{output_structure}

{writing_guidelines}

{format_instructions}

위 지침을 정확히 따라 독자에게 실질적 도움이 되는 전문적인 부동산 시장 분석 보고서를 작성하세요.
독자가 "오늘 읽길 잘했다"고 생각할 만한 실용적 인사이트를 제공하세요.
"""

    return prompt


# --- 이메일 전송 함수 ---
def send_email(subject, body, sender_email, sender_password, recipient_email):
    """지정된 주소로 이메일을 전송합니다."""
    print("결과를 이메일로 전송합니다...")
    try:
        # SMTP 서버 설정 (Gmail 기준)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        # 이메일 메시지 생성
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8')) # 인코딩 설정 추가

        # 서버 연결 및 로그인
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)

        # 이메일 전송
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        print("이메일 전송 성공!")
        return True
    except Exception as e:
        print(f"이메일 전송 중 오류 발생: {e}")
        return False


# --- Gemini 블로그 글 생성 함수 ---
def generate_post_with_gemini(api_key):
    """Gemini를 통해 오늘자 부동산 뉴스를 검색하고, 이를 바탕으로 블로그 글을 생성합니다."""
    print("Gemini를 통해 뉴스 검색 및 블로그 글 생성을 시작합니다...")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    kst = ZoneInfo("Asia/Seoul")
    today_date = datetime.now(kst).strftime('%Y-%m-%d')
    
    # 네이버 부동산 뉴스 API 호출
    try:
        print(f"{today_date}의 네이버 부동산 뉴스를 가져옵니다...")
        news_api_url = f"https://m2.land.naver.com/news/airsList.naver?baseDate={today_date}&page=1&size=30"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(news_api_url, headers=headers)
        response.raise_for_status()
        news_data = response.json()
        
        # linkUrl만 추출하여 리스트로 만듦
        link_urls = [item['linkUrl'] for item in news_data.get('list', [])]
        
        if not link_urls:
            print("가져온 뉴스 기사가 없습니다.")
            return None

        # BeautifulSoup을 사용하여 모든 기사 내용 가져오기
        print(f"{len(link_urls)}개의 뉴스 기사 내용을 가져옵니다...")
        fetched_articles_texts = []
        for url in link_urls:
            try:
                article_response = requests.get(url, headers=headers)
                article_response.raise_for_status()
                soup = BeautifulSoup(article_response.text, 'html.parser')
                
                # 네이버 뉴스 본문 선택자 (일반적인 경우)
                article_body = soup.select_one('#articleBodyContents, #newsct_article')

                if article_body:
                    # 불필요한 요소(광고, 스크립트 등) 제거
                    for el in article_body.select('script, style, .ad, .promotion, .link_news, .journalist_card'):
                        el.decompose()
                    
                    text = article_body.get_text(separator='\n', strip=True)
                    fetched_articles_texts.append(text)
                else:
                    print(f"기사 본문을 찾을 수 없습니다: {url}")

            except requests.exceptions.RequestException as e:
                print(f"기사 내용 로딩 중 오류 발생 (URL: {url}): {e}")
                continue # 한 기사 실패 시 다음으로 넘어감
        
        if not fetched_articles_texts:
            print("모든 뉴스 기사의 내용을 가져오는데 실패했습니다.")
            return None

        fetched_articles_text = "\n\n---\n\n".join(fetched_articles_texts)
        print("뉴스 기사 내용 가져오기 완료!")

    except requests.exceptions.RequestException as e:
        print(f"네이버 부동산 뉴스 API 호출 중 오류 발생: {e}")
        return None
    except (KeyError, TypeError) as e:
        print(f"뉴스 데이터 파싱 중 오류 발생: {e}")
        return None
    except Exception as e:
        print(f"웹 콘텐츠를 가져오는 중 오류 발생: {e}")
        return None


    # 개선된 프롬프트 생성
    prompt = create_analysis_prompt(today_date, fetched_articles_text)


    try:
        response = model.generate_content(prompt)
        print("Gemini 블로그 글 생성 완료!")
        print("\n--- 생성된 블로그 글 내용 ---\n")
        print(response.text)
        print("\n-------------------------------\n")
        return response.text
    except Exception as e:
        print(f"Gemini API 요청 중 오류 발생: {e}")
        return None


def post_to_tistory_requests(blog_name, tistory_id, tistory_pw, content):
    """Requests 라이브러리를 사용하여 Tistory 블로그에 글을 포스팅합니다."""
    print("Requests를 통해 Tistory 블로그 포스팅을 시작합니다...")

    # Gemini 결과에서 ```html 코드 블록 제거
    if content.strip().startswith("```html"):
        content = content.strip()[7:].strip()
    if content.strip().endswith("```"):
        content = content.strip()[:-3].strip()

    # <body> 와 </body> 태그 제거
    content = content.replace("<body>", "").replace("</body>", "").strip()

    # Selenium을 사용하여 로그인하고 쿠키를 가져오는 함수
    def get_tistory_cookies_with_selenium(tistory_id, tistory_pw):
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import os

        print("Selenium을 사용하여 로그인 쿠키를 획득합니다...")

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        if os.environ.get('CI'): # Check if running in CI environment (e.g., GitHub Actions)
            service = Service() # Let Selenium find chromedriver in PATH
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            chromedriver_path = os.path.join(script_dir, "../../chromedriver")
            service = Service(executable_path=chromedriver_path)
            
        driver = webdriver.Chrome(service=service, options=options)

        try:
            driver.get("https://accounts.kakao.com/login/?continue=https%3A%2F%2Fkauth.kakao.com%2Foauth%2Fauthorize%3Fclient_id%3D3e6ddd834b023f24221217e370daed18%26state%3DaHR0cHM6Ly9ra2Vuc3UudGlzdG9yeS5jb20vbWFuYWdlL25ld3Bvc3Qv%26prompt%3Dselect_account%26redirect_uri%3Dhttps%253A%252F%252Fwww.tistory.com%252Fauth%252Fkakao%252Fredirect%26response_type%3Dcode%26auth_tran_id%3Ddvy6kpj4uxg3e6ddd834b023f24221217e370daed18meh80vuu%26ka%3Dsdk%252F1.43.6%2520os%252Fjavascript%2520sdk_type%252Fjavascript%2520lang%252Fko-KR%2520device%252FMacIntel%2520origin%252Fhttps%25253A%25252F%25252Fwww.tistory.com%26is_popup%3Dfalse%26through_account%3Dtrue#login")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='loginId']"))
            )

            username_field = driver.find_element(By.CSS_SELECTOR, "input[name='loginId']")
            password_field = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
            username_field.send_keys(tistory_id)
            password_field.send_keys(tistory_pw)

            login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()

            WebDriverWait(driver, 10).until(
                EC.url_contains("tistory.com/manage")
            )
            print("Selenium 로그인 성공!")

            cookies = driver.get_cookies()
            tistory_cookie_str = ""
            for cookie in cookies:
                tistory_cookie_str += f"{cookie['name']}={cookie['value']}; "
            tistory_cookie_str = tistory_cookie_str.strip()

            return tistory_cookie_str

        except Exception as e:
            screenshot_path = "selenium_error.png"
            driver.save_screenshot(screenshot_path)
            print(f"Selenium 로그인 중 오류 발생: {e}")
            print(f"오류 발생 시 스크린샷 저장됨: {screenshot_path}")
            return None
        finally:
            driver.quit()

    tistory_cookie_str = get_tistory_cookies_with_selenium(tistory_id, tistory_pw)
    if not tistory_cookie_str:
        print("쿠키 획득 실패. 포스팅을 중단합니다.")
        return False, "Selenium 쿠키 획득 실패"

    session = requests.Session()
    for cookie_pair in tistory_cookie_str.split(';'):
        if '=' in cookie_pair:
            name, value = cookie_pair.split('=', 1)
            session.cookies.set(name.strip(), value.strip())

    post_api_url = f"https://{blog_name}.tistory.com/manage/post.json"

    lines = content.split('\n')
    title = lines[0].replace('# ', '').strip()
    title = re.sub(r'<[^>]+>', '', title).strip()

    extracted_tags = []
    post_body_lines = []
    tag_line_found = False

    for i in range(len(lines) - 1, 0, -1):
        line = lines[i].strip()
        if not tag_line_found and '태그::' in line:
            cleaned_line = re.sub(r'<[^>]+>', '', line)
            tag_string = cleaned_line.split('::', 1)[-1]
            tags = [tag.strip() for tag in tag_string.split(',') if tag.strip()]
            extracted_tags.extend(tags)
            tag_line_found = True
        else:
            post_body_lines.insert(0, lines[i])

    post_content = '\n'.join(post_body_lines).strip()
    tistory_tags = ','.join(extracted_tags)

    title = remove_non_bmp_chars(title)

    # HTML 콘텐츠를 개선된 스타일로 변환
    html_content = convert_to_tistory_html(post_content)

    payload = {
        "id": "0",
        "title": title,
        "content": html_content,
        "slogan": "",
        "visibility": 20,
        "category": 1532685,
        "tag": tistory_tags,
        "published": 1,
        "password": "",
        "uselessMarginForEntry": 1,
        "daumLike": "105",
        "cclCommercial": 0,
        "cclDerive": 0,
        "thumbnail": "",
        "type": "post",
        "attachments": [],
        "recaptchaValue": "",
        "draftSequence": None
    }

    headers = {
        "Host": f"{blog_name}.tistory.com",
        "Cookie": tistory_cookie_str,
        "Sec-Ch-Ua": "\"Chromium\";v=\"127\", \"Not)A;Brand\";v=\"99\"",
        "Accept": "application/json, text/plain, */*",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Accept-Language": "ko-KR",
        "Sec-Ch-Ua-Mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.100 Safari/537.36",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": f"https://{blog_name}.tistory.com",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": f"https://{blog_name}.tistory.com/manage/newpost/?type=post&returnURL=%2Fmanage%2Fposts%2F",
        "Accept-Encoding": "gzip, deflate, br",
        "Priority": "u=1, i"
    }

    print("블로그 포스팅 API를 호출합니다.")
    response = session.post(post_api_url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        print("블로그 포스팅 성공!")
        print(f"응답: {response.json()}")
        return True, title
    else:
        print(f"블로그 포스팅 실패! 상태 코드: {response.status_code}")
        print(f"응답: {response.text}")
        return False, f"포스팅 실패 (상태 코드: {response.status_code})"


# --- 메인 실행 로직 ---
if __name__ == "__main__":
    # GitHub Actions의 Secrets에서 정보 가져오기
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    tistory_id = os.environ.get("TISTORY_ID")
    tistory_pw = os.environ.get("TISTORY_PW")
    tistory_blog_name = os.environ.get("TISTORY_BLOG_NAME")
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")
    recipient_email = os.environ.get("RECIPIENT_EMAIL")

    # 필수 환경변수 확인
    required_vars = {
        "GEMINI_API_KEY": gemini_api_key,
        "TISTORY_ID": tistory_id,
        "TISTORY_PW": tistory_pw,
        "TISTORY_BLOG_NAME": tistory_blog_name,
        "SENDER_EMAIL": sender_email,
        "SENDER_PASSWORD": sender_password,
        "RECIPIENT_EMAIL": recipient_email
    }

    missing_vars = [key for key, value in required_vars.items() if not value]

    if missing_vars:
        error_message = f"오류: 다음 필수 환경변수가 설정되지 않았습니다: {', '.join(missing_vars)}"
        print(error_message)
        # 이메일 알림 시도 (비밀번호가 없으면 실패할 수 있음)
        if sender_email and sender_password and recipient_email:
            send_email("블로그 포스팅 실패: 환경변수 누락", error_message, sender_email, sender_password, recipient_email)
    else:
        try:
            # 1. 블로그 글 생성
            blog_post_content = generate_post_with_gemini(gemini_api_key)

            if blog_post_content:
                # 2. 블로그 포스팅
                success, message = post_to_tistory_requests(tistory_blog_name, tistory_id, tistory_pw, blog_post_content)

                if success:
                    email_subject = f"블로그 포스팅 성공: {message}"
                    email_body = f"성공적으로 블로그에 글을 게시했습니다.\n\n제목: {message}"
                    send_email(email_subject, email_body, sender_email, sender_password, recipient_email)
                else:
                    email_subject = "블로그 포스팅 실패"
                    email_body = f"블로그 글 게시에 실패했습니다.\n\n오류 메시지: {message}"
                    send_email(email_subject, email_body, sender_email, sender_password, recipient_email)
            else:
                error_message = "Gemini를 이용한 블로그 글 생성에 실패했습니다."
                print(error_message)
                send_email("블로그 포스팅 실패: 글 생성 오류", error_message, sender_email, sender_password, recipient_email)

        except Exception as e:
            error_message = f"스크립트 실행 중 예외 발생: {e}"
            print(error_message)
            send_email("블로그 포스팅 실패: 스크립트 오류", error_message, sender_email, sender_password, recipient_email)