# -*- coding: utf-8 -*-
"""
사건 처리 컨트롤러 (Process Controller)
======================================

app_controller.py에 있던 병렬 처리·스레딩·캡차 재시도 로직을 전담합니다.
GUI는 app 참조를 통해 콜백 형태로 UI 갱신만 수행합니다.
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


class ProcessController:
    """
    사건 조회 로드·캡차 처리·병렬 실행을 담당하는 작업 관리자.
    AppController 또는 MockApp(CLI) 인스턴스(app)를 받아, 로그/상태/진행률 등은 app 메서드로 전달합니다.
    """

    def __init__(self, app):
        """
        Args:
            app: AppController 또는 MockApp. log_message, update_case_status, ui_queue, show_warning 등에 접근.
        """
        self.app = app
        # OCR 자동 제출(웨이브) 중복 호출 방지
        self._auto_submit_lock = threading.Lock()

    # -------------------------------------------------------------------------
    # 캡차 OCR (EasyOCR + Tesseract, ocr_export)
    # -------------------------------------------------------------------------

    def _init_ocr_wave_state(self):
        """사건 조회 로드(웨이브) 시작 시 OCR 관련 상태 초기화."""
        self.app.ocr_manual_required = {}
        self.app.ocr_retry_counts = {}
        self.app._ocr_wave_auto_submit_started = False

    def _set_manual_captcha_fallback(self, case_index, case_number):
        """
        OCR 실패·재시도 한도 초과 시: 입력칸 잠금 해제, 수동 입력 유도.

        주니어 개발자 참고:
        - ocr_manual_required[사건번호]=True 이면 웨이브 자동 제출에서 제외됩니다.
        """
        self.app.ocr_manual_required[case_number] = True
        captcha_ui_module.clear_captcha_input_for_manual(self.app, case_index)
        self.app.update_case_status(case_index, "수동입력 필요", "red", "⚠️")
        self.app.ui_queue.put(
            ("function", (self.app._set_control_btn_state, self.app.complete_btn, True), {})
        )

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

        self.app.log_message(
            f"✅ OCR 자동입력중: {result.text} ({result.engine}, {result.confidence:.2f}) — 입력칸 잠금"
        )
        self.app.ocr_manual_required[case_number] = False

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
        선택 사건 전원이 OCR로 6자리 입력됐을 때 「캡cha 입력 완료」와 동일하게 자동 제출.

        반환: True면 start_processing_thread를 호출함.
        """
        if not getattr(config, "OCR_ENABLED", False):
            return False
        if not getattr(config, "OCR_AUTO_SUBMIT", False):
            return False

        with self._auto_submit_lock:
            if getattr(self.app, "_ocr_wave_auto_submit_started", False):
                return False

            lane_events = getattr(self.app, "lane_events", {})
            manual = getattr(self.app, "ocr_manual_required", {})

            for case in cases:
                case_number = case.get("사건번호", "")
                idx = self._case_index_for_number(case_number)
                if idx is None:
                    continue
                captcha_val = self.app.get_captcha_input(idx)
                if captcha_val == "CLICK":
                    continue
                if case_number not in lane_events:
                    self.app.log_message(
                        f"ℹ️ OCR 자동 제출 대기: {case_number} 아직 lane 미등록"
                    )
                    return False
                if manual.get(case_number, False):
                    self.app.log_message(
                        "⚠️ 수동입력 필요 사건 포함 — OCR 자동 제출 생략"
                    )
                    self.app.ui_queue.put(
                        (
                            "function",
                            (self.app._set_control_btn_state, self.app.complete_btn, True),
                            {},
                        )
                    )
                    return False
                if not self._lane_waiting_has_valid_captcha(case_number):
                    return False

            n_wait = len(lane_events)
            self.app._ocr_wave_auto_submit_started = True
            self.app.log_message(
                f"⚡ OCR 자동 제출 시작 (대기 사건 {n_wait}건 모두 입력됨)"
            )
            self.app.start_processing_thread()
            return True

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

    @staticmethod
    def _extract_hearing_from_result(result_data):
        """
        result_data(크롤링 결과 리스트)에서 최신 변론기일 또는 판결선고기일 하나만 추출.
        UI에는 최신 기일 하나만 표기하므로, 역순 순회 시 첫 매치 하나만 반환.
        반환: "변론기일 YY.MM.DD.(HH:MM)" 또는 "판결선고기일 YY.MM.DD.(HH:MM)" 형식 문자열, 없으면 None.
        """
        if not result_data or not isinstance(result_data, list):
            return None
        for i in range(len(result_data) - 1, -1, -1):
            row = result_data[i]
            if not isinstance(row, dict):
                continue
            raw_date = (row.get("date") or "").strip()
            raw_content = (row.get("content") or "").strip()
            if not raw_content:
                continue
            raw_content = re.sub(r"\s+", " ", raw_content)
            m = re.search(
                r"(변론기일|감정기일|판결선고기일).*?([0-9]{1,2}:[0-9]{2})",
                raw_content,
                re.DOTALL,
            )
            if not m:
                continue
            kind = m.group(1)
            time_str = m.group(2)
            formatted_date = ""
            if raw_date:
                parts = raw_date.replace("-", ".").split(".")
                if len(parts) >= 3:
                    y = parts[0].strip()
                    if len(y) >= 4:
                        y = y[-2:]
                    formatted_date = f"{y}.{parts[1].strip()}.{parts[2].strip()}."
            if formatted_date:
                return f"{kind} {formatted_date}({time_str})"
            return f"{kind}({time_str})"
        return None

    @staticmethod
    def _parse_datetime_from_row(raw_date, time_str):
        raw_date = (raw_date or "").strip()
        if not raw_date:
            return None
        parts = raw_date.replace("-", ".").split(".")
        if len(parts) < 3:
            return None
        try:
            y = int(parts[0].strip())
            mo = int(parts[1].strip())
            d = int(parts[2].strip())
            hh, mm = time_str.split(":")
            hh = int(hh)
            mm = int(mm)
            if y < 10:
                y = 2020 + y
            elif y < 100:
                y = 2000 + y
            return datetime(y, mo, d, hh, mm)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _extract_hearing_events_from_result(cls, result_data):
        """
        result_data에서 캘린더 등록용 기일 이벤트 목록을 추출.
        반환: [{"kind": str, "start_dt": datetime, "label": str}, ...]
        """
        if not isinstance(result_data, list):
            return []
        events = []
        seen = set()
        for row in result_data:
            if not isinstance(row, dict):
                continue
            raw_content = re.sub(r"\s+", " ", (row.get("content") or "").strip())
            if not raw_content:
                continue
            raw_date = (row.get("date") or "").strip()
            for m in re.finditer(
                r"(변론기일|감정기일|판결선고기일).*?([0-9]{1,2}:[0-9]{2})",
                raw_content,
                re.DOTALL,
            ):
                kind = m.group(1)
                time_str = m.group(2)
                start_dt = cls._parse_datetime_from_row(raw_date, time_str)
                if start_dt is None:
                    continue
                key = (kind, start_dt.isoformat())
                if key in seen:
                    continue
                seen.add(key)
                events.append(
                    {
                        "kind": kind,
                        "start_dt": start_dt,
                        "label": f"{kind} {start_dt.strftime('%y.%m.%d.(%H:%M)')}",
                    }
                )
        return events

    def _maybe_sync_hearing_calendar(self, case, result_data):
        if int(getattr(config, "GOOGLE_CALENDAR_ENABLED", 1)) != 1:
            return
        events = self._extract_hearing_events_from_result(result_data)
        if not events:
            return
        try:
            res = google_calendar_module.sync_hearing_events(
                case, events, log_callback=self.app.log_message
            )
            self.app.log_message(
                "📅 캘린더 동기화 완료: 생성 %s / 갱신 %s / 건너뜀 %s"
                % (res.get("created", 0), res.get("updated", 0), res.get("skipped", 0))
            )
        except Exception as e:
            self.app.log_message(f"⚠️ 캘린더 동기화 실패: {e}")

    def _compute_new_progress_rows(self, case, result_data, existing_values=None):
        """
        기존 시트의 진행내용과 대법원 result_data를 멀티셋으로 비교해,
        새로 늘어난(시트에 없는) 행만 순서대로 반환합니다.

        주니어 개발자 참고:
        - 대법원은 기일(변론/감정/선고)을 미래 날짜라 목록 맨 아래에 고정 배치하므로,
          "마지막 행 다음부터 신규"라는 가정이 깨집니다(신규가 기일 위에 끼어듦).
        - 그래서 마지막 행이 아니라 '전체 집합 차이'로 신규를 판단합니다.
        - 동일 (일자·내용·결과·공시문) 행이 여러 개여도 개수만큼만 기존으로 처리해,
          대법원에 실제로 늘어난 행만 신규로 잡습니다.
        - 반환값은 메일·기일 캐시·상태 표시(+N건)에만 사용하며, 실제 저장은
          overwrite_progress_area가 전체를 대법원과 1:1로 맞춥니다.

        매개변수:
        - existing_values: 이미 읽어둔 시트 전체 값. 넘기면 시트를 다시 읽지 않습니다.
          (예전에는 여기서 조회에 실패하면 '전체를 신규로 처리'해 +건수를 크게 오판했는데,
           이제는 호출부가 미리 안전하게 읽은 값을 넘겨주므로 그런 오판이 없습니다.)
        """
        if not isinstance(result_data, list):
            return []
        gs = self.app.google_sheets_service
        if existing_values is not None:
            existing = existing_values
        else:
            try:
                existing = gs.get_full_sheet_data(case)
            except Exception as e:
                # 시트를 못 읽었을 때 '전체를 신규'로 보면 +건수가 폭증(오판)하므로,
                # 신규 없음(빈 리스트)으로 처리해 안전하게 둡니다. 실제 동기화는 호출부가 담당.
                self.app.log_message(f"⚠️ 시트 조회 실패(신규 0건으로 처리): {e}")
                return []

        existing_counts = {}
        for row in (existing[1:] if existing else []):
            if not gs._is_progress_data_row(row):
                continue
            key = gs._sheet_row_dedup_key(row)
            existing_counts[key] = existing_counts.get(key, 0) + 1

        new_rows = []
        for progress_row in result_data:
            if not isinstance(progress_row, dict):
                continue
            key = gs._dict_row_dedup_key(progress_row)
            if existing_counts.get(key, 0) > 0:
                existing_counts[key] -= 1
            else:
                new_rows.append(progress_row)
        return new_rows

    def _verify_sheet_matches_court(self, case, result_data, case_number, sheet_count=None):
        """
        저장 직후 시트 진행내용 행 수가 대법원 result_data와 일치하는지 검증합니다.

        주니어 개발자 참고:
        - overwrite_progress_area가 정상 동작하면 항상 일치해야 합니다.
        - 불일치 시 로그에 경고만 남기고, 본 처리 흐름은 중단하지 않습니다.
        - sheet_count를 넘기면 시트를 다시 읽지 않습니다(API 호출 절감).
          overwrite_progress_area는 기록한 행 수를 반환하므로 그 값을 그대로 쓰면 됩니다.
        """
        gs = self.app.google_sheets_service
        try:
            if sheet_count is None:
                sheet_count = gs.count_progress_rows(case)
            court_count = len(result_data) if isinstance(result_data, list) else 0
            if sheet_count != court_count:
                self.app.log_message(
                    f"⚠️ 검증: {case_number} 시트 {sheet_count}행 vs 대법원 {court_count}행 불일치"
                )
                return False
            self.app.log_message(
                f"✅ 검증: {case_number} 시트·대법원 진행내용 {court_count}행 일치"
            )
            return True
        except Exception as e:
            self.app.log_message(f"⚠️ 검증 실패(무시): {case_number} - {e}")
            return False

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
                self.app.ui_queue.put(("function", (self.app._set_control_btn_state, self.app.complete_btn, True), {}))
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
            self.app.show_warning("처리할 사건을 선택해주세요.")
            return
        if self.app.processing:
            self.app.show_warning("이미 처리 중입니다.")
            return

        self.app.processed_cases = set()
        self.app.processing = True
        self._init_ocr_wave_state()
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
        if hasattr(self.app, "is_dedup_mode"):
            self.app.is_dedup_mode = False
        if hasattr(self.app, "is_reset_mode"):
            self.app.is_reset_mode = False
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
        self._init_ocr_wave_state()
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
        time.sleep(0.5)
        auto_started = self._try_auto_submit_captcha_wave(cases)
        # 선택한 사건들에 대한 캡차 이미지 로드가 모두 끝났을 때 안내 다이얼로그 표시
        self.app.ui_queue.put(
            ("function", (self.app.show_info, "선택한 모든 작업 조회 완료!"), {})
        )
        if not auto_started:
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
            status_text = self.app.get_case_status_text(case_index) or ""
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
                status_text = self.app.get_case_status_text(case_index)
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
            if self.app.ask_yesno("재실행 확인", prompt_msg):
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

                # OCR: 숫자 인식 → 입력칸 채움 (실패 시 수동 폴백 표시)
                if isinstance(result_data, str) and os.path.isfile(result_data):
                    if getattr(config, "OCR_ENABLED", False):
                        ocr_ok = self._run_ocr_fill_case(case, case_index, result_data)
                        if not ocr_ok:
                            self._set_manual_captcha_fallback(case_index, case_number)
                        else:
                            self.app.log_message(
                                f"✅ 캡차 OCR 완료: {case_number} (소요 시간: {elapsed_time}초)"
                            )
                    else:
                        self.app.update_case_status(case_index, "입력대기", "blue", "⏳")

                self.app.log_message(f"✅ 캡차 이미지 로드 완료: {case_number} (소요 시간: {elapsed_time}초)")
                need_manual_complete = (
                    not getattr(config, "OCR_ENABLED", False)
                    or not getattr(config, "OCR_AUTO_SUBMIT", False)
                    or self.app.ocr_manual_required.get(case_number, False)
                )
                if need_manual_complete:
                    self.app.ui_queue.put(
                        ("function", (self.app._set_control_btn_state, self.app.complete_btn, True), {})
                    )
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

    def _as_process_result(self, completed_delta, failed_delta, *, tuple_return=True):
        """
        처리 결과를 호출 경로에 맞는 형식으로 변환합니다.

        tuple_return=True  → (completed_delta, failed_delta)  (웨이브/캡차 완료 루프)
        tuple_return=False → True | "fail"                    (자동 클릭 스킵 경로)
        """
        if tuple_return:
            return (completed_delta, failed_delta)
        return "fail" if failed_delta else True

    def _finish_case_no_change(
        self, case, original_index, case_number, result_data, elapsed_time, hearing_info=None, *, tuple_return=True
    ):
        """변경없음 처리: 상태·타임스탬프·기일 캐시 갱신."""
        self.app.log_message(f"📭 변경없음: {case_number}")
        self.app.update_case_status(original_index, "완료 (변경없음)", "#7F8C8D", "✅")
        self.app.log_history_manager.add_to_search_log(case_number)
        self.app.ui_queue.put(("function", (self.app.update_auto_search_label, case_number), {}))
        history = self.app.load_update_history()
        prev_total = history.get(case_number, {}).get("row_count", 0) if isinstance(history.get(case_number), dict) else 0
        current_count = len(result_data) if isinstance(result_data, list) else 0
        new_total = max(prev_total, current_count)
        self.app.update_case_timestamp(case, original_index, new_total, hearing_info=hearing_info)
        self._maybe_sync_hearing_calendar(case, result_data)
        self.app.log_message(f"✅ 처리 완료: {case_number} (소요 시간: {elapsed_time}초)")
        return self._as_process_result(1, 0, tuple_return=tuple_return)

    def _finish_case_with_save(
        self,
        case,
        original_index,
        case_number,
        result_data,
        new_data,
        row_count,
        elapsed_time,
        hearing_info=None,
        reset_mode=False,
        *,
        tuple_return=True,
        verify_sheet_count=None,
    ):
        """
        저장 결과 반영: 상태·타임스탬프·기일 캐시·이메일 준비.

        verify_sheet_count: overwrite_progress_area가 기록한 행 수.
        넘기면 검증 단계에서 시트를 다시 읽지 않아 API 호출을 아낍니다(None이면 재읽기).
        """
        if row_count is False or row_count is None:
            self.app.update_case_status(original_index, "저장 실패", "red", "❌")
            self.app.log_message(f"❌ 구글 시트 저장 실패: {case_number}")
            return self._as_process_result(0, 1, tuple_return=tuple_return)
        if row_count == 0:
            self.app.update_case_status(original_index, "데이터 없음", "#7F8C8D", "📭")
        else:
            self.app.history_manager.update_last_entry(case_number, new_data[-1])
            remark_count = len(result_data) if reset_mode and isinstance(result_data, list) else row_count
            self.app.google_sheets_service.update_main_remark(case_number, remark_count)
            status_label = f"재수집 완료 (+{row_count}건)" if reset_mode else f"완료 (+{row_count}건)"
            self.app.update_case_status(original_index, status_label, "green", "✅")
        history = self.app.load_update_history()
        old_total = history.get(case_number, {}).get("row_count", 0) if isinstance(history.get(case_number), dict) else 0
        if reset_mode and row_count:
            total_rows = len(result_data) if isinstance(result_data, list) else row_count
        else:
            total_rows = (old_total + row_count) if row_count else old_total
        self.app.update_case_timestamp(case, original_index, total_rows, hearing_info=hearing_info)
        self._maybe_sync_hearing_calendar(case, result_data)
        if row_count > 0:
            update_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.app.log_message(
                f"📊 이번 조회 신규 {row_count}건 추가, 업데이트 시각 {update_ts} ({case_number})"
            )
            self.app.log_history_manager.add_to_search_log(case_number)
            self.app.ui_queue.put(("function", (self.app.update_auto_search_label, case_number), {}))
            try:
                sheet_name = self.app.google_sheets_service._get_case_worksheet_name(case)
                try:
                    sheet_url = self.app.google_sheets_service.get_case_worksheet_url(case)
                except Exception:
                    sheet_url = ""
                email_manager_module.add_new_update(
                    case_number, new_data, sheet_name=sheet_name, sheet_url=sheet_url,
                )
            except Exception:
                pass
            if hasattr(self.app, "update_email_btn_text") and callable(getattr(self.app, "update_email_btn_text", None)):
                self.app.ui_queue.put(("function", (self.app.update_email_btn_text,), {}))
        if row_count and row_count is not False:
            self._verify_sheet_matches_court(
                case, result_data, case_number, sheet_count=verify_sheet_count
            )
        log_label = "재수집 완료" if reset_mode else "처리 완료"
        self.app.log_message(f"✅ {log_label}: {case_number} (소요 시간: {elapsed_time}초)")
        return self._as_process_result(1, 0, tuple_return=tuple_return)

    def _process_result_list(
        self, case, original_index, case_number, result_data, case_start_time, *, tuple_return=True
    ):
        """
        크롤링 결과 리스트 처리 (일반 저장 / 중복 제거 / 초기화·재수집).

        tuple_return=True  → (completed_delta, failed_delta)  웨이브(캡차 완료) 루프
        tuple_return=False → True | "fail"                    자동 클릭 스킵 경로
        """
        elapsed_time = int(time.time() - case_start_time)
        hearing_info = self._extract_hearing_from_result(result_data) or ""

        is_reset_mode = getattr(self.app, "is_reset_mode", False)
        if is_reset_mode:
            self.app.log_message(f"🔄 기록 초기화 및 재수집: {case_number}")

            if not self.app.google_sheets_service.overwrite_sheet_data(case, []):
                self.app.log_message(f"❌ 시트 초기화 실패: {case_number}")
                self.app.update_case_status(original_index, "초기화 실패", "red", "❌")
                return self._as_process_result(0, 1, tuple_return=tuple_return)

            self.app.history_manager.clear_last_entry(case_number)

            if not isinstance(result_data, list) or len(result_data) == 0:
                self.app.log_message(f"📭 수집 데이터 없음(초기화만 완료): {case_number}")
                self.app.update_case_status(original_index, "초기화 완료(데이터 없음)", "#7F8C8D", "📭")
                self.app.update_case_timestamp(case, original_index, 0, hearing_info=hearing_info)
                self.app.log_message(f"✅ 초기화 완료: {case_number} (소요 시간: {elapsed_time}초)")
                return self._as_process_result(1, 0, tuple_return=tuple_return)

            new_data = list(result_data)
            try:
                row_count = self.save_to_google_sheets(case, new_data)
            except Exception as save_err:
                self.app.log_message(f"❌ 구글 시트 저장 예외: {save_err}")
                row_count = False

            return self._finish_case_with_save(
                case,
                original_index,
                case_number,
                result_data,
                new_data,
                row_count,
                elapsed_time,
                hearing_info=hearing_info,
                reset_mode=True,
                tuple_return=tuple_return,
            )

        is_dedup_mode = getattr(self.app, "is_dedup_mode", False)
        if is_dedup_mode:
            res = self.app.google_sheets_service.sync_and_remove_duplicates(case, result_data)
            removed = res.get("removed", 0)

            if res.get("success"):
                if removed > 0:
                    self.app.update_case_status(original_index, f"중복 {removed}건 제거", "green", "🧹")
                else:
                    self.app.update_case_status(original_index, "중복 없음", "#7F8C8D", "✅")
            else:
                self.app.update_case_status(original_index, "제거 실패", "red", "❌")

            self.app.update_case_timestamp(case, original_index, len(result_data), hearing_info=hearing_info)
            self._maybe_sync_hearing_calendar(case, result_data)
            self.app.log_message(f"✅ 대조/중복 제거 완료: {case_number} (소요 시간: {elapsed_time}초)")
            return self._as_process_result(1, 0, tuple_return=tuple_return)

        # ── 저장 파이프라인 직렬화 ───────────────────────────────────────────
        # 구글 시트 "읽기 + 덮어쓰기 + 검증"을 '한 번에 한 사건만' 수행하도록
        # 락(_save_lock)으로 통째로 감쌉니다. 여러 사건이 동시에 시트를 두드리면
        # 1분 60회 제한을 넘겨 429(할당량 초과)가 나기 때문입니다.
        # _save_lock은 RLock(재진입 가능)이라, 이 안에서 overwrite_progress_area가
        # 같은 락을 다시 잡아도 데드락(서로 기다리다 멈춤)이 나지 않습니다.
        gs = self.app.google_sheets_service
        court_count = len(result_data) if isinstance(result_data, list) else 0
        with gs._save_lock:
            # 1) 시트를 '딱 한 번만' 읽어 스냅샷(existing_values)을 확보합니다.
            #    예전에는 신규 계산용·행수 계산용·덮어쓰기용으로 여러 번 읽어 호출이 몰렸지만,
            #    이제 한 번 읽은 값을 아래 모든 단계에서 재사용합니다.
            try:
                existing_values = gs.get_full_sheet_data(case)
            except Exception as read_err:
                self.app.log_message(
                    f"❌ 시트 조회 실패(저장 보류): {case_number} - {read_err}"
                )
                existing_values = None

            # 읽기에 실패하면 신규 건수를 추정하지 않고(+건수 폭증 오판 방지) 저장 실패로 처리.
            if existing_values is None:
                return self._finish_case_with_save(
                    case, original_index, case_number, result_data, [], False,
                    elapsed_time, hearing_info=hearing_info, tuple_return=tuple_return,
                )

            # 2) 메모리에서 신규 행·시트 행수 계산 (추가 API 호출 0번)
            new_data = self._compute_new_progress_rows(
                case, result_data, existing_values=existing_values
            )
            sheet_count = gs.count_progress_rows_from_values(existing_values)

            # 신규가 없어도 시트에 중복 등으로 행 수가 다르면 덮어쓰기로 맞춤
            needs_sync = bool(new_data) or sheet_count != court_count
            if not needs_sync:
                return self._finish_case_no_change(
                    case,
                    original_index,
                    case_number,
                    result_data,
                    elapsed_time,
                    hearing_info=hearing_info,
                    tuple_return=tuple_return,
                )
            if not new_data and sheet_count != court_count:
                self.app.log_message(
                    f"🔄 {case_number}: 신규 없음, 시트 {sheet_count}행→대법원 {court_count}행 맞춤(중복 정리)"
                )

            # 3) 대법원 진행내용 전체를 A:F 영역에 덮어써 "나의 사건검색"과 1:1로 맞춤.
            #    위에서 읽어둔 existing_values를 넘겨 시트 재읽기를 생략합니다.
            try:
                overwrite_result = gs.overwrite_progress_area(
                    case, result_data, existing_values=existing_values
                )
            except Exception as save_err:
                self.app.log_message(f"❌ 구글 시트 저장 예외: {save_err}")
                overwrite_result = False

            if overwrite_result is False or overwrite_result is None:
                row_count = False
            elif not new_data:
                # 신규는 없지만 중복·행 수 불일치만 정리된 경우 (메일·+N건 표시 없음)
                # overwrite_result(기록된 행 수)로 검증해 시트 재읽기를 생략합니다.
                self._verify_sheet_matches_court(
                    case, result_data, case_number, sheet_count=overwrite_result
                )
                self.app.update_case_status(original_index, "중복 정리 완료", "green", "✅")
                self.app.update_case_timestamp(
                    case, original_index, court_count, hearing_info=hearing_info
                )
                self._maybe_sync_hearing_calendar(case, result_data)
                self.app.log_message(
                    f"✅ 중복 정리 완료: {case_number} (시트 {sheet_count}행→{court_count}행, "
                    f"소요 시간: {elapsed_time}초)"
                )
                return self._as_process_result(1, 0, tuple_return=tuple_return)
            else:
                row_count = len(new_data)
            return self._finish_case_with_save(
                case,
                original_index,
                case_number,
                result_data,
                new_data,
                row_count,
                elapsed_time,
                hearing_info=hearing_info,
                tuple_return=tuple_return,
                verify_sheet_count=overwrite_result,
            )

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
                        self._set_manual_captcha_fallback(original_index, case_number)
                        should_cleanup_and_release = False
                        return (0, 0)

                    if isinstance(result_data, list):
                        return self._process_result_list(
                            case, original_index, case_number, result_data, case_start_time
                        )

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

    def _kill_chrome_debug_processes(self):
        """원격 디버깅 포트 사용 중인 Chrome 프로세스 종료."""
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
                self.app.log_message(f"✅ Chrome 프로세스 {chrome_killed}개 종료 완료")
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

    def _finish_captcha_batch_ui(
        self, completed, failed, total_cases, total_elapsed, selected_cases
    ):
        """캡차 배치 완료 후 진행률·완료 메시지·버튼 복구를 UI 큐에 넣음."""
        self.app.update_progress(
            100,
            f"✅ 처리 완료! (성공: {completed}, 실패: {failed}) | 총 소요 시간: {total_elapsed}초",
        )
        self.app.log_message(
            f"🎉 모든 캡차 입력 처리 완료! (총 소요 시간: {total_elapsed}초)"
        )
        self._save_run_result_for_email([c for _, c in selected_cases])
        completion_msg = (
            f"🎉 처리가 완료되었습니다!\n\n"
            f"✅ 성공: {completed}개\n"
            f"❌ 실패: {failed}개\n"
            f"📊 총 사건: {total_cases}개\n"
            f"⏱️ 총 소요 시간: {total_elapsed}초"
        )
        self.app.ui_queue.put(("function", (self.app.show_info, completion_msg), {}))
        self.app.processing = False
        if hasattr(self.app, "is_dedup_mode"):
            self.app.is_dedup_mode = False
        if hasattr(self.app, "is_reset_mode"):
            self.app.is_reset_mode = False
        self.app.ui_queue.put(("function", (self.app._set_control_btn_state, self.app.complete_btn, False), {}))

        def _restore_start():
            self.app.start_btn.configure(
                text="🖼️ 사건 조회 로드 실행\n(캡차 로드 실행)"
            )
            self.app._set_control_btn_state(self.app.start_btn, True)

        self.app.ui_queue.put(("function", (_restore_start,), {}))
        self.app.ui_queue.put(("function", (self.app._set_control_btn_state, self.app.stop_btn, False), {}))

    def _queue_restore_ui_after_captcha_batch(self):
        """캡차 배치 오류/중지 후 시작·중지 버튼 복구를 UI 큐에 넣음."""
        def _restore_start():
            self.app.start_btn.configure(
                text="🖼️ 사건 조회 로드 실행\n(캡차 로드 실행)"
            )
            self.app._set_control_btn_state(self.app.start_btn, True)

        self.app.ui_queue.put(("function", (_restore_start,), {}))
        self.app.ui_queue.put(("function", (self.app._set_control_btn_state, self.app.stop_btn, False), {}))

    def process_all_captcha_inputs(self):
        """
        모든 캡차 입력을 한번에 처리.
        '캡차 입력 완료' 버튼 클릭 시 start_processing_thread()가 이 메서드를 백그라운드 스레드에서 실행.
        GUI 갱신은 app.ui_queue를 통해 메인 스레드에 위임.
        """
        try:
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
                self.app.ui_queue.put(("function", (self.app._set_control_btn_state, self.app.complete_btn, True), {}))
            else:
                self.app.log_message("🎉 모든 사건 처리 완료!")
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
