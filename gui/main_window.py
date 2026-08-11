# -*- coding: utf-8 -*-
"""
메인 윈도우 조립 및 실행
========================
AppController를 생성한 뒤, 헤더·좌측 패널(제어/설정/사건 목록)·우측 패널(진행상황)을
조립하고 이벤트 루프를 시작하는 진입점입니다.
Why: 레이아웃 구성과 실행 순서를 한 곳에서 관리하여, 진입점(main.py)이 간단해집니다.
"""
import json
import os
import tkinter as tk
import customtkinter as ctk
import config
from gui.app_controller import AppController


def load_right_panel_width():
    """
    저장된 우측(진행상황) 패널 너비를 로드합니다.
    없거나 잘못된 값이면 config 기본값을 반환합니다.
    Returns:
        int: 픽셀 단위 너비 (RIGHT_PANEL_MIN_WIDTH~800).
    """
    path = getattr(config, "RIGHT_PANEL_WIDTH_FILE", "right_panel_width.json")
    min_w = int(getattr(config, "RIGHT_PANEL_MIN_WIDTH", 280))
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            w = data.get("width")
            if isinstance(w, (int, float)) and min_w <= w <= 800:
                return int(w)
    except Exception:
        pass
    return max(int(config.RIGHT_PANEL_WIDTH), min_w)


def run_app():
    """
    앱을 생성·레이아웃 조립·실행합니다.
    main.py의 __main__에서 호출합니다.
    순서: GUI 객체 생성 → create_window() → 헤더 → PanedWindow(좌/우) → 좌측에 제어/설정/사건 목록, 우측에 진행상황 → run().
    """
    gui = AppController()
    root = gui.create_window()

    # 헤더 (상단 전체)
    gui.create_header(root)

    bg_primary = gui.get_theme_color("bg_primary")
    main_container = ctk.CTkFrame(root, fg_color=bg_primary)
    main_container.pack(fill=tk.BOTH, expand=True)

    right_width = load_right_panel_width()
    min_right = int(getattr(config, "RIGHT_PANEL_MIN_WIDTH", 280))
    paned = tk.PanedWindow(
        main_container,
        orient=tk.HORIZONTAL,
        bg=bg_primary,
        sashwidth=8,
        sashrelief=tk.RAISED,
    )
    paned.pack(fill=tk.BOTH, expand=True)
    gui.main_paned = paned

    left_panel = ctk.CTkFrame(paned, fg_color=bg_primary)
    paned.add(left_panel, minsize=400, stretch="always")

    right_panel = ctk.CTkFrame(paned, fg_color=bg_primary, width=right_width)
    right_panel.pack_propagate(False)
    # minsize: 로고가 잘리지 않는 최소 폭
    paned.add(right_panel, minsize=min_right, width=right_width, stretch="never")
    gui.right_panel = right_panel

    sashwidth = 8

    def apply_saved_sash():
        root.update_idletasks()
        total_w = paned.winfo_width()
        if total_w > 100:
            min_left = 400
            effective_right = min(right_width, total_w - min_left - sashwidth)
            effective_right = max(effective_right, min_right)
            paned.sash_place(0, total_w - effective_right - sashwidth, 0)

    root.after(100, apply_saved_sash)

    gui.create_control_panel(left_panel)
    # 「처리 설정」은 설정 창 탭으로 이동함 (메인 좌측 단락 제거)
    gui.create_case_list_panel(left_panel)
    gui.create_progress_panel(right_panel)

    root.bind("<F5>", lambda e: gui.load_google_sheet(force_network=True))

    gui.run()
