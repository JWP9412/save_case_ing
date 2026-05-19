"""
구글 시트 서비스 모듈
====================

구글 시트와의 모든 상호작용을 담당하는 모듈입니다.

주요 기능:
- 구글 시트에서 사건 목록 로드
- 크롤링 결과를 구글 시트에 저장
- 텍스트 색상 적용
- 열 너비 자동 조정

사용법:
    from services.google_sheets import GoogleSheetsService

    service = GoogleSheetsService()
    cases = service.load_case_list()
    service.save_progress_data(case, result_data)
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import json
import time
import functools
import threading
import config
from services.logger_service import get_logger
from services import google_oauth

logger = get_logger("google_sheets")


def _a1_end_column_letter(num_cols: int) -> str:
    """
    열 개수(1=A만, 6=A~F)에 맞는 A1 표기의 마지막 열 글자를 반환합니다.

    주니어 개발자 참고:
    - Google Sheets의 `append_rows`는 시트 안의 '표' 범위를 추정해 빈 칸을 찾기 때문에,
      오른쪽 열에 값이 있으면 새 행이 A열이 아니라 G열 등으로 밀릴 수 있습니다.
    - 그래서 `update("A10:F56", values)`처럼 범위를 명시하면 항상 A열부터 기록됩니다.
    """
    if num_cols < 1:
        raise ValueError("num_cols는 1 이상이어야 합니다.")
    n = num_cols
    parts = []
    while n > 0:
        n, rem = divmod(n - 1, 26)
        parts.append(chr(65 + rem))
    return "".join(reversed(parts))


def retry_on_quota_error(max_retries=5, base_delay=2.0):
    """
    429 (Quota Exceeded) 발생 시 지수 백오프로 재시도하는 데코레이터.
    대기 시간: base_delay * (2 ** attempt) 초 (2, 4, 8, 16, 32초).
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except gspread.exceptions.APIError as e:
                    last_exc = e
                    msg = str(e).lower()
                    if "429" not in msg and "quota" not in msg:
                        raise
                    if attempt < max_retries - 1:
                        delay = base_delay * (2**attempt)
                        logger.warning(
                            "⚠️ 구글 시트 할당량 초과(429). %s초 후 재시도 (%s/%s)",
                            delay,
                            attempt + 1,
                            max_retries,
                        )
                        time.sleep(delay)
                    else:
                        raise
            if last_exc:
                raise last_exc

        return wrapper

    return decorator


class GoogleSheetsService:
    """
    구글 시트 서비스 클래스

    구글 시트와의 모든 통신을 담당합니다.
    """

    def __init__(self, log_callback=None):
        """
        초기화

        매개변수:
            log_callback: (미사용, 하위 호환용)
        """
        self._client = None
        self._spreadsheet = None
        # 저장 직렬화용 락 (429 할당량 초과 방지: 동시 쓰기 제한)
        self._save_lock = threading.Lock()

    def _log(self, message):
        """로그 메시지 출력 (표준 로거 사용)"""
        logger.info(message)

    def _get_client(self):
        """
        구글 시트 클라이언트 가져오기 (싱글톤 패턴)

        반환값:
            gspread.Client 객체
        """
        if self._client is None:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = None
            auth_mode = str(getattr(config, "GOOGLE_AUTH_MODE", "oauth")).strip().lower()
            if auth_mode != "service_account":
                creds = google_oauth.get_credentials(
                    scopes=scope,
                    interactive=False,
                    log_callback=self._log,
                )
                if creds is not None:
                    self._log("✅ Google OAuth 사용자 인증으로 시트 연결")
            if creds is None:
                # OAuth 토큰이 없거나 service_account 모드면 서비스 계정으로 폴백
                creds = Credentials.from_service_account_file(
                    config.GOOGLE_AUTH_FILE, scopes=scope
                )
                self._log("✅ 서비스 계정 인증으로 시트 연결")
            self._client = gspread.authorize(creds)
            self._log("✅ 구글 시트 클라이언트 생성 완료")

        return self._client

    def _get_spreadsheet(self):
        """
        스프레드시트 객체 가져오기 (싱글톤 패턴)

        반환값:
            gspread.Spreadsheet 객체
        """
        if self._spreadsheet is None:
            client = self._get_client()
            # 스프레드시트 열기 (ID로)
            self._spreadsheet = client.open_by_key(config.GOOGLE_SHEET_ID)
            self._log(f"✅ 스프레드시트 열기 완료: {self._spreadsheet.title}")

        return self._spreadsheet

    def load_case_list(self):
        """
        구글 시트에서 사건 목록을 로드하는 함수

        이 함수는:
        1. 구글 시트에 연결합니다 (인증 파일 사용)
        2. "사건 목록" 워크시트를 찾습니다
        3. 모든 사건 데이터를 읽어옵니다
        4. 사건번호가 있는 행만 필터링합니다

        반환값:
            filtered_data: 사건번호가 있는 사건 데이터 리스트
            실패 시: None
        """
        try:
            # 1단계: 구글 시트 연결 (OAuth 우선, 없으면 서비스 계정)
            spreadsheet = self._get_spreadsheet()
            self._log(f"[INFO] 구글 시트 연결 성공: {spreadsheet.title}")

            # ============================================================
            # 3단계: "사건 목록" 워크시트 찾기
            # ============================================================
            worksheets = spreadsheet.worksheets()
            data_worksheet = None

            for ws in worksheets:
                if config.CASE_LIST_WORKSHEET_NAME in ws.title:
                    data_worksheet = ws
                    break

            # "사건 목록"이 없으면 첫 번째 워크시트 사용
            if not data_worksheet and worksheets:
                data_worksheet = worksheets[0]

            if not data_worksheet:
                self._log("[ERROR] 워크시트를 찾을 수 없습니다")
                return None

            self._log(f"[INFO] 데이터 워크시트 선택: {data_worksheet.title}")

            # ============================================================
            # 4단계: 모든 데이터 읽기 (헤더 중복 문제 해결)
            # ============================================================
            try:
                all_data = data_worksheet.get_all_records()
            except Exception as header_error:
                self._log(f"[WARNING] 헤더 중복 오류: {header_error}")
                # 수동으로 헤더 설정하여 데이터 읽기
                all_values = data_worksheet.get_all_values()
                if len(all_values) > 1:
                    # 첫 번째 행을 헤더로 사용하고, 빈 컬럼명 처리
                    headers = all_values[0]
                    # 빈 헤더를 '비고'로 변경
                    for i, header in enumerate(headers):
                        if not header or header.strip() == "":
                            headers[i] = f"비고_{i}"

                    # 데이터 행들 처리
                    data_rows = all_values[1:]
                    all_data = []
                    for row in data_rows:
                        if len(row) >= len(headers):  # 충분한 컬럼이 있는 경우만
                            row_dict = {}
                            for i, header in enumerate(headers):
                                if i < len(row):
                                    row_dict[header] = row[i]
                            all_data.append(row_dict)
                else:
                    all_data = []

            # ============================================================
            # 5단계: 빈 행 필터링 (사건번호가 비어있는 행 제외)
            # ============================================================
            filtered_data = []
            for row in all_data:
                raw = row.get("사건번호", "")
                case_number = (str(raw).strip() if raw is not None else "")
                if case_number:  # 사건번호가 있는 경우만 추가
                    filtered_data.append(row)

            self._log(
                f"[INFO] {len(all_data)}개 행 중 {len(filtered_data)}개 유효한 데이터 로드 완료"
            )

            return filtered_data

        except Exception as e:
            self._log(f"[ERROR] 구글 시트 데이터 로드 실패: {e}")
            self._log(f"[ERROR] 오류 타입: {type(e).__name__}")
            import traceback

            self._log(f"[ERROR] 상세 오류: {traceback.format_exc()}")
            return None

    def _get_or_create_case_worksheet(self, spreadsheet, case):
        """사건용 워크시트를 조회하거나 없으면 생성. 반환: gspread.Worksheet."""
        worksheet_name = self._get_case_worksheet_name(case)
        try:
            return spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            return spreadsheet.add_worksheet(
                title=worksheet_name, rows=100, cols=10
            )

    def _ensure_headers_and_remove_timestamp_rows(self, worksheet, num_cols=6):
        """헤더가 있도록 보장하고, 맨 아래 '업데이트 일시'/'최근 과거 업데이트' 행 제거."""
        all_values = worksheet.get_all_values()
        if len(all_values) == 0:
            headers = [
                "일자", "내용", "결과", "공시문", "비고", "이메일 송부 여부",
            ]
            worksheet.append_row(headers)
        else:
            row1 = all_values[0]
            if len(row1) < num_cols:
                extended = (row1 + ["", ""])[:num_cols]
                extended[4] = extended[4] or "비고"
                extended[5] = extended[5] or "이메일 송부 여부"
                worksheet.update("A1:F1", [extended], value_input_option="USER_ENTERED")
        all_values = worksheet.get_all_values()
        rows_to_delete = []
        for i in range(len(all_values) - 1, -1, -1):
            if len(all_values[i]) > 0 and str(all_values[i][0]).strip() in (
                "업데이트 일시",
                "최근 과거 업데이트",
            ):
                rows_to_delete.append(i + 1)
        for row_1based in sorted(rows_to_delete, reverse=True):
            worksheet.delete_rows(row_1based)

    def _build_result_rows_and_color_info(self, result_data, start_row_1based):
        """저장할 행 리스트와 색상 정보 리스트 생성. 반환: (processed_new_data, color_info)."""
        today_str = datetime.now().strftime("%Y.%m.%d")
        processed_new_data = []
        color_info = []
        for idx, progress_row in enumerate(result_data):
            row_list = [
                progress_row.get("date", ""),
                progress_row.get("content", ""),
                progress_row.get("result", ""),
                progress_row.get("document", ""),
                f"{today_str}. 업데이트 됨",
                "X",
            ]
            processed_new_data.append(row_list)
            color_info.append({
                "row": start_row_1based + idx,
                "dateColor": progress_row.get("dateColor"),
                "contentColor": progress_row.get("contentColor"),
                "resultColor": progress_row.get("resultColor"),
                "documentColor": progress_row.get("documentColor"),
            })
        return processed_new_data, color_info

    def _append_empty_and_timestamp_rows(
        self, worksheet, start_row_1based, num_cols=6
    ):
        """
        빈 행과 '업데이트 일시' 행을 지정 행부터 A열 기준으로 기록합니다.

        주니어 개발자 참고:
        append_rows 대신 update를 쓰는 이유는 save_progress_data와 동일하게
        열 밀림(우측 열에 붙는 현상)을 막기 위함입니다.
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        empty_rows = [[""] * num_cols for _ in range(config.EMPTY_ROWS_BEFORE_UPDATE)]
        rows_to_write = empty_rows + [
            ["업데이트 일시", current_time, "", "", "", ""][:num_cols]
        ]
        end_col = _a1_end_column_letter(num_cols)
        end_row = start_row_1based + len(rows_to_write) - 1
        range_a1 = f"A{start_row_1based}:{end_col}{end_row}"
        worksheet.update(
            range_a1, rows_to_write, value_input_option="USER_ENTERED"
        )

    @retry_on_quota_error(max_retries=5, base_delay=2.0)
    def save_progress_data(self, case, result_data, log_callback=None):
        """
        구글 시트에 진행내용 데이터를 저장합니다.
        Puppeteer로 크롤링한 진행내용 데이터를 구글 시트에 저장합니다.

        매개변수:
            case: 사건 정보 딕셔너리 (사건번호, 피고, 법원, 비고 등)
            result_data: 크롤링한 진행내용 데이터 리스트
            log_callback: (미사용, 하위 호환용)

        반환값:
            저장된 행 개수 (int) 또는 False (실패 시)
        """
        if result_data is True:
            result_data = []

        with self._save_lock:
            try:
                case_number = case.get("사건번호", "")
                self._log(f"💾 [DEBUG] save_progress_data 시작: {case_number}")

                if not isinstance(result_data, list) or len(result_data) == 0:
                    self._log("💾 [DEBUG] 저장할 신규 데이터 없음")
                    return False

                spreadsheet = self._get_spreadsheet()
                worksheet = self._get_or_create_case_worksheet(spreadsheet, case)
                worksheet_name = worksheet.title

                self._ensure_headers_and_remove_timestamp_rows(worksheet, num_cols=6)

                start_row_1based = len(worksheet.get_all_values()) + 1
                processed_new_data, color_info = self._build_result_rows_and_color_info(
                    result_data, start_row_1based
                )
                n_new = len(processed_new_data)
                # 타임스탬프 행 = 데이터 직후 빈 행(EMPTY_ROWS_BEFORE_UPDATE) 다음 한 줄
                timestamp_row_1based = (
                    start_row_1based
                    + n_new
                    + config.EMPTY_ROWS_BEFORE_UPDATE
                )
                self._ensure_worksheet_rows(worksheet, timestamp_row_1based + 2)

                end_col = _a1_end_column_letter(6)
                end_data_row = start_row_1based + n_new - 1
                data_range = f"A{start_row_1based}:{end_col}{end_data_row}"
                worksheet.update(
                    data_range,
                    processed_new_data,
                    value_input_option="USER_ENTERED",
                )

                self._apply_text_colors(worksheet, color_info)
                after_data_row = start_row_1based + n_new
                self._append_empty_and_timestamp_rows(
                    worksheet, after_data_row, num_cols=6
                )
                current_row = timestamp_row_1based
                self._format_update_timestamp_rows(worksheet, current_row, num_cols=6)
                self._auto_resize_columns(worksheet, num_cols=6)

                self._log(
                    f"✅ 구글 시트 저장 완료: {worksheet_name} (+{len(processed_new_data)}건)"
                )
                return len(processed_new_data)

            except gspread.exceptions.APIError:
                raise
            except Exception as e:
                self._log(f"❌ 구글 시트 저장 실패: {e}")
                import traceback
                self._log(traceback.format_exc())
                return False

    def _apply_text_colors(self, worksheet, color_info):
        """
        텍스트 색상 적용 (내부 함수)

        매개변수:
            worksheet: gspread.Worksheet 객체
            color_info: 색상 정보 리스트
                예: [
                    {'row': 2, 'dateColor': 'rgb(255,0,0)', ...},
                    ...
                ]
        """
        try:
            requests = []

            for info in color_info:
                row_idx = info["row"]

                # RGB 색상 변환 함수
                def rgb_to_google_color(rgb_string):
                    if not rgb_string or not rgb_string.startswith("rgb"):
                        return None
                    # "rgb(255, 0, 0)" -> [255, 0, 0]
                    rgb = rgb_string.replace("rgb(", "").replace(")", "").split(",")
                    r, g, b = [int(x.strip()) / 255.0 for x in rgb]
                    return {"red": r, "green": g, "blue": b}

                # 각 셀에 색상 적용
                for col_idx, color_key in enumerate(
                    ["dateColor", "contentColor", "resultColor", "documentColor"]
                ):
                    color_rgb = info.get(color_key)
                    if color_rgb:
                        google_color = rgb_to_google_color(color_rgb)
                        if google_color:
                            requests.append(
                                {
                                    "repeatCell": {
                                        "range": {
                                            "sheetId": worksheet.id,
                                            "startRowIndex": row_idx - 1,
                                            "endRowIndex": row_idx,
                                            "startColumnIndex": col_idx,
                                            "endColumnIndex": col_idx + 1,
                                        },
                                        "cell": {
                                            "userEnteredFormat": {
                                                "textFormat": {
                                                    "foregroundColor": google_color
                                                }
                                            }
                                        },
                                        "fields": "userEnteredFormat.textFormat.foregroundColor",
                                    }
                                }
                            )

            # 색상 일괄 적용
            if requests:
                body = {"requests": requests}
                worksheet.spreadsheet.batch_update(body)

        except Exception as e:
            self._log(f"⚠️ 색상 적용 실패: {e}")

    def _ensure_worksheet_rows(self, worksheet, min_rows):
        """
        워크시트 그리드 행 수가 min_rows 이상이 되도록 확장 (내부 함수).
        repeatCell 등이 'exceeds grid limits' 되지 않도록 호출한다.
        """
        try:
            current = worksheet.row_count
            if current < min_rows:
                worksheet.spreadsheet.batch_update(
                    {
                        "requests": [
                            {
                                "updateSheetProperties": {
                                    "properties": {
                                        "sheetId": worksheet.id,
                                        "gridProperties": {"rowCount": min_rows},
                                    },
                                    "fields": "gridProperties.rowCount",
                                }
                            }
                        ]
                    }
                )
        except Exception as e:
            self._log(f"⚠️ 그리드 행 수 확장 실패(무시): {e}")

    def _format_update_timestamp_rows(self, worksheet, start_row, num_cols=4):
        """
        업데이트 일시 행 포맷팅 (좌측 정렬) (내부 함수)

        매개변수:
            worksheet: gspread.Worksheet 객체
            start_row: 시작 행 번호 (1부터 시작)
            num_cols: 포맷 적용할 열 개수 (기본 4, 증분 저장 시 6)
        """
        try:
            requests = []
            for i in range(2):
                requests.append(
                    {
                        "repeatCell": {
                            "range": {
                                "sheetId": worksheet.id,
                                "startRowIndex": start_row + i - 1,
                                "endRowIndex": start_row + i,
                                "startColumnIndex": 0,
                                "endColumnIndex": num_cols,
                            },
                            "cell": {
                                "userEnteredFormat": {"horizontalAlignment": "LEFT"}
                            },
                            "fields": "userEnteredFormat.horizontalAlignment",
                        }
                    }
                )
            body = {"requests": requests}
            worksheet.spreadsheet.batch_update(body)
        except Exception as e:
            self._log(f"⚠️ 업데이트 일시 포맷팅 실패: {e}")

    def _auto_resize_columns(self, worksheet, num_cols=4):
        """
        열 너비 자동 조정 (내부 함수)

        매개변수:
            worksheet: gspread.Worksheet 객체
            num_cols: 컬럼 개수 (기본 4, 증분 저장 시 6)
        """
        try:
            requests = [
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": worksheet.id,
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": num_cols,
                        }
                    }
                },
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": worksheet.id,
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": 1,
                        },
                        "properties": {"pixelSize": config.COLUMN_WIDTH_DATE},
                        "fields": "pixelSize",
                    }
                },
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": worksheet.id,
                            "dimension": "COLUMNS",
                            "startIndex": 1,
                            "endIndex": 2,
                        },
                        "properties": {"pixelSize": config.COLUMN_WIDTH_CONTENT},
                        "fields": "pixelSize",
                    }
                },
            ]
            body = {"requests": requests}
            worksheet.spreadsheet.batch_update(body)
        except Exception as e:
            self._log(f"⚠️ 열 자동 조정 실패: {e}")

    def get_last_entry_from_sheet(self, case):
        """
        해당 사건의 개별 시트에서 실제 마지막 데이터 행(일자, 내용)을 조회.
        시트가 없거나 비어있으면 None. API/네트워크 오류는 예외 전파.
        """
        case_number = case.get("사건번호", "")
        defendant = case.get("피고", "")
        court = case.get("법원", "")
        case_name = (case.get("사건명") or "").strip()
        remark_raw = (case.get("비고") or "").strip()
        if not case_name and remark_raw and not str(remark_raw).startswith("업데이트"):
            case_name = remark_raw
        if case_name:
            worksheet_name = f"{defendant}_{case_name}_{case_number}_{court}"
        else:
            worksheet_name = f"{defendant}_{case_number}_{court}"

        spreadsheet = self._get_spreadsheet()
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            return None

        all_values = worksheet.get_all_values()
        if len(all_values) <= 1:
            return None

        skip_first_col_values = ("업데이트 일시", "최근 과거 업데이트")
        for i in range(len(all_values) - 1, 0, -1):
            row = all_values[i]
            if not row or len(row) < 2:
                continue
            first_cell = str(row[0]).strip()
            if not first_cell or first_cell in skip_first_col_values:
                continue
            entry_dict = {
                "date": row[0].strip() if row[0] else "",
                "content": row[1].strip() if len(row) > 1 and row[1] else "",
            }
            row_index = i + 1
            return (entry_dict, row_index)
        return None

    def delete_specific_row(self, case, row_index):
        """
        해당 사건의 개별 시트에서 지정한 1-based 행을 삭제.
        기일 행을 제거한 뒤 새 데이터+기일을 다시 붙이기 위한 용도.
        """
        defendant = case.get("피고", "")
        court = case.get("법원", "")
        case_name = (case.get("사건명") or "").strip()
        remark_raw = (case.get("비고") or "").strip()
        if not case_name and remark_raw and not str(remark_raw).startswith("업데이트"):
            case_name = remark_raw
        if case_name:
            worksheet_name = (
                f"{defendant}_{case_name}_{case.get('사건번호', '')}_{court}"
            )
        else:
            worksheet_name = f"{defendant}_{case.get('사건번호', '')}_{court}"
        spreadsheet = self._get_spreadsheet()
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            return False
        try:
            worksheet.delete_rows(row_index)
            return True
        except Exception as e:
            self._log(f"⚠️ 시트 행 삭제 실패: {e}")
            return False

    def append_notification_mail(self, summary_text, recipient_email=""):
        """
        '알림메일' 워크시트에 메일 내역 행을 추가합니다.
        GAS(Apps Script)가 '발송상태'가 '대기'인 행을 감지해 수신주소 열을 보고 메일 발송합니다.

        summary_text: 메일 본문으로 쓸 문자열 (사건별 업데이트 요약).
        recipient_email: 수신 메일 주소 (GUI 설정에서 입력).
        반환: True 성공, False 실패.
        """
        if not summary_text or not summary_text.strip():
            return False
        try:
            spreadsheet = self._get_spreadsheet()
            try:
                worksheet = spreadsheet.worksheet(config.NOTIFICATION_WORKSHEET_NAME)
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(
                    title=config.NOTIFICATION_WORKSHEET_NAME, rows=100, cols=10
                )
            all_values = worksheet.get_all_values()
            header = ["일시", "수신주소", "메일내용", "발송상태"]
            if len(all_values) == 0:
                worksheet.append_row(header)
            elif len(all_values) == 1 and len(all_values[0]) < 4:
                worksheet.update("A1:D1", [header], value_input_option="USER_ENTERED")
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.append_row([current_time, (recipient_email or "").strip(), summary_text.strip(), "대기"])
            self._log(f"✅ 알림메일 시트에 행 추가 완료 (발송상태: 대기)")
            return True
        except Exception as e:
            self._log(f"❌ 알림메일 시트 추가 실패: {e}")
            return False

    def get_case_worksheet_url(self, case):
        """
        사건 정보에 해당하는 구글 시트 탭의 URL(gid 포함)을 반환합니다.

        주니어 개발자 참고:
        - gspread 5.1.1의 `worksheet.url`은 사람이 보는 문서 URL이 아니라
          Sheets API URL(`https://sheets.googleapis.com/...`)을 반환합니다.
        - 메일에서 클릭 가능한 링크를 만들기 위해 `worksheet.id`(=gid)를 사용해
          docs.google.com 주소를 직접 조립합니다.
        - 메일에 "바로가기" 링크로 넣어 수신자가 해당 탭을 즉시 열 수 있도록 사용합니다.
        - 어떤 이유로든 조회에 실패하면 스프레드시트 루트 URL을 폴백으로 반환합니다.
        """
        fallback_url = (
            f"https://docs.google.com/spreadsheets/d/{config.GOOGLE_SHEET_ID}/edit"
        )
        try:
            spreadsheet = self._get_spreadsheet()
            worksheet_name = self._get_case_worksheet_name(case)
            try:
                worksheet = spreadsheet.worksheet(worksheet_name)
            except gspread.WorksheetNotFound:
                return fallback_url
            gid = getattr(worksheet, "id", None)
            if gid is None:
                return fallback_url
            return f"{fallback_url}#gid={gid}"
        except Exception as e:
            self._log(f"⚠️ 시트 URL 조회 실패(폴백 사용): {e}")
            return fallback_url

    def _get_case_worksheet_name(self, case):
        """사건 정보로 개별 시트 이름을 반환."""
        defendant = case.get("피고", "")
        court = case.get("법원", "")
        case_number = case.get("사건번호", "")
        case_name = (case.get("사건명") or "").strip()
        remark_raw = (case.get("비고") or "").strip()
        if not case_name and remark_raw and not str(remark_raw).startswith("업데이트"):
            case_name = remark_raw
        if case_name:
            return f"{defendant}_{case_name}_{case_number}_{court}"
        return f"{defendant}_{case_number}_{court}"

    def get_full_sheet_data(self, case):
        """
        해당 사건의 개별 시트에서 모든 셀 데이터를 2차원 리스트로 반환.
        시트가 없거나 비어있으면 빈 리스트. API 오류는 예외 전파.
        """
        worksheet_name = self._get_case_worksheet_name(case)
        spreadsheet = self._get_spreadsheet()
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            return []
        return worksheet.get_all_values()

    @staticmethod
    def _normalize_sheet_cell(text):
        """시트 비교용: 공백 제거 후 문자열화 (중복 판별 시 오판 방지)."""
        if text is None:
            return ""
        return "".join(str(text).split())

    @classmethod
    def _sheet_row_dedup_key(cls, row):
        """
        진행내용 한 행의 중복 판별 키.
        일자·내용·결과·공시문 4열이 모두 같으면 동일 기록으로 봅니다.
        """
        parts = []
        for col_idx in range(4):
            val = row[col_idx] if col_idx < len(row) else ""
            parts.append(cls._normalize_sheet_cell(val))
        return tuple(parts)

    @classmethod
    def _is_progress_data_row(cls, row):
        """
        헤더·업데이트 일시·빈 구분 행이 아닌, 실제 진행내용 데이터 행인지 판별.
        """
        if not row:
            return False
        first_cell = cls._normalize_sheet_cell(row[0] if len(row) > 0 else "")
        if not first_cell:
            return False
        if first_cell in ("업데이트일시", "업데이트 일시", "최근 과거 업데이트", "일자"):
            return False
        return True

    @retry_on_quota_error(max_retries=5, base_delay=2.0)
    def remove_duplicate_rows_from_sheet(self, case):
        """
        사건별 시트에서 중복된 진행내용 행을 제거합니다.

        주니어 개발자 참고:
        - 무한 증식 버그 등으로 동일 (일자, 내용, 결과, 공시문)이 여러 번 쌓인 경우 정리용.
        - 위에서부터 순회하며 첫 번째만 남기고, 이후 동일 키 행은 삭제합니다.
        - '업데이트 일시' 등 메타 행은 그대로 유지합니다.

        반환:
            dict: success(bool), removed(int), remaining_data_rows(int), message(str)
        """
        case_number = case.get("사건번호", "")
        all_values = self.get_full_sheet_data(case)
        if not all_values:
            return {
                "success": True,
                "removed": 0,
                "remaining_data_rows": 0,
                "message": f"{case_number}: 시트 없음 또는 비어 있음",
            }

        header = all_values[0]
        body = all_values[1:]

        data_out = []
        footer_out = []
        seen_keys = set()
        removed = 0

        for row in body:
            if self._is_progress_data_row(row):
                key = self._sheet_row_dedup_key(row)
                if key in seen_keys:
                    removed += 1
                    continue
                seen_keys.add(key)
                data_out.append(list(row))
            else:
                footer_out.append(list(row))

        if removed == 0:
            return {
                "success": True,
                "removed": 0,
                "remaining_data_rows": len(data_out),
                "message": f"{case_number}: 제거할 중복 없음",
            }

        new_values = [header] + data_out + footer_out
        ok = self.overwrite_sheet_data(case, new_values)
        if not ok:
            return {
                "success": False,
                "removed": 0,
                "remaining_data_rows": len(data_out),
                "message": f"{case_number}: 시트 덮어쓰기 실패",
            }

        self._log(
            f"🧹 중복 제거 완료: {case_number} (-{removed}행, 데이터 {len(data_out)}행 유지)"
        )
        return {
            "success": True,
            "removed": removed,
            "remaining_data_rows": len(data_out),
            "message": f"{case_number}: 중복 {removed}행 제거",
        }

    def overwrite_sheet_data(self, case, data):
        """
        해당 사건의 개별 시트 내용을 data(2차원 리스트)로 전부 갱신.
        clear 후 update. data가 비어있으면 시트만 비움.
        """
        if not isinstance(data, list):
            return False
        worksheet_name = self._get_case_worksheet_name(case)
        spreadsheet = self._get_spreadsheet()
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            return False
        try:
            worksheet.clear()
            if data:
                worksheet.update("A1", data, value_input_option="USER_ENTERED")
            return True
        except Exception as e:
            self._log(f"⚠️ 시트 덮어쓰기 실패: {e}")
            return False

    def update_main_remark(self, case_number, new_count):
        """
        메인 시트(사건 목록)에서 해당 사건 행의 비고 열에 업데이트 문구 기록.

        case_number: 사건번호
        new_count: 이번에 추가된 건수
        """
        try:
            spreadsheet = self._get_spreadsheet()
            for ws in spreadsheet.worksheets():
                if config.CASE_LIST_WORKSHEET_NAME not in ws.title:
                    continue
                all_values = ws.get_all_values()
                if len(all_values) < 2:
                    return
                headers = all_values[0]
                try:
                    col_case = headers.index("사건번호")
                except ValueError:
                    return
                try:
                    col_remark = headers.index("비고")
                except ValueError:
                    col_remark = len(headers)
                for r in range(1, len(all_values)):
                    row = all_values[r]
                    if (
                        col_case < len(row)
                        and str(row[col_case]).strip() == str(case_number).strip()
                    ):
                        today_str = datetime.now().strftime("%Y.%m.%d")
                        remark_text = f"{today_str} 업데이트 (+{new_count}건)"
                        ws.update_cell(r + 1, col_remark + 1, remark_text)
                        self._log(
                            f"📝 메인 시트 비고 갱신: {case_number} -> {remark_text}"
                        )
                        return
        except Exception as e:
            self._log(f"⚠️ 메인 시트 비고 갱신 실패: {e}")

    def _get_case_list_worksheet(self):
        """사건 목록 워크시트 반환. 없으면 None."""
        spreadsheet = self._get_spreadsheet()
        for ws in spreadsheet.worksheets():
            if config.CASE_LIST_WORKSHEET_NAME in ws.title:
                return ws
        return None

    def _header_order_row(self, headers, row_dict):
        """헤더 순서대로 row_dict에서 값 리스트 생성 (없는 키는 빈 문자열)."""
        return [str(row_dict.get(h, "") or "") for h in headers]

    def append_row_to_case_list(self, row_dict):
        """
        사건 목록 시트에 1행 추가.
        row_dict: 헤더 이름을 키로 하는 딕셔너리 (법원, 사건번호, 피고, 사건명, 비고, 일자, 내용 등).
        반환: True 성공, False 실패.
        """
        try:
            ws = self._get_case_list_worksheet()
            if not ws:
                self._log("[ERROR] 사건 목록 워크시트를 찾을 수 없습니다")
                return False
            all_values = ws.get_all_values()
            headers = all_values[0] if all_values else []
            if not headers:
                self._log("[ERROR] 사건 목록 헤더가 비어 있습니다")
                return False
            row_list = self._header_order_row(headers, row_dict)
            ws.append_row(row_list, value_input_option="USER_ENTERED")
            self._log(f"✅ 사건 목록에 행 추가 완료: {row_dict.get('사건번호', '')}")
            return True
        except Exception as e:
            self._log(f"⚠️ 사건 목록 행 추가 실패: {e}")
            return False

    def update_row_by_case_number(self, case_number, row_dict):
        """
        사건 목록 시트에서 사건번호가 일치하는 첫 번째 행을 row_dict 값으로 갱신.
        반환: True 성공, False 실패(행 미발견 포함).
        """
        try:
            ws = self._get_case_list_worksheet()
            if not ws:
                return False
            all_values = ws.get_all_values()
            if len(all_values) < 2:
                return False
            headers = all_values[0]
            try:
                col_case = headers.index("사건번호")
            except ValueError:
                return False
            row_index_1based = None
            for r in range(1, len(all_values)):
                row = all_values[r]
                if col_case < len(row) and str(row[col_case]).strip() == str(case_number).strip():
                    row_index_1based = r + 1
                    break
            if row_index_1based is None:
                return False
            row_list = self._header_order_row(headers, row_dict)
            num_cols = len(headers)
            end_col = ""
            i = num_cols - 1
            while i >= 0:
                end_col = chr(65 + i % 26) + end_col
                i = i // 26 - 1
            range_str = f"A{row_index_1based}:{end_col}{row_index_1based}"
            ws.update(range_str, [row_list], value_input_option="USER_ENTERED")
            self._log(f"✅ 사건 목록 행 갱신 완료: {case_number}")
            return True
        except Exception as e:
            self._log(f"⚠️ 사건 목록 행 갱신 실패: {e}")
            return False

    def delete_row_by_case_number(self, case_number):
        """
        사건 목록 시트에서 사건번호가 일치하는 첫 번째 행 삭제.
        반환: True 성공, False 실패(행 미발견 포함).
        """
        try:
            ws = self._get_case_list_worksheet()
            if not ws:
                return False
            all_values = ws.get_all_values()
            if len(all_values) < 2:
                return False
            try:
                col_case = all_values[0].index("사건번호")
            except ValueError:
                return False
            row_index_1based = None
            for r in range(1, len(all_values)):
                row = all_values[r]
                if col_case < len(row) and str(row[col_case]).strip() == str(case_number).strip():
                    row_index_1based = r + 1
                    break
            if row_index_1based is None:
                return False
            ws.delete_rows(row_index_1based, row_index_1based + 1)
            self._log(f"✅ 사건 목록에서 행 삭제 완료: {case_number}")
            return True
        except Exception as e:
            self._log(f"⚠️ 사건 목록 행 삭제 실패: {e}")
            return False


# ============================================================================
# 편의 함수 (하위 호환성을 위해 유지)
# ============================================================================
def load_google_sheet_data():
    """
    구글 시트에서 사건 데이터를 읽어오는 함수 (하위 호환성)

    이 함수는 기존 코드와의 호환성을 위해 유지됩니다.
    새로운 코드에서는 GoogleSheetsService 클래스를 직접 사용하는 것을 권장합니다.

    반환값:
        - filtered_data: 사건번호가 있는 사건 데이터 리스트
        - spreadsheet: 구글 시트 객체 (나중에 저장할 때 사용)
        - 실패 시: (None, None)
    """
    service = GoogleSheetsService()
    data = service.load_case_list()

    if data:
        # 스프레드시트 객체도 반환 (하위 호환성)
        spreadsheet = service._get_spreadsheet()
        return data, spreadsheet
    else:
        return None, None
