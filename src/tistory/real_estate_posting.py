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


    prompt = f"""
    **당신은 부동산 시장 분석 전문 연구원입니다.** 아래 제공된 최신 부동산 뉴스 기사 본문 전체를 기반으로, 전문적인 '부동산 시장 동향 분석 보고서'를 작성해 주세요.\n\n    **{today_date} 최신 부동산 뉴스 기사 본문:**\n    {fetched_articles_text}\n\n    **보고서 작성 지침:**\n    - **목표:** 뉴스 기사의 핵심 내용을 정확하게 분석하고, 객관적인 데이터와 사실에 기반하여 시장 동향을 예측하고 전문적인 분석을 제공하는 보고서 작성.\n    - **형식:** `<body>` 태그 없이, 각 HTML 요소에 CSS 스타일이 인라인으로 적용된 완벽한 HTML 형식으로 작성해주세요.\n        - 보고서 제목: `<h1 style=\"font-family: 'Noto Sans KR', sans-serif; font-size: 24px; font-weight: bold; margin-bottom: 20px;\">`\n        - 각 섹션 제목 (예: 개요, 주요 뉴스 분석): `<h2 style=\"font-family: 'Noto Sans KR', sans-serif; font-size: 20px; font-weight: bold; margin-top: 25px; margin-bottom: 15px; border-bottom: 2px solid #333;\">`\n        - 본문 단락: `<p style=\"font-family: 'Noto Sans KR', sans-serif; line-height: 1.8; margin: 10px 0;\">`\n        - 핵심 사항 목록: `<ul>`과 `<li>` 태그를 사용하여 명확하게 정리해주세요.\n    - **보고서 구조:**\n        1. **제목:** 보고서의 전체 내용을 함축하는 명료한 제목을 첫 줄에 `# 제목` 형식으로 작성해주세요.\n        2. **1. 개요:** 전체 보고서의 핵심 내용을 요약하여 서두에 제시합니다. 독자가 이 부분만 읽어도 전체 내용을 파악할 수 있도록 작성해주세요.\n        3. **2. 주요 뉴스 분석:** 기사 내용에서 도출한 3가지 핵심 주제를 바탕으로, 각각의 현상과 원인, 시장에 미치는 영향을 심층적으로 분석합니다.\n        4. **3. 시장 전망 및 제언:** 분석 내용을 종합하여 향후 시장을 전망하고, 독자들이 참고할 수 있는 구체적인 제언이나 전략을 제시합니다.\n    - **어조:** 감정적인 표현이나 이모티콘은 완전히 배제하고, 데이터와 사실에 기반한 건조하고 객관적이며, 분석적인 전문 연구원의 어조를 유지해주세요.\n    - **태그:** 글의 마지막에 `태그::부동산보고서,시장분석,부동산전망,데이터분석,정책동향` 등 보고서의 성격에 맞는 전문적인 태그를 5개 이상 추가해주세요.\n    - **분량:** 전체 내용은 2000자 이상으로 작성해주세요.\n    """


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

    html_content = ""
    for line in post_content.split('\n'):
        if line.strip() == "":
            html_content += '<p data-ke-size="size16"><br data-mce-bogus="1"></p>'
        else:
            html_content += f'<p data-ke-size="size16">{line}</p>'

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