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
    BTN_H = 34
    BTN_CORNER_RADIUS = 6  # 모든 버튼 높이·모양 통일용
    ROW_H = 40  # 각 버튼 행 프레임 높이 (상·하단 행 동일하게 맞춤)
    # 비활성화 시 표시할 회색 톤 (사용자가 "눌릴 수 없음"을 시각적으로 인지하도록)
    DISABLED_FG = "#5D6D7E"
    DISABLED_TEXT = "#ECF0F1"
    # 설정 버튼용 색상 (비활성 버튼과 구분되도록 더 진한 톤)
    SETTINGS_FG = "#34495E"
    SETTINGS_HOVER = "#2C3E50"
    SETTINGS_TEXT = "#FFFFFF"

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

        btn_font = ctk.CTkFont(family="맑은 고딕", size=12, weight="bold")

        ctk.CTkLabel(
            control_frame,
            text="🎛️ 제어 패널",
            font=ctk.CTkFont(family="맑은 고딕", size=16, weight="bold"),
            text_color=app.get_theme_color("text_main"),
        ).pack(anchor=tk.W, pady=(0, 8))

        # 버튼별 "활성 시 색상"을 저장. 나중에 _set_control_btn_state에서 복원할 때 사용
        app._control_btn_colors = {}

        row1 = ctk.CTkFrame(control_frame, fg_color="transparent", height=ControlPanel.ROW_H)
        row1.pack(fill=tk.X, padx=0, pady=(0, 6))
        row1.pack_propagate(False)

        app.refresh_btn = ctk.CTkButton(
            row1,
            text="🔄 새로고침 (F5)",
            font=btn_font,
            fg_color="#27AE60",
            hover_color="#229954",
            text_color="#FFFFFF",
            width=ControlPanel.BTN_W,
            height=ControlPanel.BTN_H,
            corner_radius=ControlPanel.BTN_CORNER_RADIUS,
            cursor="hand2",
            command=lambda: app.load_google_sheet(force_network=True),
        )
        app._control_btn_colors[app.refresh_btn] = ("#27AE60", "#229954", "#FFFFFF")
        app.refresh_btn.pack(side=tk.LEFT, padx=(0, 10), pady=(ControlPanel.ROW_H - ControlPanel.BTN_H) // 2)

        app.start_btn = ctk.CTkButton(
            row1,
            text="🖼️ 사건 조회 로드",
            font=btn_font,
            fg_color="#E67E22",
            hover_color="#D35400",
            text_color="#FFFFFF",
            width=ControlPanel.BTN_W,
            height=ControlPanel.BTN_H,
            corner_radius=ControlPanel.BTN_CORNER_RADIUS,
            cursor="hand2",
            command=app.start_batch_processing,
        )
        app._control_btn_colors[app.start_btn] = ("#E67E22", "#D35400", "#FFFFFF")
        app.start_btn.pack(side=tk.LEFT, padx=(0, 10), pady=(ControlPanel.ROW_H - ControlPanel.BTN_H) // 2)

        app.complete_btn = ctk.CTkButton(
            row1,
            text="✔️ 캡차 입력 완료",
            font=btn_font,
            fg_color=ControlPanel.DISABLED_FG,
            hover_color=ControlPanel.DISABLED_FG,
            text_color=ControlPanel.DISABLED_TEXT,
            width=ControlPanel.BTN_W,
            height=ControlPanel.BTN_H,
            corner_radius=ControlPanel.BTN_CORNER_RADIUS,
            cursor="hand2",
            command=app.start_processing_thread,
            state="disabled",
        )
        app._control_btn_colors[app.complete_btn] = ("#16A085", "#138D75", "#FFFFFF")
        app.complete_btn.pack(side=tk.LEFT, padx=(0, 10), pady=(ControlPanel.ROW_H - ControlPanel.BTN_H) // 2)

        app.stop_btn = ctk.CTkButton(
            row1,
            text="⛔ 처리 중지",
            font=btn_font,
            fg_color=ControlPanel.DISABLED_FG,
            hover_color=ControlPanel.DISABLED_FG,
            text_color=ControlPanel.DISABLED_TEXT,
            width=ControlPanel.BTN_W,
            height=ControlPanel.BTN_H,
            corner_radius=ControlPanel.BTN_CORNER_RADIUS,
            cursor="hand2",
            command=app.stop_batch_processing,
            state="disabled",
        )
        app._control_btn_colors[app.stop_btn] = ("#E74C3C", "#C0392B", "#FFFFFF")
        app.stop_btn.pack(side=tk.LEFT, pady=(ControlPanel.ROW_H - ControlPanel.BTN_H) // 2)

        row2 = ctk.CTkFrame(control_frame, fg_color="transparent", height=ControlPanel.ROW_H)
        row2.pack(fill=tk.X, padx=0, pady=(0, 10))
        row2.pack_propagate(False)

        # 알림메일 발송 버튼 (미발송 내역이 있을 때만 활성 색상 표시)
        if hasattr(app, "send_notification_email"):
            app.email_btn = ctk.CTkButton(
                row2,
                text="📧 모든 사건 메일 발송",
                font=btn_font,
                width=ControlPanel.BTN_W,
                height=ControlPanel.BTN_H,
                corner_radius=ControlPanel.BTN_CORNER_RADIUS,
                cursor="hand2",
                fg_color=ControlPanel.DISABLED_FG,
                hover_color=ControlPanel.DISABLED_FG,
                text_color=ControlPanel.DISABLED_TEXT,
                command=app.send_notification_email,
            )
            app._control_btn_colors[app.email_btn] = ("#3498DB", "#2980B9", "#FFFFFF")
            app.email_btn.pack(side=tk.LEFT, padx=(0, 10), pady=(ControlPanel.ROW_H - ControlPanel.BTN_H) // 2)

        # 설정(Config 편집기) 버튼 - user_settings.json GUI (비활성 버튼과 구분되는 진한 색)
        if hasattr(app, "_open_settings_dialog"):
            settings_btn = ctk.CTkButton(
                row2,
                text="⚙ 설정",
                font=btn_font,
                width=80,
                height=ControlPanel.BTN_H,
                corner_radius=ControlPanel.BTN_CORNER_RADIUS,
                fg_color=ControlPanel.SETTINGS_FG,
                hover_color=ControlPanel.SETTINGS_HOVER,
                text_color=ControlPanel.SETTINGS_TEXT,
                cursor="hand2",
                command=app._open_settings_dialog,
            )
            settings_btn.pack(side=tk.LEFT, padx=(0, 0), pady=(ControlPanel.ROW_H - ControlPanel.BTN_H) // 2)

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
