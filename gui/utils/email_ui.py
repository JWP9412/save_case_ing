# -*- coding: utf-8 -*-
"""
알림메일 전송 UI 래퍼
=====================

버튼 텍스트 갱신 및 메일 발송 플로우(구글 시트 기록, 웹앱 호출, 메시지 박스) 등 화면 표시용 이메일 액션.
실제 데이터 수집은 services.email_manager에서 수행합니다.
app_controller에서 update_email_btn_text, send_notification_email 호출 시 이 모듈에 위임합니다.
"""
import threading

from tkinter import messagebox

import config

from gui.panels import ControlPanel
from services import email_manager as email_manager_module


def update_email_btn_text(app):
    """알림메일 버튼의 텍스트 및 활성/비활성 색상을 갱신합니다. 보낼 내역 또는 마지막 조회 결과가 있으면 활성."""
    btn = getattr(app, "email_btn", None)
    if not btn or not btn.winfo_exists():
        return
    summary_text, last_sent = email_manager_module.get_summary_text()
    has_content = (
        bool(summary_text and summary_text.strip())
        or email_manager_module.has_last_run_result()
    )
    ControlPanel.set_control_btn_state(app, btn, has_content)
    if not last_sent:
        last_sent = "없음"
    btn.configure(
        text=f"{sanitize_email_label(config.BTN_TEXT_EMAIL)} (최근: {last_sent})",
        height=ControlPanel.BTN_H,
    )


def sanitize_email_label(text):
    """버튼 문구 sanitize 헬퍼(순환 import 방지용 지연 import)."""
    try:
        from gui.utils.glyphs import sanitize
        return sanitize(text)
    except Exception:
        return text


def send_notification_email(app):
    """미발송 누적 내역 또는 마지막 조회 결과를 구글 시트 '알림메일' 시트에 기록하고, 로컬 누적을 비웁니다. (비동기 처리)"""
    # 사건 목록 전체를 넘겨 미조회 건까지 요약에 포함
    all_cases = getattr(app, "case_list", None) or []
    summary_html, last_sent = email_manager_module.get_summary_html(all_cases=all_cases)
    if not summary_html or not summary_html.strip():
        messagebox.showinfo(
            "알림메일",
            "보낼 내역이 없습니다. (조회를 실행한 뒤 메일을 보낼 수 있습니다.)",
        )
        return

    recipient = (getattr(config, "NOTIFICATION_EMAIL_ADDRESS", "") or "").strip()
    if not recipient:
        messagebox.showwarning(
            "알림메일", "설정에서 알림 수신 메일 주소를 먼저 입력해주세요."
        )
        return

    btn = getattr(app, "email_btn", None)
    if btn and btn.winfo_exists():
        app._set_control_btn_state(btn, False)
        btn.configure(text="기록 및 발송 중...")

    def worker():
        try:
            ok = app.google_sheets_service.append_notification_mail(
                summary_html, recipient
            )
            if not ok:
                app.root.after(
                    0,
                    lambda: messagebox.showerror(
                        "알림메일", "구글 시트에 기록하는 데 실패했습니다."
                    ),
                )
                return

            email_manager_module.clear_unsent_emails_and_update_last_sent()

            msg_suffix = ""
            webapp_url = (
                getattr(config, "NOTIFICATION_GAS_WEBAPP_URL", "") or ""
            ).strip()
            if webapp_url:
                try:
                    import urllib.request

                    req = urllib.request.Request(
                        webapp_url, method="POST", data=b""
                    )
                    with urllib.request.urlopen(req, timeout=15) as _:
                        msg_suffix = "\n\n(웹 앱을 통해 즉시 발송을 요청했습니다.)"
                except Exception as e:
                    app.log_message(f"GAS 웹 앱 즉시 발송 호출 실패: {e}")
                    msg_suffix = "\n\n(웹 앱 호출에 실패했습니다. 트리거가 설정되어 있다면 1분 내로 발송됩니다.)"

            def final_update():
                update_email_btn_text(app)
                messagebox.showinfo(
                    "알림메일",
                    f"알림메일 시트에 기록했습니다. (발송상태: 대기){msg_suffix}",
                )

            app.root.after(0, final_update)

        except Exception as e:
            app.log_message(f"알림메일 기록 실패: {e}")
            app.root.after(
                0,
                lambda: messagebox.showerror(
                    "알림메일", f"기록 중 오류가 발생했습니다: {e}"
                ),
            )
        finally:
            if btn and btn.winfo_exists():
                app.root.after(0, lambda: app._set_control_btn_state(btn, True))
                app.root.after(0, lambda: update_email_btn_text(app))

    threading.Thread(target=worker, daemon=True).start()
