import json
import os
import re
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import google.generativeai as genai
import requests


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

    today_date = datetime.now().strftime('%Y년 %m월 %d일')

    prompt = f"""
    오늘 날짜({today_date})의 최신 부동산 뉴스를 오늘 날짜의 기사를 정리하고, 
    검색된 뉴스 기사들의 핵심 내용을 종합하여 현재 부동산 시장의 동향을 분석하는 전문적인 Tistory 블로그 글을 작성해 주세요.
    
    **다음의 사이트들에서 자료를 취합해 주세요**
    - https://m2.land.naver.com/news : <div class="article" id="article_today"></div> 에 오늘 날짜의 뉴스가 있습니다.
    
    **다음 지침을 반드시 따라주세요:**
    - **티스토리 TinyMCE 에디터에 맞는 html 형식**으로 작성해주세요. 단, <body> 안에 들어가는 내용만 뽑아주세요. <html><head>는 필요없습니다.
    - 글의 가장 첫 줄에는 흥미를 유발할 수 있는 **제목**을 `# 제목` 형식으로 넣어주세요.
    - 서론, 본론, 결론의 구조를 갖추고, 각 뉴스 내용을 자연스럽게 연결하여 설명해주세요.
    - 독자들이 이해하기 쉽게 친절하고 전문적인 어조를 사용해주세요.
    - 이모티콘등을 섞어서 사용해주세요. 단, 첫줄에는 이모티콘을 사용하지 마세요.
    - 글의 마지막에는 태그::부동산,부동산뉴스,시장분석,내집마련 등 관련 **태그**를 5개 이상 추가해주세요.
    - 글의 내용은 **2000자 이상** 작성해주세요.
    - 제목의 길이는 너무 길지 않게 30자에서 40자 사이로 작성해주세요.
    """

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
