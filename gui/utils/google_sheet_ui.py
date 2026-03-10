# -*- coding: utf-8 -*-
"""
구글 시트 UI
============

구글 시트에서 사건 목록을 비동기로 불러오고, 완료 시 app의 UI·데이터를 갱신합니다.
app_controller에서 load_google_sheet 호출 시 이 모듈에 위임합니다.
"""
import os
import threading
import tkinter as tk
from tkinter import messagebox

import config
from services.google_sheets import load_google_sheet_data


def _on_load_google_sheet_done(app, google_data, spreadsheet, error):
    """비동기 로드 완료 시 메인 스레드에서 호출. UI 갱신 및 버튼 복원."""
    if hasattr(app, "refresh_btn") and app.refresh_btn.winfo_exists():
        app.refresh_btn.configure(text="🔄 새로고침")
        app._set_control_btn_state(app.refresh_btn, True)
    app.start_btn.configure(text="🖼️ 사건 조회 로드 실행\n(캡차 로드 실행)")
    app._set_control_btn_state(app.start_btn, True)

    if error:
        app.log_message(f"❌ 구글 시트 로드 실패: {error}")
        messagebox.showerror("오류", f"구글 시트 로드 실패: {error}")
        return

    if not google_data:
        app.log_message("구글 시트 데이터를 로드할 수 없습니다.")
        messagebox.showerror("오류", "구글 시트 데이터를 로드할 수 없습니다.")
        return

    app.case_list = google_data
    app.sort_case_list()

    max_limit = getattr(config, "MAX_PARALLEL_LIMIT", 20)
    n_cases = len(app.case_list)
    smart_parallel = max(1, min(n_cases // 2, max_limit))
    app.max_parallel.set(smart_parallel)
    if (
        hasattr(app, "_settings_parallel_entry")
        and app._settings_parallel_entry.winfo_exists()
    ):
        app._settings_parallel_entry.delete(0, tk.END)
        app._settings_parallel_entry.insert(0, str(smart_parallel))
    if smart_parallel > 10:
        app.log_message(
            "⚠️ 고성능 모드: 인스턴스 폴더가 10개 이상 사용됩니다. 디스크/RAM 사용량이 늘어날 수 있습니다."
        )
    app.log_message(
        f"✅ {len(google_data)}개 사건 로드 완료 (병렬 처리: {smart_parallel}개)"
    )
    app.update_case_list_ui()


def load_google_sheet(app):
    """구글 시트에서 사건 목록 로드 (비동기). UI 프리징 방지를 위해 백그라운드 스레드에서 데이터를 가져옵니다."""
    app.start_btn.configure(text="🖼️ 사건 조회 로드 실행\n(캡차 로드 실행)")
    app._set_control_btn_state(app.start_btn, True)

    app.reset_internal_data()

    cookie_dir = getattr(config, "COOKIE_DATA_DIR", "cookie_data_for_save")
    search_log_path = getattr(config, "SEARCH_LOG_FILE", "search_log.json")
    if not os.path.isdir(cookie_dir) and os.path.isfile(search_log_path):
        try:
            os.remove(search_log_path)
            app.log_message("쿠키 데이터가 삭제되어 검색 기록을 초기화했습니다.")
        except Exception as e:
            app.log_message(f"⚠️ 검색 기록 초기화 실패: {e}")

    if hasattr(app, "refresh_btn") and app.refresh_btn.winfo_exists():
        app.refresh_btn.configure(text="⏳ 로딩 중...")
        app._set_control_btn_state(app.refresh_btn, False)
    app._set_control_btn_state(app.start_btn, False)
    app.log_message("구글 시트 연결 중...")

    def worker():
        try:
            google_data, spreadsheet = load_google_sheet_data()
            app.root.after(0, lambda: _on_load_google_sheet_done(app, google_data, spreadsheet, None))
        except Exception as e:
            app.root.after(0, lambda: _on_load_google_sheet_done(app, None, None, e))

    threading.Thread(target=worker, daemon=True).start()
