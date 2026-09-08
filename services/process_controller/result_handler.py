# -*- coding: utf-8 -*-
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

class ResultHandlerMixin:
    """Mixin - self.app 을 통해 GUI/서비스에 접근."""

    def _compute_progress_diff(self, case, result_data, existing_values=None):
        """
        기존 시트와 대법원 result_data를 비교해 '신규 행'과 '결과만 바뀐 행'을 나눕니다.

        주니어 개발자 참고:
        - 신규(new_rows): 시트에 (일자+내용) 조합이 아예 없는 행 → 메일 '최신 업데이트 내역'
        - 결과변경(changed_rows): (일자+내용)은 같은데 '결과' 칸만 다른 행
          → 메일 '결과 변경 내역'. old_result에 시트에 있던 이전 결과를 넣습니다.
        - 4열(일자·내용·결과·공시문)이 모두 같으면 변경 없음으로 간주합니다.
        - 반환값은 메일·상태 표시에만 쓰이고, 실제 저장은 overwrite_progress_area가 담당합니다.
        """
        if not isinstance(result_data, list):
            return [], []
        gs = self.app.google_sheets_service
        if existing_values is not None:
            existing = existing_values
        else:
            try:
                existing = gs.get_full_sheet_data(case)
            except Exception as e:
                self.app.log_message(f"⚠️ 시트 조회 실패(신규·결과변경 0건으로 처리): {e}")
                return [], []

        # 4열 완전 일치용 멀티셋 (기존과 동일)
        existing_full_counts = {}
        # 일자+내용 키별 시트 '결과' 목록 (결과만 바뀐 행 찾기용)
        existing_dc_results = {}

        for row in (existing[1:] if existing else []):
            if not gs._is_progress_data_row(row):
                continue
            full_key = gs._sheet_row_dedup_key(row)
            dc_key = gs._sheet_row_dc_key(row)
            sheet_result = row[2] if len(row) > 2 else ""
            existing_full_counts[full_key] = existing_full_counts.get(full_key, 0) + 1
            existing_dc_results.setdefault(dc_key, []).append(sheet_result)

        new_rows = []
        changed_rows = []

        for progress_row in result_data:
            if not isinstance(progress_row, dict):
                continue
            full_key = gs._dict_row_dedup_key(progress_row)
            dc_key = gs._dict_row_dc_key(progress_row)
            court_result = progress_row.get("result", "")

            # 1) 4열이 모두 같으면 변경 없음
            if existing_full_counts.get(full_key, 0) > 0:
                existing_full_counts[full_key] -= 1
                # 같은 일자+내용+결과 조합을 dc 버킷에서도 하나 소비
                bucket = existing_dc_results.get(dc_key, [])
                norm_court = gs._normalize_sheet_cell(court_result)
                for i, sheet_result in enumerate(bucket):
                    if gs._normalize_sheet_cell(sheet_result) == norm_court:
                        bucket.pop(i)
                        break
                continue

            # 2) 일자+내용은 같고 결과만 다른 경우 → 결과 변경
            bucket = existing_dc_results.get(dc_key, [])
            norm_court = gs._normalize_sheet_cell(court_result)
            changed_idx = None
            old_result = ""
            for i, sheet_result in enumerate(bucket):
                if gs._normalize_sheet_cell(sheet_result) != norm_court:
                    changed_idx = i
                    old_result = sheet_result
                    break
            if changed_idx is not None:
                bucket.pop(changed_idx)
                changed_row = dict(progress_row)
                changed_row["old_result"] = old_result
                changed_rows.append(changed_row)
                continue

            # 3) 시트에 없는 행 → 신규
            new_rows.append(progress_row)

        return new_rows, changed_rows


    def _compute_new_progress_rows(self, case, result_data, existing_values=None):
        """
        기존 시트의 진행내용과 대법원 result_data를 멀티셋으로 비교해,
        새로 늘어난(시트에 없는) 행만 순서대로 반환합니다.

        주니어 개발자 참고:
        - 내부적으로 _compute_progress_diff를 호출해 new_rows만 돌려줍니다.
        - 다른 모듈에서 이 함수를 직접 부르는 경로가 있어 래퍼로 유지합니다.
        """
        new_rows, _ = self._compute_progress_diff(
            case, result_data, existing_values=existing_values
        )
        return new_rows


    def _verify_sheet_matches_court(self, case, result_data, case_number, sheet_count=None):
        """
        저장 직후 시트 진행내용 행 수가 대법원 result_data와 일치하는지 검증합니다.

        주니어 개발자 참고:
        - overwrite_progress_area가 정상 동작하면 항상 일치해야 합니다.
        - 불일치 시 로그에 경고만 남기고, 본 처리 흐름은 중단하지 않습니다.
        - sheet_count를 넘기면 시트를 다시 읽지 않습니다(API 호출 절감).
          overwrite_progress_area는 기록한 행 수를 반환하므로 그 값을 그대로 쓰면 됩니다.
        - 2026-08-12 사고: 대법원 0건을 정상으로 보고 "0행 일치" 초록 로그가 나와
          데이터 삭제를 성공처럼 보이게 했습니다. 0건은 성공으로 표시하지 않습니다.
        """
        gs = self.app.google_sheets_service
        try:
            if sheet_count is None:
                sheet_count = gs.count_progress_rows(case)
            court_count = len(result_data) if isinstance(result_data, list) else 0
            if court_count == 0 and sheet_count > 0:
                self.app.log_message(
                    f"🛑 검증: {case_number} 대법원 0건 · 시트 {sheet_count}행 "
                    f"- 일치로 보고하지 않음(조회 실패 의심)"
                )
                return False
            if sheet_count != court_count:
                self.app.log_message(
                    f"⚠️ 검증: {case_number} 시트 {sheet_count}행 vs 대법원 {court_count}행 불일치"
                )
                return False
            if court_count == 0:
                self.app.log_message(
                    f"ℹ️ 검증: {case_number} 시트·대법원 진행내용 0행 "
                    f"(빈 결과, 성공으로 표시하지 않음)"
                )
                return True
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


    def _as_process_result(self, completed_delta, failed_delta, *, tuple_return=True):
        """
        처리 결과를 호출 경로에 맞는 형식으로 변환합니다.

        tuple_return=True  → (completed_delta, failed_delta)  (웨이브/캡차 완료 루프)
        tuple_return=False → True | "fail"                    (자동 클릭 스킵 경로)
        """
        if tuple_return:
            return (completed_delta, failed_delta)
        return "fail" if failed_delta else True


    def _finish_case_failed(
        self, original_index, case_number, elapsed_time, reason, *, tuple_return=True
    ):
        """
        조회/저장 실패로 사건을 끝냅니다. 시트는 절대 건드리지 않습니다.

        주니어 참고 (2026-08-12 사고):
        - 대법원 0건을 "정상"으로 저장하면 기존 진행내용이 통째로 지워집니다.
        - 이 함수는 실패 상태만 남기고, 재시도 대상(failed_delta=1)으로 돌려줍니다.
        """
        self.app.update_case_status(original_index, "조회 실패(보호)", "red", "🛑")
        self.app.log_message(
            f"❌ {reason}: {case_number} (소요 시간: {elapsed_time}초)"
        )
        return self._as_process_result(0, 1, tuple_return=tuple_return)


    def _log_delayed_registrations(self, case_number, new_data):
        """
        신규 행 중 영업일 지연 등록이 있으면 앱 로그에 남깁니다.
        시트 비고에 쓰는 것과 같은 delay_business_days 계산을 사용합니다.
        """
        if not isinstance(new_data, list) or not new_data:
            return
        try:
            from services.date_utils import delay_business_days

            min_days = int(getattr(config, "DELAY_REMARK_MIN_BUSINESS_DAYS", 1))
            delayed = []
            for row in new_data:
                if not isinstance(row, dict):
                    continue
                delay = delay_business_days(row.get("date", ""))
                if delay is None or delay < min_days:
                    continue
                content = re.sub(r"\s+", " ", (row.get("content") or "").strip())
                if len(content) > 40:
                    content = content[:40] + "..."
                delayed.append((row.get("date", ""), delay, content))
            if not delayed:
                return
            self.app.log_message(
                f"⏱️ 지연 등록 {len(delayed)}건: {case_number}"
            )
            for date_s, delay, content in delayed:
                self.app.log_message(
                    f"   └ {date_s} ({delay}일, 영업일) {content}"
                )
        except Exception as e:
            self.app.log_message(f"⚠️ 지연 등록 로그 생략: {e}")


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
        hearing_events = self._extract_hearing_events_from_result(result_data)
        self.app.update_case_timestamp(
            case,
            original_index,
            new_total,
            hearing_info=hearing_info,
            hearing_events=hearing_events,
        )
        self._maybe_sync_hearing_calendar(case, result_data)
        # 진행내용은 안 바뀌어도 '최근 조회 일시'는 남김
        try:
            self.app.google_sheets_service.touch_last_query_time(case)
        except Exception as e:
            self.app.log_message(f"⚠️ 최근 조회 일시 갱신 생략: {e}")
        self.app.log_message(f"✅ 처리 완료: {case_number} (소요 시간: {elapsed_time}초)")
        return self._as_process_result(1, 0, tuple_return=tuple_return)


    def _finish_case_result_changed(
        self,
        case,
        original_index,
        case_number,
        result_data,
        changed_data,
        elapsed_time,
        hearing_info=None,
        *,
        tuple_return=True,
        verify_sheet_count=None,
    ):
        """
        신규 행은 없고 송달 '결과' 칸만 바뀐 경우 마무리 처리.

        주니어 개발자 참고:
        - 상태 라벨에 '변경없음' 글자를 넣지 않습니다(메일 분류 오류 방지).
        - 메일에는 '결과 변경 내역' 섹션으로 따로 기록합니다.
        """
        changed_count = len(changed_data) if changed_data else 0
        status_label = f"완료 (결과변경 {changed_count}건)"
        self.app.update_case_status(original_index, status_label, "green", "🔁")

        hearing_events = self._extract_hearing_events_from_result(result_data)
        history = self.app.load_update_history()
        old_total = (
            history.get(case_number, {}).get("row_count", 0)
            if isinstance(history.get(case_number), dict)
            else 0
        )
        self.app.update_case_timestamp(
            case,
            original_index,
            old_total,
            hearing_info=hearing_info,
            hearing_events=hearing_events,
        )
        self._maybe_sync_hearing_calendar(case, result_data)

        self.app.log_message(f"🔁 결과 변경 {changed_count}건: {case_number}")
        for row in changed_data or []:
            if not isinstance(row, dict):
                continue
            date_s = row.get("date", "")
            content_s = row.get("content", "")
            old_r = row.get("old_result", "")
            new_r = row.get("result", "")
            self.app.log_message(f"   {date_s} {content_s} [{old_r} → {new_r}]")

        try:
            self.app.google_sheets_service.touch_last_query_time(case)
        except Exception as e:
            self.app.log_message(f"⚠️ 최근 조회 일시 갱신 생략: {e}")

        if changed_count > 0:
            self.app.log_history_manager.add_to_search_log(case_number)
            self.app.ui_queue.put(("function", (self.app.update_auto_search_label, case_number), {}))
            try:
                sheet_name = self.app.google_sheets_service._get_case_worksheet_name(case)
                try:
                    sheet_url = self.app.google_sheets_service.get_case_worksheet_url(case)
                except Exception:
                    sheet_url = ""
                email_manager_module.add_result_changes(
                    case_number,
                    changed_data,
                    sheet_name=sheet_name,
                    sheet_url=sheet_url,
                )
            except Exception:
                pass
            if hasattr(self.app, "update_email_btn_text") and callable(
                getattr(self.app, "update_email_btn_text", None)
            ):
                self.app.ui_queue.put(("function", (self.app.update_email_btn_text,), {}))

        if verify_sheet_count is not None:
            self._verify_sheet_matches_court(
                case, result_data, case_number, sheet_count=verify_sheet_count
            )

        self.app.log_message(
            f"처리 완료: {case_number} (결과변경 {changed_count}건, 소요 시간: {elapsed_time}초)"
        )
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
        changed_data=None,
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
        hearing_events = self._extract_hearing_events_from_result(result_data)
        self.app.update_case_timestamp(
            case,
            original_index,
            total_rows,
            hearing_info=hearing_info,
            hearing_events=hearing_events,
        )
        self._maybe_sync_hearing_calendar(case, result_data)
        if row_count > 0:
            update_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.app.log_message(
                f"📊 이번 조회 신규 {row_count}건 추가, 업데이트 시각 {update_ts} ({case_number})"
            )
            self._log_delayed_registrations(case_number, new_data)
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
                if changed_data:
                    email_manager_module.add_result_changes(
                        case_number,
                        changed_data,
                        sheet_name=sheet_name,
                        sheet_url=sheet_url,
                    )
            except Exception:
                pass
            if hasattr(self.app, "update_email_btn_text") and callable(getattr(self.app, "update_email_btn_text", None)):
                self.app.ui_queue.put(("function", (self.app.update_email_btn_text,), {}))
        elif changed_data:
            # 신규는 없고 결과만 바뀐 경우(동시에 신규+결과변경이면 위 블록에서 함께 기록)
            try:
                sheet_name = self.app.google_sheets_service._get_case_worksheet_name(case)
                try:
                    sheet_url = self.app.google_sheets_service.get_case_worksheet_url(case)
                except Exception:
                    sheet_url = ""
                email_manager_module.add_result_changes(
                    case_number,
                    changed_data,
                    sheet_name=sheet_name,
                    sheet_url=sheet_url,
                )
            except Exception:
                pass
            if hasattr(self.app, "update_email_btn_text") and callable(
                getattr(self.app, "update_email_btn_text", None)
            ):
                self.app.ui_queue.put(("function", (self.app.update_email_btn_text,), {}))
        if row_count and row_count is not False:
            self._verify_sheet_matches_court(
                case, result_data, case_number, sheet_count=verify_sheet_count
            )
        log_label = "재수집 완료" if reset_mode else "처리 완료"
        self.app.log_message(f"{log_label}: {case_number} (소요 시간: {elapsed_time}초)")
        return self._as_process_result(1, 0, tuple_return=tuple_return)


    def _finish_period_query_case(
        self, case, original_index, case_number, result_data, elapsed_time, *, tuple_return=True
    ):
        """기간 조회: 기간 내 행만 메모리 저장. 진행내용은 안 덮고 최근 조회 일시만 갱신."""
        from services.date_utils import in_period

        period = getattr(self.app, "period_range", None)
        if not period:
            self.app.log_message(f"기간 미설정: {case_number}")
            self.app.update_case_status(original_index, "기간 미설정", "red", "")
            return self._as_process_result(0, 1, tuple_return=tuple_return)
        start, end = period
        rows = []
        if isinstance(result_data, list):
            for r in result_data:
                if isinstance(r, dict) and in_period(r.get("date", ""), start, end):
                    rows.append(r)

        # 시트 존재 여부 주석(메일/미리보기용)
        try:
            from services import sheet_compare as sheet_compare_mod

            all_values = sheet_compare_mod.fetch_sheet_values(
                self.app.google_sheets_service, case
            )
            rows, _counts = sheet_compare_mod.annotate_rows_with_sheet_presence(
                rows, all_values
            )
        except Exception as e:
            self.app.log_message(f"시트 존재 대조 생략({case_number}): {e}")

        sheet_url = ""
        try:
            sheet_url = self.app.google_sheets_service.get_case_worksheet_url(case)
        except Exception:
            pass

        if not hasattr(self.app, "period_results") or self.app.period_results is None:
            self.app.period_results = {}
        self.app.period_results[case_number] = {
            "case": case,
            "rows": rows,
            "sheet_url": sheet_url,
        }
        # 상태칸: 기간을 보이게 (건수는 로그에만)
        try:
            from services.date_utils import format_date_yy

            period_label = f"{format_date_yy(start)} ~ {format_date_yy(end)}"
        except Exception:
            period_label = f"{start} ~ {end}"
        self.app.update_case_status(
            original_index,
            f"기간조회 완료({period_label})",
            "green",
            "",
        )
        try:
            self.app.google_sheets_service.touch_last_query_time(case)
        except Exception as e:
            self.app.log_message(f"⚠️ 최근 조회 일시 갱신 생략: {e}")
        self.app.log_message(
            f"기간조회 완료: {case_number} {len(rows)}건 (소요 {elapsed_time}초)"
        )
        return self._as_process_result(1, 0, tuple_return=tuple_return)


    def _finish_compare_case(
        self, case, original_index, case_number, result_data, elapsed_time, *, tuple_return=True
    ):
        """시트-대법원 대조: 시트에 쓰지 않고 diff 만 보관."""
        from services import sheet_compare as sheet_compare_mod

        court_rows = list(result_data) if isinstance(result_data, list) else []
        all_values = sheet_compare_mod.fetch_sheet_values(
            self.app.google_sheets_service, case
        )
        diff = sheet_compare_mod.compare_court_and_sheet(court_rows, all_values)
        sheet_url = ""
        try:
            sheet_url = self.app.google_sheets_service.get_case_worksheet_url(case)
        except Exception:
            pass

        if not hasattr(self.app, "compare_results") or self.app.compare_results is None:
            self.app.compare_results = {}
        self.app.compare_results[case_number] = {
            "case": case,
            "diff": diff,
            "sheet_url": sheet_url,
        }
        verdict = diff.get("verdict", "")
        self.app.update_case_status(original_index, f"대조 {verdict}", "green", "")
        try:
            self.app.google_sheets_service.touch_last_query_time(case)
        except Exception as e:
            self.app.log_message(f"⚠️ 최근 조회 일시 갱신 생략: {e}")
        self.app.log_message(
            f"시트 대조: {case_number} {verdict} (소요 {elapsed_time}초)"
        )
        return self._as_process_result(1, 0, tuple_return=tuple_return)


    def _show_special_mode_report(self):
        """기간 조회 / 시트 대조 완료 후 미리보기 창을 메인 스레드에서 연다."""
        is_period = getattr(self.app, "is_period_mode", False)
        is_compare = getattr(self.app, "is_compare_mode", False)
        period_results = getattr(self.app, "period_results", None)
        compare_results = getattr(self.app, "compare_results", None)
        period_range = getattr(self.app, "period_range", None)

        def _open():
            try:
                from gui.dialogs.report_preview_dialog import ReportPreviewDialog
                from services import period_report as period_report_mod
                from services.date_utils import format_date

                if is_period and period_range is not None:
                    results = period_results or {}
                    start, end = period_range
                    presence = {"있음": 0, "유사": 0, "없음": 0}
                    for payload in results.values():
                        for r in payload.get("rows") or []:
                            p = r.get("sheet_presence")
                            if p in presence:
                                presence[p] += 1
                    html = period_report_mod.render_period_html(
                        results, start, end, presence_summary=presence
                    )
                    md = period_report_mod.render_period_markdown(
                        results, start, end, presence_summary=presence
                    )
                    ReportPreviewDialog(
                        self.app.root,
                        title=f"기간 조회 {format_date(start)} ~ {format_date(end)}",
                        html_text=html,
                        markdown_text=md,
                        mail_subject_hint=f"[기간 조회] {format_date(start)} ~ {format_date(end)}",
                        app=self.app,
                    )
                    return

                if is_compare:
                    results = compare_results or {}
                    html = period_report_mod.render_compare_html(results)
                    md = period_report_mod.render_compare_markdown(results)
                    ReportPreviewDialog(
                        self.app.root,
                        title="시트-대법원 대조 결과",
                        html_text=html,
                        markdown_text=md,
                        mail_subject_hint="[시트 대조]",
                        app=self.app,
                    )
            except Exception as e:
                self.app.log_message(f"리포트 미리보기 오류: {e}")
                try:
                    self.app.show_warning(f"리포트 미리보기 오류: {e}")
                except Exception:
                    pass

        self.app.ui_queue.put(("function", (_open,), {}))


    def _process_result_list(
        self, case, original_index, case_number, result_data, case_start_time, *, tuple_return=True
    ):
        """
        크롤링 결과 리스트 처리 (일반 저장 / 중복 제거 / 초기화·재수집 / 기간조회 / 시트대조).

        tuple_return=True  → (completed_delta, failed_delta)  웨이브(캡차 완료) 루프
        tuple_return=False → True | "fail"                    자동 클릭 스킵 경로
        """
        elapsed_time = int(time.time() - case_start_time)
        hearing_info = self._extract_hearing_from_result(result_data) or ""

        # 제출 성공 캡차 → 학습 데이터셋에 정답으로 기록
        try:
            from services import captcha_dataset as captcha_dataset_module

            captcha_val = ""
            try:
                captcha_val = (self.app.get_captcha_input(original_index) or "").strip()
            except Exception:
                captcha_val = ""
            if captcha_val and captcha_val != "CLICK" and len(captcha_val) == 6:
                paths = getattr(self.app, "case_captcha_image_paths", {}) or {}
                img = paths.get(original_index) or ""
                meta = getattr(self.app, "_ocr_meta", {}).get(case_number) or {}
                if not img:
                    img = meta.get("image_path") or ""
                source = "ocr" if meta.get("guess") == captcha_val else "manual"
                captcha_dataset_module.record_sample(
                    img,
                    captcha_val,
                    source=source,
                    ocr_guess=meta.get("guess"),
                    ocr_confidence=meta.get("confidence"),
                    ocr_engine=meta.get("engine"),
                    is_correct=True,
                )
        except Exception:
            pass

        # --- 특정 기간 조회: 시트/이력에 쓰지 않고 기간 행만 메모리에 보관 ---
        if getattr(self.app, "is_period_mode", False):
            return self._finish_period_query_case(
                case,
                original_index,
                case_number,
                result_data,
                elapsed_time,
                tuple_return=tuple_return,
            )

        # --- 시트-대법원 대조: 시트 읽기만 하고 쓰지 않음 ---
        if getattr(self.app, "is_compare_mode", False):
            return self._finish_compare_case(
                case,
                original_index,
                case_number,
                result_data,
                elapsed_time,
                tuple_return=tuple_return,
            )

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
                self.app.update_case_timestamp(
                    case,
                    original_index,
                    0,
                    hearing_info=hearing_info,
                    hearing_events=self._extract_hearing_events_from_result(result_data),
                )
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

            self.app.update_case_timestamp(
                case,
                original_index,
                len(result_data),
                hearing_info=hearing_info,
                hearing_events=self._extract_hearing_events_from_result(result_data),
            )
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

            # 2) 메모리에서 신규 행·결과변경 행·시트 행수 계산 (추가 API 호출 0번)
            new_data, changed_data = self._compute_progress_diff(
                case, result_data, existing_values=existing_values
            )
            sheet_count = gs.count_progress_rows_from_values(existing_values)

            # 2026-08-12 사고 재발 방지 (99.Error case/ERROR_20260812_sheet_progress_wipe.md):
            # 대법원 결과가 0건인데 시트에는 기존 진행내용이 있으면
            # "정상 0건"이 아니라 "조회 실패"로 간주하고 덮어쓰지 않습니다.
            if court_count == 0 and sheet_count > 0:
                self.app.log_message(
                    f"🛑 보호: {case_number} 대법원 0건 · 시트 {sheet_count}행 "
                    f"- 덮어쓰기 중단(조회 실패로 간주)"
                )
                return self._finish_case_failed(
                    original_index,
                    case_number,
                    elapsed_time,
                    "조회 실패(0건 위장 차단)",
                    tuple_return=tuple_return,
                )

            # 신규·결과변경이 없어도 시트에 중복 등으로 행 수가 다르면 덮어쓰기로 맞춤
            needs_sync = bool(new_data) or bool(changed_data) or sheet_count != court_count
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
                return self._finish_case_with_save(
                    case,
                    original_index,
                    case_number,
                    result_data,
                    new_data,
                    row_count,
                    elapsed_time,
                    hearing_info=hearing_info,
                    changed_data=changed_data,
                    tuple_return=tuple_return,
                    verify_sheet_count=overwrite_result,
                )
            if new_data:
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
                    changed_data=changed_data,
                    tuple_return=tuple_return,
                    verify_sheet_count=overwrite_result,
                )
            if changed_data:
                return self._finish_case_result_changed(
                    case,
                    original_index,
                    case_number,
                    result_data,
                    changed_data,
                    elapsed_time,
                    hearing_info=hearing_info,
                    tuple_return=tuple_return,
                    verify_sheet_count=overwrite_result,
                )
            # 신규·결과변경 없이 중복·행 수 불일치만 정리된 경우
            self._verify_sheet_matches_court(
                case, result_data, case_number, sheet_count=overwrite_result
            )
            self.app.update_case_status(original_index, "중복 정리 완료", "green", "✅")
            self.app.update_case_timestamp(
                case,
                original_index,
                court_count,
                hearing_info=hearing_info,
                hearing_events=self._extract_hearing_events_from_result(result_data),
            )
            self._maybe_sync_hearing_calendar(case, result_data)
            self.app.log_message(
                f"✅ 중복 정리 완료: {case_number} (시트 {sheet_count}행→{court_count}행, "
                f"소요 시간: {elapsed_time}초)"
            )
            return self._as_process_result(1, 0, tuple_return=tuple_return)

