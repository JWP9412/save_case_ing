# -*- coding: utf-8 -*-
"""
배치 특수 작업 UI (중복 제거, 기록 초기화·재수집, 기간 조회, 시트 대조)
====================================================================

control_panel 버튼이 호출하는 확인 대화상자·플래그 설정 로직.
실제 크롤링·시트 처리는 ProcessController가 플래그로 수행합니다.
"""
from gui.dialogs.period_query_dialog import ask_period_range


def _format_case_labels(selected, max_show=15):
    """선택 사건 목록을 확인 대화상자용 문자열로 만듭니다."""
    case_labels = "\n".join(
        f"- {c.get('사건번호', '')}" for _, c in selected[:max_show]
    )
    extra = ""
    if len(selected) > max_show:
        extra = f"\n... 외 {len(selected) - max_show}건"
    return case_labels, extra


def _clear_special_modes(app):
    app.is_dedup_mode = False
    app.is_reset_mode = False
    app.is_period_mode = False
    app.is_compare_mode = False
    app.period_range = None


def remove_duplicates_for_selected_cases(app):
    """
    선택된 사건들의 구글 시트 탭에서 중복 진행내용 행을 제거합니다.
    """
    selected = app.get_selected_cases()
    if not selected:
        app.show_warning("중복을 제거할 사건을 선택해주세요.")
        return

    case_labels, extra = _format_case_labels(selected)

    if not app.ask_yesno(
        "중복 오류 제거",
        f"선택한 {len(selected)}건의 시트에서 중복 오류를 제거합니다.\n"
        "대법원 사이트의 실제 기록과 대조하기 위해 최신 사건 조회가 진행됩니다.\n\n"
        f"[대상]\n{case_labels}{extra}\n\n"
        "사건 조회를 시작하시겠습니까?",
    ):
        return

    _clear_special_modes(app)
    app.is_dedup_mode = True
    app.start_batch_processing()


def reset_and_refetch_selected_cases(app):
    """
    선택된 사건의 구글 시트 기록·로컬 캐시를 비운 뒤, 대법원에서 처음부터 다시 수집합니다.
    """
    selected = app.get_selected_cases()
    if not selected:
        app.show_warning("초기화 및 재수집할 사건을 선택해주세요.")
        return

    case_labels, extra = _format_case_labels(selected)

    if not app.ask_yesno(
        "기록 초기화 및 재수집",
        f"선택한 {len(selected)}건의 구글 시트 진행내용이 모두 삭제된 뒤,\n"
        "대법원 사이트에서 처음부터 다시 기록됩니다.\n"
        "(시트에 직접 적은 메모·서식은 복구되지 않을 수 있습니다.)\n\n"
        f"[대상]\n{case_labels}{extra}\n\n"
        "사건 조회를 시작하시겠습니까?",
    ):
        return

    _clear_special_modes(app)
    app.is_reset_mode = True
    app.start_batch_processing()


def run_period_query_for_selected_cases(app):
    """
    특정 기간의 대법원 기록만 재크롤링해 리포트로 보여줍니다.
    시트·update_history·unsent_emails 에는 쓰지 않습니다.
    """
    selected = app.get_selected_cases()
    if not selected:
        app.show_warning("기간 조회할 사건을 선택해주세요.")
        return

    period = ask_period_range(app.root)
    if not period:
        return
    start, end = period

    case_labels, extra = _format_case_labels(selected)
    from services.date_utils import format_date

    if not app.ask_yesno(
        "특정 기간 조회",
        f"기간: {format_date(start)} ~ {format_date(end)}\n"
        f"선택 {len(selected)}건을 대법원에서 조회한 뒤\n"
        "해당 기간 기록만 모아 미리보기를 엽니다.\n"
        "(구글 시트·기존 조회 이력에는 저장하지 않습니다.)\n\n"
        f"[대상]\n{case_labels}{extra}\n\n"
        "시작하시겠습니까?",
    ):
        return

    _clear_special_modes(app)
    app.is_period_mode = True
    app.period_range = (start, end)
    app.period_results = {}
    app.start_batch_processing()


def run_sheet_compare_for_selected_cases(app):
    """
    시트에 저장된 진행내용과 대법원 현재 기록을 내용 단위로 대조합니다.
    시트에는 쓰지 않습니다.
    """
    selected = app.get_selected_cases()
    if not selected:
        app.show_warning("대조할 사건을 선택해주세요.")
        return

    case_labels, extra = _format_case_labels(selected)
    if not app.ask_yesno(
        "시트-대법원 대조",
        f"선택 {len(selected)}건을 대법원에서 조회한 뒤\n"
        "구글 시트 기록과 내용이 일치하는지 비교합니다.\n"
        "(시트에는 아무것도 쓰지 않습니다.)\n\n"
        f"[대상]\n{case_labels}{extra}\n\n"
        "시작하시겠습니까?",
    ):
        return

    _clear_special_modes(app)
    app.is_compare_mode = True
    app.compare_results = {}
    app.start_batch_processing()
