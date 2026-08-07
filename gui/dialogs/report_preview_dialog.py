# -*- coding: utf-8 -*-
"""
리포트 미리보기 다이얼로그
========================

기간 조회 / 시트 대조 결과를 HTML·Markdown 으로 미리보고
브라우저 열기, 파일 저장, 클립보드 복사, 메일 발송을 지원합니다.

주니어 개발자 참고:
- 메일 발송 시 clear_unsent_emails 를 호출하지 않습니다.
  (일반 알림메일 누적과 독립이어야 함)
"""
from __future__ import annotations

import os
import tempfile
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox

import customtkinter as ctk

import config


class ReportPreviewDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        *,
        title="리포트 미리보기",
        html_text="",
        markdown_text="",
        mail_subject_hint="",
        app=None,
    ):
        super().__init__(parent)
        self.title(title)
        self.geometry("900x620")
        self.html_text = html_text or ""
        self.markdown_text = markdown_text or ""
        self.mail_subject_hint = mail_subject_hint or ""
        self.app = app
        self.transient(parent)

        self._build()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill=tk.X, padx=10, pady=8)

        ctk.CTkButton(top, text="브라우저에서 열기", width=130, command=self._open_browser).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ctk.CTkButton(top, text="파일로 저장", width=100, command=self._save_file).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ctk.CTkButton(top, text="클립보드 복사", width=110, command=self._copy).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ctk.CTkButton(
            top, text="메일로 발송", width=110, fg_color="#3498DB", command=self._send_mail
        ).pack(side=tk.LEFT, padx=(0, 6))
        ctk.CTkButton(top, text="닫기", width=80, command=self.destroy).pack(side=tk.RIGHT)

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.tabs.add("HTML")
        self.tabs.add("Markdown")

        self.html_box = ctk.CTkTextbox(
            self.tabs.tab("HTML"), font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.html_box.pack(fill=tk.BOTH, expand=True)
        self.html_box.insert("1.0", self.html_text)

        self.md_box = ctk.CTkTextbox(
            self.tabs.tab("Markdown"), font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.md_box.pack(fill=tk.BOTH, expand=True)
        self.md_box.insert("1.0", self.markdown_text)

    def _current_is_html(self) -> bool:
        try:
            return self.tabs.get() == "HTML"
        except Exception:
            return True

    def _open_browser(self):
        path = os.path.join(tempfile.gettempdir(), "case_ing_report_preview.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.html_text)
        webbrowser.open(f"file:///{path.replace(os.sep, '/')}")

    def _save_file(self):
        if self._current_is_html():
            path = filedialog.asksaveasfilename(
                parent=self,
                defaultextension=".html",
                filetypes=[("HTML", "*.html"), ("All", "*.*")],
            )
            content = self.html_box.get("1.0", "end-1c")
        else:
            path = filedialog.asksaveasfilename(
                parent=self,
                defaultextension=".md",
                filetypes=[("Markdown", "*.md"), ("All", "*.*")],
            )
            content = self.md_box.get("1.0", "end-1c")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("저장", f"저장했습니다.\n{path}", parent=self)

    def _copy(self):
        content = (
            self.html_box.get("1.0", "end-1c")
            if self._current_is_html()
            else self.md_box.get("1.0", "end-1c")
        )
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("복사", "클립보드에 복사했습니다.", parent=self)

    def _send_mail(self):
        app = self.app
        if app is None:
            messagebox.showwarning("메일", "앱 연결이 없습니다.", parent=self)
            return
        recipient = (getattr(config, "NOTIFICATION_EMAIL_ADDRESS", "") or "").strip()
        if not recipient:
            messagebox.showwarning(
                "메일", "설정에서 알림 수신 메일 주소를 먼저 입력해주세요.", parent=self
            )
            return
        html = self.html_text
        if self.mail_subject_hint and "<h3>" in html:
            # 머리말에 이미 [기간 조회]/[시트 대조] 가 있음
            pass

        def worker():
            try:
                ok = app.google_sheets_service.append_notification_mail(html, recipient)
                # 중요: clear_unsent_emails 호출하지 않음
                def done():
                    if ok:
                        msg = "알림메일 시트에 기록했습니다. (발송상태: 대기)"
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
                                    msg += "\n\n(웹 앱을 통해 즉시 발송을 요청했습니다.)"
                            except Exception as e:
                                if hasattr(app, "log_message"):
                                    app.log_message(f"GAS 웹 앱 호출 실패: {e}")
                                msg += "\n\n(웹 앱 호출 실패. 트리거가 있으면 곧 발송됩니다.)"
                        messagebox.showinfo("메일", msg, parent=self)
                    else:
                        messagebox.showerror(
                            "메일", "구글 시트 기록에 실패했습니다.", parent=self
                        )

                self.after(0, done)
            except Exception as e:
                self.after(
                    0,
                    lambda: messagebox.showerror(
                        "메일", f"발송 중 오류: {e}", parent=self
                    ),
                )

        threading.Thread(target=worker, daemon=True).start()
