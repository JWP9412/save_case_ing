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
                    if app.status_text and app.status_text.winfo_exists():
                        app.status_text.insert("end", msg + "\n")
                        app.status_text.see("end")

                elif task == "status":
                    case_index, display_text, text_color, bg_color = args

                    if case_index in app.case_status and app.case_status[case_index].winfo_exists():
                        app.case_status[case_index].configure(text=display_text, text_color=text_color)

                    if case_index in app.case_frames and app.case_frames[case_index].winfo_exists():
                        if bg_color:
                            app.case_frames[case_index].configure(fg_color=bg_color)
                            for widget in app.case_frames[case_index].winfo_children():
                                if widget.winfo_exists():
                                    try:
                                        widget.configure(fg_color=bg_color)
                                    except (tk.TclError, AttributeError):
                                        try:
                                            widget.config(bg=bg_color)
                                        except Exception:
                                            pass

                elif task == "progress":
                    percentage, text_status = args
                    if hasattr(app, "progress_var") and app.progress_var:
                        app.progress_var.set(percentage)
                    if hasattr(app, "progress_bar") and app.progress_bar.winfo_exists():
                        app.progress_bar.set(percentage / 100.0)
                    if text_status and app.status_text and app.status_text.winfo_exists():
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        app.status_text.insert("end", f"[{timestamp}] {text_status}\n")
                        app.status_text.see("end")

                elif task == "function":
                    func = args[0]
                    func(*args[1:], **kwargs)

            except Exception as e:
                print(f"UI Queue 처리 중 오류: {e}")
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
    bg_color = None
    if status.startswith("처리중"):
        bg_color = "#FFF3CD"
    elif status.startswith("완료"):
        bg_color = "#D4EDDA"
    elif status.startswith("실패") or status.startswith("오류"):
        bg_color = "#F8D7DA"

    app.ui_queue.put(("status", (case_index, display_text, color, bg_color), {}))


def update_progress(app, percentage, status_text=""):
    """진행률 업데이트 (Thread-Safe). 큐를 통해 메인 스레드에서 처리됩니다."""
    app.ui_queue.put(("progress", (percentage, status_text), {}))


def processing_completed(app):
    """처리 완료 후 UI 업데이트 (시작/중지 버튼 상태 및 완료 메시지)."""
    app._set_control_btn_state(app.start_btn, True)
    app._set_control_btn_state(app.stop_btn, False)
    app.log_message("🎉 모든 사건 처리 완료!")
    messagebox.showinfo("완료", "모든 사건 처리가 완료되었습니다.")
