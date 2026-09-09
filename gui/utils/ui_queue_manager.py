# -*- coding: utf-8 -*-
"""
UI 비동기 큐 및 상태 갱신 유틸리티
===================================

멀티스레딩 환경에서 메인 스레드 블로킹 없이 UI(진행률, 사건 상태, 로그)를 갱신합니다.
app_controller에서 _process_ui_queue, update_case_status, update_progress, processing_completed 호출 시 이 모듈에 위임합니다.
"""
import queue
import threading
from datetime import datetime

import tkinter as tk
from tkinter import messagebox

from services.logger_service import get_logger

_ui_logger = get_logger("ui_queue")


def append_status_log(app, text):
    """
    진행상황 로그에 한 줄 추가.
    status_text 는 CTkTextbox 또는 StatusLogCanvas 어댑터입니다.
    (Canvas도 insert/see/configure(state=...) API를 맞춰 두었습니다.)
    Text 계열은 disabled 이므로 쓸 때만 normal 로 열었다가 다시 잠급니다.
    Canvas 어댑터는 configure(state=...) 를 무시합니다.
    """
    st = getattr(app, "status_text", None)
    if not st:
        return
    try:
        if not st.winfo_exists():
            return
    except Exception:
        return
    try:
        st.configure(state="normal")
        st.insert("end", text)
        st.see("end")
    except Exception:
        pass
    finally:
        try:
            st.configure(state="disabled")
        except Exception:
            pass


def process_ui_queue(app):
    """
    메인 스레드에서 주기적으로 호출되어 UI 업데이트 큐를 처리합니다.
    여러 스레드에서 요청한 UI 변경 사항을 한 번에 모아서 처리하여 병목을 방지합니다.
    """
    try:
        for _ in range(100):
            if app.ui_queue.empty():
                break
            task, args, kwargs = app.ui_queue.get_nowait()

            try:
                if task == "log":
                    msg = args[0]
                    append_status_log(app, msg + "\n")

                elif task == "status":
                    case_index, display_text, text_color, bg_color = args

                    if case_index in app.case_status and app.case_status[case_index].winfo_exists():
                        lbl = app.case_status[case_index]
                        # tk.Label 은 fg, CTkLabel 은 text_color
                        try:
                            lbl.configure(text=display_text, fg=text_color)
                        except (tk.TclError, AttributeError):
                            try:
                                lbl.configure(text=display_text, text_color=text_color)
                            except Exception:
                                pass

                    if (
                        bg_color
                        and case_index in app.case_frames
                        and app.case_frames[case_index].winfo_exists()
                    ):
                        from gui.panels.case_row import apply_row_background

                        apply_row_background(
                            app.case_frames[case_index], bg_color, text_color="#000000"
                        )
                        # 행 배경을 칠한 뒤에도 상태 라벨 글씨색 유지 (완료=파란)
                        if (
                            case_index in app.case_status
                            and app.case_status[case_index].winfo_exists()
                        ):
                            lbl = app.case_status[case_index]
                            try:
                                lbl.configure(fg=text_color, bg=bg_color)
                            except (tk.TclError, AttributeError):
                                try:
                                    lbl.configure(text_color=text_color)
                                except Exception:
                                    pass

                elif task == "progress":
                    percentage, text_status = args
                    if hasattr(app, "progress_var") and app.progress_var:
                        app.progress_var.set(percentage)
                    if hasattr(app, "progress_bar") and app.progress_bar.winfo_exists():
                        app.progress_bar.set(percentage / 100.0)
                    if text_status:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        append_status_log(app, f"[{timestamp}] {text_status}\n")

                elif task == "function":
                    func = args[0]
                    func(*args[1:], **kwargs)

            except Exception as e:
                # print만 하면 콘솔 없는 빌드에서 흔적이 사라지므로 파일 로그에 남깁니다.
                _ui_logger.exception("UI Queue 처리 중 오류: %s", e)
            finally:
                app.ui_queue.task_done()

    except queue.Empty:
        pass
    finally:
        if hasattr(app, "root") and app.root and app.root.winfo_exists():
            app.root.after(100, lambda: process_ui_queue(app))


def update_case_status(app, case_index, status, color, emoji=""):
    """사건 상태 업데이트 (Thread-Safe). 파일 저장은 별도 스레드, UI 갱신은 큐로 메인 스레드에서 처리."""
    from gui.utils.glyphs import sanitize
    from gui.panels.case_row import STATUS_COMPLETE_FG, _is_complete_status

    # 완료 계열 글씨는 항상 파란색 (호출부가 green/회색이어도 UI·history 통일)
    if _is_complete_status(status):
        color = STATUS_COMPLETE_FG

    if 0 <= case_index < len(app.case_list):
        case_number = app.case_list[case_index].get("사건번호", "")
        if case_number:
            threading.Thread(
                target=app.log_history_manager.save_status_history,
                args=(case_number, status, color, emoji),
                daemon=True,
            ).start()

    # 맑은 고딕에서 이모지가 깨지므로 sanitize 후 표시
    raw = f"{emoji} {status}" if emoji else status
    display_text = sanitize(raw)
    # 행 배경: 처리중=노랑, 성공 계열=초록, 실패=분홍
    # 주니어 참고: "기간조회 완료(...)" 는 startswith("완료")에 안 걸리므로
    # 별도 접두어/포함 검사로 초록을 줍니다. 안 주면 이전 노랑이 남습니다.
    bg_color = None
    if status.startswith("처리중"):
        bg_color = "#FFF3CD"
    elif _is_complete_status(status):
        bg_color = "#D4EDDA"
    elif status.startswith("실패") or status.startswith("오류"):
        bg_color = "#F8D7DA"

    app.ui_queue.put(("status", (case_index, display_text, color, bg_color), {}))


def update_progress(app, percentage, status_text=""):
    """진행률 업데이트 (Thread-Safe). 큐를 통해 메인 스레드에서 처리됩니다."""
    app.ui_queue.put(("progress", (percentage, status_text), {}))


def processing_completed(app):
    """처리 완료 후 UI 업데이트 (시작/중지 버튼 상태 및 완료 메시지)."""
    app._set_control_btn_state(app.stop_btn, False)
    try:
        from gui.utils import selection_manager as selection_manager_module

        selection_manager_module.update_selection_dependent_buttons(app)
    except Exception:
        app._set_control_btn_state(app.start_btn, True)
    app.log_message("🎉 모든 사건 처리 완료!")
    messagebox.showinfo("완료", "모든 사건 처리가 완료되었습니다.")
