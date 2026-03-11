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
from config import COL_NAMES


from gui.panels.case_row import CaseRow

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
        # ... (생략된 코드는 create 메서드 내부 내용과 동일) ...
        # (이 부분은 StrReplace로 기존 create 메서드 내용을 유지하면서 아래 메서드만 교체합니다)
        # 실제로는 파일 전체를 다시 쓰는 것이 안전하지만, StrReplace를 사용하므로 create 메서드 내용은 유지된다고 가정합니다.
        # 그러나 여기서는 CaseListPanel 클래스 전체를 재작성하여 create_case_row를 수정하는 것이 목표입니다.
        
        # 구분선: 설정 패널과 사건 목록 시각적 구분
        sep = ctk.CTkFrame(
            parent, fg_color=app.get_theme_color("border"), height=2, corner_radius=0
        )
        sep.pack(fill=tk.X, padx=10, pady=(0, 4))
        sep.pack_propagate(False)

        case_frame = ctk.CTkFrame(parent, fg_color="transparent")
        case_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # ---- 제목 + 열 순서 설정 버튼 + 검색창 한 줄 (사건목록 관리 버튼 최우측) ----
        title_row = ctk.CTkFrame(case_frame, fg_color="transparent")
        title_row.pack(fill=tk.X, pady=(0, 4))
        manage_btn = ctk.CTkButton(
            title_row,
            text="사건목록 관리",
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            width=100,
            height=28,
            fg_color="#5DADE2",
            hover_color="#4A9FD4",
            cursor="hand2",
            command=app._open_case_list_manage_dialog,
        )
        manage_btn.pack(side=tk.RIGHT, padx=(8, 0))
        search_frame = ctk.CTkFrame(title_row, fg_color="transparent")
        search_frame.pack(side=tk.RIGHT, padx=(16, 0))
        settings_btn = ctk.CTkButton(
            title_row,
            text="⚙",
            font=ctk.CTkFont(size=16),
            width=36,
            height=28,
            fg_color="#5DADE2",
            hover_color="#4A9FD4",
            cursor="hand2",
            command=app._open_column_order_dialog,
        )
        settings_btn.pack(side=tk.LEFT, padx=(8, 0))
        app.case_list_title_label = ctk.CTkLabel(
            title_row,
            text="📋 사건 목록(0)",
            font=ctk.CTkFont(family="맑은 고딕", size=16, weight="bold"),
            text_color=app.get_theme_color("text_main"),
        )
        app.case_list_title_label.pack(side=tk.LEFT)
        app.search_entry = ctk.CTkEntry(
            search_frame,
            width=200,
            height=28,
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            placeholder_text="검색...",
        )
        app.search_entry.pack(side=tk.LEFT, padx=(0, 6))
        app.search_entry.bind("<Return>", lambda e: app.perform_search(direction="next"))
        app.search_entry.bind("<KeyRelease>", lambda e: app.update_search_count())
        app.search_count_label = ctk.CTkLabel(
            search_frame,
            text="0/0",
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            text_color=app.get_theme_color("text_sub"),
            width=36,
        )
        app.search_count_label.pack(side=tk.LEFT, padx=(0, 4))
        prev_btn = ctk.CTkButton(
            search_frame,
            text="▲",
            width=32,
            height=28,
            font=ctk.CTkFont(size=12),
            cursor="hand2",
            command=lambda: app.perform_search(direction="prev"),
        )
        prev_btn.pack(side=tk.LEFT, padx=(0, 2))
        next_btn = ctk.CTkButton(
            search_frame,
            text="▼",
            width=32,
            height=28,
            font=ctk.CTkFont(size=12),
            cursor="hand2",
            command=lambda: app.perform_search(direction="next"),
        )
        next_btn.pack(side=tk.LEFT)

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

    @staticmethod
    def create_list_header(app):
        """사건 목록 헤더 생성 (col_order 순서대로 표시). app에 header_cell_frames 등 저장."""
        for widget in app.header_container.winfo_children():
            widget.destroy()
        app.header_cell_frames = []
        sortable_internal = (1, 2, 3, 4, 8, 9)
        header_frame = ctk.CTkFrame(app.header_container, fg_color="#34495E")
        header_frame.pack(fill=tk.BOTH, expand=True)
        extra_last = getattr(app, "_extra_width_last_col", 0)
        last_internal = app.col_order[-1] if app.col_order else None
        for disp_idx, internal_idx in enumerate(app.col_order):
            name = COL_NAMES[internal_idx]
            width = app.col_widths[internal_idx] + (
                extra_last if internal_idx == last_internal else 0
            )
            cell = tk.Frame(
                header_frame,
                bg="#34495E",
                width=width,
                height=40,
                bd=0,
                highlightthickness=0,
            )
            cell.pack(side=tk.LEFT)
            cell.pack_propagate(False)
            app.header_cell_frames.append(cell)
            if internal_idx == 0:
                handle = tk.Frame(cell, bg="#34495E", width=10, height=40)
                handle.pack(side=tk.RIGHT, fill=tk.Y)
                handle.pack_propagate(False)
                line = tk.Frame(handle, bg="white", width=1, height=40)
                line.pack(side=tk.RIGHT, fill=tk.Y, padx=1)
                handle.config(cursor="sb_h_double_arrow")
                handle.bind(
                    "<ButtonPress-1>",
                    lambda e, d=disp_idx: app._on_resize_press(d, e),
                )
                handle.bind(
                    "<B1-Motion>",
                    lambda e, d=disp_idx: app._on_resize_motion(d, e),
                )
                handle.bind("<ButtonRelease-1>", lambda e: app._on_resize_release(e))
                header_cb = ctk.CTkCheckBox(
                    cell,
                    text="",
                    variable=app.header_select_all_var,
                    font=ctk.CTkFont(family="맑은 고딕", size=12),
                    width=24,
                    fg_color="#3D5A6C",
                    text_color=app.get_theme_color("text_header"),
                    command=app._on_header_select_toggle,
                )
                header_cb.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            elif internal_idx in sortable_internal:
                arrow = (
                    " ▼"
                    if (app.sort_column_index == internal_idx and app.sort_reverse)
                    else " ▲"
                )
                if app.sort_column_index != internal_idx:
                    arrow = ""
                display_text = name + arrow
                btn = ctk.CTkButton(
                    cell,
                    text=display_text,
                    font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"),
                    fg_color="transparent",
                    hover_color="#3D5A6C",
                    text_color=app.get_theme_color("text_header"),
                    anchor=tk.CENTER,
                    cursor="hand2",
                    command=lambda c=internal_idx: app.on_header_click(c),
                )
                btn.pack(fill=tk.BOTH, expand=True)
            else:
                label = ctk.CTkLabel(
                    cell,
                    text=name,
                    font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"),
                    text_color=app.get_theme_color("text_header"),
                )
                label.pack(fill=tk.BOTH, expand=True)
            if internal_idx != 0:
                handle = tk.Frame(cell, bg="#34495E", width=10, height=40)
                handle.pack(side=tk.RIGHT, fill=tk.Y)
                handle.pack_propagate(False)
                line = tk.Frame(handle, bg="white", width=1, height=40)
                line.pack(side=tk.RIGHT, fill=tk.Y, padx=1)
                handle.config(cursor="sb_h_double_arrow")
                handle.bind(
                    "<ButtonPress-1>",
                    lambda e, d=disp_idx: app._on_resize_press(d, e),
                )
                handle.bind(
                    "<B1-Motion>",
                    lambda e, d=disp_idx: app._on_resize_motion(d, e),
                )
                handle.bind("<ButtonRelease-1>", lambda e: app._on_resize_release(e))

    @staticmethod
    def create_case_row(app, parent, case, index, total_width, initial_status=None):
        """단일 사건 행 위젯 생성. CaseRow.create에 위임."""
        return CaseRow.create(app, parent, case, index, total_width, initial_status)
