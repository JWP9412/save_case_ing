# -*- coding: utf-8 -*-
"""
진행상황 패널 (Progress Panel)
==============================
진행률 바와 로그 텍스트 영역을 제공합니다.
Why: 사용자가 배치 처리 진행률과 상세 로그를 한눈에 볼 수 있게 합니다.
"""
import tkinter as tk
import customtkinter as ctk
from gui.dialogs.log_viewer_dialog import LogViewerDialog


class ProgressPanel:
    """
    진행률 바와 로그(CTkTextbox)만 생성하는 클래스.
    생성한 progress_var, progress_bar, status_text 를 app에 붙여 두어,
    메인 윈도우의 로직에서 진행률 갱신·로그 출력이 가능하도록 합니다.
    """

    @staticmethod
    def create(parent, app):
        """
        진행상황 패널 프레임을 생성하고, app에 progress_var, progress_bar, status_text 를 저장한 뒤 반환합니다.

        Parameters
        ----------
        parent : tk.Widget
            부모 위젯 (우측 패널 등).
        app : object
            메인 윈도우. get_theme_color(key) 가 필요합니다.
            생성 후 app.progress_var, app.progress_bar, app.status_text 가 설정됩니다.

        Returns
        -------
        ctk.CTkFrame
            진행상황 패널 프레임.
        """
        progress_frame = ctk.CTkFrame(
            parent, fg_color=app.get_theme_color("bg_primary")
        )
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        title_row = ctk.CTkFrame(progress_frame, fg_color="transparent")
        title_row.pack(anchor=tk.W, pady=(0, 8))
        ctk.CTkLabel(
            title_row,
            text="📊 진행상황",
            font=ctk.CTkFont(family="맑은 고딕", size=16, weight="bold"),
            text_color=app.get_theme_color("text_main"),
        ).pack(side=tk.LEFT)

        app.progress_var = tk.DoubleVar()
        app.progress_bar = ctk.CTkProgressBar(progress_frame, height=16)
        app.progress_bar.pack(fill=tk.X, padx=0, pady=10)
        app.progress_bar.set(0)

        # 진행률 바와 로그 영역 사이 구분선
        sep = ctk.CTkFrame(
            progress_frame,
            fg_color=app.get_theme_color("border"),
            height=2,
            corner_radius=0,
        )
        sep.pack(fill=tk.X, pady=(0, 8))
        sep.pack_propagate(False)

        app.status_text = ctk.CTkTextbox(
            progress_frame,
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            fg_color="#34495E",
            text_color="#ECF0F1",
            wrap=tk.WORD,
            height=300,
            width=100,
        )
        app.status_text.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 8))

        def copy_log_to_clipboard():
            try:
                text = app.status_text.get("1.0", "end-1c")
                app.root.clipboard_clear()
                app.root.clipboard_append(text)
            except Exception:
                pass

        def open_log_viewer():
            try:
                LogViewerDialog(app.root)
            except Exception:
                pass

        bottom_row = ctk.CTkFrame(progress_frame, fg_color="transparent")
        bottom_row.pack(fill=tk.X, pady=(0, 10))
        ctk.CTkButton(
            bottom_row,
            text="📋 복사",
            width=60,
            command=copy_log_to_clipboard,
        ).pack(side=tk.LEFT, padx=(0, 8))
        ctk.CTkButton(
            bottom_row,
            text="과거 로그",
            width=70,
            command=open_log_viewer,
        ).pack(side=tk.LEFT)

        return progress_frame
