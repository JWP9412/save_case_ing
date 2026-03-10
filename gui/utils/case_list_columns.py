# -*- coding: utf-8 -*-
"""
사건 목록 컬럼 설정 및 정렬 유틸리티
====================================

열 순서 다이얼로그, 컬럼 클릭 정렬, 헤더 전체선택 토글, 열 순서/너비 JSON 로드·저장.
app_controller에서 해당 메서드 호출 시 이 모듈에 위임합니다.
"""
import json
import os
import threading

import config
from config import COL_NAMES, COL_WIDTHS
from gui.dialogs.column_order_dialog import ColumnOrderDialog
from services.sort_manager import sort_cases


def open_column_order_dialog(app):
    """열 순서 설정 팝업. 위로/아래로로 순서 변경 후 적용 시 저장 및 목록 갱신."""
    if (
        getattr(app, "_column_order_dialog", None) is not None
        and app._column_order_dialog.winfo_exists()
    ):
        app._column_order_dialog.focus_set()
        return

    def on_apply(new_order):
        app.col_order[:] = new_order
        save_column_order(app)
        if hasattr(app, "case_list") and app.case_list:
            app.update_case_list_ui()
        app._column_order_dialog = None

    app._column_order_dialog = ColumnOrderDialog(
        app.root,
        app.col_order,
        app.get_theme_color,
        on_apply,
    )


def sort_case_list(app):
    """현재 정렬 기준(sort_column_index, sort_reverse)으로 case_list를 정렬한다."""
    if not app.case_list:
        return
    history = app.load_update_history()
    search_log = app.log_history_manager.load_search_log()
    app.case_list = sort_cases(
        app.case_list,
        app.sort_column_index,
        app.sort_reverse,
        history,
        search_log,
    )


def on_header_click(app, col_idx):
    """헤더 클릭 시 정렬 기준 변경 후 목록 재정렬 및 UI 갱신."""
    sortable = (1, 2, 3, 7, 8)
    if col_idx not in sortable:
        return
    if app.sort_column_index == col_idx:
        app.sort_reverse = not app.sort_reverse
    else:
        app.sort_column_index = col_idx
        app.sort_reverse = False
    sort_case_list(app)
    app.update_case_list_ui()


def on_header_select_toggle(app):
    """헤더 '전체' 체크박스 클릭 시: 체크면 전체 선택, 해제면 전체 해제."""
    if app.header_select_all_var.get():
        app.select_all_cases()
    else:
        app.deselect_all_cases()


def load_column_widths():
    """저장된 열 너비 JSON 로드. 리스트 길이가 COL_WIDTHS와 같을 때만 반환, 아니면 None."""
    path = getattr(config, "COLUMN_WIDTHS_FILE", "column_widths.json")
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                widths = json.load(f)
            if isinstance(widths, list) and len(widths) == len(COL_WIDTHS):
                return widths
    except Exception:
        pass
    return None


def load_column_order():
    """저장된 열 순서 JSON 로드. 리스트 길이·0~n-1 검증 후 반환, 아니면 None."""
    path = getattr(config, "COLUMN_ORDER_FILE", "column_order.json")
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                order = json.load(f)
            if (
                isinstance(order, list)
                and len(order) == len(COL_NAMES)
                and set(order) == set(range(len(COL_NAMES)))
            ):
                return order
    except Exception:
        pass
    return None


def save_column_order(app):
    """현재 열 순서를 COLUMN_ORDER_FILE에 JSON 배열로 저장."""
    path = getattr(config, "COLUMN_ORDER_FILE", "column_order.json")
    try:
        with getattr(app, "_file_lock", threading.Lock()):
            if hasattr(app, "col_order") and app.col_order:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(app.col_order, f, indent=2)
    except Exception:
        pass


def save_column_widths(app):
    """현재 열 너비를 COLUMN_WIDTHS_FILE에 JSON 배열로 저장."""
    path = getattr(config, "COLUMN_WIDTHS_FILE", "column_widths.json")
    try:
        with getattr(app, "_file_lock", threading.Lock()):
            if hasattr(app, "col_widths") and app.col_widths:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(app.col_widths, f, indent=2)
    except Exception:
        pass
