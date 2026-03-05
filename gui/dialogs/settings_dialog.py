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


class SettingsDialog(ctk.CTkToplevel):
    """설정 창. 탭별로 구글 시트 / 자동화 / 일반 항목을 편집하고 저장합니다."""

    def __init__(self, parent, on_save_callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_save_callback = on_save_callback  # 저장 후 호출 (예: 헤더 색상 즉시 반영)
        self.title("설정")
        self.geometry("520x420")
        self.resizable(True, True)
        self.transient(parent)
        self.entries = {}
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
        self._add_row(tab_gs, "CASE_LIST_WORKSHEET_NAME", "사건 목록 시트 이름", 1)

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

    def _fill_from_config(self):
        for key in self.entries:
            val = getattr(config, key, "")
            self.entries[key].insert(0, str(val))

    def _collect_data(self):
        data = {}
        for key in config.USER_SETTINGS_OVERRIDABLE:
            if key not in self.entries:
                continue
            raw = self.entries[key].get().strip()
            if key in ("PUPPETEER_CAPTCHA_TIMEOUT", "PUPPETEER_PROCESSING_TIMEOUT",
                       "CAPTCHA_INPUT_TIMEOUT", "MAX_PARALLEL_LIMIT"):
                try:
                    data[key] = int(raw) if raw else getattr(config, key, 0)
                except ValueError:
                    data[key] = getattr(config, key, 0)
            else:
                data[key] = raw or getattr(config, key, "")
        return data

    def _on_save(self):
        try:
            data = self._collect_data()
            config.save_user_settings(data)
            config.load_user_settings()
            if self.on_save_callback:
                self.on_save_callback()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("저장 실패", str(e))
            return
        self.destroy()
