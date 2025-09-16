"""
GUI 위젯 컴포넌트
공통으로 사용되는 커스텀 위젯들
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, List, Any


class StatusLabel(ttk.Frame):
    """상태 표시 라벨 위젯"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.status_var = tk.StringVar()
        self.status_var.set("준비")

        self.icon_label = ttk.Label(self, text="⚫", font=('Arial', 12))
        self.icon_label.pack(side=tk.LEFT, padx=(0, 5))

        self.text_label = ttk.Label(self, textvariable=self.status_var, font=('Arial', 10))
        self.text_label.pack(side=tk.LEFT)

    def set_status(self, status: str, color: str = "⚫"):
        """상태 설정"""
        self.status_var.set(status)
        self.icon_label.config(text=color)


class ProgressSection(ttk.Frame):
    """진행 상황 표시 섹션"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # 진행률 표시
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self,
            variable=self.progress_var,
            maximum=100,
            length=400
        )
        self.progress_bar.pack(fill=tk.X, padx=10, pady=5)

        # 상태 메시지
        self.status_var = tk.StringVar()
        self.status_var.set("대기 중...")
        self.status_label = ttk.Label(self, textvariable=self.status_var, font=('Arial', 10))
        self.status_label.pack(pady=5)

    def set_progress(self, value: float, message: str = ""):
        """진행률 설정"""
        self.progress_var.set(value)
        if message:
            self.status_var.set(message)

    def reset(self):
        """진행률 리셋"""
        self.progress_var.set(0)
        self.status_var.set("대기 중...")


class PlatformCheckbox(ttk.Frame):
    """플랫폼 선택 체크박스"""

    def __init__(self, parent, platform_name: str, enabled: bool = True, **kwargs):
        super().__init__(parent, **kwargs)

        self.platform_name = platform_name
        self.var = tk.BooleanVar()
        self.var.set(enabled)

        # 체크박스
        self.checkbox = ttk.Checkbutton(
            self,
            text=platform_name.upper(),
            variable=self.var,
            onvalue=True,
            offvalue=False
        )
        self.checkbox.pack(side=tk.LEFT)

        # 상태 표시
        self.status_label = StatusLabel(self)
        self.status_label.pack(side=tk.RIGHT, padx=(10, 0))

        if enabled:
            self.set_ready()
        else:
            self.set_disabled()

    def set_ready(self):
        """준비 완료 상태"""
        self.status_label.set_status("준비 완료", "✅")
        self.checkbox.config(state='normal')

    def set_disabled(self):
        """비활성화 상태"""
        self.status_label.set_status("설정 필요", "❌")
        self.checkbox.config(state='disabled')
        self.var.set(False)

    def set_processing(self):
        """처리 중 상태"""
        self.status_label.set_status("처리 중", "🔄")

    def set_success(self):
        """성공 상태"""
        self.status_label.set_status("성공", "✅")

    def set_error(self, error_msg: str = "오류"):
        """오류 상태"""
        self.status_label.set_status(error_msg, "❌")

    def is_selected(self) -> bool:
        """선택 여부 반환"""
        return self.var.get() and self.checkbox.cget('state') == 'normal'


class ScrollableText(ttk.Frame):
    """스크롤 가능한 텍스트 위젯"""

    def __init__(self, parent, height: int = 10, **kwargs):
        super().__init__(parent, **kwargs)

        # 텍스트 위젯
        self.text = tk.Text(
            self,
            height=height,
            wrap=tk.WORD,
            font=('Consolas', 10),
            state=tk.DISABLED
        )

        # 스크롤바
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        self.text.config(yscrollcommand=self.scrollbar.set)

        # 배치
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def append_text(self, text: str):
        """텍스트 추가"""
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, text + "\n")
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)

    def clear(self):
        """텍스트 클리어"""
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        self.text.config(state=tk.DISABLED)


class SettingsFrame(ttk.LabelFrame):
    """설정 프레임"""

    def __init__(self, parent, title: str, **kwargs):
        super().__init__(parent, text=title, **kwargs)
        self.fields = {}

    def add_field(self, label: str, field_type: str = "entry", options: List[str] = None,
                  default_value: str = "", **kwargs) -> tk.Widget:
        """필드 추가"""
        row = len(self.fields)

        # 라벨
        ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)

        # 위젯 생성
        if field_type == "entry":
            widget = ttk.Entry(self, **kwargs)
            widget.insert(0, default_value)
        elif field_type == "combobox":
            widget = ttk.Combobox(self, values=options or [], state="readonly", **kwargs)
            if default_value in (options or []):
                widget.set(default_value)
        elif field_type == "spinbox":
            widget = ttk.Spinbox(self, **kwargs)
            widget.set(default_value)
        elif field_type == "checkbutton":
            var = tk.BooleanVar()
            var.set(default_value)
            widget = ttk.Checkbutton(self, variable=var, **kwargs)
            widget.var = var
        else:
            widget = ttk.Entry(self, **kwargs)

        widget.grid(row=row, column=1, sticky="ew", padx=5, pady=2)

        # 그리드 설정
        self.columnconfigure(1, weight=1)

        self.fields[label] = widget
        return widget

    def get_values(self) -> dict:
        """모든 필드 값 반환"""
        values = {}
        for label, widget in self.fields.items():
            if isinstance(widget, ttk.Entry):
                values[label] = widget.get()
            elif isinstance(widget, ttk.Combobox):
                values[label] = widget.get()
            elif isinstance(widget, ttk.Spinbox):
                values[label] = widget.get()
            elif isinstance(widget, ttk.Checkbutton):
                values[label] = widget.var.get()

        return values

    def set_values(self, values: dict):
        """필드 값 설정"""
        for label, value in values.items():
            if label in self.fields:
                widget = self.fields[label]
                if isinstance(widget, ttk.Entry):
                    widget.delete(0, tk.END)
                    widget.insert(0, str(value))
                elif isinstance(widget, ttk.Combobox):
                    widget.set(str(value))
                elif isinstance(widget, ttk.Spinbox):
                    widget.set(str(value))
                elif isinstance(widget, ttk.Checkbutton):
                    widget.var.set(bool(value))