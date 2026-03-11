# -*- coding: utf-8 -*-
"""
업데이트 기록 UI 갱신
====================

사건 처리 후 로컬 업데이트 기록(services.update_history) 저장 및 화면에 D+n/날짜 라벨 갱신.
app_controller에서 update_case_timestamp 호출 시 이 모듈에 위임합니다.
"""
import threading
from datetime import datetime

import config
import customtkinter as ctk

from services import update_history as update_history_service


def update_case_timestamp(app, case, original_index=None, row_count=0, is_auto=False, hearing_info=None):
    """사건 업데이트 타임스탬프 및 행 개수·기일 정보 기록, GUI 갱신 (기록은 services.update_history 사용)"""
    try:
        case_number = case.get("사건번호", "")

        with getattr(app, "_file_lock", threading.Lock()):
            history = update_history_service.load_update_history(config.UPDATE_HISTORY_FILE)

            old_data = history.get(case_number, {})
            if isinstance(old_data, str):
                old_row_count = 0
            else:
                old_row_count = old_data.get("row_count", 0)

            new_history = update_history_service.update_case_record(
                case_number, row_count, history, is_auto=is_auto, hearing_info=hearing_info
            )
            update_history_service.save_update_history(
                new_history, config.UPDATE_HISTORY_FILE
            )

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_rows = row_count - old_row_count if row_count > old_row_count else 0

        app.log_message(
            f"📝 업데이트 기록: {case_number} - {current_time} (행: {row_count}, 신규: +{new_rows}, 자동: {is_auto})"
        )

        if original_index is not None:
            # Format YYYY-MM-DD HH:MM:SS to YY.MM.DD.\nHH:MM:SS
            try:
                dt = datetime.strptime(current_time, "%Y-%m-%d %H:%M:%S")
                date_str = dt.strftime("%y.%m.%d.\n%H:%M:%S")
            except:
                date_str = current_time
            
            new_rows_text = f" (+{new_rows})" if new_rows > 0 else ""
            d_suffix = " (자동 조회)" if is_auto else ""
            display_text = f"D+0{d_suffix}{new_rows_text}"
            color = "#28A745" if new_rows > 0 else "#0D6EFD"

            def update_labels():
                if original_index in app.case_update_labels:
                    app.case_update_labels[original_index].configure(
                        text=display_text, text_color=color
                    )
                if original_index in app.case_update_date_labels:
                    if app.case_update_date_labels[original_index]:
                        app.case_update_date_labels[original_index].configure(
                            text=date_str
                        )
                    else:
                        if original_index in app.case_update_labels:
                            parent = app.case_update_labels[original_index].master
                            try:
                                parent_fg = (
                                    parent.cget("fg_color")
                                    if hasattr(parent, "cget")
                                    else "#2B2B2B"
                                )
                            except Exception:
                                parent_fg = "#2B2B2B"
                            new_date_label = ctk.CTkLabel(
                                parent,
                                text=date_str,
                                font=ctk.CTkFont(family="맑은 고딕", size=12),
                                text_color="#6C757D",
                            )
                            new_date_label.pack(
                                before=app.case_update_labels[original_index]
                            )
                            app.case_update_date_labels[original_index] = new_date_label

            app.root.after(0, update_labels)

    except Exception as e:
        app.log_message(f"⚠️ 업데이트 기록 실패: {e}")
