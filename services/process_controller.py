# -*- coding: utf-8 -*-
"""
사건 처리 컨트롤러 (Process Controller)
======================================

batch_gui_maker.py에 있던 병렬 처리·스레딩·캡차 재시도 로직을 전담합니다.
GUI는 app 참조를 통해 콜백 형태로 UI 갱신만 수행합니다.
"""

import hashlib
import subprocess as sp
import threading
import time
from tkinter import messagebox

import psutil

import config
from utils import email_manager as email_manager_module


class ProcessController:
    """
    사건 조회 로드·캡차 처리·병렬 실행을 담당하는 작업 관리자.
    BatchProcessingGUI 인스턴스(app)를 받아, 로그/상태/진행률 등은 app 메서드로 전달합니다.
    """

    def __init__(self, app):
        """
        Args:
            app: BatchProcessingGUI 인스턴스. log_message, update_case_status, ui_queue 등에 접근.
        """
        self.app = app

    # -------------------------------------------------------------------------
    # 순수 로직 (GUI 의존 없음) — 구현해 둠
    # -------------------------------------------------------------------------

    def _lane_for_case(self, case_number, n_lanes):
        """전용 차로: 사건번호 해시로 0 ~ n_lanes-1 인덱스 반환."""
        h = int(hashlib.md5(case_number.encode("utf-8")).hexdigest(), 16)
        return h % n_lanes

    def get_case_profile_index(self, case_number):
        """사건번호에 따른 고정 프로필(인스턴스) 번호. 쿠키/스마트스킵 유지용."""
        max_profiles = getattr(config, "MAX_PARALLEL_LIMIT", 20)
        h = int(hashlib.md5(case_number.encode("utf-8")).hexdigest(), 16)
        return h % max_profiles

    # -------------------------------------------------------------------------
    # 데이터/시트·Puppeteer 래퍼 (GUI 없이 app 서비스만 사용)
    # -------------------------------------------------------------------------

    @staticmethod
    def _normalize_text(text):
        """비교용: 공백 제거하여 중복 오판 방지."""
        if text is None:
            return ""
        return "".join(str(text).split())

    def filter_new_data(self, scraped_data, last_entry):
        """last_entry 이후 신규 데이터만 반환. 없으면 전체 반환."""
        if not last_entry or not isinstance(scraped_data, list) or len(scraped_data) == 0:
            return scraped_data if isinstance(scraped_data, list) else []
        le_date = self._normalize_text(last_entry.get("date", ""))
        le_content = self._normalize_text(last_entry.get("content", ""))
        for i, row in enumerate(scraped_data):
            if not isinstance(row, dict):
                continue
            if (
                self._normalize_text(row.get("date", "")) == le_date
                and self._normalize_text(row.get("content", "")) == le_content
            ):
                return scraped_data[i + 1:]
        return scraped_data

    def save_to_google_sheets(self, case, result_data):
        """구글 시트에 진행내용 저장. 반환: 저장된 행 개수 또는 False."""
        return self.app.google_sheets_service.save_progress_data(case, result_data)

    def capture_captcha_image(self, case_number, defendant, court, instance_index=0):
        """캡차 이미지 캡처. PuppeteerService 사용, ws_url/process는 app에 저장."""
        try:
            image_path, ws_url, process = self.app.puppeteer_service.capture_captcha_image(
                case_number, defendant, court, instance_index
            )
            if ws_url:
                self.app.browser_ws_urls[case_number] = ws_url
            if process:
                self.app.browser_processes[case_number] = process
            return image_path
        except Exception as e:
            self.app.log_message(f"❌ 캡차 이미지 캡처 오류: {e}")
            return None

    def execute_case_processing_with_captcha(self, case, case_index, instance_index=0):
        """캡차 이미지 캡처 후 GUI 표시 및 완료 버튼 활성화."""
        try:
            case_number = case.get("사건번호", "")
            defendant = case.get("피고", "")
            court = case.get("법원", "")
            self.app.log_message(f"🔄 처리 시작: {case_number} (법원: {court})")
            self.app.log_message(f"📸 캡차 이미지 캡처 중: {case_number}")
            image_path = self.capture_captcha_image(
                case_number, defendant, court, instance_index
            )
            if image_path:
                self.app.update_captcha_image(case_index, image_path)
                self.app.update_case_status(case_index, "캡차입력", "blue")
                self.app.log_message(f"🔐 캡차 입력 대기: {case_number}")
                self.app.root.after(0, lambda: self.app._set_control_btn_state(self.app.complete_btn, True))
                self.app.log_message("✅ 캡차 입력 완료 버튼 활성화됨")
                return image_path
            self.app.log_message(f"❌ 캡차 이미지 캡처 실패: {case_number}")
            return False
        except Exception as e:
            case_number = case.get("사건번호", "")
            self.app.log_message(f"❌ 처리 오류: {case_number} - {e}")
            return False

    def execute_case_processing(self, case, captcha_input):
        """Puppeteer로 사건 처리 실행. 반환: 진행내용 리스트 또는 False 또는 WRONG_CAPTCHA 딕셔너리."""
        try:
            case_number = case.get("사건번호", "")
            browser_ws_url = self.app.browser_ws_urls.get(case_number)
            result = self.app.puppeteer_service.execute_case_processing(
                case, captcha_input, browser_ws_url
            )
            return result
        except Exception as e:
            case_number = case.get("사건번호", "")
            self.app.log_message(f"❌ Puppeteer 실행 오류: {case_number} - {e}")
            return False

    # -------------------------------------------------------------------------
    # 배치 시작/중지
    # -------------------------------------------------------------------------

    def start_processing(self, cases):
        """
        캡차 이미지 로드 시작.
        선택 사건 검증 → processing 플래그·UI 설정 → 스레드에서 execute_actual_processing 실행.
        """
        if not cases:
            messagebox.showwarning("경고", "처리할 사건을 선택해주세요.")
            return
        if self.app.processing:
            messagebox.showwarning("경고", "이미 처리 중입니다.")
            return

        self.app.processed_cases = set()
        self.app.processing = True
        self.app.start_btn.configure(text="🔄 로딩 중...")
        self.app._set_control_btn_state(self.app.start_btn, False)
        self.app._set_control_btn_state(self.app.stop_btn, True)

        self.app.processing_thread = threading.Thread(
            target=self.execute_actual_processing, args=(cases,)
        )
        self.app.processing_thread.daemon = True
        self.app.processing_thread.start()

    def stop_processing(self):
        """일괄 처리 중지: 플래그 해제, 레인 이벤트 신호, Puppeteer 프로세스 정리."""
        self.app.processing = False
        for ev in getattr(self.app, "lane_events", {}).values():
            ev.set()
        if hasattr(self.app, "puppeteer_service") and getattr(self.app.puppeteer_service, "running_processes", None):
            for case_number in list(self.app.puppeteer_service.running_processes.keys()):
                self.app.puppeteer_service.cleanup_process(case_number)
                self.app.log_message(f"🔄 프로세스 종료: {case_number}")
        self.app.start_btn.configure(text="🖼️ 사건 조회 로드")
        self.app._set_control_btn_state(self.app.start_btn, True)
        self.app._set_control_btn_state(self.app.stop_btn, False)
        self.app.log_message("⏹️ 처리 중지됨")

    # -------------------------------------------------------------------------
    # 프로세스 정리
    # -------------------------------------------------------------------------

    def cleanup_case_process(self, case_number):
        """한 사건의 브라우저/Node 프로세스 정리."""
        try:
            if case_number in self.app.browser_processes:
                process = self.app.browser_processes[case_number]
                try:
                    if process.poll() is None:
                        self.app.log_message(f"🔄 프로세스 종료 중: {case_number}")
                        process.kill()
                        try:
                            process.wait(timeout=2)
                        except Exception:
                            pass
                        self.app.log_message(f"✅ 프로세스 종료 완료: {case_number}")
                except Exception as e:
                    self.app.log_message(f"⚠️ 프로세스 종료 실패: {case_number} - {e}")
                del self.app.browser_processes[case_number]
            if case_number in self.app.browser_ws_urls:
                del self.app.browser_ws_urls[case_number]
        except Exception as e:
            self.app.log_message(f"⚠️ 프로세스 정리 오류: {case_number} - {e}")

    # -------------------------------------------------------------------------
    # 실제 실행 루프
    # -------------------------------------------------------------------------

    def execute_actual_processing(self, cases):
        """전용 차로제: 사건을 레인별로 나누고, 레인마다 스레드로 순차 처리."""
        if not cases:
            return

        self.app.lane_events = {}
        self.app.log_message("🔄 병렬 처리 시작 (전용 차로제)")

        max_limit = getattr(config, "MAX_PARALLEL_LIMIT", 20)
        n_lanes = min(self.app.max_parallel.get(), len(cases), max_limit)
        if n_lanes < 1:
            n_lanes = 1

        lanes = [[] for _ in range(n_lanes)]
        for case in cases:
            case_number = case.get("사건번호", "")
            case_index = self.app.find_case_index(case_number)
            if case_index == -1 or case_index not in self.app.case_images:
                continue
            lane = self._lane_for_case(case_number, n_lanes)
            lanes[lane].append((case, case_index))

        def run_lane(lane_index, queue):
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

        self.app.log_message("🎉 모든 캡차 이미지 로드 완료!")
        self.app.processing = False

        def _restore_start_btn():
            self.app.start_btn.configure(text="🖼️ 사건 조회 로드")
            self.app._set_control_btn_state(self.app.start_btn, True)

        self.app.ui_queue.put(("function", (_restore_start_btn,), {}))
        self.app.ui_queue.put(("function", (self.app._set_control_btn_state, self.app.stop_btn, False), {}))
        self._save_run_result_for_email(cases)
        self._check_and_prompt_failed_cases(cases)

    def _save_run_result_for_email(self, processed_cases):
        """
        처리된 사건 목록을 case_status 기준으로 성공/실패/변경없음으로 나누어
        email_manager에 저장합니다. 메일 하단 "이번 조회 결과"에 사용됩니다.
        """
        success_cases = []
        failed_cases = []
        no_update_cases = []
        for case in processed_cases:
            case_number = case.get("사건번호", "")
            if not case_number:
                continue
                
            case_info = {
                "사건번호": case_number,
                "피고": case.get("피고", ""),
                "사건명": case.get("사건명", "")
            }
            
            case_index = self.app.find_case_index(case_number)
            if case_index == -1 or case_index not in getattr(self.app, "case_status", {}):
                continue
            status_text = self.app.case_status[case_index].cget("text") or ""
            if any(k in status_text for k in ["실패", "오류", "취소", "재입력대기"]):
                failed_cases.append(case_info)
            elif "변경없음" in status_text:
                no_update_cases.append(case_info)
            else:
                success_cases.append(case_info)
        email_manager_module.set_last_run_result(
            success_cases=success_cases,
            failed_cases=failed_cases,
            no_update_cases=no_update_cases if no_update_cases else None,
            captcha_cases=None,
        )

    def _check_and_prompt_failed_cases(self, processed_cases):
        """처리된 사건 중 실패/오류/재입력대기 상태인 사건들을 찾아 재실행 여부를 묻습니다."""
        failed_cases = []
        for case in processed_cases:
            case_number = case.get("사건번호", "")
            case_index = self.app.find_case_index(case_number)
            if case_index != -1 and case_index in self.app.case_status:
                status_text = self.app.case_status[case_index].cget("text")
                if any(keyword in status_text for keyword in ["실패", "오류", "취소", "재입력대기"]):
                    failed_cases.append((case_index, case_number))

        if not failed_cases:
            return

        def _show_prompt():
            failed_msg = "\n".join([f"- {num}" for _, num in failed_cases])
            prompt_msg = (
                f"총 {len(failed_cases)}건의 사건 처리에 실패했습니다.\n\n[실패 목록]\n{failed_msg}\n\n"
                "실패한 사건들만 다시 실행하시겠습니까?"
            )
            if messagebox.askyesno("재실행 확인", prompt_msg):
                self.app.log_message(f"🔄 실패한 {len(failed_cases)}건 재실행 시작")
                self.app.deselect_all_cases()
                for case_idx, _ in failed_cases:
                    if case_idx in self.app.case_checkboxes:
                        self.app.case_checkboxes[case_idx].set(True)
                self.app.header_select_all_var.set(False)
                self.app.start_batch_processing()

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
                elapsed_time = int(time.time() - self.app.case_start_times.get(case_index, time.time()))
                try:
                    last_entry_result = self.app.google_sheets_service.get_last_entry_from_sheet(case)
                    if last_entry_result is not None:
                        last_entry, sheet_last_row_index = last_entry_result
                        self.app.log_message(f"📋 [DEBUG] 구글 시트 기준 비교: {case_number}")
                    else:
                        last_entry = None
                        sheet_last_row_index = None
                except Exception as e:
                    self.app.log_message(f"⚠️ 시트 조회 실패, 로컬 기록 사용: {e}")
                    last_entry = self.app.history_manager.get_last_entry(case_number)
                    sheet_last_row_index = None
                new_data = self.filter_new_data(result_data, last_entry)

                if not new_data and sheet_last_row_index is not None:
                    sheet_data_count = sheet_last_row_index - 1
                    current_len = len(result_data)
                    if sheet_data_count < current_len:
                        missing = current_len - sheet_data_count
                        if self.app.google_sheets_service.delete_specific_row(case, sheet_last_row_index):
                            new_data = result_data[-(missing + 1) :]
                            self.app.log_message(f"⚠️ [보정] 기일 행 제거 후 +{missing + 1}건 추가 (기일 순서 유지)")
                        else:
                            new_data = result_data[-missing:]
                            self.app.log_message(f"⚠️ [보정] 시트 누락: +{missing}건 강제 추가 (행 삭제 실패)")
                if not new_data:
                    self.app.log_message(f"📭 변경없음: {case_number}")
                    self.app.update_case_status(case_index, "완료 (변경없음)", "#7F8C8D", "✅")
                    history = self.app.load_update_history()
                    prev_total = history.get(case_number, {}).get("row_count", 0) if isinstance(history.get(case_number), dict) else 0
                    current_count = len(result_data) if isinstance(result_data, list) else 0
                    new_total = max(prev_total, current_count)
                    self.app.update_case_timestamp(case, case_index, new_total)
                    if hasattr(self.app, "processed_cases"):
                        self.app.processed_cases.add(case_index)
                    self.app.log_message(f"✅ 자동 처리 완료: {case_number} (소요 시간: {elapsed_time}초)")
                    return True
                row_count = None
                try:
                    row_count = self.save_to_google_sheets(case, new_data)
                except Exception as save_err:
                    self.app.log_message(f"❌ 구글 시트 저장 예외: {save_err}")
                    row_count = False
                if row_count is False or row_count is None:
                    self.app.update_case_status(case_index, "저장 실패", "red", "❌")
                    self.app.log_message(f"❌ 구글 시트 저장 실패: {case_number}")
                    return "fail"
                if row_count == 0:
                    self.app.update_case_status(case_index, "데이터 없음", "#7F8C8D", "📭")
                else:
                    self.app.history_manager.update_last_entry(case_number, new_data[-1])
                    self.app.google_sheets_service.update_main_remark(case_number, row_count)
                    self.app.update_case_status(case_index, f"완료 (+{row_count}건)", "green", "✅")
                history = self.app.load_update_history()
                old_total = history.get(case_number, {}).get("row_count", 0) if isinstance(history.get(case_number), dict) else 0
                total_rows = (old_total + row_count) if row_count else old_total
                self.app.update_case_timestamp(case, case_index, total_rows)
                if row_count > 0:
                    self.app.add_to_search_log(case_number)
                    try:
                        sheet_name = self.app.google_sheets_service._get_case_worksheet_name(case)
                        email_manager_module.add_new_update(case_number, new_data, sheet_name=sheet_name)
                    except Exception:
                        pass
                    if hasattr(self.app, "update_email_btn_text") and callable(getattr(self.app, "update_email_btn_text", None)):
                        self.app.root.after(0, self.app.update_email_btn_text)
                if hasattr(self.app, "processed_cases"):
                    self.app.processed_cases.add(case_index)
                self.app.log_message(f"✅ 자동 처리 완료: {case_number} (소요 시간: {elapsed_time}초)")
                return True
            else:
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
            ev = getattr(self.app, "lane_events", {}).pop(case_number, None)
            if ev:
                ev.set()

    def process_cli_auto_case(self, case, case_index):
        """CLI 전용: 브라우저 기동 후 바로 'CLICK' 명령을 전송합니다."""
        case_number = case.get("사건번호", "")
        profile_index = self.get_case_profile_index(case_number)
        
        try:
            self.app.case_start_times[case_index] = time.time()
            self.app.update_case_status(case_index, "처리중(캡차로딩)", "orange", "🔄")

            with self.app.profile_locks[profile_index]:
                # 브라우저 기동 및 캡차 캡처 (스마트 스킵 시 '__CLICK__' 반환)
                result_data = self.execute_case_processing_with_captcha(case, case_index, profile_index)

            elapsed_time = int(time.time() - self.app.case_start_times[case_index])

            if result_data == "__CLICK__":
                self.app.update_case_status(case_index, "입력완료", "green", "⚡")
                self.app.log_message(f"⚡ 캡차 스킵: {case_number} (자동 클릭 준비 완료)")
                # 브라우저가 정상적으로 떴으므로 CLICK 전송 및 크롤링 실행
                return self._process_auto_case(case, case_index)
            elif result_data:
                # 일반 캡차 이미지가 반환된 경우 (CLI 모드는 CLICK 전용이므로 실패 처리)
                self.app.log_message(f"⚠️ 스마트 스킵 불가 (일반 캡차 발생): {case_number}")
                return "captcha"
            else:
                self.app.update_case_status(case_index, f"실패 ({elapsed_time}초)", "red", "❌")
                self.app.log_message(f"❌ 캡차 이미지 로딩 실패: {case_number}")
                return "fail"

        except Exception as e:
            elapsed_time = int(time.time() - self.app.case_start_times.get(case_index, time.time()))
            self.app.log_message(f"❌ CLI 처리 오류: {case_number} - {e}")
            self.app.update_case_status(case_index, f"오류 ({elapsed_time}초)", "red", "⚠️")
            return "fail"

    def process_single_case_parallel(self, case, case_index, instance_index=0):
        """병렬 처리용 단일 사건: 캡차 캡처 후 대기 또는 자동 처리."""
        case_number = case.get("사건번호", "")
        profile_index = self.get_case_profile_index(case_number)

        try:
            self.app.case_start_times[case_index] = time.time()
            self.app.update_case_status(case_index, "처리중(캡차로딩)", "orange", "🔄")

            with self.app.profile_locks[profile_index]:
                result_data = self.execute_case_processing_with_captcha(case, case_index, profile_index)

            elapsed_time = int(time.time() - self.app.case_start_times[case_index])

            if result_data:
                if result_data == "__CLICK__":
                    if case_index in self.app.case_inputs:
                        self.app.case_inputs[case_index].set("CLICK")
                    self.app.update_case_status(case_index, "입력완료", "green", "⚡")
                    self.app.log_message(f"⚡ 캡차 스킵: {case_number} (자동 클릭 준비 완료)")
                    self._process_auto_case(case, case_index)
                    return True

                self.app.update_case_status(case_index, "입력대기", "blue", "⏳")
                self.app.log_message(f"✅ 캡차 이미지 로드 완료: {case_number} (소요 시간: {elapsed_time}초)")
                self.app.root.after(0, lambda: self.app._set_control_btn_state(self.app.complete_btn, True))
                ev = threading.Event()
                self.app.lane_events[case_number] = ev
                ev.wait()
                return True
            else:
                self.app.update_case_status(case_index, f"실패 ({elapsed_time}초)", "red", "❌")
                return False

        except Exception as e:
            elapsed_time = int(time.time() - self.app.case_start_times.get(case_index, time.time()))
            self.app.log_message(f"❌ 처리 오류: {case_number} - {e}")
            self.app.update_case_status(case_index, f"오류 ({elapsed_time}초)", "red", "⚠️")
            return False

    # -------------------------------------------------------------------------
    # 캡차 입력 완료 플로우 (Wave Processing)
    # -------------------------------------------------------------------------

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
            case_start_time = time.time()
            self.app.case_start_times[original_index] = case_start_time

            current_progress = len(
                [
                    i
                    for i, _ in selected_cases[
                        : selected_cases.index((original_index, case)) + 1
                    ]
                ]
            )
            progress_percent = (current_progress / total_cases) * 100
            elapsed = int(time.time() - total_start_time)
            if current_progress > 0:
                avg_time = elapsed / current_progress
                remaining_time = int(avg_time * (total_cases - current_progress))
                self.app.update_progress(
                    progress_percent,
                    f"🔄 처리 중... ({current_progress}/{total_cases}) - {case_number} | 예상 남은 시간: {remaining_time}초",
                )
            else:
                self.app.update_progress(
                    progress_percent,
                    f"🔄 처리 중... ({current_progress}/{total_cases}) - {case_number}",
                )

            if not (captcha_input and captcha_input.strip()):
                self.app.log_message(f"⚠️ 캡차 입력이 비어있음: {case_number}")
                self.app.update_case_status(original_index, "입력없음", "red", "⚠️")
                return (0, 1)

            self.app.log_message(
                f"📋 [DEBUG] GUI에서 가져온 캡차 입력: '{captcha_input}' (타입: {type(captcha_input).__name__}, 길이: {len(captcha_input)})"
            )
            is_click = captcha_input == "CLICK"
            is_valid_captcha = len(captcha_input) == 6 and captcha_input.isdigit()
            if not (is_click or is_valid_captcha):
                self.app.log_message(
                    f"⚠️ 캡차 입력 형식 오류: {case_number} (입력: {captcha_input}, 길이: {len(captcha_input)})"
                )
                self.app.update_case_status(original_index, "형식오류", "red", "⚠️")
                return (0, 1)

            self.app.log_message(f"✅ [DEBUG] 캡차 형식 검증 통과: {captcha_input}")
            self.app.log_message(f"🔄 처리 시작: {case_number} (캡차: {captcha_input})")
            self.app.update_case_status(original_index, "처리중(크롤링)", "orange", "🔄")

            self.app.log_message("🔄 [DEBUG] execute_case_processing 호출 전")
            should_cleanup_and_release = True
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
                    self.app.log_message("⚠️ 캡차 불일치 - 재시도 필요")
                    new_path = result_data.get("image_path")
                    if new_path:
                        self.app.root.after(
                            0,
                            lambda p=new_path, i=original_index: self.app.update_captcha_image(
                                i, p
                            ),
                        )
                    self.app.update_case_status(original_index, "재입력대기", "red", "⚠️")
                    should_cleanup_and_release = False
                    return (0, 0)

                if isinstance(result_data, list):
                    try:
                        last_entry_result = (
                            self.app.google_sheets_service.get_last_entry_from_sheet(case)
                        )
                        if last_entry_result is not None:
                            last_entry, sheet_last_row_index = last_entry_result
                            self.app.log_message(
                                f"📋 [DEBUG] 구글 시트 기준 비교: {case_number}"
                            )
                        else:
                            last_entry = None
                            sheet_last_row_index = None
                    except Exception as e:
                        self.app.log_message(f"⚠️ 시트 조회 실패, 로컬 기록 사용: {e}")
                        last_entry = self.app.history_manager.get_last_entry(case_number)
                        sheet_last_row_index = None
                    new_data = self.filter_new_data(result_data, last_entry)

                    if not new_data and sheet_last_row_index is not None:
                        sheet_data_count = sheet_last_row_index - 1
                        current_len = len(result_data)
                        if sheet_data_count < current_len:
                            missing = current_len - sheet_data_count
                            if self.app.google_sheets_service.delete_specific_row(
                                case, sheet_last_row_index
                            ):
                                new_data = result_data[-(missing + 1) :]
                                self.app.log_message(
                                    f"⚠️ [보정] 기일 행 제거 후 +{missing + 1}건 추가 (기일 순서 유지)"
                                )
                            else:
                                new_data = result_data[-missing:]
                                self.app.log_message(
                                    f"⚠️ [보정] 시트 누락: +{missing}건 강제 추가 (행 삭제 실패)"
                                )
                    if not new_data:
                        self.app.log_message(f"📭 변경없음: {case_number}")
                        self.app.update_case_status(
                            original_index, "완료 (변경없음)", "#7F8C8D", "✅"
                        )
                        history = self.app.load_update_history()
                        prev_total = 0
                        if isinstance(history.get(case_number), dict):
                            prev_total = history.get(case_number, {}).get(
                                "row_count", 0
                            )
                        current_count = (
                            len(result_data) if isinstance(result_data, list) else 0
                        )
                        new_total = max(prev_total, current_count)
                        self.app.update_case_timestamp(case, original_index, new_total)
                        self.app.log_message(
                            f"✅ 처리 완료: {case_number} (소요 시간: {elapsed_time}초)"
                        )
                        return (1, 0)
                    row_count = None
                    try:
                        row_count = self.save_to_google_sheets(case, new_data)
                    except Exception as save_err:
                        self.app.log_message(f"❌ 구글 시트 저장 예외: {save_err}")
                        row_count = False
                    if row_count is False or row_count is None:
                        self.app.update_case_status(
                            original_index, "저장 실패", "red", "❌"
                        )
                        self.app.log_message(f"❌ 구글 시트 저장 실패: {case_number}")
                        return (0, 1)
                    if row_count == 0:
                        self.app.update_case_status(
                            original_index, "데이터 없음", "#7F8C8D", "📭"
                        )
                    else:
                        self.app.history_manager.update_last_entry(
                            case_number, new_data[-1]
                        )
                        self.app.google_sheets_service.update_main_remark(
                            case_number, row_count
                        )
                        self.app.update_case_status(
                            original_index,
                            f"완료 (+{row_count}건)",
                            "green",
                            "✅",
                        )
                    history = self.app.load_update_history()
                    old_total = 0
                    if isinstance(history.get(case_number), dict):
                        old_total = history.get(case_number, {}).get("row_count", 0)
                    total_rows = (old_total + row_count) if row_count else old_total
                    self.app.update_case_timestamp(case, original_index, total_rows)
                    if row_count > 0:
                        self.app.add_to_search_log(case_number)
                        try:
                            sheet_name = self.app.google_sheets_service._get_case_worksheet_name(case)
                            email_manager_module.add_new_update(case_number, new_data, sheet_name=sheet_name)
                        except Exception:
                            pass
                        if hasattr(self.app, "update_email_btn_text") and callable(getattr(self.app, "update_email_btn_text", None)):
                            self.app.root.after(0, self.app.update_email_btn_text)
                    self.app.log_message(
                        f"✅ 처리 완료: {case_number} (소요 시간: {elapsed_time}초)"
                    )
                    return (1, 0)
                else:
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

    def process_all_captcha_inputs(self):
        """
        모든 캡차 입력을 한번에 처리.
        '캡차 입력 완료' 버튼 클릭 시 start_processing_thread()가 이 메서드를 백그라운드 스레드에서 실행.
        GUI 갱신은 self.app.root.after(0, ...) 로 메인 스레드에 위임.
        """
        try:
            total_start_time = time.time()
            self.app.processing = True
            self.app.puppeteer_service.processing_flag = lambda: self.app.processing
            self.app.log_message("🔄 모든 캡차 입력 처리 시작")

            self.app.root.after(0, lambda: self.app._set_control_btn_state(self.app.complete_btn, False))
            if not hasattr(self.app, "processed_cases"):
                self.app.processed_cases = set()

            self.app.root.after(0, lambda: self.app._set_control_btn_state(self.app.start_btn, False))
            self.app.root.after(0, lambda: self.app._set_control_btn_state(self.app.stop_btn, True))

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
                self.app.root.after(0, lambda: self.app._set_control_btn_state(self.app.complete_btn, True))
            else:
                self.app.log_message("🎉 모든 사건 처리 완료!")

                try:
                    self.app.log_message("🔄 [DEBUG] Chrome 프로세스 정리 중...")
                    chrome_killed = 0
                    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                        try:
                            if (
                                proc.info.get("name")
                                and "chrome.exe" in (proc.info.get("name") or "").lower()
                            ):
                                cmdline = proc.info.get("cmdline", []) or []
                                if any(
                                    "--remote-debugging-port" in str(arg)
                                    for arg in cmdline
                                ):
                                    self.app.log_message(
                                        f"🔄 [DEBUG] Chrome 프로세스 종료: PID {proc.info.get('pid')}"
                                    )
                                    proc.kill()
                                    chrome_killed += 1
                        except (
                            psutil.NoSuchProcess,
                            psutil.AccessDenied,
                            psutil.ZombieProcess,
                        ):
                            pass

                    if chrome_killed > 0:
                        self.app.log_message(
                            f"✅ Chrome 프로세스 {chrome_killed}개 종료 완료"
                        )
                    else:
                        self.app.log_message("ℹ️ 종료할 Chrome 프로세스 없음")

                except Exception as e:
                    self.app.log_message(f"⚠️ Chrome 프로세스 정리 오류: {e}")
                    try:
                        sp.run(
                            ["taskkill", "/F", "/IM", "chrome.exe"],
                            capture_output=True,
                            timeout=3,
                        )
                        self.app.log_message("⚠️ taskkill로 Chrome 강제 종료 시도")
                    except Exception:
                        pass

                self.app.browser_processes.clear()
                self.app.browser_ws_urls.clear()
                self.app.log_message("✅ 모든 브라우저 프로세스 종료 완료")

                total_elapsed = int(time.time() - total_start_time)
                self.app.update_progress(
                    100,
                    f"✅ 처리 완료! (성공: {completed}, 실패: {failed}) | 총 소요 시간: {total_elapsed}초",
                )
                self.app.log_message(
                    f"🎉 모든 캡차 입력 처리 완료! (총 소요 시간: {total_elapsed}초)"
                )
                self._save_run_result_for_email([c for _, c in selected_cases])

                self.app.root.after(
                    0,
                    lambda: messagebox.showinfo(
                        "처리 완료",
                        f"🎉 처리가 완료되었습니다!\n\n"
                        f"✅ 성공: {completed}개\n"
                        f"❌ 실패: {failed}개\n"
                        f"📊 총 사건: {total_cases}개\n"
                        f"⏱️ 총 소요 시간: {total_elapsed}초",
                    ),
                )

                self.app.processing = False
                self.app.root.after(
                    0, lambda: self.app._set_control_btn_state(self.app.complete_btn, False)
                )

                def _restore_start():
                    self.app.start_btn.configure(
                        text="🖼️ 사건 조회 로드 실행\n(캡차 로드 실행)"
                    )
                    self.app._set_control_btn_state(self.app.start_btn, True)

                self.app.root.after(0, _restore_start)
                self.app.root.after(
                    0, lambda: self.app._set_control_btn_state(self.app.stop_btn, False)
                )

        except Exception as e:
            self.app.log_message(f"❌ 캡차 입력 처리 오류: {e}")
            self.app.update_progress(0, "오류 발생")
            self.app.root.after(0, lambda: self.app._set_control_btn_state(self.app.complete_btn, True))

            def _restore_start():
                self.app.start_btn.configure(
                    text="🖼️ 사건 조회 로드 실행\n(캡차 로드 실행)"
                )
                self.app._set_control_btn_state(self.app.start_btn, True)

            self.app.root.after(0, _restore_start)
            self.app.root.after(
                0, lambda: self.app._set_control_btn_state(self.app.stop_btn, False)
            )
            self.app.processing = False
