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

    def _lane_for_case(self, case_number, n_lanes):
        """전용 차로: 사건번호 해시로 0 ~ n_lanes-1 인덱스 반환."""
        h = int(hashlib.md5(case_number.encode("utf-8")).hexdigest(), 16)
        return h % n_lanes


    def get_case_profile_index(self, case_number):
        """사건번호에 따른 고정 프로필(인스턴스) 번호. 쿠키/스마트스킵 유지용."""
        max_profiles = getattr(config, "MAX_PARALLEL_LIMIT", 20)
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
        """일괄 처리 중지: 플래그 해제, 레인 이벤트 신호, Puppeteer 프로세스 정리."""
        self.app.processing = False
        self.app._user_cancelled = True
        for ev in getattr(self.app, "lane_events", {}).values():
            ev.set()
        if hasattr(self.app, "puppeteer_service") and getattr(self.app.puppeteer_service, "running_processes", None):
            for case_number in list(self.app.puppeteer_service.running_processes.keys()):
                self.app.puppeteer_service.cleanup_process(case_number)
                self.app.log_message(f"🔄 프로세스 종료: {case_number}")
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

        max_limit = getattr(config, "MAX_PARALLEL_LIMIT", 20)
        n_lanes = min(self.app.max_parallel.get(), len(cases), max_limit)
        if n_lanes < 1:
            n_lanes = 1

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
            time.sleep(1.0 * lane_index)
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

        # CLICK 스마트 스킵으로 이미 처리가 끝난 경우(기간/대조) 미리보기
        if (is_period or is_compare) and not auto_started:
            # 선택 사건 대부분이 CLICK으로 이미 _process_auto_case 를 탄 상태
            self._show_special_mode_report()
        elif not is_period and not is_compare:
            self.app.ui_queue.put(
                ("function", (self.app.show_info, "선택한 모든 작업 조회 완료!"), {})
            )

        if not auto_started:
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


    def _check_and_prompt_failed_cases(self, processed_cases):
        """
        처리된 사건 중 실패/오류/재입력대기 상태인 사건들을 찾아 재실행 여부를 묻습니다.

        주니어 참고:
        - 기간/대조 모드에서도 호출됩니다. '예'면 is_period_mode 등을 유지한 채
          실패 건만 다시 start_batch_processing 합니다.
        - '아니오'이거나 실패가 없으면 특수 모드 플래그를 해제합니다.
        """
        failed_cases = []
        for case in processed_cases:
            case_number = case.get("사건번호", "")
            case_index = self.app.find_case_index(case_number)
            if case_index != -1 and case_index in getattr(self.app, "case_status", {}):
                status_text = self.app.get_case_status_text(case_index) or ""
                if any(
                    keyword in status_text
                    for keyword in ["실패", "오류", "취소", "재입력대기", "타임아웃"]
                ):
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


    def process_cli_auto_case(self, case, case_index):
        """CLI 전용: 브라우저 기동 후 바로 'CLICK' 명령을 전송합니다."""
        case_number = case.get("사건번호", "")
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
                # 브라우저 기동 및 캡차 캡처 (스마트 스킵 시 '__CLICK__' 반환)
                result_data = self.execute_case_processing_with_captcha(
                    case, case_index, profile_index
                )

                elapsed_time = int(time.time() - self.app.case_start_times[case_index])

                if result_data == "__CLICK__":
                    self.app.update_case_status(case_index, "입력완료", "green", "⚡")
                    self.app.log_message(f"⚡ 캡차 스킵: {case_number} (자동 클릭 준비 완료)")
                    # 브라우저가 살아있는 동안 같은 프로필 락을 유지합니다.
                    return self._process_auto_case(case, case_index)
                elif result_data:
                    # 일반 캡차 이미지가 반환된 경우 (CLI 모드는 CLICK 전용이므로 실패 처리)
                    self.app.log_message(f"⚠️ 스마트 스킵 불가 (일반 캡차 발생): {case_number}")
                    self.cleanup_case_process(case_number)
                    return "captcha"
                else:
                    self.app.update_case_status(case_index, f"실패 ({elapsed_time}초)", "red", "❌")
                    self.app.log_message(f"❌ 캡차 이미지 로딩 실패: {case_number}")
                    self.cleanup_case_process(case_number)
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
            return "fail"


    def process_single_case_parallel(self, case, case_index, instance_index=0):
        """
        병렬 처리용 단일 사건: 캡차 캡처 후 대기 또는 자동 처리.

        주니어 참고:
        - instance_index(레인)를 userDataDir(instance_N)와 동일하게 씁니다.
          예전처럼 사건번호 해시 % 20 이면 다른 레인이 같은 폴더를 열어 Code 21이 납니다.
        - 프로필 락은 브라우저 cleanup 까지 유지합니다(CLICK/캡차대기 포함).
        """
        case_number = case.get("사건번호", "")
        max_limit = getattr(config, "MAX_PARALLEL_LIMIT", 20)
        # 레인 인덱스 = Chromium userDataDir 인덱스
        profile_index = int(instance_index) % max(1, max_limit)
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
                    # lane 등록 직후(wait 전)에 전원 입력됐는지 확인하고 자동 제출.
                    wave = getattr(self, "_wave_cases", None) or []
                    if wave:
                        self._try_auto_submit_captcha_wave(wave)
                    ev.wait()
                    return True
                else:
                    self.app.update_case_status(
                        case_index, f"실패 ({elapsed_time}초)", "red", "❌"
                    )
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
                        time.sleep(3)
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
            completed = 0
            failed = 0

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
                completed += c_delta
                failed += f_delta
                self.app.log_message(
                    f"🔄 [DEBUG] 루프 끝: {idx+1}/{len(selected_cases)} - 인덱스={original_index}"
                )

            self.app.log_message(
                f"🔄 [DEBUG] 현재 파도 처리 완료 - 성공: {completed}, 실패: {failed}"
            )

            pending_count = len(selected_cases) - len(
                getattr(self.app, "processed_cases", set())
            )

            if pending_count > 0:
                self.app.log_message(
                    f"⏳ 다음 파도 대기 중... (남은 사건: {pending_count}건)"
                )
                # 자동 제출 스레드 중복 기동을 막기 위해 배치 중에는 플래그를 유지합니다.
                self.app.ui_queue.put(("function", (self.app._set_control_btn_state, self.app.complete_btn, True), {}))
            else:
                self.app.log_message("🎉 모든 사건 처리 완료!")
                # 수동 모아보기 창 정리
                self.app.ui_queue.put(
                    ("function", (self._close_manual_captcha_dialog_safe,), {})
                )
                self._kill_chrome_debug_processes()
                self.app.browser_processes.clear()
                self.app.browser_ws_urls.clear()
                self.app.log_message("✅ 모든 브라우저 프로세스 종료 완료")
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
