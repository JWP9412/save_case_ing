# -*- coding: utf-8 -*-
"""
체크박스 및 선택 관리 유틸리티
==============================

사건 목록의 좌측 체크박스 전체 선택/해제 및 상태 동기화.
app_controller에서 select_all_cases, deselect_all_cases, get_selected_cases,
on_checkbox_change, find_case_index 호출 시 이 모듈에 위임합니다.

주니어:
- 선택이 없으면 「수집 실행」「사건 시트 관리」「특정 기간 조회」는 비활성입니다.
- 체크가 바뀔 때마다 update_selection_dependent_buttons()를 호출하세요.
"""


def _selected_count(app):
    boxes = getattr(app, "case_checkboxes", None) or {}
    return sum(1 for v in boxes.values() if v.get())


def update_selection_dependent_buttons(app):
    """
    사건 선택 여부에 따라 제어 패널 버튼을 켜고 끕니다.

    선택 필요: start_btn, sheet_mgmt_btn, period_btn
    (처리 중이면 start는 계속 끔. complete/stop/email/refresh/설정/버전확인은 여기 미포함)
    """
    has_sel = _selected_count(app) > 0
    processing = bool(getattr(app, "processing", False))
    set_state = getattr(app, "_set_control_btn_state", None)
    if not callable(set_state):
        return

    # 수집 실행: 선택 있음 + 처리 중이 아닐 때만
    start = getattr(app, "start_btn", None)
    if start is not None:
        try:
            if start.winfo_exists():
                set_state(start, has_sel and not processing)
        except Exception:
            pass

    for attr in ("sheet_mgmt_btn", "period_btn"):
        btn = getattr(app, attr, None)
        if btn is None:
            continue
        try:
            if btn.winfo_exists():
                # 처리 중에도 시트관리/기간조회는 막아 두는 편이 안전
                set_state(btn, has_sel and not processing)
        except Exception:
            pass


def restore_start_button_ui(app, button_text=None):
    """
    처리 종료·중지 후 시작 버튼 문구를 되돌리고,
    선택 여부에 맞게 활성/비활성합니다. (무조건 켜지 않음)
    """
    start = getattr(app, "start_btn", None)
    if start is not None and button_text:
        try:
            if start.winfo_exists():
                start.configure(text=button_text)
        except Exception:
            pass
    update_selection_dependent_buttons(app)


def select_all_cases(app):
    """전체 사건 선택"""
    for var in app.case_checkboxes.values():
        var.set(True)
    if app.case_checkboxes:
        app.header_select_all_var.set(True)
    update_selection_dependent_buttons(app)


def deselect_all_cases(app):
    """전체 사건 해제"""
    for var in app.case_checkboxes.values():
        var.set(False)
    if getattr(app, "header_select_all_var", None) is not None:
        app.header_select_all_var.set(False)
    update_selection_dependent_buttons(app)


def get_selected_cases(app):
    """선택된 사건 목록 반환 (인덱스 포함). (index, case) 튜플 리스트."""
    selected = []
    for i, var in app.case_checkboxes.items():
        if var.get():
            selected.append((i, app.case_list[i]))
    return selected


def on_checkbox_change(app, index):
    """체크박스 변경 이벤트 핸들러. 행 선택 개수에 따라 헤더 토글·버튼도 동기화."""
    if app.case_checkboxes:
        n = len(app.case_checkboxes)
        selected_count = _selected_count(app)
        app.header_select_all_var.set(selected_count == n and n > 0)
    update_selection_dependent_buttons(app)


def find_case_index(app, case_number):
    """사건번호로 사건 인덱스 찾기"""
    for i, case in enumerate(app.case_list):
        if case.get("사건번호", "") == case_number:
            return i
    return -1
