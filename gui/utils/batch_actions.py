# -*- coding: utf-8 -*-
"""
배치 특수 작업 UI (중복 제거, 기록 초기화·재수집)
==================================================

control_panel의 dedup_btn, reset_btn이 호출하는 확인 대화상자·플래그 설정 로직.
실제 크롤링·시트 처리는 ProcessController가 is_dedup_mode / is_reset_mode 플래그로 수행합니다.

주니어 개발자 참고:
- app_controller는 이 모듈로 위임만 하고, 비즈니스 로직은 여기에 둡니다.
- 두 기능 모두 start_batch_processing()으로 기존 '사건 조회 로드' 흐름을 재사용합니다.
"""


def _format_case_labels(selected, max_show=15):
    """선택 사건 목록을 확인 대화상자용 문자열로 만듭니다."""
    case_labels = "\n".join(
        f"- {c.get('사건번호', '')}" for _, c in selected[:max_show]
    )
    extra = ""
    if len(selected) > max_show:
        extra = f"\n... 외 {len(selected) - max_show}건"
    return case_labels, extra


def remove_duplicates_for_selected_cases(app):
    """
    선택된 사건들의 구글 시트 탭에서 중복 진행내용 행을 제거합니다.

    - 대법원 실제 기록과 대조하기 위해 먼저 사건 조회(캡차)를 진행합니다.
    - 조회 완료 시 is_dedup_mode 플래그에 따라 일반 저장이 아닌 대조/삭제 로직을 수행합니다.
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

    app.is_dedup_mode = True
    app.is_reset_mode = False
    app.start_batch_processing()


def reset_and_refetch_selected_cases(app):
    """
    선택된 사건의 구글 시트 기록·로컬 캐시를 비운 뒤, 대법원에서 처음부터 다시 수집합니다.

    - is_reset_mode 플래그를 켠 뒤 기존 '사건 조회 로드' 배치와 동일하게 진행합니다.
    - 조회 완료 시 process_controller가 시트를 비우고 전체 데이터를 새로 저장합니다.
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

    app.is_reset_mode = True
    app.is_dedup_mode = False
    app.start_batch_processing()
