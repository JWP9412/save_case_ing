# -*- coding: utf-8 -*-
"""
사건 목록 패널 (Case List Panel)
================================
사건 목록 테이블(헤더 + 행 영역)과 검색, 열 순서 설정 버튼을 제공합니다.
헤더와 행 영역은 각각 Canvas 위에 올려 가로 스크롤을 동기화하고, 열 너비 리사이즈를 지원합니다.
Why: 대량의 사건을 스크롤·검색·정렬·리사이즈할 수 있는 하나의 통합 뷰를 제공합니다.
"""
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk


class CaseListPanel:
    """
    사건 목록 영역(제목, 검색, 헤더 캔버스, 행 캔버스, 스크롤바)만 생성하는 클래스.
    실제 행 데이터는 메인 윈도우의 update_case_list_ui() 등에서 채웁니다.
    생성한 위젯 참조는 app에 붙여 두어, apply_column_width, _bind_mousewheel_to_case_list 등에서 사용합니다.
    """

    @staticmethod
    def create(parent, app):
        """
        사건 목록 패널 프레임을 생성하고, app에 다음을 저장한 뒤 반환합니다.
        - search_entry
        - header_canvas, case_canvas
        - header_container, case_list_frame
        - _case_list_mousewheel_handler
        root에 Ctrl+F 바인딩(_open_find_dialog)도 수행합니다.

        Parameters
        ----------
        parent : tk.Widget
            부모 위젯.
        app : object
            메인 윈도우. 필요:
            - get_theme_color(key)
            - _open_column_order_dialog(), perform_search()
            - col_order, apply_column_width()
            - root, _open_find_dialog()

        Returns
        -------
        ctk.CTkFrame
            사건 목록 전체를 담는 프레임.
        """
        # 구분선: 설정 패널과 사건 목록 시각적 구분
        sep = ctk.CTkFrame(
            parent, fg_color=app.get_theme_color("border"), height=2, corner_radius=0
        )
        sep.pack(fill=tk.X, padx=10, pady=(0, 4))
        sep.pack_propagate(False)

        case_frame = ctk.CTkFrame(parent, fg_color="transparent")
        case_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # ---- 제목 + 열 순서 설정 버튼 + 검색창 한 줄 ----
        title_row = ctk.CTkFrame(case_frame, fg_color="transparent")
        title_row.pack(anchor=tk.W, pady=(0, 4))
        app.case_list_title_label = ctk.CTkLabel(
            title_row,
            text="📋 사건 목록(0)",
            font=ctk.CTkFont(family="맑은 고딕", size=16, weight="bold"),
            text_color=app.get_theme_color("text_main"),
        )
        app.case_list_title_label.pack(side=tk.LEFT)
        settings_btn = ctk.CTkButton(
            title_row,
            text="⚙",
            font=ctk.CTkFont(size=16),
            width=36,
            height=28,
            fg_color="transparent",
            hover_color="#3D5A6C",
            cursor="hand2",
            command=app._open_column_order_dialog,
        )
        settings_btn.pack(side=tk.LEFT, padx=(8, 0))
        search_frame = ctk.CTkFrame(title_row, fg_color="transparent")
        search_frame.pack(side=tk.LEFT, padx=(16, 0))
        app.search_entry = ctk.CTkEntry(
            search_frame,
            width=200,
            height=28,
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            placeholder_text="검색...",
        )
        app.search_entry.pack(side=tk.LEFT, padx=(0, 6))
        app.search_entry.bind("<Return>", lambda e: app.perform_search())
        search_btn = ctk.CTkButton(
            search_frame,
            text="찾기",
            width=60,
            height=28,
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            cursor="hand2",
            command=app.perform_search,
        )
        search_btn.pack(side=tk.LEFT)

        main_container = ctk.CTkFrame(case_frame, fg_color="transparent")
        main_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # 헤더/행 캔버스를 먼저 만들어 app에 붙인 뒤, 스크롤 동기화 콜백에서 참조
        app.header_canvas = tk.Canvas(
            main_container,
            bg="#2B2B2B",
            height=40,
            highlightthickness=0,
            bd=0,
        )
        app.header_canvas.pack(fill=tk.X)

        app.case_canvas = tk.Canvas(
            main_container, bg="#2B2B2B", highlightthickness=0, bd=0
        )
        v_scrollbar = ttk.Scrollbar(
            main_container, orient="vertical", command=app.case_canvas.yview
        )

        def _sync_xview(*args):
            """가로 스크롤 시 헤더/행 캔버스를 동기화. scrollbar는 xview('moveto', f) 또는 xview('scroll', n, 'units') 형태로 호출."""
            app.header_canvas.xview(*args)
            app.case_canvas.xview(*args)

        h_scrollbar = ttk.Scrollbar(
            main_container, orient="horizontal", command=_sync_xview
        )

        app.header_container = ctk.CTkFrame(
            app.header_canvas, fg_color="#34495E", height=40, width=400
        )
        app.header_container.pack_propagate(False)
        app.header_canvas.create_window(
            (0, 0), window=app.header_container, anchor="nw"
        )
        app.header_canvas.configure(xscrollcommand=h_scrollbar.set)
        app.header_canvas.configure(scrollregion=(0, 0, 400, 40))

        app.case_list_frame = ctk.CTkFrame(
            app.case_canvas,
            fg_color="#2B2B2B",
            width=400,
            corner_radius=0,
            border_width=0,
        )
        app.case_canvas.create_window(
            (0, 0), window=app.case_list_frame, anchor="nw"
        )

        def _update_scroll_region(_=None):
            app.case_canvas.update_idletasks()
            app.case_canvas.configure(scrollregion=app.case_canvas.bbox("all"))

        app.case_list_frame.bind("<Configure>", _update_scroll_region)

        def _on_canvas_configure(_=None):
            _update_scroll_region()
            if hasattr(app, "col_order") and len(app.col_order) > 0:
                app.apply_column_width(len(app.col_order) - 1)

        app.case_canvas.bind("<Configure>", _on_canvas_configure)
        app.case_canvas.configure(yscrollcommand=v_scrollbar.set)
        app.case_canvas.configure(xscrollcommand=h_scrollbar.set)

        # 마우스 휠로 세로 스크롤. 행/하위 위젯에는 메인 윈도우의 _bind_mousewheel_to_case_list()에서 일괄 바인딩
        app._case_list_mousewheel_handler = lambda e: app.case_canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"
        )
        app.case_canvas.bind("<MouseWheel>", app._case_list_mousewheel_handler)
        app.case_list_frame.bind("<MouseWheel>", app._case_list_mousewheel_handler)

        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=0, pady=0)
        app.case_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=0, pady=0)

        app.root.bind("<Control-f>", app._open_find_dialog)

        return case_frame
