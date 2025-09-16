"""
메인 GUI 윈도우
통합 블로그 포스팅 시스템의 메인 사용자 인터페이스
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from typing import Dict, Optional, Callable
import sys
import os

# 프로젝트 루트를 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from src.config.settings import ConfigManager
from src.platforms.poster_factory import PosterFactory, MultiPlatformPoster
from src.core.content_generator import ContentGenerator, ContentRequest, GeneratedContent
from src.core.image_manager import ImageManager
from src.core.base_poster import BlogPost, PlatformType
from .widgets import StatusLabel, ProgressSection, PlatformCheckbox, ScrollableText, SettingsFrame


class BlogPosterGUI:
    """통합 블로그 포스팅 시스템 GUI"""

    def __init__(self):
        self.root = tk.Tk()
        self.config_manager = None
        self.content_generator = None
        self.image_manager = None
        self.multi_poster = None
        self.generated_content = None

        self._setup_window()
        self._create_widgets()
        self._load_config()

    def _setup_window(self):
        """윈도우 기본 설정"""
        self.root.title("통합 블로그 포스팅 시스템 v1.0")
        self.root.geometry("800x700")
        self.root.minsize(750, 650)

        # 아이콘 설정 (선택사항)
        try:
            # 윈도우 아이콘이 있다면 설정
            pass
        except:
            pass

        # 종료 이벤트
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_widgets(self):
        """위젯 생성"""
        # 메인 노트북 (탭)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 탭 생성
        self._create_main_tab()
        self._create_settings_tab()

    def _create_main_tab(self):
        """메인 탭 생성"""
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text="📝 포스팅")

        # 제목 및 로고
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=10, pady=10)

        title_label = ttk.Label(
            title_frame,
            text="🚀 통합 블로그 포스팅 시스템",
            font=('Arial', 16, 'bold')
        )
        title_label.pack()

        subtitle_label = ttk.Label(
            title_frame,
            text="네이버 블로그 & 티스토리 동시 포스팅 • Gemini AI 콘텐츠 생성",
            font=('Arial', 10),
            foreground='gray'
        )
        subtitle_label.pack(pady=(0, 10))

        # 플랫폼 선택 섹션
        self._create_platform_section()

        # 콘텐츠 생성 섹션
        self._create_content_section()

        # 진행 상황 섹션
        self._create_progress_section()

        # 버튼 섹션
        self._create_button_section()

        # 결과 표시 섹션
        self._create_result_section()

    def _create_platform_section(self):
        """플랫폼 선택 섹션"""
        platform_frame = ttk.LabelFrame(self.main_frame, text="📋 플랫폼 선택", padding=10)
        platform_frame.pack(fill=tk.X, padx=10, pady=5)

        self.platform_checkboxes = {}

        # 네이버 플랫폼
        self.platform_checkboxes['naver'] = PlatformCheckbox(
            platform_frame,
            "네이버 블로그",
            enabled=False  # 초기값, 설정 로드 후 업데이트
        )
        self.platform_checkboxes['naver'].pack(fill=tk.X, pady=2)

        # 티스토리 플랫폼
        self.platform_checkboxes['tistory'] = PlatformCheckbox(
            platform_frame,
            "티스토리",
            enabled=False  # 초기값, 설정 로드 후 업데이트
        )
        self.platform_checkboxes['tistory'].pack(fill=tk.X, pady=2)

        # 새로고침 버튼
        refresh_btn = ttk.Button(
            platform_frame,
            text="🔄 상태 새로고침",
            command=self._refresh_platform_status
        )
        refresh_btn.pack(anchor=tk.E, pady=(5, 0))

    def _create_content_section(self):
        """콘텐츠 생성 섹션"""
        content_frame = ttk.LabelFrame(self.main_frame, text="✏️ 콘텐츠 생성 설정", padding=10)
        content_frame.pack(fill=tk.X, padx=10, pady=5)

        # 콘텐츠 유형 선택
        type_frame = ttk.Frame(content_frame)
        type_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(type_frame, text="콘텐츠 유형:").pack(side=tk.LEFT)

        self.content_type_var = tk.StringVar(value="news")
        type_radio1 = ttk.Radiobutton(
            type_frame,
            text="📰 부동산 뉴스 분석",
            variable=self.content_type_var,
            value="news"
        )
        type_radio1.pack(side=tk.LEFT, padx=(10, 0))

        type_radio2 = ttk.Radiobutton(
            type_frame,
            text="✍️ 자유 주제 작성",
            variable=self.content_type_var,
            value="custom"
        )
        type_radio2.pack(side=tk.LEFT, padx=(10, 0))

        # 자유 주제 입력
        self.custom_topic_frame = ttk.Frame(content_frame)
        self.custom_topic_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(self.custom_topic_frame, text="주제:").pack(side=tk.LEFT)
        self.custom_topic_var = tk.StringVar(value="유용한 생활 정보 및 팁")
        self.topic_entry = ttk.Entry(
            self.custom_topic_frame,
            textvariable=self.custom_topic_var,
            font=('Arial', 10)
        )
        self.topic_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

        # 라디오 버튼 이벤트 연결
        self.content_type_var.trace('w', self._on_content_type_change)
        self._on_content_type_change()  # 초기 상태 설정

    def _create_progress_section(self):
        """진행 상황 섹션"""
        progress_frame = ttk.LabelFrame(self.main_frame, text="📊 진행 상황", padding=10)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)

        self.progress_section = ProgressSection(progress_frame)
        self.progress_section.pack(fill=tk.X)

    def _create_button_section(self):
        """버튼 섹션"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        # 콘텐츠 생성 버튼
        self.generate_btn = ttk.Button(
            button_frame,
            text="🎯 콘텐츠 생성",
            command=self._generate_content,
            style="Accent.TButton"
        )
        self.generate_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 포스팅 버튼
        self.post_btn = ttk.Button(
            button_frame,
            text="🚀 블로그 포스팅",
            command=self._post_content,
            state=tk.DISABLED
        )
        self.post_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 미리보기 버튼
        self.preview_btn = ttk.Button(
            button_frame,
            text="👁️ 미리보기",
            command=self._preview_content,
            state=tk.DISABLED
        )
        self.preview_btn.pack(side=tk.LEFT)

    def _create_result_section(self):
        """결과 표시 섹션"""
        result_frame = ttk.LabelFrame(self.main_frame, text="📄 결과 로그", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.result_text = ScrollableText(result_frame, height=8)
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # 로그 지우기 버튼
        clear_btn = ttk.Button(
            result_frame,
            text="🗑️ 로그 지우기",
            command=self.result_text.clear
        )
        clear_btn.pack(anchor=tk.E, pady=(5, 0))

    def _create_settings_tab(self):
        """설정 탭 생성"""
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="⚙️ 설정")

        # 스크롤 가능한 프레임
        canvas = tk.Canvas(self.settings_frame)
        scrollbar = ttk.Scrollbar(self.settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # AI 설정
        self.ai_settings = SettingsFrame(scrollable_frame, "🤖 AI 설정")
        self.ai_settings.pack(fill=tk.X, padx=10, pady=5)

        self.ai_settings.add_field("모델명", "combobox", ["gemini-1.5-flash", "gemini-1.5-pro"], "gemini-1.5-flash")
        self.ai_settings.add_field("Temperature", "spinbox", from_=0.0, to=2.0, increment=0.1, default_value="0.7")
        self.ai_settings.add_field("Gemini API 키", "entry", default_value="환경변수에서 로드됨", width=50)

        # 네이버 설정
        self.naver_settings = SettingsFrame(scrollable_frame, "🟢 네이버 블로그 설정")
        self.naver_settings.pack(fill=tk.X, padx=10, pady=5)

        self.naver_settings.add_field("활성화", "checkbutton", default_value=False)
        self.naver_settings.add_field("사용자명", "entry", width=30)
        self.naver_settings.add_field("비밀번호", "entry", show="*", width=30)

        # 티스토리 설정
        self.tistory_settings = SettingsFrame(scrollable_frame, "🟠 티스토리 설정")
        self.tistory_settings.pack(fill=tk.X, padx=10, pady=5)

        self.tistory_settings.add_field("활성화", "checkbutton", default_value=True)
        self.tistory_settings.add_field("사용자명", "entry", width=30)
        self.tistory_settings.add_field("비밀번호", "entry", show="*", width=30)
        self.tistory_settings.add_field("블로그명", "entry", width=30)
        self.tistory_settings.add_field("카테고리 ID", "spinbox", from_=1, to=9999999, default_value="1532685")

        # 기타 설정
        self.misc_settings = SettingsFrame(scrollable_frame, "🔧 기타 설정")
        self.misc_settings.pack(fill=tk.X, padx=10, pady=5)

        self.misc_settings.add_field("헤드리스 모드", "checkbutton", default_value=True)
        self.misc_settings.add_field("디버그 모드", "checkbutton", default_value=False)
        self.misc_settings.add_field("이미지 저장 경로", "entry", default_value="./images", width=40)
        self.misc_settings.add_field("최대 이미지 크기(MB)", "spinbox", from_=1, to=10, default_value="2")

        # 설정 버튼
        settings_btn_frame = ttk.Frame(scrollable_frame)
        settings_btn_frame.pack(fill=tk.X, padx=10, pady=10)

        save_settings_btn = ttk.Button(
            settings_btn_frame,
            text="💾 설정 저장",
            command=self._save_settings
        )
        save_settings_btn.pack(side=tk.LEFT, padx=(0, 10))

        load_settings_btn = ttk.Button(
            settings_btn_frame,
            text="🔄 설정 새로고침",
            command=self._reload_config
        )
        load_settings_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 백업 복원 버튼
        restore_settings_btn = ttk.Button(
            settings_btn_frame,
            text="📂 백업 복원",
            command=self._restore_settings
        )
        restore_settings_btn.pack(side=tk.LEFT, padx=(0, 10))

        test_settings_btn = ttk.Button(
            settings_btn_frame,
            text="🔍 연결 테스트",
            command=self._test_connections
        )
        test_settings_btn.pack(side=tk.LEFT)

        # 스크롤 설정
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _load_config(self):
        """설정 로드"""
        try:
            self.config_manager = ConfigManager()
            self.log("✅ 설정 파일 로드 완료")

            # 설정값을 GUI에 반영
            self._update_settings_ui()

            # 플랫폼 상태 업데이트
            self._refresh_platform_status()

            # 컴포넌트 초기화
            self._initialize_components()

        except Exception as e:
            self.log(f"❌ 설정 로드 실패: {e}")
            messagebox.showerror("오류", f"설정 로드에 실패했습니다:\n{e}")

    def _update_settings_ui(self):
        """설정값을 UI에 반영"""
        if not self.config_manager:
            return

        try:
            config = self.config_manager.config

            # AI 설정
            ai_values = {
                "모델명": config.ai.model_name,
                "Temperature": str(config.ai.temperature),
                "Gemini API 키": config.ai.gemini_api_key or "환경변수에서 로드됨"
            }
            self.ai_settings.set_values(ai_values)

            # 네이버 설정
            naver_config = self.config_manager.get_platform_config(PlatformType.NAVER)
            naver_values = {
                "활성화": naver_config.enabled,
                "사용자명": naver_config.username or "",
                "비밀번호": "****" if naver_config.password else ""
            }
            self.naver_settings.set_values(naver_values)

            # 티스토리 설정
            tistory_config = self.config_manager.get_platform_config(PlatformType.TISTORY)
            tistory_values = {
                "활성화": tistory_config.enabled,
                "사용자명": tistory_config.username or "",
                "비밀번호": "****" if tistory_config.password else "",
                "블로그명": tistory_config.additional_settings.get("blog_name", ""),
                "카테고리 ID": str(tistory_config.additional_settings.get("category_id", 1532685))
            }
            self.tistory_settings.set_values(tistory_values)

            # 기타 설정
            misc_values = {
                "헤드리스 모드": config.headless,
                "디버그 모드": config.debug,
                "이미지 저장 경로": config.image.storage_path,
                "최대 이미지 크기(MB)": str(config.image.max_file_size_mb)
            }
            self.misc_settings.set_values(misc_values)

        except Exception as e:
            self.log(f"⚠️ 설정 UI 업데이트 실패: {e}")

    def _initialize_components(self):
        """백엔드 컴포넌트 초기화"""
        if not self.config_manager:
            return

        try:
            # 콘텐츠 생성기 초기화
            if self.config_manager.config.ai.gemini_api_key:
                self.content_generator = ContentGenerator(
                    self.config_manager.config.ai.gemini_api_key
                )
                self.log("✅ 콘텐츠 생성기 초기화 완료")
            else:
                self.log("⚠️ Gemini API 키가 없어 콘텐츠 생성기를 초기화하지 못했습니다")

            # 이미지 매니저 초기화
            self.image_manager = ImageManager(
                storage_path=self.config_manager.config.image.storage_path,
                max_file_size=self.config_manager.config.image.max_file_size_mb * 1024 * 1024
            )
            self.log("✅ 이미지 매니저 초기화 완료")

            # 멀티플랫폼 포스터 초기화
            self.multi_poster = MultiPlatformPoster(self.config_manager)
            self.log("✅ 멀티플랫폼 포스터 초기화 완료")

        except Exception as e:
            self.log(f"❌ 컴포넌트 초기화 실패: {e}")

    def _refresh_platform_status(self):
        """플랫폼 상태 새로고침"""
        if not self.multi_poster:
            return

        try:
            status = self.multi_poster.get_platform_status()

            for platform_key, checkbox in self.platform_checkboxes.items():
                platform_type = PlatformType.NAVER if platform_key == 'naver' else PlatformType.TISTORY

                if platform_type in status:
                    platform_status = status[platform_type]
                    if platform_status['ready']:
                        checkbox.set_ready()
                    else:
                        checkbox.set_disabled()

            self.log("🔄 플랫폼 상태 업데이트 완료")

        except Exception as e:
            self.log(f"❌ 플랫폼 상태 업데이트 실패: {e}")

    def _on_content_type_change(self, *args):
        """콘텐츠 유형 변경 시 호출"""
        is_custom = self.content_type_var.get() == "custom"

        for widget in self.custom_topic_frame.winfo_children():
            if isinstance(widget, ttk.Entry):
                widget.config(state=tk.NORMAL if is_custom else tk.DISABLED)

    def _generate_content(self):
        """콘텐츠 생성"""
        if not self.content_generator:
            messagebox.showerror("오류", "콘텐츠 생성기가 초기화되지 않았습니다.\nGemini API 키를 확인해주세요.")
            return

        # 버튼 비활성화
        self.generate_btn.config(state=tk.DISABLED)
        self.post_btn.config(state=tk.DISABLED)
        self.preview_btn.config(state=tk.DISABLED)

        # 백그라운드 작업으로 실행
        thread = threading.Thread(target=self._generate_content_worker)
        thread.daemon = True
        thread.start()

    def _generate_content_worker(self):
        """콘텐츠 생성 작업 스레드"""
        try:
            self._update_progress(10, "콘텐츠 생성 중...")
            self.log("🎯 콘텐츠 생성 시작")

            # 콘텐츠 요청 생성
            if self.content_type_var.get() == "news":
                # 부동산 뉴스 분석
                self._update_progress(30, "부동산 뉴스 수집 중...")
                content = self.content_generator.generate_from_news(PlatformType.TISTORY)
            else:
                # 자유 주제
                topic = self.custom_topic_var.get().strip()
                if not topic:
                    topic = "유용한 생활 정보 및 팁"

                self._update_progress(30, f"주제 '{topic}' 콘텐츠 생성 중...")

                request = ContentRequest(
                    topic=topic,
                    platform=PlatformType.TISTORY,
                    content_type="article",
                    target_length=2500,
                    include_images=True,
                    writing_style="professional"
                )
                content = self.content_generator.generate_content(request)

            self._update_progress(70, "이미지 처리 중...")

            # 이미지 처리
            image_paths = []
            if content and content.image_captions and self.image_manager:
                from src.core.image_manager import ImageRequest, ImageSource

                image_requests = []
                for caption in content.image_captions:
                    request = ImageRequest(
                        caption=caption,
                        width=800,
                        height=600,
                        source_type=ImageSource.DUMMY,
                        platform=PlatformType.TISTORY
                    )
                    image_requests.append(request)

                processed_images = self.image_manager.process_images(image_requests)
                image_paths = [img.file_path for img in processed_images]

            self._update_progress(90, "콘텐츠 생성 완료")

            # 결과 저장
            self.generated_content = content

            self._update_progress(100, "✅ 콘텐츠 생성 완료!")

            self.root.after(0, self._on_content_generated, content, image_paths)

        except Exception as e:
            self.root.after(0, self._on_content_generation_error, str(e))

    def _on_content_generated(self, content: GeneratedContent, image_paths: list):
        """콘텐츠 생성 완료 시 호출"""
        self.log(f"✅ 콘텐츠 생성 완료: {content.title}")
        self.log(f"   길이: {len(content.content)}자")
        self.log(f"   태그: {', '.join(content.tags)}")
        self.log(f"   이미지: {len(image_paths)}개")

        # 버튼 활성화
        self.generate_btn.config(state=tk.NORMAL)
        self.preview_btn.config(state=tk.NORMAL)

        # 선택된 플랫폼이 있으면 포스팅 버튼 활성화
        if any(cb.is_selected() for cb in self.platform_checkboxes.values()):
            self.post_btn.config(state=tk.NORMAL)

    def _on_content_generation_error(self, error_msg: str):
        """콘텐츠 생성 오류 시 호출"""
        self.log(f"❌ 콘텐츠 생성 실패: {error_msg}")
        messagebox.showerror("콘텐츠 생성 실패", f"콘텐츠 생성에 실패했습니다:\n{error_msg}")

        # 버튼 활성화
        self.generate_btn.config(state=tk.NORMAL)
        self._update_progress(0, "대기 중...")

    def _post_content(self):
        """블로그 포스팅"""
        if not self.generated_content:
            messagebox.showwarning("경고", "먼저 콘텐츠를 생성해주세요.")
            return

        # 선택된 플랫폼 확인
        selected_platforms = [
            PlatformType.NAVER if key == 'naver' else PlatformType.TISTORY
            for key, cb in self.platform_checkboxes.items()
            if cb.is_selected()
        ]

        if not selected_platforms:
            messagebox.showwarning("경고", "포스팅할 플랫폼을 선택해주세요.")
            return

        # 확인 대화상자
        platform_names = [p.value for p in selected_platforms]
        confirm = messagebox.askyesno(
            "포스팅 확인",
            f"다음 플랫폼에 포스팅하시겠습니까?\n{', '.join(platform_names)}\n\n제목: {self.generated_content.title}"
        )

        if not confirm:
            return

        # 버튼 비활성화
        self.post_btn.config(state=tk.DISABLED)
        self.generate_btn.config(state=tk.DISABLED)

        # 백그라운드 작업으로 실행
        thread = threading.Thread(target=self._post_content_worker, args=(selected_platforms,))
        thread.daemon = True
        thread.start()

    def _post_content_worker(self, selected_platforms):
        """포스팅 작업 스레드"""
        try:
            self._update_progress(10, "포스팅 준비 중...")

            # BlogPost 객체 생성
            blog_post = BlogPost(
                title=self.generated_content.title,
                content=self.generated_content.content,
                tags=self.generated_content.tags,
                images=[],  # 이미지 경로들 (구현 필요)
                visibility="public"
            )

            self.log("🚀 블로그 포스팅 시작")

            # 플랫폼별 포스팅
            results = self.multi_poster.post_to_specific_platforms(blog_post, selected_platforms)

            self._update_progress(100, "포스팅 완료!")

            self.root.after(0, self._on_posting_completed, results)

        except Exception as e:
            self.root.after(0, self._on_posting_error, str(e))

    def _on_posting_completed(self, results: dict):
        """포스팅 완료 시 호출"""
        self.log("📊 포스팅 결과:")

        success_count = 0
        for platform, result in results.items():
            if result['success']:
                success_count += 1
                self.log(f"✅ {platform.value.upper()}: {result['message']}")
                if result.get('post_url'):
                    self.log(f"   🔗 URL: {result['post_url']}")

                # 플랫폼 상태 업데이트
                platform_key = 'naver' if platform == PlatformType.NAVER else 'tistory'
                if platform_key in self.platform_checkboxes:
                    self.platform_checkboxes[platform_key].set_success()
            else:
                self.log(f"❌ {platform.value.upper()}: {result['message']}")
                if result.get('error_code'):
                    self.log(f"   ⚠️ 오류 코드: {result['error_code']}")

                # 플랫폼 상태 업데이트
                platform_key = 'naver' if platform == PlatformType.NAVER else 'tistory'
                if platform_key in self.platform_checkboxes:
                    self.platform_checkboxes[platform_key].set_error("포스팅 실패")

        # 결과 메시지
        total_count = len(results)
        if success_count == total_count:
            messagebox.showinfo("성공", f"🎉 모든 플랫폼({success_count}개)에 성공적으로 포스팅되었습니다!")
        elif success_count > 0:
            messagebox.showwarning("부분 성공", f"⚠️ {total_count}개 중 {success_count}개 플랫폼에 성공했습니다.")
        else:
            messagebox.showerror("실패", "😞 모든 플랫폼에서 포스팅이 실패했습니다.")

        # 버튼 활성화
        self.post_btn.config(state=tk.NORMAL)
        self.generate_btn.config(state=tk.NORMAL)

    def _on_posting_error(self, error_msg: str):
        """포스팅 오류 시 호출"""
        self.log(f"❌ 포스팅 실패: {error_msg}")
        messagebox.showerror("포스팅 실패", f"포스팅에 실패했습니다:\n{error_msg}")

        # 버튼 활성화
        self.post_btn.config(state=tk.NORMAL)
        self.generate_btn.config(state=tk.NORMAL)
        self._update_progress(0, "대기 중...")

    def _preview_content(self):
        """콘텐츠 미리보기"""
        if not self.generated_content:
            messagebox.showwarning("경고", "먼저 콘텐츠를 생성해주세요.")
            return

        # 미리보기 창 생성
        preview_window = tk.Toplevel(self.root)
        preview_window.title(f"미리보기 - {self.generated_content.title}")
        preview_window.geometry("700x600")

        # 제목
        title_label = ttk.Label(
            preview_window,
            text=self.generated_content.title,
            font=('Arial', 14, 'bold'),
            wraplength=650
        )
        title_label.pack(pady=10)

        # 태그
        tags_label = ttk.Label(
            preview_window,
            text=f"태그: {', '.join(self.generated_content.tags)}",
            font=('Arial', 10),
            foreground='blue'
        )
        tags_label.pack(pady=(0, 10))

        # 내용
        content_frame = ttk.Frame(preview_window)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        content_text = ScrollableText(content_frame, height=20)
        content_text.pack(fill=tk.BOTH, expand=True)
        content_text.append_text(self.generated_content.content)

        # 이미지 캡션
        if self.generated_content.image_captions:
            ttk.Separator(preview_window, orient='horizontal').pack(fill=tk.X, padx=10, pady=5)

            images_label = ttk.Label(
                preview_window,
                text=f"이미지: {', '.join(self.generated_content.image_captions)}",
                font=('Arial', 10),
                foreground='green'
            )
            images_label.pack(pady=5)

    def _save_settings(self):
        """설정 저장"""
        try:
            if not self.config_manager:
                messagebox.showerror("오류", "설정 관리자가 초기화되지 않았습니다.")
                return

            # GUI에서 설정값 수집
            gui_values = {}

            # AI 설정 수집
            ai_values = self.ai_settings.get_values()
            gui_values['ai'] = {
                'model_name': ai_values.get('모델명', ''),
                'temperature': ai_values.get('Temperature', '')
            }

            # 네이버 설정 수집
            naver_values = self.naver_settings.get_values()
            gui_values['naver'] = {
                'enabled': naver_values.get('활성화', False),
                'username': naver_values.get('사용자명', '')
            }

            # 티스토리 설정 수집
            tistory_values = self.tistory_settings.get_values()
            gui_values['tistory'] = {
                'enabled': tistory_values.get('활성화', False),
                'username': tistory_values.get('사용자명', ''),
                'blog_name': tistory_values.get('블로그명', ''),
                'category_id': tistory_values.get('카테고리 ID', '')
            }

            # 기타 설정 수집
            misc_values = self.misc_settings.get_values()
            gui_values['app'] = {
                'headless': misc_values.get('헤드리스 모드', True),
                'debug': misc_values.get('디버그 모드', False)
            }
            gui_values['image'] = {
                'storage_path': misc_values.get('이미지 저장 경로', './images'),
                'max_file_size_mb': misc_values.get('최대 이미지 크기(MB)', 2)
            }

            # 저장 전 백업
            backup_success = self.config_manager.backup_config()
            if not backup_success:
                response = messagebox.askyesno(
                    "백업 실패",
                    "설정 백업에 실패했습니다. 그래도 계속하시겠습니까?"
                )
                if not response:
                    return

            # 설정 저장
            success = self.config_manager.save_config_from_gui(gui_values)

            if success:
                # 백엔드 컴포넌트 다시 초기화
                self._initialize_components()

                # 플랫폼 상태 새로고침
                self._refresh_platform_status()

                # 성공 메시지
                messagebox.showinfo("성공", "설정이 성공적으로 저장되었습니다!")
                self.log("✅ 설정 저장 완료")

            else:
                messagebox.showerror("오류", "설정 저장에 실패했습니다.")

        except Exception as e:
            self.log(f"❌ 설정 저장 오류: {e}")
            messagebox.showerror("오류", f"설정 저장에 실패했습니다:\n{e}")

    def _reload_config(self):
        """설정 새로고침"""
        try:
            self.log("🔄 설정 새로고침 시작...")
            self._load_config()
            messagebox.showinfo("완료", "설정이 새로고침되었습니다.")

        except Exception as e:
            self.log(f"❌ 설정 새로고침 실패: {e}")
            messagebox.showerror("오류", f"설정 새로고침에 실패했습니다:\n{e}")

    def _restore_settings(self):
        """백업에서 설정 복원"""
        try:
            if not self.config_manager:
                messagebox.showerror("오류", "설정 관리자가 초기화되지 않았습니다.")
                return

            # 백업 파일 목록 가져오기
            backup_files = self.config_manager.get_backup_files()

            if not backup_files:
                messagebox.showinfo("알림", "복원할 백업 파일이 없습니다.")
                return

            # 백업 파일 선택 창
            backup_window = tk.Toplevel(self.root)
            backup_window.title("백업 복원")
            backup_window.geometry("500x300")
            backup_window.transient(self.root)
            backup_window.grab_set()

            ttk.Label(backup_window, text="복원할 백업 파일을 선택하세요:", font=('Arial', 12)).pack(pady=10)

            # 백업 파일 리스트
            listbox_frame = ttk.Frame(backup_window)
            listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            listbox = tk.Listbox(listbox_frame, font=('Consolas', 10))
            scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)

            listbox.config(yscrollcommand=scrollbar.set)

            for backup_file in backup_files:
                # 파일명에서 타임스탬프 추출하여 읽기 쉬운 형태로 변환
                import time
                import datetime

                filename = backup_file.name
                if 'backup.' in filename:
                    try:
                        timestamp_str = filename.split('backup.')[1].split('.ini')[0]
                        timestamp = int(timestamp_str)
                        date_str = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                        display_name = f"{date_str} ({filename})"
                    except:
                        display_name = filename
                else:
                    display_name = filename

                listbox.insert(tk.END, display_name)

            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # 버튼 프레임
            button_frame = ttk.Frame(backup_window)
            button_frame.pack(fill=tk.X, padx=10, pady=10)

            def restore_selected():
                selection = listbox.curselection()
                if not selection:
                    messagebox.showwarning("경고", "백업 파일을 선택해주세요.")
                    return

                selected_backup = backup_files[selection[0]]

                # 확인 대화상자
                confirm = messagebox.askyesno(
                    "복원 확인",
                    f"다음 백업에서 설정을 복원하시겠습니까?\n\n{selected_backup.name}\n\n현재 설정은 덮어써집니다."
                )

                if not confirm:
                    return

                # 복원 실행
                success = self.config_manager.restore_config(selected_backup)

                if success:
                    # GUI 업데이트
                    self._update_settings_ui()
                    self._initialize_components()
                    self._refresh_platform_status()

                    self.log(f"✅ 설정 복원 완료: {selected_backup.name}")
                    messagebox.showinfo("성공", "설정이 성공적으로 복원되었습니다!")
                    backup_window.destroy()
                else:
                    messagebox.showerror("오류", "설정 복원에 실패했습니다.")

            ttk.Button(button_frame, text="복원", command=restore_selected).pack(side=tk.LEFT)
            ttk.Button(button_frame, text="취소", command=backup_window.destroy).pack(side=tk.LEFT, padx=(10, 0))

        except Exception as e:
            self.log(f"❌ 백업 복원 오류: {e}")
            messagebox.showerror("오류", f"백업 복원에 실패했습니다:\n{e}")

    def _test_connections(self):
        """연결 테스트"""
        try:
            self.log("🔍 연결 테스트 시작")

            if self.config_manager:
                errors = self.config_manager.validate_config()
                if errors:
                    for category, error_list in errors.items():
                        for error in error_list:
                            self.log(f"⚠️ {category}: {error}")
                else:
                    self.log("✅ 설정 검증 완료")

            messagebox.showinfo("연결 테스트", "연결 테스트가 완료되었습니다.\n결과를 로그에서 확인해주세요.")

        except Exception as e:
            self.log(f"❌ 연결 테스트 실패: {e}")
            messagebox.showerror("오류", f"연결 테스트에 실패했습니다:\n{e}")

    def _update_progress(self, value: float, message: str = ""):
        """진행률 업데이트 (스레드 안전)"""
        self.root.after(0, lambda: self.progress_section.set_progress(value, message))

    def log(self, message: str):
        """로그 메시지 (스레드 안전)"""
        self.root.after(0, lambda: self.result_text.append_text(message))

    def _on_closing(self):
        """윈도우 종료 시 호출"""
        if messagebox.askokcancel("종료", "프로그램을 종료하시겠습니까?"):
            self.root.destroy()

    def run(self):
        """GUI 실행"""
        self.root.mainloop()


def main():
    """메인 함수"""
    try:
        app = BlogPosterGUI()
        app.run()
    except Exception as e:
        print(f"GUI 실행 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()