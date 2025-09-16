import os
import configparser
import threading
import logging

import ttkbootstrap as ttk # ttkbootstrap 임포트
from ttkbootstrap.dialogs import Messagebox # ttkbootstrap의 messagebox 임포트
from tkinter.scrolledtext import ScrolledText # tkinter의 ScrolledText 임포트

from domain import ConfigError, ContentGenerationError, ImageGenerationError
from use_cases import AutoPostingUseCase
from infrastructure import (
    GeminiContentGenerator,
    PixabayImageSearchGenerator,
    SeleniumNaverPoster,
)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NaverBloggerApp:
    def __init__(self, master):
        self.master = master
        master.title("네이버 블로그 자동 포스팅 시스템")
        master.geometry("650x800") # 윈도우 크기 조정

        # ttkbootstrap은 Window에서 테마를 설정하므로, 여기서는 스타일만 설정
        self.style = ttk.Style()

        # 폰트 설정 (ttkbootstrap 테마와 어울리도록 조정)
        self.style.configure('TFrame', background=self.style.lookup('TFrame', 'background')) # 테마의 배경색 사용
        self.style.configure('TLabel', font=('맑은 고딕', 11))
        self.style.configure('TButton', font=('맑은 고딕', 11, 'bold'), padding=8)
        self.style.configure('TEntry', padding=5, font=('맑은 고딕', 11))
        self.style.configure('Header.TLabel', font=('맑은 고딕', 13, 'bold'), foreground=self.style.lookup('TLabel', 'foreground'))

        self.config = None
        self.auto_posting_use_case = None

        # UI 요소 생성
        self.create_widgets()

        # 설정 로드 시도
        self.load_configuration()

    def create_widgets(self):
        # 설정 섹션
        self.settings_frame = ttk.LabelFrame(self.master, text="네이버 계정 설정", padding="15 15 15 15")
        self.settings_frame.pack(pady=10, padx=10, fill=ttk.X)

        # ID 입력
        self.id_label = ttk.Label(self.settings_frame, text="아이디:")
        self.id_label.grid(row=0, column=0, sticky=ttk.W, pady=5, padx=5)
        self.id_entry = ttk.Entry(self.settings_frame, width=40)
        self.id_entry.grid(row=0, column=1, sticky=ttk.EW, pady=5, padx=5)

        # Password 입력
        self.pw_label = ttk.Label(self.settings_frame, text="비밀번호:")
        self.pw_label.grid(row=1, column=0, sticky=ttk.W, pady=5, padx=5)
        self.pw_entry = ttk.Entry(self.settings_frame, width=40, show="*") # 비밀번호 숨김
        self.pw_entry.grid(row=1, column=1, sticky=ttk.EW, pady=5, padx=5)

        # 설정 저장 버튼
        self.save_button = ttk.Button(self.settings_frame, text="설정 저장", command=self.save_settings, bootstyle="primary") # bootstyle 추가
        self.save_button.grid(row=2, column=0, columnspan=2, pady=10)

        # 주제 입력 섹션
        self.topic_frame = ttk.LabelFrame(self.master, text="포스팅 주제 입력", padding="15 15 15 15")
        self.topic_frame.pack(pady=10, padx=10, fill=ttk.X)

        self.topic_label = ttk.Label(self.topic_frame, text="주제:")
        self.topic_label.grid(row=0, column=0, sticky=ttk.W, pady=5, padx=5)
        self.topic_entry = ttk.Entry(self.topic_frame, width=40)
        self.topic_entry.grid(row=0, column=1, sticky=ttk.EW, pady=5, padx=5)
        self.topic_entry.insert(0, "케이팝 데몬 헌터스") # 기본값 설정

        self.secondary_keywords_label = ttk.Label(self.topic_frame, text="보조 키워드:")
        self.secondary_keywords_label.grid(row=1, column=0, sticky=ttk.W, pady=5, padx=5)
        self.secondary_keywords_entry = ttk.Entry(self.topic_frame, width=40)
        self.secondary_keywords_entry.grid(row=1, column=1, sticky=ttk.EW, pady=5, padx=5)

        self.negative_keywords_label = ttk.Label(self.topic_frame, text="제외 키워드:")
        self.negative_keywords_label.grid(row=2, column=0, sticky=ttk.W, pady=5, padx=5)
        self.negative_keywords_entry = ttk.Entry(self.topic_frame, width=40)
        self.negative_keywords_entry.grid(row=2, column=1, sticky=ttk.EW, pady=5, padx=5)

        self.target_url_label = ttk.Label(self.topic_frame, text="참고 URL:")
        self.target_url_label.grid(row=3, column=0, sticky=ttk.W, pady=5, padx=5)
        self.target_url_entry = ttk.Entry(self.topic_frame, width=40)
        self.target_url_entry.grid(row=3, column=1, sticky=ttk.EW, pady=5, padx=5)

        # Dropdown options
        purposes = ["정보 제공", "문제 해결", "설득", "엔터테인먼트"]
        audiences = ["초보자", "중급자", "전문가", "일반 대중"]
        styles = ["친근하고 대화체", "전문적이고 분석적", "유머러스하고 가벼운", "감성적이고 서정적인"]
        lengths = ["짧은 글 (500자 내외)", "중간 글 (1000자 내외)", "긴 글 (2000자 이상)"]

        # Purpose Dropdown
        self.purpose_label = ttk.Label(self.topic_frame, text="목적:")
        self.purpose_label.grid(row=4, column=0, sticky=ttk.W, pady=5, padx=5)
        self.purpose_combobox = ttk.Combobox(self.topic_frame, values=purposes, state="readonly")
        self.purpose_combobox.grid(row=4, column=1, sticky=ttk.EW, pady=5, padx=5)
        self.purpose_combobox.set(purposes[0])

        # Audience Dropdown
        self.audience_label = ttk.Label(self.topic_frame, text="대상 독자:")
        self.audience_label.grid(row=5, column=0, sticky=ttk.W, pady=5, padx=5)
        self.audience_combobox = ttk.Combobox(self.topic_frame, values=audiences, state="readonly")
        self.audience_combobox.grid(row=5, column=1, sticky=ttk.EW, pady=5, padx=5)
        self.audience_combobox.set(audiences[0])

        # Style Dropdown
        self.style_label = ttk.Label(self.topic_frame, text="스타일:")
        self.style_label.grid(row=6, column=0, sticky=ttk.W, pady=5, padx=5)
        self.style_combobox = ttk.Combobox(self.topic_frame, values=styles, state="readonly")
        self.style_combobox.grid(row=6, column=1, sticky=ttk.EW, pady=5, padx=5)
        self.style_combobox.set(styles[0])

        # Length Dropdown
        self.length_label = ttk.Label(self.topic_frame, text="길이:")
        self.length_label.grid(row=7, column=0, sticky=ttk.W, pady=5, padx=5)
        self.length_combobox = ttk.Combobox(self.topic_frame, values=lengths, state="readonly")
        self.length_combobox.grid(row=7, column=1, sticky=ttk.EW, pady=5, padx=5)
        self.length_combobox.set(lengths[2])

        # 버튼 섹션
        self.button_frame = ttk.Frame(self.master, padding="5 5 5 5")
        self.button_frame.pack(pady=5, fill=ttk.X)

        self.start_button = ttk.Button(self.button_frame, text="포스팅 시작", command=self.start_posting_thread, bootstyle="success") # bootstyle 추가
        self.start_button.pack(side=ttk.LEFT, expand=True, fill=ttk.X, padx=5)

        self.exit_button = ttk.Button(self.button_frame, text="종료", command=self.master.quit, bootstyle="danger") # bootstyle 추가
        self.exit_button.pack(side=ttk.RIGHT, expand=True, fill=ttk.X, padx=5)

        # 상태 메시지 출력 영역
        self.status_label = ttk.Label(self.master, text="준비 완료.", relief=ttk.SUNKEN, anchor=ttk.W) # relief도 ttk.SUNKEN으로 변경
        self.status_label.pack(side=ttk.BOTTOM, fill=ttk.X, ipady=2)

        # 로그 출력 영역 (ScrolledText)
        self.log_text = ScrolledText(self.master, wrap=ttk.WORD, height=10, state='disabled', font=('맑은 고딕', 10)) # ttkbootstrap의 ScrolledText 사용
        self.log_text.pack(padx=10, pady=10, fill=ttk.BOTH, expand=True)

        # 로그 핸들러 설정
        self.log_handler = TextHandler(self.log_text)
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.INFO) # 모든 로그를 INFO 레벨로 설정

    def update_status(self, message):
        self.status_label.config(text=message)
        self.master.update_idletasks() # UI 즉시 업데이트

    def show_messagebox_safe(self, type, title, message):
        """메인 스레드에서 메시지 박스를 안전하게 표시합니다."""
        if type == "info":
            Messagebox.show_info(title=title, message=message)
        elif type == "warning":
            Messagebox.show_warning(title=title, message=message)
        elif type == "error":
            Messagebox.show_error(title=title, message=message)

    def load_configuration(self):
        self.update_status("설정 파일 로드 중...")
        try:
            env = os.environ.get("APP_ENV", "development").lower()
            self.config_file_path = f"config.{env}.ini" # 설정 파일 경로 저장

            if not os.path.exists(self.config_file_path):
                # 파일이 없으면 기본 설정으로 생성
                self.config = configparser.ConfigParser()
                self.config["NAVER"] = {"ID": "", "PASSWORD": ""}
                self.config["GEMINI"] = {"API_KEY": "YOUR_GEMINI_API_KEY"}
                self.config["PIXABAY"] = {"API_KEY": "YOUR_PIXABAY_API_KEY"}
                with open(self.config_file_path, 'w') as configfile:
                    self.config.write(configfile)
                logging.warning(f"설정 파일 '{self.config_file_path}'이(가) 없어 새로 생성했습니다. API 키와 계정 정보를 입력해주세요.")
            else:
                self.config = configparser.ConfigParser()
                self.config.read(self.config_file_path)
                logging.info(f"'{self.config_file_path}' 설정 파일을 로드했습니다.")

            # UI 필드에 설정 값 채우기
            self.id_entry.insert(0, self.config.get("NAVER", "ID", fallback=""))
            self.pw_entry.insert(0, self.config.get("NAVER", "PASSWORD", fallback=""))

            self.update_status("설정 로드 완료. 계정 정보 확인 및 포스팅 주제를 입력하세요.")

            # 의존성 인스턴스 생성 (DI - Dependency Injection) - 초기화 시점에는 UI 필드 값 사용 안함
            # 실제 포스팅 시작 시점에 UI 필드 값으로 Poster 인스턴스 재생성
            gemini_api_key = self.config.get("GEMINI", "API_KEY")
            pixabay_api_key = self.config.get("PIXABAY", "API_KEY")

            content_generator = GeminiContentGenerator(api_key=gemini_api_key)
            image_generator = PixabayImageSearchGenerator(api_key=pixabay_api_key)
            # Poster는 start_posting_thread에서 최신 UI 값으로 생성

            self.auto_posting_use_case = AutoPostingUseCase(
                content_generator=content_generator,
                image_generator=image_generator,
                poster=None, # Poster는 나중에 설정
                image_save_path="images",
            )
            logging.info("콘텐츠 생성 및 이미지 생성 서비스가 초기화되었습니다.")

        except Exception as e:
            self.master.after(0, self.show_messagebox_safe, "error", "초기화 오류", f"애플리케이션 초기화 중 오류 발생: {e}")
            self.update_status(f"초기화 오류: {e}")
            logging.error(f"초기화 오류: {e}")
            self.start_button.config(state=ttk.DISABLED) # ttk.DISABLED 사용
            self.save_button.config(state=ttk.DISABLED) # ttk.DISABLED 사용

    def save_settings(self):
        naver_id = self.id_entry.get().strip()
        naver_pw = self.pw_entry.get().strip()

        if not naver_id or not naver_pw:
            self.master.after(0, self.show_messagebox_safe, "warning", "경고", "아이디와 비밀번호를 모두 입력해주세요.")
            return

        try:
            # configparser 객체 업데이트
            if "NAVER" not in self.config:
                self.config["NAVER"] = {}
            self.config["NAVER"]["ID"] = naver_id
            self.config["NAVER"]["PASSWORD"] = naver_pw

            # 파일에 쓰기
            with open(self.config_file_path, 'w') as configfile:
                self.config.write(configfile)
            self.master.after(0, self.show_messagebox_safe, "info", "설정 저장", "계정 정보가 성공적으로 저장되었습니다.")
            logging.info("계정 정보가 설정 파일에 저장되었습니다.")
            self.update_status("계정 정보 저장 완료.")

            # Poster 인스턴스 재생성 (저장된 최신 정보로)
            self.auto_posting_use_case.poster = SeleniumNaverPoster(
                user_id=naver_id,
                user_pw=naver_pw,
            )
            logging.info("네이버 포스터 서비스가 최신 계정 정보로 업데이트되었습니다.")

        except Exception as e:
            self.master.after(0, self.show_messagebox_safe, "error", "저장 오류", f"설정 저장 중 오류 발생: {e}")
            logging.error(f"설정 저장 중 오류 발생: {e}")
            self.update_status(f"설정 저장 오류: {e}")

    def start_posting_thread(self):
        # 포스팅 시작 전에 최신 계정 정보로 Poster 인스턴스 확인/생성
        naver_id = self.id_entry.get().strip()
        naver_pw = self.pw_entry.get().strip()

        if not naver_id or not naver_pw:
            self.master.after(0, self.show_messagebox_safe, "warning", "경고", "포스팅을 시작하려면 아이디와 비밀번호를 먼저 입력하고 '설정 저장'을 눌러주세요.")
            return

        if self.auto_posting_use_case.poster is None or \
           self.auto_posting_use_case.poster.user_id != naver_id or \
           self.auto_posting_use_case.poster.user_pw != naver_pw:
            # UI의 최신 정보로 Poster 인스턴스 업데이트
            try:
                self.auto_posting_use_case.poster = SeleniumNaverPoster(
                    user_id=naver_id,
                    user_pw=naver_pw,
                )
                logging.info("네이버 포스터 서비스가 최신 계정 정보로 업데이트되었습니다.")
            except Exception as e:
                self.master.after(0, self.show_messagebox_safe, "error", "초기화 오류", f"네이버 포스터 초기화 중 오류 발생: {e}")
                logging.error(f"네이버 포스터 초기화 중 오류 발생: {e}")
                self.update_status(f"네이버 포스터 초기화 오류: {e}")
                return

        topic = self.topic_entry.get().strip()
        secondary_keywords = self.secondary_keywords_entry.get().strip()
        negative_keywords = self.negative_keywords_entry.get().strip()
        target_url = self.target_url_entry.get().strip()
        purpose = self.purpose_combobox.get()
        audience = self.audience_combobox.get()
        style = self.style_combobox.get()
        length = self.length_combobox.get()

        if not topic:
            self.master.after(0, self.show_messagebox_safe, "warning", "입력 오류", "포스팅 주제를 입력해주세요.")
            return

        self.start_button.config(state=ttk.DISABLED) # ttk.DISABLED 사용
        self.save_button.config(state=ttk.DISABLED) # ttk.DISABLED 사용
        self.update_status("포스팅 시작 중...")
        # 별도의 스레드에서 포스팅 프로세스 실행
        threading.Thread(target=self._run_posting_process, args=(topic, secondary_keywords, negative_keywords, target_url, purpose, audience, style, length)).start()

    def _run_posting_process(self, topic, secondary_keywords, negative_keywords, target_url, purpose, audience, style, length):
        try:
            logging.info(f"'{topic}' 주제로 포스팅을 시작합니다.")
            self.update_status(f"'{topic}' 주제로 포스팅 진행 중...")
            post_url = self.auto_posting_use_case.execute(topic, secondary_keywords, negative_keywords, target_url, purpose, audience, style, length)
            logging.info(f"🎉 포스팅 성공! URL: {post_url}")
            self.update_status(f"포스팅 성공! URL: {post_url}")
            self.master.after(0, self.show_messagebox_safe, "info", "포스팅 완료", f"블로그 포스팅이 성공적으로 완료되었습니다!\nURL: {post_url}")

        except ContentGenerationError as e:
            logging.error(f"콘텐츠 생성 오류: {e}")
            self.master.after(0, self.show_messagebox_safe, "error", "콘텐츠 생성 오류", f"콘텐츠 생성 중 오류 발생: {e}")
            self.update_status(f"콘텐츠 생성 오류: {e}")
        except ImageGenerationError as e:
            logging.error(f"이미지 생성 오류: {e}")
            self.master.after(0, self.show_messagebox_safe, "error", "이미지 생성 오류", f"이미지 생성 중 오류 발생: {e}")
            self.update_status(f"이미지 생성 오류: {e}")
        except Exception as e: # 기타 모든 예외 처리
            logging.exception("예상치 못한 오류 발생:") # 스택 트레이스 포함
            self.master.after(0, self.show_messagebox_safe, "error", "오류", f"포스팅 중 예상치 못한 오류 발생: {e}")
            self.update_status(f"오류 발생: {e}")
        finally:
            self.master.after(0, lambda: self.start_button.config(state=ttk.NORMAL))
            self.master.after(0, lambda: self.save_button.config(state=ttk.NORMAL))

class TextHandler(logging.Handler):
    """로깅 메시지를 Tkinter ScrolledText 위젯으로 리다이렉트하는 핸들러"""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        # UI 업데이트는 메인 스레드에서만 가능하도록 after() 사용
        self.text_widget.after(0, self._update_text_widget, msg)

    def _update_text_widget(self, msg):
        self.text_widget.configure(state='normal')
        self.text_widget.insert(ttk.END, msg + '\n')
        self.text_widget.configure(state='disabled')
        self.text_widget.see(ttk.END) # 스크롤을 항상 맨 아래로

if __name__ == "__main__":
    # ttkbootstrap Window 사용 및 테마 설정
    root = ttk.Window(themename="flatly") # 'flatly' 테마 적용
    app = NaverBloggerApp(root)
    root.mainloop()
