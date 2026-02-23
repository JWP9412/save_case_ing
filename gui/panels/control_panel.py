# -*- coding: utf-8 -*-
"""
제어 패널 (Control Panel)
=========================
새로고침, 사건 조회 로드 실행, 캡차 입력 완료, 처리 중지 버튼을 배치합니다.
Why: 사용자가 구글 시트 로드·캡차 로드·실제 처리·중지를 한 곳에서 제어할 수 있게 합니다.
"""
import tkinter as tk
import customtkinter as ctk


class ControlPanel:
    """
    제어 버튼 영역만 생성하는 클래스.
    생성한 버튼 참조(start_btn, complete_btn, stop_btn)와 색상 정보를
    app에 붙여 두어, 메인 윈도우에서 상태에 따라 버튼 활성/비활성 제어가 가능하도록 합니다.
    """

    # 버튼 공통 크기 (픽셀). 일관된 UI를 위해 상수로 관리
    BTN_W = 200
    BTN_H = 36
    # 비활성화 시 표시할 회색 톤 (사용자가 "눌릴 수 없음"을 시각적으로 인지하도록)
    DISABLED_FG = "#5D6D7E"
    DISABLED_TEXT = "#ECF0F1"

    @staticmethod
    def create(parent, app):
        """
        제어 패널 프레임을 생성하고, app에 버튼 참조를 저장한 뒤 반환합니다.

        Parameters
        ----------
        parent : tk.Widget
            부모 위젯.
        app : object
            메인 윈도우. 다음 메서드/속성이 필요합니다.
            - get_theme_color(key)
            - load_google_sheet()
            - start_batch_processing()
            - start_processing_thread()
            - stop_batch_processing()
            생성 후 app.refresh_btn, app.start_btn, app.complete_btn, app.stop_btn,
            app._control_btn_colors, app._set_control_btn_state 가 설정됩니다.

        Returns
        -------
        ctk.CTkFrame
            제어 패널 프레임.
        """
        control_frame = ctk.CTkFrame(
            parent, fg_color=app.get_theme_color("bg_primary")
        )
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        ctk.CTkLabel(
            control_frame,
            text="🎛️ 제어 패널",
            font=ctk.CTkFont(family="맑은 고딕", size=16, weight="bold"),
            text_color="#ECF0F1",
        ).pack(anchor=tk.W, pady=(0, 8))

        button_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        button_frame.pack(fill=tk.X, padx=0, pady=10)

        # 버튼별 "활성 시 색상"을 저장. 나중에 _set_control_btn_state에서 복원할 때 사용
        app._control_btn_colors = {}

        app.refresh_btn = ctk.CTkButton(
            button_frame,
            text="🔄 새로고침",
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
            fg_color="#27AE60",
            hover_color="#229954",
            text_color="#FFFFFF",
            width=ControlPanel.BTN_W,
            height=ControlPanel.BTN_H,
            cursor="hand2",
            command=app.load_google_sheet,
        )
        app._control_btn_colors[app.refresh_btn] = ("#27AE60", "#229954", "#FFFFFF")
        app.refresh_btn.pack(side=tk.LEFT, padx=(0, 10))

        app.start_btn = ctk.CTkButton(
            button_frame,
            text="🖼️ 사건 조회 로드 실행\n(캡차 로드 실행)",
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
            fg_color="#E67E22",
            hover_color="#D35400",
            text_color="#FFFFFF",
            width=ControlPanel.BTN_W,
            height=ControlPanel.BTN_H,
            cursor="hand2",
            command=app.start_batch_processing,
        )
        app._control_btn_colors[app.start_btn] = ("#E67E22", "#D35400", "#FFFFFF")
        app.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        app.complete_btn = ctk.CTkButton(
            button_frame,
            text="✔️ 캡차 입력 완료",
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
            fg_color=ControlPanel.DISABLED_FG,
            hover_color=ControlPanel.DISABLED_FG,
            text_color=ControlPanel.DISABLED_TEXT,
            width=ControlPanel.BTN_W,
            height=ControlPanel.BTN_H,
            cursor="hand2",
            command=app.start_processing_thread,
            state="disabled",
        )
        app._control_btn_colors[app.complete_btn] = ("#16A085", "#138D75", "#FFFFFF")
        app.complete_btn.pack(side=tk.LEFT, padx=(0, 10))

        app.stop_btn = ctk.CTkButton(
            button_frame,
            text="⛔ 처리 중지",
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
            fg_color=ControlPanel.DISABLED_FG,
            hover_color=ControlPanel.DISABLED_FG,
            text_color=ControlPanel.DISABLED_TEXT,
            width=ControlPanel.BTN_W,
            height=ControlPanel.BTN_H,
            cursor="hand2",
            command=app.stop_batch_processing,
            state="disabled",
        )
        app._control_btn_colors[app.stop_btn] = ("#E74C3C", "#C0392B", "#FFFFFF")
        app.stop_btn.pack(side=tk.LEFT)

        # 설정(Config 편집기) 버튼 - user_settings.json GUI
        if hasattr(app, "_open_settings_dialog"):
            settings_btn = ctk.CTkButton(
                button_frame,
                text="⚙ 설정",
                font=ctk.CTkFont(family="맑은 고딕", size=12),
                width=80,
                height=ControlPanel.BTN_H,
                fg_color="#5D6D7E",
                hover_color="#4A5A6A",
                cursor="hand2",
                command=app._open_settings_dialog,
            )
            settings_btn.pack(side=tk.LEFT, padx=(12, 0))

        return control_frame

    @staticmethod
    def set_control_btn_state(app, btn, enabled):
        """
        제어 패널 버튼 하나의 활성/비활성 상태와 색상을 갱신합니다.
        비활성 시 회색으로 보이도록 하고, 활성 시 _control_btn_colors에 저장된 색으로 복원합니다.

        Parameters
        ----------
        app : object
            _control_btn_colors 속성을 가진 메인 윈도우.
        btn : ctk.CTkButton
            대상 버튼.
        enabled : bool
            True면 활성(normal), False면 비활성(disabled) + 회색.
        """
        if enabled:
            colors = app._control_btn_colors.get(btn)
            if colors:
                fg, hover, text = colors
                btn.configure(
                    state="normal",
                    fg_color=fg,
                    hover_color=hover,
                    text_color=text,
                )
            else:
                btn.configure(state="normal")
        else:
            btn.configure(
                state="disabled",
                fg_color=ControlPanel.DISABLED_FG,
                hover_color=ControlPanel.DISABLED_FG,
                text_color=ControlPanel.DISABLED_TEXT,
            )
