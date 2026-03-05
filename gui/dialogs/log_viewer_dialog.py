# -*- coding: utf-8 -*-
"""
과거 로그 뷰어 다이얼로그
=========================
logs/ 폴더의 app.log 및 날짜별 순환 파일을 선택해 내용을 표시합니다.
"""
import os
import tkinter as tk
import customtkinter as ctk
from services.logger_service import get_available_log_paths, LOG_DIR

# 대용량 로그 시 마지막 N줄만 표시
MAX_LINES = 5000
# 또는 파일 크기 제한 (바이트), 초과 시 뒷부분만 읽기
MAX_BYTES = 1024 * 1024  # 1MB


def _read_log_tail(path):
    """파일 경로에서 UTF-8로 읽어 마지막 MAX_LINES줄 또는 MAX_BYTES 이내로 반환."""
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            size = os.path.getsize(path)
            if size > MAX_BYTES:
                f.seek(size - MAX_BYTES)
                # 첫 줄이 잘렸을 수 있으므로 한 줄 버리기
                f.readline()
            lines = f.readlines()
        if len(lines) > MAX_LINES:
            lines = lines[-MAX_LINES:]
        return "".join(lines)
    except Exception:
        return None


class LogViewerDialog(ctk.CTkToplevel):
    """과거 로그 파일 목록 선택 및 내용 표시 다이얼로그."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.title("과거 로그 보기")
        self.geometry("720x480")
        self.resizable(True, True)
        self.transient(parent)
        self._paths = []  # [(display_name, path), ...]
        self._path_by_display = {}
        self._build_ui()
        self._refresh_list_and_load()
        self.grab_set()

    def _build_ui(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill=tk.X, padx=12, pady=(12, 8))
        ctk.CTkLabel(
            top,
            text="로그 파일:",
            font=ctk.CTkFont(size=12),
        ).pack(side=tk.LEFT, padx=(0, 8))
        self._option_var = tk.StringVar(self, value="")
        self._option_menu = ctk.CTkOptionMenu(
            top,
            variable=self._option_var,
            values=[],
            command=self._on_select,
            width=220,
        )
        self._option_menu.pack(side=tk.LEFT)

        self._text = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap=tk.WORD,
        )
        self._text.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(0, 12))
        ctk.CTkButton(
            btn_frame,
            text="새로고침",
            width=90,
            command=self._refresh_list_and_load,
        ).pack(side=tk.LEFT, padx=4)
        ctk.CTkButton(
            btn_frame,
            text="폴더 열기",
            width=90,
            command=self._open_folder,
        ).pack(side=tk.LEFT, padx=4)
        ctk.CTkButton(
            btn_frame,
            text="클립보드에 복사",
            width=120,
            command=self._copy_to_clipboard,
        ).pack(side=tk.LEFT, padx=4)
        ctk.CTkButton(
            btn_frame,
            text="닫기",
            width=90,
            fg_color="#5D6D7E",
            command=self.destroy,
        ).pack(side=tk.LEFT, padx=4)

    def _copy_to_clipboard(self):
        try:
            text = self._text.get("1.0", "end-1c")
            self.clipboard_clear()
            self.clipboard_append(text)
            import tkinter.messagebox as messagebox
            messagebox.showinfo("복사 완료", "로그 내용이 클립보드에 복사되었습니다.", parent=self)
        except Exception:
            pass

    def _refresh_list_and_load(self):
        self._paths = get_available_log_paths()
        self._path_by_display = dict(self._paths)
        values = [d for d, _ in self._paths]
        self._option_menu.configure(values=values if values else ["(로그 파일 없음)"])
        if values:
            self._option_var.set(values[0])
            self._load_file(self._path_by_display.get(values[0]))
        else:
            self._option_var.set("(로그 파일 없음)")
            self._text.delete("1.0", tk.END)
            self._text.insert("1.0", "로그 파일이 없습니다.")

    def _on_select(self, choice):
        path = self._path_by_display.get(choice)
        self._load_file(path)

    def _load_file(self, path):
        self._text.delete("1.0", tk.END)
        if not path:
            self._text.insert("1.0", "파일을 읽을 수 없습니다.")
            return
        content = _read_log_tail(path)
        if content is None:
            self._text.insert("1.0", "파일을 읽을 수 없습니다.")
            return
        self._text.insert("1.0", content)
        self._text.see(tk.END)

    def _open_folder(self):
        folder = os.path.abspath(LOG_DIR)
        if not os.path.isdir(folder):
            return
        try:
            if os.name == "nt":
                os.startfile(folder)
            else:
                import subprocess
                subprocess.run(["xdg-open", folder], check=False)
        except Exception:
            pass
