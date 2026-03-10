# -*- coding: utf-8 -*-
"""
체크박스 및 선택 관리 유틸리티
==============================

사건 목록의 좌측 체크박스 전체 선택/해제 및 상태 동기화.
app_controller에서 select_all_cases, deselect_all_cases, get_selected_cases, on_checkbox_change, find_case_index 호출 시 이 모듈에 위임합니다.
"""


def select_all_cases(app):
    """전체 사건 선택"""
    for var in app.case_checkboxes.values():
        var.set(True)


def deselect_all_cases(app):
    """전체 사건 해제"""
    for var in app.case_checkboxes.values():
        var.set(False)


def get_selected_cases(app):
    """선택된 사건 목록 반환 (인덱스 포함). (index, case) 튜플 리스트."""
    selected = []
    print(f"[DEBUG] 체크박스 개수: {len(app.case_checkboxes)}")
    print(f"[DEBUG] 사건 목록 개수: {len(app.case_list)}")

    for i, var in app.case_checkboxes.items():
        is_checked = var.get()
        print(
            f"[DEBUG] 사건 {i}: {app.case_list[i].get('사건번호', '')} - 체크됨: {is_checked}"
        )
        if is_checked:
            selected.append((i, app.case_list[i]))

    print(f"[DEBUG] 선택된 사건 수: {len(selected)}")
    return selected


def on_checkbox_change(app, index):
    """체크박스 변경 이벤트 핸들러. 행 선택 개수에 따라 헤더 토글도 동기화."""
    is_checked = app.case_checkboxes[index].get()
    case_number = app.case_list[index].get("사건번호", "")
    print(f"[DEBUG] 체크박스 변경: {case_number} - 체크됨: {is_checked}")
    if app.case_checkboxes:
        n = len(app.case_checkboxes)
        selected_count = sum(1 for v in app.case_checkboxes.values() if v.get())
        app.header_select_all_var.set(selected_count == n)


def find_case_index(app, case_number):
    """사건번호로 사건 인덱스 찾기"""
    for i, case in enumerate(app.case_list):
        if case.get("사건번호", "") == case_number:
            return i
    return -1
