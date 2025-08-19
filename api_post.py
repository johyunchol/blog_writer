import json
import os
import re
from datetime import datetime

import google.generativeai as genai
import requests


# --- Helper function for BMP filtering ---
def remove_non_bmp_chars(s):
    return "".join(c for c in s if c <= '\uFFFF')

# --- 2. Gemini를 이용한 블로그 글 생성 함수 ---
def generate_post_with_gemini(api_key):
    """Gemini를 통해 오늘자 부동산 뉴스를 검색하고, 이를 바탕으로 블로그 글을 생성합니다."""
    print("Gemini를 통해 뉴스 검색 및 블로그 글 생성을 시작합니다...")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

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
        print("\n--- 생성된 블로그 글 내용 ---\\n")
        print(response.text)
        print("\n------------------------------\\n")
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
        import os # os 모듈 추가

        print("Selenium을 사용하여 로그인 쿠키를 획득합니다...")

        # ChromeDriver 설정 (main.py와 동일)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        chromedriver_path = os.path.join(script_dir, "chromedriver")
        service = Service(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service)

        try:
            # 카카오 로그인 페이지로 이동 (사용자가 제공한 정확한 URL)
            driver.get("https://accounts.kakao.com/login/?continue=https%3A%2F%2Fkauth.kakao.com%2Foauth%2Fauthorize%3Fclient_id%3D3e6ddd834b023f24221217e370daed18%26state%3DaHR0cHM6Ly9ra2Vuc3UudGlzdG9yeS5jb20vbWFuYWdlL25ld3Bvc3Qv%26prompt%3Dselect_account%26redirect_uri%3Dhttps%253A%252F%252Fwww.tistory.com%252Fauth%252Fkakao%252Fredirect%26response_type%3Dcode%26auth_tran_id%3Ddvy6kpj4uxg3e6ddd834b023f24221217e370daed18meh80vuu%26ka%3Dsdk%252F1.43.6%2520os%252Fjavascript%2520sdk_type%252Fjavascript%2520lang%252Fko-KR%2520device%252FMacIntel%2520origin%252Fhttps%25253A%25252F%25252Fwww.tistory.com%26is_popup%3Dfalse%26through_account%3Dtrue#login")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='loginId']"))
            )

            # 아이디/비밀번호 입력
            username_field = driver.find_element(By.CSS_SELECTOR, "input[name='loginId']")
            password_field = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
            username_field.send_keys(tistory_id)
            password_field.send_keys(tistory_pw)

            # 로그인 버튼 클릭
            login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()

            # Tistory 관리 페이지로 리다이렉션 대기
            WebDriverWait(driver, 10).until(
                EC.url_contains("tistory.com/manage")
            )
            print("Selenium 로그인 성공!")

            # 쿠키 추출
            cookies = driver.get_cookies()
            tistory_cookie_str = ""
            for cookie in cookies:
                tistory_cookie_str += f"{cookie['name']}={cookie['value']}; "
            tistory_cookie_str = tistory_cookie_str.strip()

            return tistory_cookie_str

        except Exception as e:
            print(f"Selenium 로그인 중 오류 발생: {e}")
            return None
        finally:
            driver.quit() # 드라이버 종료

    # Selenium을 통해 쿠키 획득
    tistory_cookie_str = get_tistory_cookies_with_selenium(tistory_id, tistory_pw)
    if not tistory_cookie_str:
        print("쿠키 획득 실패. 포스팅을 중단합니다.")
        return False

    session = requests.Session()
    # 획득한 쿠키를 requests 세션에 추가
    for cookie_pair in tistory_cookie_str.split(';'):
        if '=' in cookie_pair:
            name, value = cookie_pair.split('=', 1)
            session.cookies.set(name.strip(), value.strip())

    # 2. 포스팅 API 호출
    post_api_url = f"https://{blog_name}.tistory.com/manage/post.json" # 블로그 이름 동적 사용

    # Gemini가 생성한 글의 첫 줄을 제목으로, 나머지를 내용으로 분리
    lines = content.split('\n')
    title = lines[0].replace('# ', '').strip()

    # 제목에서 HTML 태그 제거
    title = re.sub(r'<[^>]+>', '', title).strip()

    # 태그 추출 및 본문에서 제거
    extracted_tags = []
    post_body_lines = []
    tag_line_found = False

    # 마지막 줄부터 역순으로 탐색하여 태그 라인을 찾음
    for i in range(len(lines) - 1, 0, -1):
        line = lines[i].strip()
        if not tag_line_found and '태그::' in line:
            # HTML 태그가 포함될 수 있으므로 정규식으로 제거
            cleaned_line = re.sub(r'<[^>]+>', '', line)
            # '태그::' 부분을 제거하고, 쉼표로 태그들을 분리
            tag_string = cleaned_line.split('::', 1)[-1]
            tags = [tag.strip() for tag in tag_string.split(',') if tag.strip()]
            extracted_tags.extend(tags)
            tag_line_found = True # 태그 라인을 찾았으므로 플래그를 설정
        else:
            post_body_lines.insert(0, lines[i]) # 태그 라인이 아닌 경우, 본문으로 간주하고 순서를 유지하며 추가

    post_content = '\n'.join(post_body_lines).strip()
    tistory_tags = ','.join(extracted_tags)

    # ChromeDriver BMP-only 에러 방지를 위해 제목에서 특수문자(이모티콘 등) 필터링
    title = remove_non_bmp_chars(title)

    # post_content를 HTML 형식으로 변환 (사용자 요청에 따라)
    html_content = ""
    for line in post_content.split('\n'):
        if line.strip() == "":
            html_content += '<p data-ke-size="size16"><br data-mce-bogus="1"></p>'
        else:
            html_content += f'<p data-ke-size="size16">{line}</p>'

    payload = {
        "id": "0", # 새 글 작성 시 "0"
        "title": title,
        "content": html_content,
        "slogan": "", # 슬로건은 비워둠
        "visibility": 20, # 0: 공개, 1: 비공개, 3: 보호, 20: 발행 (사용자 요청 open20과 유사)
        "category": 1532685, # 부동산 카테고리 ID
        "tag": tistory_tags, # 추출된 태그 사용
        "published": 1, # 1: 발행
        "password": "", # 보호글이 아니므로 비워둠
        "uselessMarginForEntry": 1,
        "daumLike": "105", # 부동산 카테고리 view-channel 값
        "cclCommercial": 0,
        "cclDerive": 0,
        "thumbnail": "",
        "type": "post",
        "attachments": [],
        "recaptchaValue": "", # 캡챠는 비워둠
        "draftSequence": None
    }

    headers = {
        "Host": f"{blog_name}.tistory.com",
        "Cookie": tistory_cookie_str, # Use the extracted cookie string
        "Sec-Ch-Ua": "\"Chromium\";v=\"127\", \"Not)A;Brand\";v=\"99\"", # Example value, can be dynamic or fixed
        "Accept": "application/json, text/plain, */*",
        "Sec-Ch-Ua-Platform": "\"Windows\"", # Example value, can be dynamic or fixed
        "Accept-Language": "ko-KR",
        "Sec-Ch-Ua-Mobile": "?0",
        "User-Agent": "Mozilla/50 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.100 Safari/537.36", # Example value, can be dynamic or fixed
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
        return True
    else:
        print(f"블로그 포스팅 실패! 상태 코드: {response.status_code}")
        print(f"응답: {response.text}")
        return False


# --- 메인 실행 로직 ---
if __name__ == "__main__":
    # GitHub Actions의 Secrets에서 정보 가져오기
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    tistory_id = os.environ.get("TISTORY_ID")
    tistory_pw = os.environ.get("TISTORY_PW")
    tistory_blog_name = os.environ.get("TISTORY_BLOG_NAME") # 예: "kkensu"

    if not all([gemini_api_key, tistory_id, tistory_pw, tistory_blog_name]):
        print("오류: 필요한 환경변수가 설정되지 않았습니다.")
        print("GEMINI_API_KEY, TISTORY_ID, TISTORY_PW, TISTORY_BLOG_NAME를 확인해주세요.")
    else:
        # 1. 블로그 글 생성 (Gemini가 뉴스 검색 포함)
        blog_post_content = generate_post_with_gemini(gemini_api_key)
        # blog_post_content = (f"#블로그 제목\n\n"
        #                      f"이거 내용입니다.")

        if blog_post_content:
            # 2. 블로그 포스팅 (Requests)
            post_to_tistory_requests(tistory_blog_name, tistory_id, tistory_pw, blog_post_content)
