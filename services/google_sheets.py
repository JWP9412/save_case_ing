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
                        if args and hasattr(args[0], "_log"):
                            args[0]._log(
                                f"⚠️ 구글 시트 할당량 초과(429). {delay}초 후 재시도 ({attempt + 1}/{max_retries})"
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
            log_callback: 로그 메시지를 출력할 함수 (선택사항)
                예: lambda msg: print(msg)
        """
        self.log_callback = log_callback
        self._client = None
        self._spreadsheet = None
        # 저장 직렬화용 락 (429 할당량 초과 방지: 동시 쓰기 제한)
        self._save_lock = threading.Lock()

    def _log(self, message):
        """로그 메시지 출력 (콜백 함수 사용)"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def _get_client(self):
        """
        구글 시트 클라이언트 가져오기 (싱글톤 패턴)

        반환값:
            gspread.Client 객체
        """
        if self._client is None:
            # 서비스 계정 인증
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = Credentials.from_service_account_file(
                config.GOOGLE_AUTH_FILE, scopes=scope
            )
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
            # ============================================================
            # 1단계: 구글 시트 연결
            # ============================================================
            gc = gspread.service_account(filename=config.GOOGLE_AUTH_FILE)

            # ============================================================
            # 2단계: 특정 스프레드시트 열기 (ID로)
            # ============================================================
            spreadsheet = gc.open_by_key(config.GOOGLE_SHEET_ID)
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
                case_number = row.get("사건번호", "").strip()
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

    @retry_on_quota_error(max_retries=5, base_delay=2.0)
    def save_progress_data(self, case, result_data, log_callback=None):
        """
        구글 시트에 진행내용 데이터를 저장하는 함수

        이 함수는 Puppeteer로 크롤링한 진행내용 데이터를 구글 시트에 저장합니다.

        매개변수:
            case: 사건 정보 딕셔너리 (사건번호, 피고, 법원, 비고 등)
            result_data: 크롤링한 진행내용 데이터 리스트
                예: [
                    {'date': '2024-01-01', 'content': '...', 'result': '...', 'document': '...'},
                    ...
                ]
            log_callback: 로그 메시지를 출력할 함수 (선택사항)

        반환값:
            저장된 행 개수 (int) 또는 False (실패 시)

        처리 순서:
            1. 구글 시트에 연결 (인증)
            2. 워크시트 찾기 또는 생성 (시트명: 피고_비고_사건번호_법원)
            3. 기존 데이터에서 이전 업데이트 시간 추출
            4. 워크시트 초기화 (기존 데이터 삭제)
            5. 헤더 추가 (일자, 내용, 결과, 공시문)
            6. 진행내용 데이터 저장
            7. 텍스트 색상 적용 (원본 웹사이트 색상 유지)
            8. 빈 줄 5개 추가
            9. 업데이트 일시 기록 (현재 시간 + 이전 시간)
            10. 열 너비 자동 조정
        """
        # 로그 콜백 설정
        if log_callback:
            self.log_callback = log_callback

        # [Fix] result_data가 True인 경우 (데이터 없음) 빈 리스트로 처리
        if result_data is True:
            result_data = []

        with self._save_lock:
            try:
                case_number = case.get("사건번호", "")
                self._log(f"💾 [DEBUG] save_progress_data 시작: {case_number}")

                # 신규 데이터가 없으면 저장 생략 (Step 4)
                if not isinstance(result_data, list) or len(result_data) == 0:
                    self._log(f"💾 [DEBUG] 저장할 신규 데이터 없음")
                    return False

                client = self._get_client()
                spreadsheet = self._get_spreadsheet()

                defendant = case.get("피고", "")
                court = case.get("법원", "")
                # 시트 이름용: 사건명 우선, 비고는 보조(업데이트 문구는 제외)
                case_name = (case.get("사건명") or "").strip()
                remark_raw = (case.get("비고") or "").strip()
                if (
                    not case_name
                    and remark_raw
                    and not str(remark_raw).startswith("업데이트")
                ):
                    case_name = remark_raw
                if case_name:
                    worksheet_name = f"{defendant}_{case_name}_{case_number}_{court}"
                else:
                    worksheet_name = f"{defendant}_{case_number}_{court}"

                try:
                    worksheet = spreadsheet.worksheet(worksheet_name)
                except gspread.WorksheetNotFound:
                    worksheet = spreadsheet.add_worksheet(
                        title=worksheet_name, rows=100, cols=10
                    )

                # ----- Step 3: 헤더 확인 및 확장, 기존 타임스탬프 행 삭제 -----
                all_values = worksheet.get_all_values()
                if len(all_values) == 0:
                    headers = [
                        "일자",
                        "내용",
                        "결과",
                        "공시문",
                        "비고",
                        "이메일 송부 여부",
                    ]
                    worksheet.append_row(headers)
                else:
                    row1 = all_values[0]
                    if len(row1) < 6:
                        extended = (row1 + ["", ""])[:6]
                        extended[4] = extended[4] or "비고"
                        extended[5] = extended[5] or "이메일 송부 여부"
                        worksheet.update(
                            "A1:F1", [extended], value_input_option="USER_ENTERED"
                        )
                # 맨 아래 '업데이트 일시' / '최근 과거 업데이트' 행 제거 (뒤에서부터)
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

                # ----- Step 4: 신규 데이터에 비고·이메일 열 추가 후 append -----
                today_str = datetime.now().strftime("%Y.%m.%d")
                processed_new_data = []
                color_info = []
                start_row_1based = len(worksheet.get_all_values()) + 1
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
                    color_info.append(
                        {
                            "row": start_row_1based + idx,
                            "dateColor": progress_row.get("dateColor"),
                            "contentColor": progress_row.get("contentColor"),
                            "resultColor": progress_row.get("resultColor"),
                            "documentColor": progress_row.get("documentColor"),
                        }
                    )
                worksheet.append_rows(
                    processed_new_data, value_input_option="USER_ENTERED"
                )

                # ----- Step 5: 새로 추가된 행에만 색상 적용, 타임스탬프 행 추가 -----
                self._apply_text_colors(worksheet, color_info)
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                empty_rows = [[""] * 6 for _ in range(config.EMPTY_ROWS_BEFORE_UPDATE)]
                worksheet.append_rows(empty_rows, value_input_option="USER_ENTERED")
                worksheet.append_rows(
                    [["업데이트 일시", current_time, "", "", "", ""]],
                    value_input_option="USER_ENTERED",
                )
                current_row = (
                    start_row_1based
                    + len(processed_new_data)
                    + config.EMPTY_ROWS_BEFORE_UPDATE
                    + 1
                )
                self._ensure_worksheet_rows(worksheet, current_row + 2)
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
