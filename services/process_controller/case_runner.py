# -*- coding: utf-8 -*-
"""
배치 실행 · 레인 병렬 · CLI (CaseRunnerMixin)
=============================================
흐름:
1. start_processing → 레인별 캡차 로드
2. OCR 자동 제출 또는 수동 입력 (CaptchaOcrMixin)
3. process_all_captcha_inputs / _process_auto_case → _process_result_list
4. stop_processing / cleanup_case_process (CleanupMixin)

호출: gui/app_controller.py, auto_runner.py

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

class CaseRunnerMixin:
    """Mixin - self.app 을 통해 GUI/서비스에 접근."""

    def _schedule_easyocr_idle_unload(self):
        """
        배치 종료 후 OCR_IDLE_UNLOAD_SEC 동안 OCR이 없으면 EasyOCR 언로드.
        다음 배치 시작 시 warmup_easyocr_async 가 다시 로드합니다.
        """
        delay = int(getattr(config, "OCR_IDLE_UNLOAD_SEC", 600) or 600)
        if delay <= 0:
            return
        token = time.time()
        self.app._ocr_unload_token = token

        def _later():
            time.sleep(delay)
            if getattr(self.app, "_ocr_unload_token", None) != token:
                return  # 새 배치가 시작됨
            if getattr(self.app, "processing", False):
                return
            try:
                captcha_ocr_service.unload_easyocr_model()
                self.app.log_message("ℹ️ EasyOCR 유휴 언로드 완료 (메모리 절약)")
            except Exception:
                pass

        threading.Thread(target=_later, daemon=True, name="easyocr-idle-unload").start()

    def _lane_for_case(self, case_number, n_lanes):
        """
        워커(레인) 분배용 인덱스 0 ~ n_lanes-1.

        주니어 참고:
        - Chrome 프로필은 get_case_profile_index(PROFILE_COUNT)로 정합니다.
        - PROFILE_COUNT == n_lanes 이면 lane == profile (1:1) 이 되어
          레인 하나가 프로필 하나를 전담 → Chrome 기동 1회/레인.
        """
        if n_lanes < 1:
            return 0
        return self.get_case_profile_index(case_number) % n_lanes


    def get_case_profile_index(self, case_number):
        """
        사건번호 → 고정 Chrome 프로필(instance_N). GUI·CLI 공통.

        cookie_data_for_save/instance_N + 대법원 최근 검색(스마트 스킵)이
        이 번호에 묶이므로, 병렬 수와 관계없이 항상 같아야 합니다.
        """
        max_profiles = int(getattr(config, "PROFILE_COUNT", None) or getattr(config, "MAX_PARALLEL_LIMIT", 20))
        if max_profiles < 1:
            max_profiles = 1
        h = int(hashlib.md5(case_number.encode("utf-8")).hexdigest(), 16)
        return h % max_profiles

    def start_processing(self, cases):
        """
        캡차 이미지 로드 시작.
        선택 사건 검증 → processing 플래그·UI 설정 → 스레드에서 execute_actual_processing 실행.
        """
        if not cases:
            self.app.show_warning("처리할 사건을 선택해주세요.")
            return
        if self.app.processing:
            self.app.show_warning("이미 처리 중입니다.")
            return

        self.app.processed_cases = set()
        self.app.processing = True
        # 새 배치 시작 → EasyOCR 유휴 언로드 취소 + 워밍업
        self.app._ocr_unload_token = time.time()
        try:
            captcha_ocr_service.warmup_easyocr_async()
        except Exception:
            pass
        # 배치 전체(여러 파도)에 걸친 성공/실패 누적 — 파도마다 리셋되지 않음
        self.app._batch_completed = 0
        self.app._batch_failed = 0
        self.app._batch_failed_cases = set()  # 사건번호 집합 (재실행 팝업용)
        # 종국 숨김 확인용 후보 — 배치마다 새로 모음
        try:
            from services import finalized_case as finalized_case_module

            finalized_case_module.clear_pending_finalized(self.app)
        except Exception:
            self.app._pending_finalized_for_hide = []
            self.app._pending_finalized_case_numbers = set()
        self._init_ocr_wave_state(clear_manual_dialog=True)
        self.app.start_btn.configure(text=getattr(config, "BTN_TEXT_START_LOADING", "로딩 중..."))
        self.app._set_control_btn_state(self.app.start_btn, False)
        self.app._set_control_btn_state(self.app.stop_btn, True)
        # 처리 중: 시트관리·기간조회도 끔
        from gui.utils import selection_manager as selection_manager_module

        selection_manager_module.update_selection_dependent_buttons(self.app)

        self.app.processing_thread = threading.Thread(
            target=self.execute_actual_processing, args=(cases,)
        )
        self.app.processing_thread.daemon = True
        self.app.processing_thread.start()


    def stop_processing(self):
        """일괄 처리 중지: 플래그 해제, 레인 이벤트 신호, 워커 정리."""
        self.app.processing = False
        self.app._user_cancelled = True
        for ev in getattr(self.app, "lane_events", {}).values():
            ev.set()
        svc = getattr(self.app, "puppeteer_service", None)
        if svc is not None:
            if hasattr(svc, "shutdown_all_workers"):
                try:
                    svc.shutdown_all_workers()
                except Exception:
                    pass
            elif getattr(svc, "running_processes", None):
                for case_number in list(svc.running_processes.keys()):
                    svc.cleanup_process(case_number)
                    self.app.log_message(f"🔄 프로세스 종료: {case_number}")
        try:
            self._kill_chrome_debug_processes()
        except Exception:
            pass
        self.app.browser_processes.clear()
        self.app.browser_ws_urls.clear()
        self.app.start_btn.configure(
            text=getattr(config, "BTN_TEXT_START_COLLECT", "▶ 사건 기록 수집 실행")
        )
        from gui.utils import selection_manager as selection_manager_module

        selection_manager_module.restore_start_button_ui(self.app)
        self.app._set_control_btn_state(self.app.stop_btn, False)
        if hasattr(self.app, "is_dedup_mode"):
            self.app.is_dedup_mode = False
        if hasattr(self.app, "is_reset_mode"):
            self.app.is_reset_mode = False
        if hasattr(self.app, "is_period_mode"):
            self.app.is_period_mode = False
        if hasattr(self.app, "is_compare_mode"):
            self.app.is_compare_mode = False
        self.app.log_message("처리 중지됨")

    # -------------------------------------------------------------------------
    # 프로세스 정리
    # -------------------------------------------------------------------------


    def execute_actual_processing(self, cases):
        """전용 차로제: 사건을 레인별로 나누고, 레인마다 스레드로 순차 처리."""
        if not cases:
            return

        self.app.lane_events = {}
        self._init_ocr_wave_state(clear_manual_dialog=False)
        self.app.log_message("🔄 병렬 처리 시작 (전용 차로제)")

        # AUTO/이전 실행에서 남은 interactive_runner·Chrome 이 프로필을 잠그면
        # 첫 워커 READY 가 타임아웃 납니다. 배치 시작 전에 한 번 청소합니다.
        try:
            from services.puppeteer import kill_orphan_interactive_runners

            kill_orphan_interactive_runners(log_fn=self.app.log_message)
        except Exception:
            pass

        # 레인 수 = PROFILE_COUNT (프로필과 1:1). 사용자 max_parallel 도 동일하게 맞춤.
        profile_count = int(getattr(config, "PROFILE_COUNT", 4) or 4)
        max_limit = getattr(config, "MAX_PARALLEL_LIMIT", 20)
        profile_count = max(1, min(profile_count, max_limit))
        # 앱 IntVar 가 있으면 프로필 수에 동기화
        if getattr(self.app, "max_parallel", None) is not None:
            try:
                self.app.max_parallel.set(profile_count)
            except Exception:
                pass
        n_lanes = min(profile_count, len(cases), max_limit)
        if n_lanes < 1:
            n_lanes = 1

        per_profile = max(1, (len(cases) + n_lanes - 1) // n_lanes)
        if per_profile > 40:
            self.app.log_message(
                f"⚠️ 프로필당 사건 약 {per_profile}건 — 대법원 기록 한도(50)에 근접합니다. "
                f"설정에서 프로필 수를 올리세요."
            )
        self.app.log_message(
            f"ℹ️ 레인/프로필 {n_lanes}개 (PROFILE_COUNT={profile_count}, 사건 {len(cases)}건)"
        )

        lanes = [[] for _ in range(n_lanes)]
        queued_cases = []
        for case in cases:
            case_number = case.get("사건번호", "")
            case_index = self.app.find_case_index(case_number)
            if case_index == -1 or case_index not in self.app.case_images:
                continue
            lane = self._lane_for_case(case_number, n_lanes)
            lanes[lane].append((case, case_index))
            queued_cases.append(case)
        # OCR auto-submit은 실제로 레인에 올라간 사건만 대기
        self._wave_cases = list(queued_cases)

        def run_lane(lane_index, queue):
            # 레인마다 시작 시점을 어긋내 동시 Chrome launch 폭주를 줄입니다.
            # 4레인이면 최대 약 3초 지연이라 체감은 거의 없습니다.
            time.sleep(0.3 * lane_index)
            for case, case_index in queue:
                if not self.app.processing:
                    return
                self.process_single_case_parallel(case, case_index, lane_index)

        threads = []
        for i in range(n_lanes):
            if not lanes[i]:
                continue
            t = threading.Thread(target=run_lane, args=(i, lanes[i]))
            t.daemon = True
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.app.log_message("모든 캡차 이미지 로드 완료!")
        if not self.app.processing:
            self.app.log_message("ℹ️ 처리 중지됨 - OCR 자동 제출 생략")
            self.app.ui_queue.put(("function", (self.app._set_control_btn_state, self.app.stop_btn, False), {}))
            return
        time.sleep(0.5)
        auto_started = self._try_auto_submit_captcha_wave(cases)

        is_period = getattr(self.app, "is_period_mode", False)
        is_compare = getattr(self.app, "is_compare_mode", False)

        # 수동 캡차가 lane_events 에서 아직 대기 중이면 processing 을 끄지 않음
        # (끄면 「입력된 건 제출」의 자동 제출 경로가 processing=False 로 막힘)
        manual_waiting = False
        try:
            manual = getattr(self.app, "ocr_manual_required", {}) or {}
            lane_events = getattr(self.app, "lane_events", {}) or {}
            for c in getattr(self, "_wave_cases", None) or cases or []:
                cn = c.get("사건번호", "")
                if cn and manual.get(cn, False) and cn in lane_events:
                    manual_waiting = True
                    break
        except Exception:
            manual_waiting = False

        # CLICK 스마트 스킵으로 이미 처리가 끝난 경우(기간/대조) 미리보기
        if (is_period or is_compare) and not auto_started:
            # 선택 사건 대부분이 CLICK으로 이미 _process_auto_case 를 탄 상태
            self._show_special_mode_report()
        elif not is_period and not is_compare and not manual_waiting:
            self.app.ui_queue.put(
                ("function", (self.app.show_info, "선택한 모든 작업 조회 완료!"), {})
            )
        elif manual_waiting:
            self.app.log_message(
                "⏳ 수동 캡차 입력 대기 중 — 입력 후 「입력된 건 제출」을 누르세요"
            )
            self.app.ui_queue.put(
                (
                    "function",
                    (self.app._set_control_btn_state, self.app.complete_btn, True),
                    {},
                )
            )

        if not auto_started and not manual_waiting:
            self.app.processing = False

        def _restore_start_btn():
            from gui.utils import selection_manager as selection_manager_module

            selection_manager_module.restore_start_button_ui(
                self.app,
                getattr(config, "BTN_TEXT_START_COLLECT", "▶ 사건 기록 수집 실행"),
            )

        self.app.ui_queue.put(("function", (_restore_start_btn,), {}))
        self.app.ui_queue.put(("function", (self.app._set_control_btn_state, self.app.stop_btn, False), {}))
        if not is_period and not is_compare:
            self._save_run_result_for_email(cases)
        # 기간/대조에서도 실패 건 재실행 확인 (플래그는 콜백에서 유지/해제)
        self._check_and_prompt_failed_cases(cases)


    def _save_run_result_for_email(self, processed_cases):
        """
        처리된 사건 목록을 case_status 기준으로 성공/실패/변경없음으로 나누어
        email_manager에 **누적** 저장합니다. 메일 하단 "이번 조회 결과"에 사용됩니다.

        주니어 개발자 참고:
        - 예전에는 set_last_run_result로 매번 덮어써서 마지막 배치만 남았습니다.
        - 지금은 record_run_results로 사건번호 단위로 병합합니다.
        """
        results = {}
        for case in processed_cases:
            case_number = case.get("사건번호", "")
            if not case_number:
                continue

            case_info = {
                "사건번호": case_number,
                "피고": case.get("피고", ""),
                "사건명": case.get("사건명", ""),
            }

            case_index = self.app.find_case_index(case_number)
            if case_index == -1:
                # CLI(MockApp)는 find_case_index가 사건번호 문자열을 돌려줄 수 있음
                status_text = ""
                if hasattr(self.app, "get_case_status_text"):
                    try:
                        status_text = self.app.get_case_status_text(case_number) or ""
                    except Exception:
                        status_text = ""
            elif case_index not in getattr(self.app, "case_status", {}):
                # CLI: case_status 메모리를 안 쓰는 경우 status_history/텍스트로 판별
                status_text = ""
                if hasattr(self.app, "get_case_status_text"):
                    try:
                        status_text = self.app.get_case_status_text(case_index) or ""
                    except Exception:
                        status_text = ""
            else:
                status_text = self.app.get_case_status_text(case_index) or ""

            if any(k in status_text for k in ["실패", "오류", "취소", "재입력대기"]):
                case_info["상태"] = email_manager_module.STATUS_FAIL
            elif "변경없음" in status_text:
                case_info["상태"] = email_manager_module.STATUS_NO_UPDATE
            elif "결과변경" in status_text:
                case_info["상태"] = email_manager_module.STATUS_RESULT_CHANGED
            elif "캡차" in status_text and "재시도" in status_text:
                case_info["상태"] = email_manager_module.STATUS_CAPTCHA
            else:
                case_info["상태"] = email_manager_module.STATUS_SUCCESS
            results[case_number] = case_info

        email_manager_module.record_run_results(results)


    def _record_batch_failure(self, case_number):
        """배치 실패 집합에 사건번호를 기록합니다 (재실행 팝업·집계용)."""
        if not case_number:
            return
        failed_set = getattr(self.app, "_batch_failed_cases", None)
        if failed_set is None:
            self.app._batch_failed_cases = set()
            failed_set = self.app._batch_failed_cases
        # 이미 집계된 건은 중복 증가하지 않음
        if case_number in failed_set:
            return
        failed_set.add(case_number)
        self.app._batch_failed = getattr(self.app, "_batch_failed", 0) + 1

    def _check_and_prompt_failed_cases(self, processed_cases):
        """
        처리된 사건 중 실패/오류/재입력대기 상태인 사건들을 찾아 재실행 여부를 묻습니다.

        주니어 참고:
        - 우선 app._batch_failed_cases(사건번호 집합)를 씁니다.
          위젯 텍스트를 백그라운드에서 읽으면 UI 큐 반영 전이라 누락될 수 있습니다.
        - 집합이 비어 있으면 상태 라벨 키워드 스캔으로 폴백합니다.
        - 기간/대조 모드에서도 호출됩니다. '예'면 is_period_mode 등을 유지한 채
          실패 건만 다시 start_batch_processing 합니다.
        - '아니오'이거나 실패가 없으면 특수 모드 플래그를 해제합니다.
        """
        failed_cases = []
        batch_failed = getattr(self.app, "_batch_failed_cases", None) or set()
        fail_keywords = [
            "실패",
            "오류",
            "취소",
            "재입력대기",
            "타임아웃",
            "입력없음",
            "형식오류",
            "수동입력",
        ]

        for case in processed_cases:
            case_number = case.get("사건번호", "")
            case_index = self.app.find_case_index(case_number)
            if case_index == -1:
                continue
            # 1순위: 배치에서 명시적으로 기록한 실패
            if case_number in batch_failed:
                failed_cases.append((case_index, case_number))
                continue
            # 2순위(폴백): 상태 라벨 키워드 (캡차 로드 단계 실패 등)
            if case_index in getattr(self.app, "case_status", {}):
                status_text = self.app.get_case_status_text(case_index) or ""
                if any(keyword in status_text for keyword in fail_keywords):
                    failed_cases.append((case_index, case_number))

        was_period = getattr(self.app, "is_period_mode", False)
        was_compare = getattr(self.app, "is_compare_mode", False)
        saved_period_range = getattr(self.app, "period_range", None)

        def _clear_special_flags():
            if hasattr(self.app, "is_period_mode"):
                self.app.is_period_mode = False
            if hasattr(self.app, "is_compare_mode"):
                self.app.is_compare_mode = False

        if not failed_cases:
            _clear_special_flags()
            return

        def _show_prompt():
            failed_msg = "\n".join([f"- {num}" for _, num in failed_cases])
            mode_hint = ""
            if was_period:
                mode_hint = "\n(기간 조회 모드로 다시 실행됩니다)"
            elif was_compare:
                mode_hint = "\n(시트 대조 모드로 다시 실행됩니다)"
            prompt_msg = (
                f"총 {len(failed_cases)}건의 사건 처리에 실패했습니다.\n\n"
                f"[실패 목록]\n{failed_msg}\n\n"
                f"실패한 사건들만 다시 실행하시겠습니까?{mode_hint}"
            )
            if self.app.ask_yesno("재실행 확인", prompt_msg):
                self.app.log_message(f"🔄 실패한 {len(failed_cases)}건 재실행 시작")
                # 특수 모드 유지 (배치가 같은 경로로 돌도록)
                if was_period:
                    self.app.is_period_mode = True
                    if saved_period_range is not None:
                        self.app.period_range = saved_period_range
                    if not getattr(self.app, "period_results", None):
                        self.app.period_results = {}
                if was_compare:
                    self.app.is_compare_mode = True
                    if not getattr(self.app, "compare_results", None):
                        self.app.compare_results = {}
                self.app.deselect_all_cases()
                for case_idx, _ in failed_cases:
                    if case_idx in self.app.case_checkboxes:
                        self.app.case_checkboxes[case_idx].set(True)
                self.app.header_select_all_var.set(False)
                self.app.start_batch_processing()
            else:
                _clear_special_flags()

        self.app.ui_queue.put(("function", (_show_prompt,), {}))


    def _process_auto_case(self, case, case_index):
        """자동 클릭(스마트 스킵) 케이스 한 건 처리.
        Returns: True | "captcha" | "fail"
        - True: 성공
        - "captcha": WRONG_CAPTCHA(캡차 불일치), 재시도 무의
        - "fail": 그 외 실패(네트워크/저장 등), 재시도 가능
        """
        case_number = case.get("사건번호", "")
        try:
            self.app.log_message(f"⚡ 캡차 스킵: 자동 처리 시작 - {case_number}")
            result_data = self.execute_case_processing(case, "CLICK")

            if isinstance(result_data, dict) and result_data.get("status") == "WRONG_CAPTCHA":
                self.app.log_message("⚠️ 자동 클릭 중 캡차 불일치 - 재시도 필요")
                self.app.update_case_status(case_index, "재입력대기", "red", "⚠️")
                return "captcha"

            if isinstance(result_data, list):
                case_start_time = self.app.case_start_times.get(case_index, time.time())
                return self._process_result_list(
                    case,
                    case_index,
                    case_number,
                    result_data,
                    case_start_time,
                    tuple_return=False,
                )

            elapsed_time = int(time.time() - self.app.case_start_times.get(case_index, time.time()))
            self.app.update_case_status(case_index, "실패", "red", "❌")
            self.app.log_message(f"❌ 자동 처리 실패: {case_number}")
            return "fail"

        except Exception as e:
            elapsed_time = int(time.time() - self.app.case_start_times.get(case_index, time.time()))
            self.app.update_case_status(case_index, f"오류 ({elapsed_time}초)", "red", "⚠️")
            self.app.log_message(f"❌ 자동 처리 오류: {case_number} - {e}")
            return "fail"
        finally:
            self.cleanup_case_process(case_number)
            if hasattr(self.app, "processed_cases"):
                self.app.processed_cases.add(case_index)
            ev = getattr(self.app, "lane_events", {}).pop(case_number, None)
            if ev:
                ev.set()


    def process_cli_auto_case(self, case, case_index, attempt=1, max_attempts=3):
        """CLI 전용: 브라우저 기동 후 바로 'CLICK' 명령을 전송합니다."""
        case_number = case.get("사건번호", "")
        profile_index = self.get_case_profile_index(case_number)
        locks = getattr(self.app, "profile_locks", None)
        lock = None
        if locks and 0 <= profile_index < len(locks):
            lock = locks[profile_index]

        try:
            self.app.case_start_times[case_index] = time.time()
            self.app.log_message(
                f"▶ CLI 처리 시작: {case_number} "
                f"(프로필 instance_{profile_index}, 시도 {attempt}/{max_attempts})"
            )
            self.app.update_case_status(case_index, "처리중(캡차로딩)", "orange", "🔄")

            if lock is not None:
                lock.acquire()
            try:
                # 브라우저 기동 및 캡차 캡처 (스마트 스킵 시 '__CLICK__' 반환)
                captcha_t0 = time.time()
                self.app.log_message(f"▶ 캡차 로드 호출: {case_number}")
                result_data = self.execute_case_processing_with_captcha(
                    case, case_index, profile_index
                )
                captcha_elapsed = int(time.time() - captcha_t0)

                elapsed_time = int(time.time() - self.app.case_start_times[case_index])

                if result_data == "__CLICK__":
                    self.app.log_message(
                        f"◀ 캡차 로드 결과: CLICK (소요 {captcha_elapsed}s) — 스마트 스킵 진행"
                    )
                    self.app.update_case_status(case_index, "입력완료", "green", "⚡")
                    self.app.log_message(f"⚡ 캡차 스킵: {case_number} (자동 클릭 준비 완료)")
                    # 브라우저가 살아있는 동안 같은 프로필 락을 유지합니다.
                    return self._process_auto_case(case, case_index)
                elif result_data:
                    # 일반 캡차 이미지가 반환된 경우 (CLI 모드는 CLICK 전용이므로 실패 처리)
                    path_hint = str(result_data)
                    if len(path_hint) > 80:
                        path_hint = "..." + path_hint[-60:]
                    self.app.log_message(
                        f"◀ 캡차 로드 결과: 이미지 ({path_hint}, 소요 {captcha_elapsed}s) "
                        f"— 일반 캡차 → captcha 분류"
                    )
                    self.app.log_message(f"⚠️ 스마트 스킵 불가 (일반 캡차 발생): {case_number}")
                    # 주니어: cleanup 만 하면 Node 가 캡차 입력 대기에 남아
                    # 다음 CASE 를 무시하고 30초 타임아웃이 납니다 → 레인 워커까지 kill
                    self._reset_cli_lane_worker(profile_index, case_number)
                    return "captcha"
                else:
                    self.app.log_message(
                        f"◀ 캡차 로드 결과: 실패 (소요 {captcha_elapsed}s) "
                        f"— 브라우저 준비/응답 지연·크래시 가능"
                    )
                    self.app.update_case_status(case_index, f"실패 ({elapsed_time}초)", "red", "❌")
                    self.app.log_message(f"❌ 캡차 이미지 로딩 실패: {case_number}")
                    self._record_batch_failure(case_number)
                    self._reset_cli_lane_worker(profile_index, case_number)
                    return "fail"
            finally:
                if lock is not None:
                    try:
                        lock.release()
                    except RuntimeError:
                        pass

        except Exception as e:
            elapsed_time = int(time.time() - self.app.case_start_times.get(case_index, time.time()))
            self.app.log_message(f"❌ CLI 처리 오류: {case_number} - {e}")
            self.app.update_case_status(case_index, f"오류 ({elapsed_time}초)", "red", "⚠️")
            try:
                self._reset_cli_lane_worker(profile_index, case_number)
            except Exception:
                pass
            return "fail"

    def _reset_cli_lane_worker(self, profile_index, case_number):
        """
        CLI 캡차 포기/실패 후 레인 워커를 강제 종료합니다.

        주니어: cleanup_case_process 는 사건↔프로세스 매핑만 지우고
        Node 는 캡차 입력 대기(waitForInput)에 남을 수 있습니다.
        같은 프로필로 다음 CASE 를 보내면 '무시' 후 타임아웃이 납니다.
        """
        self.cleanup_case_process(case_number)
        svc = getattr(self.app, "puppeteer_service", None)
        if svc is None:
            return
        try:
            if hasattr(svc, "_kill_lane_worker"):
                svc._kill_lane_worker(profile_index)
            elif hasattr(svc, "shutdown_all_workers"):
                svc.shutdown_all_workers()
        except Exception as e:
            try:
                self.app.log_message(
                    f"⚠️ CLI 레인 워커 정리 실패 instance_{profile_index}: {e}"
                )
            except Exception:
                pass

    def process_single_case_parallel(self, case, case_index, instance_index=0):
        """
        병렬 처리용 단일 사건: 캡차 캡처 후 대기 또는 자동 처리.

        주니어 참고:
        - Chrome userDataDir(instance_N)는 get_case_profile_index로 고정합니다 (CLI와 동일).
        - instance_index는 워커(레인) 번호일 뿐, 프로필 선택에는 쓰지 않습니다.
        - 같은 instance를 두 워커가 쓰려 하면 profile_locks[N]이 막아 Code 21을 방지합니다.
        - 프로필 락은 브라우저 cleanup 까지 유지합니다(CLICK/캡차대기 포함).
        """
        case_number = case.get("사건번호", "")
        # GUI·CLI 공통: 사건번호 해시 % MAX_PARALLEL_LIMIT
        profile_index = self.get_case_profile_index(case_number)
        locks = getattr(self.app, "profile_locks", None)
        lock = None
        if locks and 0 <= profile_index < len(locks):
            lock = locks[profile_index]

        try:
            self.app.case_start_times[case_index] = time.time()
            self.app.update_case_status(case_index, "처리중(캡차로딩)", "orange", "🔄")

            if lock is not None:
                lock.acquire()
            try:
                result_data = self.execute_case_processing_with_captcha(
                    case, case_index, profile_index
                )

                elapsed_time = int(time.time() - self.app.case_start_times[case_index])

                if result_data:
                    if result_data == "__CLICK__":
                        if case_index in self.app.case_inputs:
                            self.app.case_inputs[case_index].set("CLICK")
                        self.app.update_case_status(case_index, "입력완료", "green", "⚡")
                        self.app.log_message(f"ℹ️ 캡차 생략(최근 검색 기록): {case_number}")
                        self.app.log_message(
                            f"⚡ 캡차 스킵: {case_number} (자동 클릭 준비 완료)"
                        )
                        auto_result = self._process_auto_case(case, case_index)
                        if auto_result is True:
                            return True
                        self.app.log_message(
                            f"⚠️ 스마트 스킵 실패 → 캡차 정규 경로 재시도: {case_number}"
                        )
                        self.app.update_case_status(
                            case_index, "스킵 실패→캡차 재시도", "orange", "🔄"
                        )
                        # 스킵 실패 시 같은 사건을 캡차/OCR 경로로 강제 전환합니다.
                        result_data = self.execute_case_processing_with_captcha(
                            case,
                            case_index,
                            profile_index,
                            smart_skip_enabled=False,
                        )
                        if not result_data:
                            self.app.update_case_status(
                                case_index, f"실패 ({elapsed_time}초)", "red", "❌"
                            )
                            self._record_batch_failure(case_number)
                            self.cleanup_case_process(case_number)
                            self._drop_case_from_wave(case_number)
                            return False

                    # OCR: 숫자 인식 → 입력칸 채움 (실패 시 수동 폴백 표시)
                    if isinstance(result_data, str) and os.path.isfile(result_data):
                        if getattr(config, "OCR_ENABLED", False):
                            # sync_apply: UI 큐에 값이 들어간 뒤 auto-submit이 읽도록 대기
                            ocr_ok = self._run_ocr_fill_case(
                                case, case_index, result_data, sync_apply=True
                            )
                            if not ocr_ok:
                                self._set_manual_captcha_fallback(
                                    case_index, case_number, image_path=result_data
                                )
                            else:
                                self.app.log_message(
                                    f"✅ 캡차 OCR 완료: {case_number} (소요 시간: {elapsed_time}초)"
                                )
                        else:
                            self.app.update_case_status(case_index, "입력대기", "blue", "⏳")

                    self.app.log_message(
                        f"✅ 캡차 이미지 로드 완료: {case_number} (소요 시간: {elapsed_time}초)"
                    )
                    need_manual_complete = (
                        not getattr(config, "OCR_ENABLED", False)
                        or not getattr(config, "OCR_AUTO_SUBMIT", False)
                        or self.app.ocr_manual_required.get(case_number, False)
                    )
                    if need_manual_complete:
                        self.app.ui_queue.put(
                            (
                                "function",
                                (self.app._set_control_btn_state, self.app.complete_btn, True),
                                {},
                            )
                        )
                    # 캡차 완료·cleanup 후 lane_events 가 set 될 때까지 락 유지
                    ev = threading.Event()
                    self.app.lane_events[case_number] = ev
                    # 주니어: join() 뒤에 auto-submit을 두면 ev.wait()와 교착남.
                    # lane 등록 직후(wait 전)에 자동 제출 시도.
                    # 자동 제출은 lane 등록된 건만 대상(미등록 웨이브 전체를 기다리지 않음).
                    # 같은 레인 뒤 사건이 시작되려면, 등록된 건이 먼저 제출·ev.set 되어야 함.
                    wave = getattr(self, "_wave_cases", None) or []
                    if wave:
                        self._try_auto_submit_captcha_wave(wave)
                    ev.wait()
                    return True
                else:
                    self.app.update_case_status(
                        case_index, f"실패 ({elapsed_time}초)", "red", "❌"
                    )
                    self._record_batch_failure(case_number)
                    self.cleanup_case_process(case_number)
                    # 캡차 로드 실패 건은 웨이브에서 빼서 자동 제출이 막히지 않게 함
                    self._drop_case_from_wave(case_number)
                    return False
            finally:
                if lock is not None:
                    try:
                        lock.release()
                    except RuntimeError:
                        pass

        except Exception as e:
            elapsed_time = int(
                time.time() - self.app.case_start_times.get(case_index, time.time())
            )
            self.app.log_message(f"❌ 처리 오류: {case_number} - {e}")
            self.app.update_case_status(case_index, f"오류 ({elapsed_time}초)", "red", "⚠️")
            self._record_batch_failure(case_number)
            try:
                self.cleanup_case_process(case_number)
            except Exception:
                pass
            self._drop_case_from_wave(case_number)
            return False


    def _drop_case_from_wave(self, case_number):
        """캡차 로드 실패 등으로 더 이상 기다릴 수 없는 사건을 웨이브 목록에서 제거."""
        wave = getattr(self, "_wave_cases", None)
        if not wave:
            return
        new_wave = [c for c in wave if c.get("사건번호") != case_number]
        if len(new_wave) == len(wave):
            return
        self._wave_cases = new_wave
        self.app.log_message(f"ℹ️ 웨이브에서 제외: {case_number} (남은 {len(new_wave)}건)")
        if new_wave:
            self._try_auto_submit_captcha_wave(new_wave)

    # -------------------------------------------------------------------------
    # 캡차 입력 완료 플로우 (Wave Processing)
    # -------------------------------------------------------------------------


    def _report_progress(self, selected_cases, original_index, case, total_cases, total_start_time):
        """진행률 메시지 갱신."""
        case_number = case.get("사건번호", "")
        current_progress = len([i for i, _ in selected_cases[: selected_cases.index((original_index, case)) + 1]])
        progress_percent = (current_progress / total_cases) * 100
        elapsed = int(time.time() - total_start_time)
        if current_progress > 0:
            avg_time = elapsed / current_progress
            remaining_time = int(avg_time * (total_cases - current_progress))
            msg = f"🔄 처리 중... ({current_progress}/{total_cases}) - {case_number} | 예상 남은 시간: {remaining_time}초"
        else:
            msg = f"🔄 처리 중... ({current_progress}/{total_cases}) - {case_number}"
        self.app.update_progress(progress_percent, msg)


    def _process_one_case(
        self, original_index, case, total_cases, total_start_time, selected_cases
    ):
        """
        선택된 사건 하나에 대해 캡차 검증·실행·저장·GUI 갱신.
        process_all_captcha_inputs 루프 안에서만 호출.
        반환: (completed_delta, failed_delta)
        """
        case_number = case.get("사건번호", "")
        should_cleanup_and_release = True
        try:
            if original_index not in self.app.case_inputs:
                return (0, 0)

            captcha_input = self.app.get_captcha_input(original_index)
            self.app.log_message(f"📋 [DEBUG] 캡차 입력값: '{captcha_input}'")

            # 수동 필요인데 아직 6자리가 없으면 이번 파도에서 스킵 (실패로 세지 않음)
            manual = getattr(self.app, "ocr_manual_required", {})
            if manual.get(case_number, False):
                valid = bool(
                    captcha_input
                    and len(str(captcha_input).strip()) == 6
                    and str(captcha_input).strip().isdigit()
                )
                if not valid:
                    self.app.log_message(
                        f"⏳ 수동입력 대기 - 이번 파도 스킵: {case_number}"
                    )
                    should_cleanup_and_release = False
                    return (0, 0)

            case_start_time = time.time()
            self.app.case_start_times[original_index] = case_start_time

            self._report_progress(
                selected_cases, original_index, case, total_cases, total_start_time
            )
            if not self._validate_captcha_input(original_index, case_number, captcha_input):
                return (0, 1)

            max_ocr_retry = (
                getattr(config, "OCR_MAX_AUTO_RETRY", 3)
                if getattr(config, "OCR_ENABLED", False)
                else 0
            )
            if not hasattr(self.app, "ocr_retry_counts"):
                self.app.ocr_retry_counts = {}
            retried_once = False

            while True:
                captcha_input = self.app.get_captcha_input(original_index)
                if not self._validate_captcha_input(original_index, case_number, captcha_input):
                    return (0, 1)

                self.app.log_message(
                    f"📋 [DEBUG] GUI에서 가져온 캡차 입력: '{captcha_input}' (타입: {type(captcha_input).__name__}, 길이: {len(captcha_input)})"
                )
                self.app.log_message(f"✅ [DEBUG] 캡차 형식 검증 통과: {captcha_input}")
                self.app.log_message(f"🔄 처리 시작: {case_number} (캡차: {captcha_input})")
                self.app.update_case_status(original_index, "처리중(크롤링)", "orange", "🔄")

                result_data = self.execute_case_processing(case, captcha_input.strip())
                self.app.log_message(
                    f"🔄 [DEBUG] execute_case_processing 호출 후 - result_data 타입: {type(result_data)}"
                )
                elapsed_time = int(time.time() - case_start_time)

                try:
                    if (
                        isinstance(result_data, dict)
                        and result_data.get("status") == "WRONG_CAPTCHA"
                    ):
                        new_path = result_data.get("image_path")
                        retry_n = self.app.ocr_retry_counts.get(case_number, 0) + 1
                        self.app.ocr_retry_counts[case_number] = retry_n

                        # 틀린 캡차 값을 오답 샘플로 기록
                        try:
                            from services import captcha_dataset as captcha_dataset_module

                            meta = getattr(self.app, "_ocr_meta", {}).get(case_number) or {}
                            wrong_label = (captcha_input or "").strip()
                            wrong_img = meta.get("image_path") or ""
                            if wrong_label and len(wrong_label) == 6:
                                captcha_dataset_module.record_sample(
                                    wrong_img,
                                    wrong_label,
                                    source="wrong",
                                    ocr_guess=meta.get("guess"),
                                    ocr_confidence=meta.get("confidence"),
                                    ocr_engine=meta.get("engine"),
                                    is_correct=False,
                                )
                        except Exception:
                            pass

                        if new_path:
                            self.app.ui_queue.put(
                                (
                                    "function",
                                    (self.app.update_captcha_image, original_index, new_path),
                                    {},
                                )
                            )

                        if max_ocr_retry > 0 and retry_n <= max_ocr_retry and new_path:
                            self.app.update_case_status(
                                original_index,
                                f"OCR 재시도 ({retry_n}/{max_ocr_retry})",
                                "orange",
                                "🔄",
                            )
                            self.app.log_message(
                                f"⚠️ 캡차 불일치, OCR 재시도 {retry_n}/{max_ocr_retry}: {case_number}"
                            )
                            if self._run_ocr_fill_case(
                                case, original_index, new_path, sync_apply=True
                            ):
                                continue

                        self.app.log_message("⚠️ 캡차 불일치 - 수동 입력 필요")
                        self._set_manual_captcha_fallback(
                            original_index, case_number, image_path=new_path
                        )
                        should_cleanup_and_release = False
                        return (0, 0)

                    if isinstance(result_data, list):
                        return self._process_result_list(
                            case, original_index, case_number, result_data, case_start_time
                        )

                    if not retried_once:
                        retried_once = True
                        self.app.update_case_status(
                            original_index, "그리드 로딩 재시도", "orange", "🔄"
                        )
                        self.app.log_message(
                            f"⚠️ 그리드/결과 수신 실패로 1회 재시도: {case_number}"
                        )

                        # Node 프로세스가 이미 죽었으면 같은 캡차 재전송은 의미 없음
                        # → 브라우저를 다시 띄우고 새 캡차 + OCR 후 continue
                        svc = getattr(self.app, "puppeteer_service", None)
                        proc = None
                        if svc is not None:
                            proc = getattr(svc, "running_processes", {}).get(case_number)
                        process_alive = bool(proc is not None and proc.poll() is None)

                        if not process_alive:
                            self.app.log_message(
                                f"🔄 프로세스 종료됨 → 브라우저 재기동 후 재시도: {case_number}"
                            )
                            profile_index = self.get_case_profile_index(case_number)
                            new_image = self.execute_case_processing_with_captcha(
                                case,
                                original_index,
                                profile_index,
                                smart_skip_enabled=False,
                            )
                            if not new_image or new_image == "__CLICK__":
                                self.app.log_message(
                                    f"❌ 브라우저 재기동 실패 — 즉시 실패 처리: {case_number}"
                                )
                                self.app.update_case_status(
                                    original_index,
                                    f"실패 ({elapsed_time}초)",
                                    "red",
                                    "❌",
                                )
                                return (0, 1)
                            # 새 캡차로 OCR (실패해도 수동 입력이 채워져 있으면 진행)
                            if isinstance(new_image, str) and os.path.isfile(new_image):
                                self._run_ocr_fill_case(
                                    case, original_index, new_image, sync_apply=True
                                )
                            # lane_events 재등록 (재기동 시 해제됐을 수 있음)
                            if case_number not in getattr(self.app, "lane_events", {}):
                                if not hasattr(self.app, "lane_events"):
                                    self.app.lane_events = {}
                                self.app.lane_events[case_number] = threading.Event()
                            continue

                        # 프로세스가 살아 있으면 짧게 대기 후 같은 세션으로 재전송
                        time.sleep(1)
                        continue

                    self.app.update_case_status(
                        original_index, f"실패 ({elapsed_time}초)", "red", "❌"
                    )
                    self.app.log_message(f"❌ 처리 실패: {case_number}")
                    return (0, 1)
                except Exception as e:
                    self.app.log_message(f"❌ [DEBUG] 사건 처리 중 예외 발생: {e}")
                    import traceback
                    self.app.log_message(f"❌ [DEBUG] 예외 스택: {traceback.format_exc()}")
                    self.app.update_case_status(
                        original_index, f"오류 ({elapsed_time}초)", "red", "⚠️"
                    )
                    return (0, 1)
        finally:
            if should_cleanup_and_release:
                self.cleanup_case_process(case_number)
                if hasattr(self.app, "processed_cases"):
                    self.app.processed_cases.add(original_index)
                ev = getattr(self.app, "lane_events", {}).pop(case_number, None)
                if ev:
                    ev.set()
                # 캡차 PhotoImage 메모리 해제
                self.app.ui_queue.put(
                    (
                        "function",
                        (captcha_ui_module.release_captcha_image_memory, self.app, original_index),
                        {},
                    )
                )
                # 수동 모아보기 창에서 해당 행 제거
                self.app.ui_queue.put(
                    ("function", (self._remove_manual_captcha_row, original_index), {})
                )


    def process_all_captcha_inputs(self):
        """
        모든 캡차 입력을 한번에 처리.
        '캡차 입력 완료' 버튼 클릭 시 start_processing_thread()가 이 메서드를 백그라운드 스레드에서 실행.
        GUI 갱신은 app.ui_queue를 통해 메인 스레드에 위임.
        """
        try:
            self.app._captcha_batch_running = True
            total_start_time = time.time()
            self.app.processing = True
            self.app.puppeteer_service.processing_flag = lambda: self.app.processing
            self.app.log_message("🔄 모든 캡차 입력 처리 시작")

            self.app.ui_queue.put(("function", (self.app._set_control_btn_state, self.app.complete_btn, False), {}))
            if not hasattr(self.app, "processed_cases"):
                self.app.processed_cases = set()

            self.app.ui_queue.put(("function", (self.app._set_control_btn_state, self.app.start_btn, False), {}))
            self.app.ui_queue.put(("function", (self.app._set_control_btn_state, self.app.stop_btn, True), {}))

            selected_cases = self.app.get_selected_cases()
            total_cases = len(selected_cases)
            self.app.update_progress(0, f"⏳ 처리 준비 중... (0/{total_cases})")
            # 파도마다 0으로 리셋하지 않음 — 배치 전체 누적
            if not hasattr(self.app, "_batch_completed"):
                self.app._batch_completed = 0
            if not hasattr(self.app, "_batch_failed"):
                self.app._batch_failed = 0
            wave_completed = 0
            wave_failed = 0

            self.app.log_message(f"🔄 [DEBUG] 처리할 사건 목록: {len(selected_cases)}개")
            for idx, (original_index, case) in enumerate(selected_cases):
                if not self.app.processing:
                    self.app.log_message("⏹️ 사용자가 처리를 중지했습니다")
                    break

                case_number = case.get("사건번호", "")
                if case_number not in getattr(self.app, "lane_events", {}):
                    continue

                c_delta, f_delta = self._process_one_case(
                    original_index, case, total_cases, total_start_time, selected_cases
                )
                wave_completed += c_delta
                wave_failed += f_delta
                self.app._batch_completed = getattr(self.app, "_batch_completed", 0) + c_delta
                self.app._batch_failed = getattr(self.app, "_batch_failed", 0) + f_delta
                if f_delta > 0:
                    # _record_batch_failure는 집합 추가 + 카운터+1 이므로,
                    # 위에서 이미 +f_delta 한 뒤엔 집합만 직접 추가
                    failed_set = getattr(self.app, "_batch_failed_cases", None)
                    if failed_set is None:
                        self.app._batch_failed_cases = set()
                        failed_set = self.app._batch_failed_cases
                    failed_set.add(case_number)
                self.app.log_message(
                    f"🔄 [DEBUG] 루프 끝: {idx+1}/{len(selected_cases)} - 인덱스={original_index}"
                )

            completed = getattr(self.app, "_batch_completed", wave_completed)
            failed = getattr(self.app, "_batch_failed", wave_failed)
            self.app.log_message(
                f"🔄 [DEBUG] 현재 파도 처리 완료 - 이번파도 성공:{wave_completed}/실패:{wave_failed}"
                f" | 배치누적 성공:{completed}/실패:{failed}"
            )

            pending_count = len(selected_cases) - len(
                getattr(self.app, "processed_cases", set())
            )

            if pending_count > 0:
                self.app.log_message(
                    f"⏳ 다음 파도 대기 중... (남은 사건: {pending_count}건)"
                )
                # 다음 파도 OCR 자동 제출을 허용하려면 플래그를 풀어야 합니다.
                # (안 풀면 뒤 레인 사건이 lane 등록·OCR 해도 자동 제출이 한 번만 됨)
                self.app._ocr_wave_auto_submit_started = False
                self.app.ui_queue.put(("function", (self.app._set_control_btn_state, self.app.complete_btn, True), {}))
            else:
                self.app.log_message("🎉 모든 사건 처리 완료!")
                # 수동 모아보기 창 정리
                self.app.ui_queue.put(
                    ("function", (self._close_manual_captcha_dialog_safe,), {})
                )
                # 레인 워커 종료 (Chrome 재사용 세션 정리)
                try:
                    svc = getattr(self.app, "puppeteer_service", None)
                    if svc is not None and hasattr(svc, "shutdown_all_workers"):
                        svc.shutdown_all_workers()
                except Exception as e:
                    self.app.log_message(f"⚠️ 워커 종료 중 오류: {e}")
                self._kill_chrome_debug_processes()
                self.app.browser_processes.clear()
                self.app.browser_ws_urls.clear()
                self.app.log_message("✅ 모든 브라우저 프로세스 종료 완료")
                # 프로필 캐시·스크린샷 정리
                try:
                    from services import profile_maintenance as profile_maintenance_module

                    profile_maintenance_module.prune_after_batch(self.app.log_message)
                except Exception:
                    pass
                # EasyOCR 유휴 언로드 타이머
                try:
                    self._schedule_easyocr_idle_unload()
                except Exception:
                    pass
                total_elapsed = int(time.time() - total_start_time)
                self._finish_captcha_batch_ui(
                    completed, failed, total_cases, total_elapsed, selected_cases
                )

        except Exception as e:
            self.app.log_message(f"❌ 캡차 입력 처리 오류: {e}")
            self.app.update_progress(0, "오류 발생")
            self.app.ui_queue.put(("function", (self.app._set_control_btn_state, self.app.complete_btn, True), {}))
            self._queue_restore_ui_after_captcha_batch()
            self.app.processing = False
        finally:
            self.app._captcha_batch_running = False
            # 배치 종료 직후: 이미 lane 등록된 OCR 완료 건이 있으면 다음 파도 자동 제출
            if getattr(self.app, "processing", False):
                wave = getattr(self, "_wave_cases", None) or []
                if wave and getattr(self.app, "lane_events", None):
                    self._try_auto_submit_captcha_wave(wave)
