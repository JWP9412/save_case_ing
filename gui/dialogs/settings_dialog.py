# -*- coding: utf-8 -*-
"""
설정 다이얼로그 (Config 편집기)
================================
user_settings.json에서 로드 가능한 항목을 GUI로 편집합니다.
저장 시 config.save_user_settings() 후 config.load_user_settings()로 메모리 반영.

[주니어 개발자] 새 설정 항목 추가 방법:
  1. config.py: USER_SETTINGS_OVERRIDABLE 튜플에 키 이름 추가.
  2. config.py: load_user_settings()에서 정수형이면 int(val) 처리 추가(필요 시).
  3. 본 파일: 해당 탭에 _add_row(탭, "키", "라벨", 1) 호출 추가.
  4. _collect_data(): 정수형 키면 int 변환, 나머지는 str 그대로 저장.
"""
import tkinter as tk
import customtkinter as ctk
import config
from tkinter import messagebox, filedialog
from services import google_oauth


class SettingsDialog(ctk.CTkToplevel):
    """설정 창. 탭별로 구글 시트 / 자동화 / 일반 항목을 편집하고 저장합니다."""

    def __init__(self, parent, on_save_callback=None, app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_save_callback = on_save_callback  # 저장 후 호출 (예: 헤더 색상 즉시 반영)
        self.app = app
        self.title("설정")
        self.geometry("520x420")
        self.resizable(True, True)
        self.transient(parent)
        self.entries = {}
        self.textboxes = {}
        self.calendar_enabled_var = tk.IntVar(
            value=int(getattr(config, "GOOGLE_CALENDAR_ENABLED", 0))
        )
        self._build_ui()
        self._fill_from_config()
        self.grab_set()

    def _build_ui(self):
        tabview = ctk.CTkTabview(self, width=480, height=320)
        tabview.pack(padx=12, pady=12, fill=tk.BOTH, expand=True)

        # ---------- 구글 시트 탭 ----------
        tab_gs = tabview.add("구글 시트")
        self._add_row(tab_gs, "GOOGLE_SHEET_ID", "스프레드시트 ID", 40)
        self._add_row(tab_gs, "SPREADSHEET_NAME", "스프레드시트 이름", 1)
        self._add_row(tab_gs, "GOOGLE_AUTH_FILE", "인증 파일 경로", 1)
        self._add_row(tab_gs, "GOOGLE_AUTH_MODE", "인증 모드(oauth/service_account)", 1)
        self._add_row_with_browse_file(
            tab_gs,
            "GOOGLE_OAUTH_CLIENT_SECRET_FILE",
            "OAuth 클라이언트 파일 경로",
            dialog_title="OAuth 클라이언트 JSON 선택",
            filetypes=[("JSON", "*.json"), ("모든 파일", "*.*")],
        )
        ctk.CTkLabel(
            tab_gs,
            text=(
                "GCP에서 받은 데스크톱 앱 OAuth JSON입니다. "
                "[찾아보기]로 선택 후 [저장], 그다음 [Google 계정 연동]을 누르세요."
            ),
            font=ctk.CTkFont(size=11),
            anchor="w",
            justify="left",
            wraplength=460,
        ).pack(fill=tk.X, pady=(0, 4))
        self._add_row(tab_gs, "GOOGLE_USER_TOKEN_FILE", "OAuth 토큰 파일 경로", 1)
        self._add_row(tab_gs, "CASE_LIST_WORKSHEET_NAME", "사건 목록 시트 이름", 1)
        self._add_row(tab_gs, "GOOGLE_CALENDAR_ID", "캘린더 ID(primary 권장)", 1)
        self._add_row(tab_gs, "GOOGLE_CALENDAR_EVENT_DURATION_MINUTES", "캘린더 기본 길이(분)", 1)
        cal_toggle_row = ctk.CTkFrame(tab_gs, fg_color="transparent")
        cal_toggle_row.pack(fill=tk.X, pady=4)
        ctk.CTkLabel(
            cal_toggle_row,
            text="캘린더 자동 등록",
            font=ctk.CTkFont(size=12),
            width=200,
            anchor="w",
        ).pack(side=tk.LEFT, padx=(0, 8))
        ctk.CTkSwitch(
            cal_toggle_row,
            text="사용",
            variable=self.calendar_enabled_var,
            onvalue=1,
            offvalue=0,
        ).pack(side=tk.LEFT)
        ctk.CTkLabel(
            tab_gs,
            text="켜면 조회 완료 시 변론/감정/판결선고 기일이 지정 캘린더에 등록됩니다.",
            font=ctk.CTkFont(size=11),
            anchor="w",
            justify="left",
        ).pack(fill=tk.X, pady=(0, 4))
        self._add_textbox(
            tab_gs,
            "GOOGLE_CALENDAR_SUMMARY_TEMPLATE",
            "캘린더 제목 템플릿",
            height=72,
        )
        self._add_textbox(
            tab_gs,
            "GOOGLE_CALENDAR_DESCRIPTION_TEMPLATE",
            "캘린더 설명 템플릿",
            height=120,
        )
        ctk.CTkLabel(
            tab_gs,
            text=(
                "치환자: {case_number}, {defendant}, {case_name}, {court}, "
                "{kind}, {start_date}, {start_time}, {label}, {start_iso}"
            ),
            font=ctk.CTkFont(size=11),
            anchor="w",
            justify="left",
        ).pack(fill=tk.X, pady=(0, 6))

        oauth_btn_frame = ctk.CTkFrame(tab_gs, fg_color="transparent")
        oauth_btn_frame.pack(fill=tk.X, pady=(8, 2))
        ctk.CTkButton(
            oauth_btn_frame,
            text="Google 계정 연동",
            width=140,
            command=self._on_link_google,
        ).pack(side=tk.LEFT, padx=(0, 6))
        ctk.CTkButton(
            oauth_btn_frame,
            text="연동 해제",
            width=110,
            fg_color="#5D6D7E",
            command=self._on_unlink_google,
        ).pack(side=tk.LEFT, padx=(0, 6))
        ctk.CTkButton(
            oauth_btn_frame,
            text="연동 상태 확인",
            width=130,
            fg_color="#2E86C1",
            command=self._on_check_link_status,
        ).pack(side=tk.LEFT)

        # ---------- 자동화 탭 ----------
        tab_auto = tabview.add("자동화")
        self._add_row(tab_auto, "PUPPETEER_CAPTCHA_TIMEOUT", "캡차 캡처 타임아웃(초)", 1)
        self._add_row(tab_auto, "PUPPETEER_PROCESSING_TIMEOUT", "처리 타임아웃(초)", 1)
        self._add_row(tab_auto, "CAPTCHA_INPUT_TIMEOUT", "캡차 입력 대기(초)", 1)

        # ---------- 일반 탭 ----------
        tab_gen = tabview.add("일반")
        self._add_row(tab_gen, "NOTIFICATION_EMAIL_ADDRESS", "알림 수신 메일 주소", 1)
        self._add_row(tab_gen, "NOTIFICATION_GAS_WEBAPP_URL", "GAS 웹 앱 URL (즉시 발송용)", 1)
        self._add_row(tab_gen, "HEADER_IMAGE_PATH", "배너 이미지 경로", 1)
        self._add_row(tab_gen, "HEADER_BG_COLOR", "헤더 배경색(#RRGGBB)", 1)
        self._add_row(tab_gen, "MAX_PARALLEL_LIMIT", "최대 병렬 처리 수", 1)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(0, 12))
        ctk.CTkButton(
            btn_frame,
            text="저장",
            width=100,
            command=self._on_save,
        ).pack(side=tk.LEFT, padx=4)
        ctk.CTkButton(
            btn_frame,
            text="취소",
            width=100,
            fg_color="#5D6D7E",
            command=self.destroy,
        ).pack(side=tk.LEFT, padx=4)

    def _add_row(self, parent, key, label_text, height_lines=1):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill=tk.X, pady=4)
        ctk.CTkLabel(
            row,
            text=label_text,
            font=ctk.CTkFont(size=12),
            width=200,
            anchor="w",
        ).pack(side=tk.LEFT, padx=(0, 8))
        entry = ctk.CTkEntry(row, height=28, font=ctk.CTkFont(size=12))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entries[key] = entry

    def _add_row_with_browse_file(
        self, parent, key, label_text, dialog_title, filetypes
    ):
        """
        한 줄 입력 + [찾아보기] 버튼.
        주니어: OAuth JSON처럼 긴 절대 경로를 손으로 치기 어려울 때 파일 대화상자로 넣습니다.
        """
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill=tk.X, pady=4)
        ctk.CTkLabel(
            row,
            text=label_text,
            font=ctk.CTkFont(size=12),
            width=200,
            anchor="w",
        ).pack(side=tk.LEFT, padx=(0, 8))
        entry = ctk.CTkEntry(row, height=28, font=ctk.CTkFont(size=12))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.entries[key] = entry
        ctk.CTkButton(
            row,
            text="찾아보기",
            width=72,
            command=lambda: self._browse_into_entry(entry, dialog_title, filetypes),
        ).pack(side=tk.LEFT)

    def _browse_into_entry(self, entry_widget, title, filetypes):
        path = filedialog.askopenfilename(parent=self, title=title, filetypes=filetypes)
        if path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, path)

    def _add_textbox(self, parent, key, label_text, height=100):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill=tk.BOTH, pady=4)
        ctk.CTkLabel(
            row,
            text=label_text,
            font=ctk.CTkFont(size=12),
            anchor="w",
        ).pack(anchor="w", padx=(0, 8), pady=(0, 4))
        tb = ctk.CTkTextbox(row, height=height, font=ctk.CTkFont(size=12))
        tb.pack(fill=tk.BOTH, expand=True)
        self.textboxes[key] = tb

    def _fill_from_config(self):
        for key in self.entries:
            val = getattr(config, key, "")
            self.entries[key].insert(0, str(val))
        self.calendar_enabled_var.set(int(getattr(config, "GOOGLE_CALENDAR_ENABLED", 0)))
        for key, tb in self.textboxes.items():
            val = str(getattr(config, key, "") or "")
            tb.delete("1.0", tk.END)
            tb.insert("1.0", val)

    def _collect_data(self):
        data = {}
        data["GOOGLE_CALENDAR_ENABLED"] = int(self.calendar_enabled_var.get())
        for key in config.USER_SETTINGS_OVERRIDABLE:
            if key == "GOOGLE_CALENDAR_ENABLED":
                continue
            if key in self.textboxes:
                raw_text = self.textboxes[key].get("1.0", tk.END).strip()
                data[key] = raw_text or str(getattr(config, key, "") or "")
                continue
            if key not in self.entries:
                continue
            raw = self.entries[key].get().strip()
            if key in ("PUPPETEER_CAPTCHA_TIMEOUT", "PUPPETEER_PROCESSING_TIMEOUT",
                       "CAPTCHA_INPUT_TIMEOUT", "MAX_PARALLEL_LIMIT",
                       "GOOGLE_CALENDAR_ENABLED", "GOOGLE_CALENDAR_EVENT_DURATION_MINUTES"):
                try:
                    data[key] = int(raw) if raw else getattr(config, key, 0)
                except ValueError:
                    data[key] = getattr(config, key, 0)
            else:
                data[key] = raw or getattr(config, key, "")
        return data

    def _on_link_google(self):
        # [저장] 전에도 연동 시도 가능: 입력창에 적힌 경로를 이번 호출용으로 config에 반영
        ent = self.entries.get("GOOGLE_OAUTH_CLIENT_SECRET_FILE")
        if ent is not None:
            typed = (ent.get() or "").strip()
            if typed:
                config.GOOGLE_OAUTH_CLIENT_SECRET_FILE = typed
        try:
            google_oauth.get_credentials(interactive=True, log_callback=getattr(self.app, "log_message", None))
            messagebox.showinfo("Google 연동", "Google 계정 연동이 완료되었습니다.")
        except Exception as e:
            messagebox.showerror("Google 연동 실패", str(e))

    def _on_unlink_google(self):
        if not messagebox.askyesno("연동 해제", "저장된 Google 사용자 토큰을 삭제하시겠습니까?"):
            return
        try:
            removed = google_oauth.clear_token()
            if removed:
                messagebox.showinfo("연동 해제", "저장된 사용자 토큰을 삭제했습니다.")
            else:
                messagebox.showinfo("연동 해제", "삭제할 사용자 토큰이 없습니다.")
        except Exception as e:
            messagebox.showerror("연동 해제 실패", str(e))

    def _on_check_link_status(self):
        linked = google_oauth.has_valid_token()
        message = "연동됨 (유효한 사용자 토큰 있음)" if linked else "미연동 (유효한 사용자 토큰 없음)"
        messagebox.showinfo("Google 연동 상태", message)

    def _on_save(self):
        try:
            data = self._collect_data()
            config.save_user_settings(data)
            config.load_user_settings()
            if self.on_save_callback:
                self.on_save_callback()
        except Exception as e:
            messagebox.showerror("저장 실패", str(e))
            return
        self.destroy()
