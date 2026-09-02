# -*- coding: utf-8 -*-
"""
제어 패널 (Control Panel)
=========================
새로고침, 사건 기록 수집, 캡차 입력 완료, 처리 중지,
사건 시트 관리(드롭다운), 기간 조회, 버전 업데이트 확인 버튼을 배치합니다.
(기일 달력 버튼은 사건 목록 패널 · 사건목록 관리 왼쪽에 있습니다.)

Why: 사용자가 구글 시트 로드·수집·처리·중지를 한 곳에서 제어할 수 있게 합니다.

주니어 개발자 참고:
- 버튼 문구는 config.BTN_TEXT_* 상수를 사용합니다(깨지는 이모지 제거).
- glyphs.sanitize()로 한 번 더 감싸 혹시 남은 이모지도 정리합니다.
- '사건 시트 관리'는 CTkOptionMenu가 아니라 CTkToplevel 팝업입니다.
  (값을 고르는 UI가 아니라 액션을 실행하는 UI이기 때문입니다.
   tk.Menu는 Windows 기본 흰 메뉴라 버튼과 폭·색이 안 맞아 CTk 팝업으로 통일.)
"""
import tkinter as tk
import customtkinter as ctk

import config
from gui.utils.glyphs import sanitize

# 시트 관리 팝업 항목 높이·여백 (트리거 버튼과 톤 맞춤)
_SHEET_POPUP_ITEM_H = 32
_SHEET_POPUP_PAD = 4
_SHEET_POPUP_FG = "#2980B9"
_SHEET_POPUP_HOVER = "#1F618D"
_SHEET_POPUP_BG = "#1A5276"


def _close_sheet_mgmt_popup(app):
    """열려 있는 시트 관리 팝업을 닫고 바깥클릭 바인딩을 해제합니다."""
    popup = getattr(app, "_sheet_mgmt_popup", None)
    app._sheet_mgmt_popup = None
    bind_id = getattr(app, "_sheet_mgmt_outside_bind", None)
    root = getattr(app, "root", None)
    if root is not None and bind_id is not None:
        try:
            root.unbind("<Button-1>", bind_id)
        except Exception:
            pass
        app._sheet_mgmt_outside_bind = None
    esc_id = getattr(app, "_sheet_mgmt_esc_bind", None)
    if root is not None and esc_id is not None:
        try:
            root.unbind("<Escape>", esc_id)
        except Exception:
            pass
        app._sheet_mgmt_esc_bind = None
    if popup is not None:
        try:
            if popup.winfo_exists():
                popup.destroy()
        except Exception:
            pass


def _open_sheet_mgmt_popup(app):
    """
    사건 시트 관리 CTk 드롭다운을 버튼 바로 아래에, 버튼과 같은 폭으로 엽니다.
    이미 열려 있으면 토글로 닫습니다.
    """
    btn = getattr(app, "sheet_mgmt_btn", None)
    if btn is None:
        return
    try:
        if str(btn.cget("state")) == "disabled":
            return
    except Exception:
        pass

    # 토글: 이미 열려 있으면 닫기
    existing = getattr(app, "_sheet_mgmt_popup", None)
    if existing is not None:
        try:
            if existing.winfo_exists():
                _close_sheet_mgmt_popup(app)
                return
        except Exception:
            app._sheet_mgmt_popup = None

    items = []
    if hasattr(app, "remove_duplicates_for_selected_cases"):
        items.append(
            (sanitize(config.BTN_TEXT_DEDUP), app.remove_duplicates_for_selected_cases)
        )
    if hasattr(app, "reset_and_refetch_selected_cases"):
        items.append(
            (sanitize(config.BTN_TEXT_RESET), app.reset_and_refetch_selected_cases)
        )
    if hasattr(app, "run_sheet_compare_for_selected_cases"):
        items.append(
            (sanitize(config.BTN_TEXT_COMPARE), app.run_sheet_compare_for_selected_cases)
        )
    if not items:
        return

    root = getattr(app, "root", None) or btn.winfo_toplevel()
    btn.update_idletasks()
    bw = max(ControlPanel.BTN_W, int(btn.winfo_width() or ControlPanel.BTN_W))
    bx = int(btn.winfo_rootx())
    by = int(btn.winfo_rooty() + btn.winfo_height())
    n = len(items)
    ph = _SHEET_POPUP_PAD * 2 + n * _SHEET_POPUP_ITEM_H + max(0, n - 1) * 2

    popup = ctk.CTkToplevel(root)
    popup.overrideredirect(True)
    try:
        popup.transient(root)
    except Exception:
        pass
    popup.configure(fg_color=_SHEET_POPUP_BG)
    popup.geometry(f"{bw}x{ph}+{bx}+{by}")
    try:
        popup.attributes("-topmost", True)
    except Exception:
        pass

    frame = ctk.CTkFrame(popup, fg_color=_SHEET_POPUP_BG, corner_radius=6)
    frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

    btn_font = ctk.CTkFont(family="맑은 고딕", size=12, weight="bold")

    def _run_and_close(cmd):
        _close_sheet_mgmt_popup(app)
        if cmd:
            cmd()

    inner = ctk.CTkFrame(frame, fg_color="transparent")
    inner.pack(fill=tk.BOTH, expand=True, padx=_SHEET_POPUP_PAD, pady=_SHEET_POPUP_PAD)
    for i, (label, cmd) in enumerate(items):
        row_btn = ctk.CTkButton(
            inner,
            text=label,
            font=btn_font,
            width=bw - _SHEET_POPUP_PAD * 2,
            height=_SHEET_POPUP_ITEM_H,
            corner_radius=ControlPanel.BTN_CORNER_RADIUS,
            fg_color=_SHEET_POPUP_FG,
            hover_color=_SHEET_POPUP_HOVER,
            text_color="#FFFFFF",
            cursor="hand2",
            command=lambda c=cmd: _run_and_close(c),
        )
        row_btn.pack(fill=tk.X, pady=(0, 2) if i < n - 1 else 0)

    app._sheet_mgmt_popup = popup

    def _on_outside(event):
        """팝업·트리거 버튼 밖을 클릭하면 닫기."""
        try:
            if not popup.winfo_exists():
                return
            px, py = popup.winfo_rootx(), popup.winfo_rooty()
            pw, ph2 = popup.winfo_width(), popup.winfo_height()
            ex, ey = event.x_root, event.y_root
            inside_popup = px <= ex <= px + pw and py <= ey <= py + ph2
            bx0, by0 = btn.winfo_rootx(), btn.winfo_rooty()
            bw0, bh0 = btn.winfo_width(), btn.winfo_height()
            inside_btn = bx0 <= ex <= bx0 + bw0 and by0 <= ey <= by0 + bh0
            if not inside_popup and not inside_btn:
                _close_sheet_mgmt_popup(app)
        except Exception:
            _close_sheet_mgmt_popup(app)

    def _on_esc(_event=None):
        _close_sheet_mgmt_popup(app)

    # 살짝 뒤에 바인딩해, 방금 누른 버튼 클릭이 바로 닫히지 않게 함
    def _bind_outside():
        if getattr(app, "_sheet_mgmt_popup", None) is not popup:
            return
        try:
            app._sheet_mgmt_outside_bind = root.bind("<Button-1>", _on_outside, add="+")
            app._sheet_mgmt_esc_bind = root.bind("<Escape>", _on_esc, add="+")
        except Exception:
            pass

    root.after(50, _bind_outside)
    try:
        popup.focus_force()
    except Exception:
        pass


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
        """
        control_frame = ctk.CTkFrame(
            parent, fg_color=app.get_theme_color("bg_primary")
        )
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        btn_font = ctk.CTkFont(family="맑은 고딕", size=12, weight="bold")

        ctk.CTkLabel(
            control_frame,
            text=sanitize(getattr(config, "BTN_TEXT_CONTROL_TITLE", "제어 패널")),
            font=ctk.CTkFont(family="맑은 고딕", size=16, weight="bold"),
            text_color=app.get_theme_color("text_main"),
        ).pack(anchor=tk.W, pady=(0, 8))

        app._control_btn_colors = {}
        app._sheet_mgmt_popup = None

        row1 = ctk.CTkFrame(control_frame, fg_color="transparent", height=ControlPanel.ROW_H)
        row1.pack(fill=tk.X, padx=0, pady=(0, 6))
        row1.pack_propagate(False)

        app.refresh_btn = ctk.CTkButton(
            row1,
            text=sanitize(config.BTN_TEXT_REFRESH),
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
            text=sanitize(config.BTN_TEXT_START_COLLECT),
            font=btn_font,
            fg_color=ControlPanel.DISABLED_FG,
            hover_color=ControlPanel.DISABLED_FG,
            text_color=ControlPanel.DISABLED_TEXT,
            width=ControlPanel.BTN_W,
            height=ControlPanel.BTN_H,
            corner_radius=ControlPanel.BTN_CORNER_RADIUS,
            cursor="hand2",
            command=app.start_batch_processing,
            state="disabled",
        )
        app._control_btn_colors[app.start_btn] = ("#E67E22", "#D35400", "#FFFFFF")
        app.start_btn.pack(side=tk.LEFT, padx=(0, 10), pady=(ControlPanel.ROW_H - ControlPanel.BTN_H) // 2)

        app.complete_btn = ctk.CTkButton(
            row1,
            text=sanitize(config.BTN_TEXT_COMPLETE),
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
            text=sanitize(config.BTN_TEXT_STOP),
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
        row2.pack(fill=tk.X, padx=0, pady=(0, 6))
        row2.pack_propagate(False)

        # --- 사건 시트 관리: CTk 팝업 (버튼과 동일 폭·파란 톤) ---
        has_sheet_actions = any(
            hasattr(app, name)
            for name in (
                "remove_duplicates_for_selected_cases",
                "reset_and_refetch_selected_cases",
                "run_sheet_compare_for_selected_cases",
            )
        )
        if has_sheet_actions:
            app.sheet_mgmt_btn = ctk.CTkButton(
                row2,
                text=sanitize(getattr(config, "BTN_TEXT_SHEET_MGMT", "사건 시트 관리")),
                font=btn_font,
                width=ControlPanel.BTN_W,
                height=ControlPanel.BTN_H,
                corner_radius=ControlPanel.BTN_CORNER_RADIUS,
                cursor="hand2",
                fg_color=ControlPanel.DISABLED_FG,
                hover_color=ControlPanel.DISABLED_FG,
                text_color=ControlPanel.DISABLED_TEXT,
                command=lambda: _open_sheet_mgmt_popup(app),
                state="disabled",
            )
            app._control_btn_colors[app.sheet_mgmt_btn] = ("#2980B9", "#1F618D", "#FFFFFF")
            app.sheet_mgmt_btn.pack(
                side=tk.LEFT,
                padx=(0, 10),
                pady=(ControlPanel.ROW_H - ControlPanel.BTN_H) // 2,
            )

        if hasattr(app, "send_notification_email"):
            app.email_btn = ctk.CTkButton(
                row2,
                text=sanitize(config.BTN_TEXT_EMAIL),
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

        if hasattr(app, "_open_settings_dialog"):
            settings_btn = ctk.CTkButton(
                row2,
                text=sanitize(config.BTN_TEXT_SETTINGS),
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

        row3 = ctk.CTkFrame(control_frame, fg_color="transparent", height=ControlPanel.ROW_H)
        row3.pack(fill=tk.X, padx=0, pady=(0, 10))
        row3.pack_propagate(False)

        if hasattr(app, "run_period_query_for_selected_cases"):
            app.period_btn = ctk.CTkButton(
                row3,
                text=sanitize(config.BTN_TEXT_PERIOD),
                font=btn_font,
                width=ControlPanel.BTN_W,
                height=ControlPanel.BTN_H,
                corner_radius=ControlPanel.BTN_CORNER_RADIUS,
                cursor="hand2",
                fg_color=ControlPanel.DISABLED_FG,
                hover_color=ControlPanel.DISABLED_FG,
                text_color=ControlPanel.DISABLED_TEXT,
                command=app.run_period_query_for_selected_cases,
                state="disabled",
            )
            app._control_btn_colors[app.period_btn] = ("#1ABC9C", "#16A085", "#FFFFFF")
            app.period_btn.pack(
                side=tk.LEFT,
                padx=(0, 10),
                pady=(ControlPanel.ROW_H - ControlPanel.BTN_H) // 2,
            )

        if hasattr(app, "check_app_update"):
            app.update_check_btn = ctk.CTkButton(
                row3,
                text=sanitize(
                    getattr(config, "BTN_TEXT_CHECK_UPDATE", "버전 업데이트 확인")
                ),
                font=btn_font,
                width=ControlPanel.BTN_W,
                height=ControlPanel.BTN_H,
                corner_radius=ControlPanel.BTN_CORNER_RADIUS,
                cursor="hand2",
                fg_color="#7F8C8D",
                hover_color="#5D6D7E",
                text_color="#FFFFFF",
                command=app.check_app_update,
            )
            app._control_btn_colors[app.update_check_btn] = ("#7F8C8D", "#5D6D7E", "#FFFFFF")
            app.update_check_btn.pack(
                side=tk.LEFT,
                padx=(0, 10),
                pady=(ControlPanel.ROW_H - ControlPanel.BTN_H) // 2,
            )

        return control_frame

    @staticmethod
    def set_control_btn_state(app, btn, enabled):
        """
        제어 패널 버튼 하나의 활성/비활성 상태와 색상을 갱신합니다.
        비활성 시 회색으로 보이도록 하고, 활성 시 _control_btn_colors에 저장된 색으로 복원합니다.
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
            if btn is getattr(app, "sheet_mgmt_btn", None):
                _close_sheet_mgmt_popup(app)
