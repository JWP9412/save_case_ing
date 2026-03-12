# -*- coding: utf-8 -*-
"""
열(Column) 리사이즈 UI 조작
==========================

마우스 드래그로 사건 목록 테이블 열 너비 조절 시 가이드라인 표시 및 칸 너비 적용.
app_controller에서 _on_resize_press, _on_resize_motion, _on_resize_release, apply_column_width 호출 시 이 모듈에 위임합니다.
"""
import tkinter as tk

from gui.utils import case_list_columns as case_list_columns_module


def on_resize_press(app, display_idx, event):
    """display_idx: 표시 순서상 열 인덱스 (0~10). 내부 열 인덱스는 col_order[display_idx]."""
    if event is None:
        return
    app._resize_col = display_idx
    internal_idx = app.col_order[display_idx]
    app._resize_start_x = event.x_root
    app._resize_start_width = app.col_widths[internal_idx]
    app._resize_current_width = app.col_widths[internal_idx]
    if hasattr(app, "case_list_frame") and app.case_list_frame.winfo_exists():
        if app.resize_guide_line and app.resize_guide_line.winfo_exists():
            app.resize_guide_line.destroy()
        x_pos = app._display_width_up_to(display_idx)
        app.resize_guide_line = tk.Frame(
            app.case_list_frame, width=1, bg="#2C3E50", height=10000
        )
        app.resize_guide_line.place(x=x_pos, y=0, anchor=tk.NW)


def on_resize_motion(app, display_idx, event):
    if event is None or app._resize_col is None:
        return
    delta = event.x_root - app._resize_start_x
    new_w = max(30, min(500, app._resize_start_width + delta))
    app._resize_current_width = new_w
    if app.resize_guide_line and app.resize_guide_line.winfo_exists():
        x_pos = (
            sum(app.col_widths[app.col_order[i]] for i in range(display_idx))
            + new_w
        )
        app.resize_guide_line.place_configure(x=x_pos)


def on_resize_release(app, event):
    if event is None:
        return
    if app._resize_col is not None:
        display_idx = app._resize_col
        internal_idx = app.col_order[display_idx]
        app._resize_col = None
        app._resize_start_x = None
        app._resize_start_width = None
        if app.resize_guide_line and app.resize_guide_line.winfo_exists():
            app.resize_guide_line.destroy()
            app.resize_guide_line = None
        if app._resize_current_width is not None:
            app.col_widths[internal_idx] = int(app._resize_current_width)
            app._resize_current_width = None
        case_list_columns_module.save_column_widths(app)
        apply_column_width(app, display_idx)


def apply_column_width(app, display_idx):
    """리사이즈 후 해당 표시 열 너비만 적용 (display_idx = 표시 순서상 인덱스). 비고 열은 캔버스 여분 반영."""
    if not hasattr(app, "col_order") or display_idx >= len(app.col_order):
        return
    effective_total, extra_last = app._get_effective_widths()
    app._extra_width_last_col = extra_last
    last_internal = app.col_order[-1]
    last_disp_idx = len(app.col_order) - 1
    internal_idx = app.col_order[display_idx]
    w = app.col_widths[internal_idx] + (
        extra_last if internal_idx == last_internal else 0
    )
    if hasattr(app, "header_cell_frames") and display_idx < len(app.header_cell_frames):
        app.header_cell_frames[display_idx].configure(width=w)
    if hasattr(app, "case_cell_frames"):
        for row_cells in app.case_cell_frames.values():
            if display_idx < len(row_cells):
                row_cells[display_idx].config(width=w)
    w_last = app.col_widths[last_internal] + extra_last
    if last_disp_idx != display_idx and hasattr(app, "header_cell_frames") and last_disp_idx < len(app.header_cell_frames):
        app.header_cell_frames[last_disp_idx].configure(width=w_last)
    if hasattr(app, "case_cell_frames"):
        for row_cells in app.case_cell_frames.values():
            if last_disp_idx < len(row_cells):
                row_cells[last_disp_idx].config(width=w_last)
    if hasattr(app, "header_container") and app.header_container.winfo_exists():
        app.header_container.configure(width=effective_total)
    if hasattr(app, "header_canvas") and app.header_canvas.winfo_exists():
        app.header_canvas.configure(scrollregion=(0, 0, effective_total, 40))
    if hasattr(app, "case_list_frame") and app.case_list_frame.winfo_exists():
        app.case_list_frame.configure(width=effective_total)
    if hasattr(app, "case_frames"):
        for case_frame in app.case_frames.values():
            if case_frame.winfo_exists():
                case_frame.configure(width=effective_total)
    if hasattr(app, "case_separators"):
        for sep in app.case_separators.values():
            if sep.winfo_exists():
                sep.config(width=effective_total)
