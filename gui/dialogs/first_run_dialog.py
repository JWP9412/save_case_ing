# -*- coding: utf-8 -*-
"""
첫 실행 설정 가이드 다이얼로그
================================

세팅이 안 된 사용자에게 3단계(인증 파일 → Google 연동 → 시트 연결)를
앱 안에서 버튼으로 끝낼 수 있게 안내합니다.

주니어 개발자:
- 시작 시 app_controller.maybe_show_first_run_guide() 에서 호출됩니다.
- 설정 창의 [첫 실행 가이드 열기]에서도 같은 창을 띄울 수 있습니다.
"""

import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

import config
from services import google_oauth
from services import sheet_setup


class FirstRunDialog(ctk.CTkToplevel):
    """첫 실행 설정 가이드 (체크리스트 + 단계별 버튼)."""

    def __init__(self, parent, app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.title("첫 실행 설정 가이드")
        self.geometry("560x620")
        self.resizable(True, True)
        self.transient(parent)

        self._status_labels = {}
        self._step_frames = {}
        self._dont_show_var = tk.IntVar(value=0)
        self._sheet_url_entry = None
        self._btn_link = None
        self._btn_create_sheet = None
        self._btn_connect_sheet = None
        self._btn_browse_secret = None

        self._build_ui()
        self.refresh_status()
        self.grab_set()
        self.focus_set()

    def _log(self, message):
        if self.app and hasattr(self.app, "log_message"):
            self.app.log_message(message)

    def _build_ui(self):
        header = ctk.CTkLabel(
            self,
            text="처음 사용 전에 아래 3가지만 준비하면 됩니다.\n모두 이 창에서 끝낼 수 있습니다.",
            font=ctk.CTkFont(size=14),
            justify="left",
            anchor="w",
        )
        header.pack(fill=tk.X, padx=16, pady=(16, 8))

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        # ---- 1. 인증 파일 ----
        self._step_frames[1] = self._make_step_frame(
            body,
            step_no=1,
            title="인증 파일 넣기 (client_secret.json)",
            hint=(
                "Google Cloud에서 받은 JSON 파일을 고르면,\n"
                "앱이 api\\certification\\client_secret.json 으로 자동 복사합니다."
            ),
        )
        self._btn_browse_secret = ctk.CTkButton(
            self._step_frames[1],
            text="파일 찾아보기…",
            width=160,
            command=self._on_browse_secret,
        )
        self._btn_browse_secret.pack(anchor="w", padx=8, pady=(0, 8))

        # ---- 2. Google 연동 ----
        self._step_frames[2] = self._make_step_frame(
            body,
            step_no=2,
            title="Google 계정 로그인",
            hint="브라우저가 열리면 구글 계정으로 로그인·허용을 눌러 주세요.",
        )
        self._btn_link = ctk.CTkButton(
            self._step_frames[2],
            text="연동하기",
            width=160,
            command=self._on_link_google,
        )
        self._btn_link.pack(anchor="w", padx=8, pady=(0, 8))

        # ---- 3. 시트 연결 ----
        self._step_frames[3] = self._make_step_frame(
            body,
            step_no=3,
            title="구글 시트 연결",
            hint=(
                "추천: [새 시트 자동 만들기] — 클릭 한 번으로 시트·탭·헤더까지 생성.\n"
                "이미 쓰는 시트가 있으면 URL을 붙여넣고 [기존 시트 연결]."
            ),
        )
        sheet_btn_row = ctk.CTkFrame(self._step_frames[3], fg_color="transparent")
        sheet_btn_row.pack(fill=tk.X, padx=8, pady=(0, 6))
        self._btn_create_sheet = ctk.CTkButton(
            sheet_btn_row,
            text="새 시트 자동 만들기",
            width=160,
            command=self._on_create_sheet,
        )
        self._btn_create_sheet.pack(side=tk.LEFT, padx=(0, 8))

        url_row = ctk.CTkFrame(self._step_frames[3], fg_color="transparent")
        url_row.pack(fill=tk.X, padx=8, pady=(0, 4))
        self._sheet_url_entry = ctk.CTkEntry(
            url_row,
            placeholder_text="기존 시트 URL 또는 ID 붙여넣기",
            height=28,
        )
        self._sheet_url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self._btn_connect_sheet = ctk.CTkButton(
            url_row,
            text="기존 시트 연결",
            width=120,
            command=self._on_connect_sheet,
        )
        self._btn_connect_sheet.pack(side=tk.LEFT)

        # ---- 하단 ----
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill=tk.X, padx=16, pady=(8, 16))
        ctk.CTkCheckBox(
            footer,
            text="다시 보지 않기 (설정에서 다시 열 수 있음)",
            variable=self._dont_show_var,
            onvalue=1,
            offvalue=0,
        ).pack(side=tk.LEFT)
        ctk.CTkButton(
            footer,
            text="나중에 하기",
            width=120,
            fg_color="#5D6D7E",
            command=self._on_later,
        ).pack(side=tk.RIGHT, padx=(6, 0))
        ctk.CTkButton(
            footer,
            text="완료 · 닫기",
            width=120,
            command=self._on_done,
        ).pack(side=tk.RIGHT)

    def _make_step_frame(self, parent, step_no, title, hint):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill=tk.X, pady=6, padx=4)

        title_row = ctk.CTkFrame(frame, fg_color="transparent")
        title_row.pack(fill=tk.X, padx=8, pady=(8, 2))
        status = ctk.CTkLabel(
            title_row,
            text="[ ]",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=36,
            anchor="w",
        )
        status.pack(side=tk.LEFT)
        self._status_labels[step_no] = status
        ctk.CTkLabel(
            title_row,
            text=f"{step_no}. {title}",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        ctk.CTkLabel(
            frame,
            text=hint,
            font=ctk.CTkFont(size=11),
            anchor="w",
            justify="left",
            wraplength=480,
        ).pack(fill=tk.X, padx=8, pady=(0, 6))
        return frame

    def refresh_status(self):
        """체크 표시와 버튼 활성/비활성을 현재 세팅 상태에 맞게 갱신."""
        status = google_oauth.get_setup_status()
        self._set_check(1, status["client_secret"])
        self._set_check(2, status["token"])
        self._set_check(3, status["sheet_id"])

        # 순서 유도: 앞 단계 완료 전엔 뒤 단계 비활성
        step1_ok = status["client_secret"]
        step2_ok = status["token"]
        if self._btn_browse_secret:
            self._btn_browse_secret.configure(state="normal")
        if self._btn_link:
            self._btn_link.configure(state="normal" if step1_ok else "disabled")
        sheet_state = "normal" if (step1_ok and step2_ok) else "disabled"
        if self._btn_create_sheet:
            self._btn_create_sheet.configure(state=sheet_state)
        if self._btn_connect_sheet:
            self._btn_connect_sheet.configure(state=sheet_state)
        if self._sheet_url_entry:
            self._sheet_url_entry.configure(state=sheet_state)

    def _set_check(self, step_no, done):
        label = self._status_labels.get(step_no)
        if not label:
            return
        if done:
            label.configure(text="[OK]", text_color="#2ECC71")
        else:
            label.configure(text="[ ]", text_color=("gray40", "gray70"))

    def _on_browse_secret(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="OAuth 클라이언트 JSON 선택",
            filetypes=[("JSON", "*.json"), ("모든 파일", "*.*")],
        )
        if not path:
            return
        dest = config.path_from_base("api", "certification", "client_secret.json")
        try:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(path, dest)
            # 설정 경로도 표준 위치로 맞춤
            config.update_user_settings(
                {"GOOGLE_OAUTH_CLIENT_SECRET_FILE": "./api/certification/client_secret.json"}
            )
            self._log(f"인증 파일 복사 완료: {dest}")
            messagebox.showinfo(
                "인증 파일",
                "인증 파일을 준비했습니다.\n이제 2단계에서 [연동하기]를 눌러 주세요.",
                parent=self,
            )
        except Exception as e:
            messagebox.showerror("복사 실패", str(e), parent=self)
        self.refresh_status()

    def _on_link_google(self):
        if not google_oauth.has_client_secret_file():
            messagebox.showwarning(
                "인증 파일 필요",
                "먼저 1단계에서 인증 파일(JSON)을 넣어 주세요.",
                parent=self,
            )
            return
        try:
            google_oauth.get_credentials(interactive=True, log_callback=self._log)
            messagebox.showinfo("Google 연동", "Google 계정 연동이 완료되었습니다.", parent=self)
        except Exception as e:
            messagebox.showerror("Google 연동 실패", str(e), parent=self)
        self.refresh_status()

    def _on_create_sheet(self):
        try:
            result = sheet_setup.create_new_spreadsheet(
                title="case-ing",
                log_callback=self._log,
            )
            sheet_setup.apply_sheet_to_config(result["id"], result.get("title"))
            messagebox.showinfo(
                "시트 생성 완료",
                f"새 시트가 만들어졌습니다.\n\n"
                f"이름: {result.get('title')}\n"
                f"주소: {result.get('url')}\n\n"
                "프로그램 설정에 자동 저장했습니다.",
                parent=self,
            )
        except Exception as e:
            messagebox.showerror("시트 생성 실패", str(e), parent=self)
        self.refresh_status()

    def _on_connect_sheet(self):
        raw = ""
        if self._sheet_url_entry:
            raw = (self._sheet_url_entry.get() or "").strip()
        if not raw:
            messagebox.showwarning(
                "입력 필요",
                "시트 URL 또는 ID를 붙여넣어 주세요.",
                parent=self,
            )
            return
        try:
            sheet_id = sheet_setup.extract_sheet_id(raw)
            result = sheet_setup.verify_and_prepare(sheet_id, log_callback=self._log)
            sheet_setup.apply_sheet_to_config(result["id"], result.get("title"))
            messagebox.showinfo(
                "시트 연결 완료",
                f"시트에 연결했습니다.\n\n"
                f"이름: {result.get('title')}\n"
                f"주소: {result.get('url')}\n\n"
                "사건 목록 탭·헤더도 확인(없으면 자동 생성)했습니다.",
                parent=self,
            )
        except Exception as e:
            messagebox.showerror("시트 연결 실패", str(e), parent=self)
        self.refresh_status()

    def _persist_dont_show_if_checked(self):
        if int(self._dont_show_var.get() or 0) == 1:
            config.update_user_settings({"SHOW_FIRST_RUN_GUIDE": 0})
            self._log("첫 실행 가이드: 다시 보지 않기로 저장했습니다.")

    def _on_later(self):
        self._persist_dont_show_if_checked()
        self.destroy()

    def _on_done(self):
        self._persist_dont_show_if_checked()
        if google_oauth.is_setup_complete():
            # 세팅이 끝났으면 목록을 다시 불러 시도
            if self.app and hasattr(self.app, "load_google_sheet"):
                try:
                    self.app.load_google_sheet()
                except Exception:
                    pass
        self.destroy()
