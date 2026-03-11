# -*- coding: utf-8 -*-
"""
구글 시트 UI
============

구글 시트에서 사건 목록을 비동기로 불러오고, 완료 시 app의 UI·데이터를 갱신합니다.
app_controller에서 load_google_sheet 호출 시 이 모듈에 위임합니다.
숨긴 사건(hidden_cases.json) 로드/저장 및 로드 시 필터 적용.
"""
import json
import os
import threading
import tkinter as tk
from tkinter import messagebox

import config
from services.google_sheets import load_google_sheet_data


def load_hidden_cases():
    """data/hidden_cases.json에서 숨긴 사건번호 리스트 로드. 없거나 오류 시 []."""
    path = getattr(config, "HIDDEN_CASES_FILE", "data/hidden_cases.json")
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return [str(x).strip() for x in data if str(x).strip()]
    except Exception:
        pass
    return []


def save_hidden_cases(hidden_list):
    """숨긴 사건번호 리스트를 data/hidden_cases.json에 저장."""
    path = getattr(config, "HIDDEN_CASES_FILE", "data/hidden_cases.json")
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(hidden_list, f, ensure_ascii=False, indent=2)
    except Exception:
        raise


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

    hidden_set = set(load_hidden_cases())
    def _case_number_str(c):
        raw = c.get("사건번호") or ""
        return (str(raw).strip() if raw is not None else "")

    app.case_list = [
        c for c in google_data
        if _case_number_str(c) not in hidden_set
    ]
    if not app.case_list and google_data:
        app.log_message(
            "⚠️ 숨긴 사건이 전체와 같아 목록이 비었습니다. 숨김을 해제하고 목록을 표시합니다."
        )
        save_hidden_cases([])
        app.case_list = list(google_data)
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
