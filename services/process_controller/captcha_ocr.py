# -*- coding: utf-8 -*-
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

"""

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

class CaptchaOcrMixin:
    """Mixin - self.app 을 통해 GUI/서비스에 접근."""

    def _init_ocr_wave_state(self, clear_manual_dialog=True):
        """사건 조회 로드(웨이브) 시작 시 OCR 관련 상태 초기화."""
        self.app.ocr_manual_required = {}
        self.app.ocr_retry_counts = {}
        self.app._ocr_wave_auto_submit_started = False
        self.app._user_cancelled = False
        self.app._lane_wait_log_ts = {}
        self.app.case_captcha_image_paths = getattr(
            self.app, "case_captcha_image_paths", {}
        )
        if clear_manual_dialog:
            # 새 배치를 시작할 때는 이전 수동 창을 닫고 새로 모읍니다.
            self.app.ui_queue.put(
                ("function", (self._close_manual_captcha_dialog_safe,), {})
            )
        else:
            # 실패 재실행처럼 같은 배치 맥락이면 창을 유지하고 포커스만 갱신합니다.
            self.app.ui_queue.put(
                ("function", (self._refresh_manual_captcha_dialog_safe,), {})
            )


    def _set_manual_captcha_fallback(self, case_index, case_number, image_path=None):
        """
        OCR 실패·재시도 한도 초과 시: 입력칸 잠금 해제, 수동 입력 유도.

        주니어 개발자 참고:
        - ocr_manual_required[사건번호]=True 이면 이번 파도에서 OCR 자동 제출 대상에서 제외됩니다.
          (OCR 완료 건은 그대로 자동 진행되고, 수동 건만 모아보기 창으로 안내합니다.)
        """
        self.app.ocr_manual_required[case_number] = True
        captcha_ui_module.clear_captcha_input_for_manual(self.app, case_index)
        self.app.update_case_status(case_index, "수동입력 필요", "red", "⚠️")
        # 이미지 경로 보관 (모아보기 창에서 표시)
        if image_path and image_path != "__CLICK__":
            paths = getattr(self.app, "case_captcha_image_paths", None)
            if paths is None:
                self.app.case_captcha_image_paths = {}
                paths = self.app.case_captcha_image_paths
            paths[case_index] = image_path
        # 완료 버튼은 보조 탈출구로만 켬 + 수동 모아보기 창에 행 추가
        self.app.ui_queue.put(
            ("function", (self.app._set_control_btn_state, self.app.complete_btn, True), {})
        )
        self.app.ui_queue.put(
            (
                "function",
                (self._open_manual_captcha_dialog_add, case_index, case_number, image_path),
                {},
            )
        )
        self.app.log_message(f"⚠️ OCR 실패 → 수동 입력: {case_number}")


    def _open_manual_captcha_dialog_add(self, case_index, case_number, image_path=None):
        """메인 스레드: 수동 캡차 모아보기 창을 열고 행을 추가합니다."""
        try:
            from gui.dialogs.manual_captcha_dialog import ensure_manual_captcha_dialog

            path = image_path
            if not path:
                path = getattr(self.app, "case_captcha_image_paths", {}).get(case_index)
            dlg = ensure_manual_captcha_dialog(self.app)
            dlg.add_case(case_index, case_number, path)
            self.app.log_message(f"ℹ️ 수동 캡차 창 열림: {case_number}")
        except Exception as e:
            self.app.log_message(f"⚠️ 수동 캡차 창 열기 실패: {e}")


    def _run_ocr_fill_case(self, case, case_index, image_path, *, sync_apply=False):
        """
        캡cha 이미지 경로에서 OCR 후 입력칸 채움.

        sync_apply=True: ui_queue 적용 후 Event로 대기 (WRONG_CAPTCHA 즉시 재제출용).
        반환: OCR 성공 여부(bool).
        """
        case_number = case.get("사건번호", "")
        if not getattr(config, "OCR_ENABLED", False):
            return False
        if not image_path or image_path == "__CLICK__":
            return False

        self.app.update_case_status(case_index, "OCR 인식 중", "orange", "🔍")
        self.app.log_message(f"🔍 OCR 인식 중: {case_number}")

        if getattr(config, "OCR_AUTO_SUBMIT", False):
            captcha_ui_module.set_captcha_entry_locked(self.app, case_index, True)

        if not captcha_ocr_service.ocr_import_available() and captcha_ocr_service.ocr_import_error_message():
            self.app.log_message(
                f"⚠️ OCR 모듈 사용 불가(수동 입력): {captcha_ocr_service.ocr_import_error_message()}"
            )
            return False

        result = captcha_ocr_service.recognize_from_path(image_path)
        if not result:
            return False
        text = (result.text or "").strip()
        if not (len(text) == 6 and text.isdigit()):
            self.app.log_message(
                f"⚠️ OCR 결과 형식 불일치(수동 전환): '{text}' / 사건 {case_number}"
            )
            return False

        self.app.log_message(
            f"✅ OCR 자동입력중: {text} ({result.engine}, {result.confidence:.2f}) - 입력칸 잠금"
        )
        self.app.ocr_manual_required[case_number] = False

        # 경로 보관 (WRONG_CAPTCHA 후 수동 폴백 시 창에 표시)
        paths = getattr(self.app, "case_captcha_image_paths", None)
        if paths is None:
            self.app.case_captcha_image_paths = {}
            paths = self.app.case_captcha_image_paths
        paths[case_index] = image_path

        lock_after = getattr(config, "OCR_AUTO_SUBMIT", False)
        if sync_apply:
            applied = threading.Event()

            def _apply():
                captcha_ui_module._apply_set_captcha_input(
                    self.app, case_index, result.text, lock_after=lock_after
                )
                applied.set()

            self.app.ui_queue.put(("function", (_apply,), {}))
            applied.wait(timeout=10.0)
        else:
            captcha_ui_module.set_captcha_input(
                self.app, case_index, result.text, lock_after=lock_after
            )

        self.app.update_case_status(case_index, "OCR 자동입력중", "blue", "🔍")
        # WRONG_CAPTCHA 재인식 등으로 lane 이 이미 있으면 즉시 자동 제출 재검사
        wave = getattr(self, "_wave_cases", None) or []
        if wave and case_number in getattr(self.app, "lane_events", {}):
            self._try_auto_submit_captcha_wave(wave)
        return True


    def _case_index_for_number(self, case_number):
        """사건번호 → 목록 인덱스."""
        idx = self.app.find_case_index(case_number)
        return idx if idx != -1 else None


    def _lane_waiting_has_valid_captcha(self, case_number):
        """lane_events 대기 중인 사건의 입력이 6자리 숫자인지."""
        idx = self._case_index_for_number(case_number)
        if idx is None:
            return False
        val = self.app.get_captcha_input(idx)
        return bool(val and len(val) == 6 and val.isdigit())


    def _try_auto_submit_captcha_wave(self, cases):
        """
        비수동(OCR) 사건이 모두 6자리면 「캡차 입력 완료」와 동일하게 자동 제출.

        수동 필요 건이 섞여 있어도 OCR 완료 건은 진행합니다.
        반환: True면 start_processing_thread를 호출함.
        """
        if not getattr(config, "OCR_ENABLED", False):
            return False
        if not getattr(config, "OCR_AUTO_SUBMIT", False):
            return False
        if not getattr(self.app, "processing", False):
            return False
        if getattr(self.app, "_captcha_batch_running", False):
            return False

        with self._auto_submit_lock:
            if getattr(self.app, "_ocr_wave_auto_submit_started", False):
                return False

            lane_events = getattr(self.app, "lane_events", {})
            manual = getattr(self.app, "ocr_manual_required", {})

            ready_count = 0
            manual_pending = 0

            for case in cases:
                case_number = case.get("사건번호", "")
                idx = self._case_index_for_number(case_number)
                if idx is None:
                    continue
                captcha_val = self.app.get_captcha_input(idx)
                if captcha_val == "CLICK":
                    continue
                if case_number not in lane_events:
                    # 아직 캡차 로드/OCR 중인 비완료 사건 → 대기
                    ts_now = time.time()
                    ts_map = getattr(self.app, "_lane_wait_log_ts", {})
                    ts_last = ts_map.get(case_number, 0)
                    if ts_now - ts_last >= 10.0:
                        self.app.log_message(
                            f"ℹ️ OCR 자동 제출 대기: {case_number} 아직 lane 미등록"
                        )
                        ts_map[case_number] = ts_now
                        self.app._lane_wait_log_ts = ts_map
                    return False
                if manual.get(case_number, False):
                    # 수동 필요: 자동 제출을 막지 않고 개수만 센다
                    if self._lane_waiting_has_valid_captcha(case_number):
                        ready_count += 1
                    else:
                        manual_pending += 1
                    continue
                if not self._lane_waiting_has_valid_captcha(case_number):
                    # OCR 결과가 아직 안 들어온 비수동 건 → 대기
                    return False
                ready_count += 1

            if ready_count == 0:
                # 채울 OCR 건이 없고 수동만 남음 → 버튼/창으로 유도, 제출은 보류
                if manual_pending > 0:
                    self.app.ui_queue.put(
                        (
                            "function",
                            (self.app._set_control_btn_state, self.app.complete_btn, True),
                            {},
                        )
                    )
                return False

            self.app._ocr_wave_auto_submit_started = True
            self.app.log_message(
                f"⚡ OCR 자동 제출 시작 (OCR완료 {ready_count}건, 수동대기 {manual_pending}건)"
            )
            self.app.start_processing_thread()
            if manual_pending > 0:
                # 다음 파도용 탈출구(완료 버튼) 유지
                self.app.ui_queue.put(
                    (
                        "function",
                        (self.app._set_control_btn_state, self.app.complete_btn, True),
                        {},
                    )
                )
            return True

    # -------------------------------------------------------------------------
    # 순수 로직 (GUI 의존 없음) - 구현해 둠
    # -------------------------------------------------------------------------


    def _validate_captcha_input(self, original_index, case_number, captcha_input):
        """캡차 입력 검증. 유효하면 True, 아니면 False(상태 업데이트 후)."""
        if not (captcha_input and captcha_input.strip()):
            self.app.log_message(f"⚠️ 캡차 입력이 비어있음: {case_number}")
            self.app.update_case_status(original_index, "입력없음", "red", "⚠️")
            return False
        is_click = captcha_input == "CLICK"
        is_valid_captcha = len(captcha_input) == 6 and captcha_input.isdigit()
        if not (is_click or is_valid_captcha):
            self.app.log_message(
                f"⚠️ 캡차 입력 형식 오류: {case_number} (입력: {captcha_input}, 길이: {len(captcha_input)})"
            )
            self.app.update_case_status(original_index, "형식오류", "red", "⚠️")
            return False
        return True


    def _remove_manual_captcha_row(self, case_index):
        """메인 스레드: 수동 캡차 창에서 행 제거."""
        dlg = getattr(self.app, "_manual_captcha_dialog", None)
        if dlg is None:
            return
        try:
            if dlg.winfo_exists():
                dlg.remove_case(case_index)
        except Exception:
            pass


    def _close_manual_captcha_dialog_safe(self):
        """메인 스레드: 수동 캡차 창 닫기."""
        dlg = getattr(self.app, "_manual_captcha_dialog", None)
        if dlg is None:
            return
        try:
            if dlg.winfo_exists():
                dlg._on_close()
        except Exception:
            self.app._manual_captcha_dialog = None


    def _refresh_manual_captcha_dialog_safe(self):
        """메인 스레드: 이미 열린 수동 캡차 창을 전면으로 다시 보여줍니다."""
        dlg = getattr(self.app, "_manual_captcha_dialog", None)
        if dlg is None:
            return
        try:
            if dlg.winfo_exists():
                dlg.refresh()
        except Exception:
            pass


    def _finish_captcha_batch_ui(
        self, completed, failed, total_cases, total_elapsed, selected_cases
    ):
        """캡차 배치 완료 후 진행률·완료 메시지·버튼 복구를 UI 큐에 넣음."""
        self.app.update_progress(
            100,
            f"처리 완료! (성공: {completed}, 실패: {failed}) | 총 소요 시간: {total_elapsed}초",
        )
        self.app.log_message(
            f"모든 캡차 입력 처리 완료! (총 소요 시간: {total_elapsed}초)"
        )

        is_period = getattr(self.app, "is_period_mode", False)
        is_compare = getattr(self.app, "is_compare_mode", False)

        # 기간/대조 모드는 일반 메일 누적에 넣지 않음
        if not is_period and not is_compare:
            self._save_run_result_for_email([c for _, c in selected_cases])
        else:
            self._show_special_mode_report()

        completion_msg = (
            f"처리가 완료되었습니다!\n\n"
            f"성공: {completed}개\n"
            f"실패: {failed}개\n"
            f"총 사건: {total_cases}개\n"
            f"총 소요 시간: {total_elapsed}초"
        )
        if not is_period and not is_compare:
            self.app.ui_queue.put(("function", (self.app.show_info, completion_msg), {}))
        self.app.processing = False
        if hasattr(self.app, "is_dedup_mode"):
            self.app.is_dedup_mode = False
        if hasattr(self.app, "is_reset_mode"):
            self.app.is_reset_mode = False
        # 기간/대조 플래그는 실패 재실행 확인 콜백에서 해제/유지
        self._check_and_prompt_failed_cases([c for _, c in selected_cases])
        self.app.ui_queue.put(("function", (self.app._set_control_btn_state, self.app.complete_btn, False), {}))

        def _restore_start():
            from gui.utils import selection_manager as selection_manager_module

            selection_manager_module.restore_start_button_ui(
                self.app,
                getattr(
                    config,
                    "BTN_TEXT_START_COLLECT_TWO_LINE",
                    "▶ 사건 기록 수집 실행\n(캡차 로드 실행)",
                ),
            )

        self.app.ui_queue.put(("function", (_restore_start,), {}))
        self.app.ui_queue.put(("function", (self.app._set_control_btn_state, self.app.stop_btn, False), {}))


    def _queue_restore_ui_after_captcha_batch(self):
        """캡차 배치 오류/중지 후 시작·중지 버튼 복구를 UI 큐에 넣음."""
        def _restore_start():
            from gui.utils import selection_manager as selection_manager_module

            selection_manager_module.restore_start_button_ui(
                self.app,
                getattr(
                    config,
                    "BTN_TEXT_START_COLLECT_TWO_LINE",
                    "▶ 사건 기록 수집 실행\n(캡차 로드 실행)",
                ),
            )

        self.app.ui_queue.put(("function", (_restore_start,), {}))
        self.app.ui_queue.put(("function", (self.app._set_control_btn_state, self.app.stop_btn, False), {}))

