#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
프로그램 진입점
===============

실행: python main.py
역할: GUI 객체 생성 → 창/패널 구성 → 이벤트 루프 시작.
"""
import json
import os
import tkinter as tk
import customtkinter as ctk
import config
from batch_gui_maker import BatchProcessingGUI


def load_right_panel_width():
    """저장된 우측(진행상황) 패널 너비 로드. 없거나 잘못된 값이면 config 기본값 사용."""
    path = getattr(config, "RIGHT_PANEL_WIDTH_FILE", "right_panel_width.json")
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            w = data.get("width")
            if isinstance(w, (int, float)) and 200 <= w <= 800:
                return int(w)
    except Exception:
        pass
    return config.RIGHT_PANEL_WIDTH


def main():
    """
    프로그램의 메인 함수 (진입점)

    이 함수는 프로그램이 시작될 때 가장 먼저 실행됩니다.
    GUI를 생성하고 화면에 표시합니다.

    실행 순서:
        1. BatchProcessingGUI 객체 생성
        2. 메인 창 생성
        3. 헤더 영역 생성 (상단 제목)
        4. 좌측 패널 생성 (제어 패널, 설정, 사건 목록)
        5. 우측 패널 생성 (진행상황)
        6. GUI 실행 (이벤트 루프 시작)

    GUI 레이아웃:
        ┌─────────────────────────────────────┐
        │         헤더 (제목)                │
        ├──────────────┬──────────────────────┤
        │              │                      │
        │   좌측 패널   │    우측 패널         │
        │              │   (진행상황)         │
        │  - 제어      │                      │
        │  - 설정      │   - 진행률 바         │
        │  - 사건목록  │   - 로그 창           │
        │              │                      │
        └──────────────┴──────────────────────┘
    """
    print("=== 일괄 처리 GUI 시작 ===")

    # ============================================================
    # 1단계: GUI 객체 생성
    # ============================================================
    # BatchProcessingGUI 클래스의 인스턴스 생성
    # 이 객체가 모든 GUI 기능을 관리합니다
    gui = BatchProcessingGUI()

    # ============================================================
    # 2단계: 메인 창 생성
    # ============================================================
    # create_window()는 tk.Tk() 객체를 생성하고 반환합니다
    root = gui.create_window()

    # ============================================================
    # 3단계: 헤더 영역 생성 (상단 전체)
    # ============================================================
    # 상단에 제목과 부제목을 표시하는 영역
    gui.create_header(root)

    # ============================================================
    # 4단계: 메인 컨테이너 생성 (좌측 + 우측, 사용자가 구분선 드래그로 크기 조절 가능)
    # ============================================================
    # 테마와 통일된 배경색 사용 (다크 모드 시 사건 목록 밖 영역이 어두운 톤으로 맞춰짐)
    bg_primary = gui.get_theme_color("bg_primary")
    main_container = ctk.CTkFrame(root, fg_color=bg_primary)
    main_container.pack(fill=tk.BOTH, expand=True)

    # PanedWindow: 좌/우 패널 경계 구분선, 드래그로 진행상황 창 크기 조절 (배경색은 테마와 동일하게)
    right_width = load_right_panel_width()
    paned = tk.PanedWindow(
        main_container,
        orient=tk.HORIZONTAL,
        bg=bg_primary,
        sashwidth=8,
        sashrelief=tk.RAISED,
    )
    paned.pack(fill=tk.BOTH, expand=True)

    # ============================================================
    # 5단계: 좌측 패널 생성 (제어 + 설정 + 사건 목록)
    # ============================================================
    left_panel = ctk.CTkFrame(paned, fg_color=bg_primary)
    # stretch="always": 창 크기 변경 시 좌측 패널이 먼저 늘어나도록 함
    paned.add(left_panel, minsize=400, stretch="always")

    # ============================================================
    # 6단계: 우측 패널 생성 (진행상황) - 저장된 너비 복원 또는 기본값, 드래그로 조절 가능
    # ============================================================
    right_panel = ctk.CTkFrame(paned, fg_color=bg_primary, width=right_width)
    right_panel.pack_propagate(False)
    # stretch="never": 우측 패널은 지정한 너비를 우선 유지
    paned.add(right_panel, minsize=200, width=right_width, stretch="never")

    # 종료 시 우측 패널 너비 저장을 위해 gui에 참조 전달
    gui.right_panel = right_panel

    # 창이 뜬 후 저장된 우측 패널 너비에 맞춰 구분선 위치 강제 조정
    # (PanedWindow는 초기 렌더 시 width만으로는 위치를 정확히 잡지 못하는 경우가 있음)
    sashwidth = 8  # PanedWindow 생성 시 지정한 값과 동일

    def apply_saved_sash():
        root.update_idletasks()
        total_w = paned.winfo_width()
        if total_w > 100:
            # 좌측 최소 400px 확보, 구분선 두께(sashwidth) 반영
            min_left = 400
            effective_right = min(right_width, total_w - min_left - sashwidth)
            effective_right = max(effective_right, 200)  # 우측 최소 200
            paned.sash_place(0, total_w - effective_right - sashwidth, 0)

    root.after(100, apply_saved_sash)

    # ============================================================
    # 7단계: 좌측 패널에 위젯들 배치
    # ============================================================
    # 제어 패널: 버튼들 (구글 시트 로드, 전체 선택, 캡차 이미지 로드 등)
    gui.create_control_panel(left_panel)
    # 설정 패널: 병렬 처리 수, 재시도 횟수 등
    gui.create_settings_panel(left_panel)
    # 사건 목록 패널: 체크박스와 사건 정보가 표시되는 테이블
    gui.create_case_list_panel(left_panel)

    # ============================================================
    # 8단계: 우측 패널에 진행상황 배치
    # ============================================================
    # 진행률 바와 로그 텍스트 창
    gui.create_progress_panel(right_panel)

    # ============================================================
    # 9단계: GUI 실행 (이벤트 루프 시작)
    # ============================================================
    # run() 함수는 root.mainloop()를 호출합니다
    # 이 함수가 실행되면 GUI가 화면에 표시되고 사용자 입력을 기다립니다
    # 프로그램이 종료될 때까지 계속 실행됩니다
    gui.run()


if __name__ == "__main__":
    main()
