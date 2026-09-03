# -*- coding: utf-8 -*-
"""process_controller.py 를 mixin 패키지로 분리하는 일회성 스크립트."""
import ast
import os
import textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "services", "process_controller.py")
PKG = os.path.join(ROOT, "services", "process_controller")

# 메서드명 → 모듈 (plan Step 1 분류 + _compute_progress_diff)
BUCKETS = {
    "hearing": {
        "_normalize_text",
        "_extract_hearing_from_result",
        "_parse_datetime_from_row",
        "_extract_hearing_events_from_result",
        "_maybe_sync_hearing_calendar",
    },
    "captcha_ocr": {
        "_init_ocr_wave_state",
        "_set_manual_captcha_fallback",
        "_open_manual_captcha_dialog_add",
        "_run_ocr_fill_case",
        "_case_index_for_number",
        "_lane_waiting_has_valid_captcha",
        "_try_auto_submit_captcha_wave",
        "_validate_captcha_input",
        "_remove_manual_captcha_row",
        "_close_manual_captcha_dialog_safe",
        "_refresh_manual_captcha_dialog_safe",
        "_finish_captcha_batch_ui",
        "_queue_restore_ui_after_captcha_batch",
    },
    "result_handler": {
        "_compute_progress_diff",
        "_compute_new_progress_rows",
        "_verify_sheet_matches_court",
        "save_to_google_sheets",
        "_as_process_result",
        "_finish_case_failed",
        "_log_delayed_registrations",
        "_finish_case_no_change",
        "_finish_case_result_changed",
        "_finish_case_with_save",
        "_finish_period_query_case",
        "_finish_compare_case",
        "_show_special_mode_report",
        "_process_result_list",
    },
    "case_runner": {
        "_lane_for_case",
        "get_case_profile_index",
        "start_processing",
        "stop_processing",
        "execute_actual_processing",
        "_save_run_result_for_email",
        "_check_and_prompt_failed_cases",
        "_process_auto_case",
        "process_cli_auto_case",
        "process_single_case_parallel",
        "_drop_case_from_wave",
        "_report_progress",
        "_process_one_case",
        "process_all_captcha_inputs",
    },
    "cleanup": {
        "cleanup_case_process",
        "_kill_chrome_debug_processes",
    },
    "controller": {
        "__init__",
        "capture_captcha_image",
        "execute_case_processing_with_captcha",
        "execute_case_processing",
        "_persist_general_info",
    },
}

MODULE_DOCS = {
    "hearing": '''# -*- coding: utf-8 -*-
"""
기일 추출 및 Google Calendar 동기화 (HearingMixin)
==================================================
이 파일이 하는 일:
- 크롤링 결과에서 변론/감정/판결선고 기일을 추출합니다.
- 설정이 켜져 있으면 Google Calendar에 기일을 동기화합니다.

이 파일이 하지 않는 일:
- 시트 저장, 캡차 처리 (다른 mixin 담당)

주의:
- 달력 동기화 실패는 로그만 남기고 본 조회 흐름을 막지 않습니다.
''',
    "captcha_ocr": '''# -*- coding: utf-8 -*-
"""
캡차 OCR · 수동 입력 창 · 자동 제출 (CaptchaOcrMixin)
====================================================
이 파일이 하는 일:
- OCR 웨이브 상태 초기화, EasyOCR/Tesseract 인식, 수동 캡차 모아보기 창
- 조건이 맞으면 「캡차 입력 완료」와 동일하게 자동 제출

주의 (주니어용):
- `_ocr_wave_auto_submit_started`: 한 파도에서 자동 제출 스레드를 두 번 띄우지 않기 위한 플래그
- `_captcha_batch_running`: process_all_captcha_inputs 중복 진입 방지
- `processing=False`이면 자동 제출 금지 (중지 후에도 제출되던 버그 방지)
- 수동 캡차 창은 반드시 메인 스레드(ui_queue)에서만 열어야 합니다
''',
    "result_handler": '''# -*- coding: utf-8 -*-
"""
시트 저장 · 비교 · 마무리 (ResultHandlerMixin)
==============================================
이 파일이 하는 일:
- 대법원 결과와 시트를 비교해 신규/결과변경 행을 구분합니다.
- overwrite_progress_area로 시트를 맞추고 finish_* 로 상태·메일을 갱신합니다.

2026-08-12 사고 가드 (반드시 유지):
- `_process_result_list`: court_count==0 이고 sheet_count>0 이면 덮어쓰기 금지
- `_verify_sheet_matches_court`: 0행 일치를 성공으로 찍지 않음
- 배경: 99.Error case/ERROR_20260812_sheet_progress_wipe.md

_finish_* 차이:
- `_finish_case_failed`: 조회/저장 실패, 시트 건드리지 않음
- `_finish_case_no_change`: 진행내용 동일, 최근 조회 일시만 갱신
- `_finish_case_result_changed`: 결과 칸만 변경, 메일 '결과 변경 내역'
- `_finish_case_with_save`: 신규 행 저장 완료 (+N건)
''',
    "case_runner": '''# -*- coding: utf-8 -*-
"""
배치 실행 · 레인 병렬 · CLI (CaseRunnerMixin)
=============================================
흐름:
1. start_processing → 레인별 캡차 로드
2. OCR 자동 제출 또는 수동 입력 (CaptchaOcrMixin)
3. process_all_captcha_inputs / _process_auto_case → _process_result_list
4. stop_processing / cleanup_case_process (CleanupMixin)

호출: gui/app_controller.py, auto_runner.py
''',
    "cleanup": '''# -*- coding: utf-8 -*-
"""
브라우저·Chrome 프로세스 정리 (CleanupMixin)
============================================
한 사건 처리 후 Puppeteer/Chrome 프로세스를 정리합니다.
배치 종료 시 원격 디버깅 Chrome 일괄 종료도 담당합니다.
''',
    "controller": '''# -*- coding: utf-8 -*-
"""
ProcessController 본체 — mixin 조합 + Puppeteer 래퍼
==================================================
외부에서는 `from services.process_controller import ProcessController` 만 사용합니다.
''',
}

COMMON_IMPORTS = textwrap.dedent("""
    import hashlib
    import os
    import re
    import subprocess as sp
    import threading
    import time
    from datetime import datetime

    import psutil

    import config
    from gui.utils import captcha_ui as captcha_ui_module
    from services import captcha_ocr_service
    from services import email_manager as email_manager_module
    from services import google_calendar as google_calendar_module
""").strip()


def parse_methods(source):
    tree = ast.parse(source)
    cls = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "ProcessController":
            cls = node
            break
    if cls is None:
        raise RuntimeError("ProcessController class not found")
    lines = source.splitlines(keepends=True)
    methods = {}
    for i, node in enumerate(cls.body):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # 데코레이터(@staticmethod 등)가 def 위에 있으면 함께 포함
        start = node.lineno - 1
        if node.decorator_list:
            start = node.decorator_list[0].lineno - 1
        if i + 1 < len(cls.body):
            next_node = cls.body[i + 1]
            end = next_node.lineno - 1
        else:
            end = len(lines)
        methods[node.name] = "".join(lines[start:end])
    return methods


def assign_bucket(name):
    for bucket, names in BUCKETS.items():
        if name in names:
            return bucket
    raise KeyError(f"Unassigned method: {name}")


def main():
    with open(SRC, "r", encoding="utf-8") as f:
        source = f.read()

    methods = parse_methods(source)
    assigned = set()
    for bucket, names in BUCKETS.items():
        for n in names:
            if n not in methods:
                raise KeyError(f"Missing method in source: {n}")
            assigned.add(n)
    extra = set(methods) - assigned
    if extra:
        raise RuntimeError(f"Unbucketed methods: {extra}")

    os.makedirs(PKG, exist_ok=True)

    mixin_names = {
        "hearing": "HearingMixin",
        "captcha_ocr": "CaptchaOcrMixin",
        "result_handler": "ResultHandlerMixin",
        "case_runner": "CaseRunnerMixin",
        "cleanup": "CleanupMixin",
        "controller": "ProcessController",
    }

    for bucket, class_name in mixin_names.items():
        if bucket == "controller":
            continue
        parts = [MODULE_DOCS[bucket], "", COMMON_IMPORTS, "", f"class {class_name}:", '    """Mixin — self.app 을 통해 GUI/서비스에 접근."""', ""]
        for name in sorted(methods.keys(), key=lambda n: source.find(f"def {n}")):
            if assign_bucket(name) != bucket:
                continue
            body = methods[name]
            # dedent one level (class method indent)
            parts.append(body)
        path = os.path.join(PKG, f"{bucket}.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(parts))
        print(f"Wrote {path}")

    # controller.py — multiple inheritance
    ctrl_parts = [
        MODULE_DOCS["controller"],
        "",
        COMMON_IMPORTS,
        "",
        "from .captcha_ocr import CaptchaOcrMixin",
        "from .case_runner import CaseRunnerMixin",
        "from .cleanup import CleanupMixin",
        "from .hearing import HearingMixin",
        "from .result_handler import ResultHandlerMixin",
        "",
        "class ProcessController(",
        "    CleanupMixin,",
        "    HearingMixin,",
        "    ResultHandlerMixin,",
        "    CaptchaOcrMixin,",
        "    CaseRunnerMixin,",
        "):",
        '    """사건 조회·캡차·저장 통합 컨트롤러 (mixin 조합)."""',
        "",
    ]
    for name in ["__init__", "capture_captcha_image", "execute_case_processing_with_captcha", "execute_case_processing", "_persist_general_info"]:
        ctrl_parts.append(methods[name])

    with open(os.path.join(PKG, "controller.py"), "w", encoding="utf-8") as f:
        f.write("\n".join(ctrl_parts))
    print("Wrote controller.py")

    init_content = '''# -*- coding: utf-8 -*-
"""ProcessController 패키지 — 외부 import 호환 유지."""
from .controller import ProcessController

__all__ = ["ProcessController"]
'''
    with open(os.path.join(PKG, "__init__.py"), "w", encoding="utf-8") as f:
        f.write(init_content)
    print("Wrote __init__.py")


if __name__ == "__main__":
    main()
