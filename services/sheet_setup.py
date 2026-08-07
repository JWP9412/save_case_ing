# -*- coding: utf-8 -*-
"""
구글 시트 첫 실행 준비 유틸
============================

주니어 개발자 참고:
- 사용자가 URL에서 ID를 손으로 복사하거나, 시트를 직접 만들고
  탭·헤더를 꾸밀 필요 없이, 앱 버튼만으로 준비되게 합니다.
- OAuth 토큰이 있어야 동작합니다 (drive + spreadsheets 권한).
"""

import re

import gspread
from google.oauth2.credentials import Credentials

import config
from services import google_oauth

# 사건 목록 탭 1행에 넣을 기본 헤더 (프로그램이 읽는 열 이름)
CASE_LIST_HEADERS = ["법원", "사건번호", "피고", "사건명", "비고"]


def extract_sheet_id(url_or_id):
    """
    시트 URL 또는 ID 문자열에서 스프레드시트 ID만 뽑아냅니다.

    예:
      https://docs.google.com/spreadsheets/d/ABC123xyz/edit#gid=0  → ABC123xyz
      ABC123xyz  → ABC123xyz
    """
    text = (url_or_id or "").strip()
    if not text:
        raise ValueError("시트 URL 또는 ID를 입력해 주세요.")

    # URL 형태: /spreadsheets/d/<ID>/
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", text)
    if match:
        return match.group(1)

    # 이미 ID만 넣은 경우 (공백·슬래시 없이 긴 문자열)
    if re.fullmatch(r"[a-zA-Z0-9-_]+", text) and len(text) >= 20:
        return text

    raise ValueError(
        "시트 ID를 알아내지 못했습니다.\n"
        "구글 시트 주소 전체를 붙여넣거나, /d/ 와 /edit 사이의 ID를 넣어 주세요."
    )


def _authorize_client(log_callback=None):
    """저장된 OAuth 토큰으로 gspread 클라이언트를 만듭니다 (브라우저 연동 없음)."""
    creds = google_oauth.get_credentials(interactive=False, log_callback=log_callback)
    if creds is None:
        raise RuntimeError(
            "Google 계정 연동이 필요합니다.\n"
            "가이드 2단계 [연동하기]를 먼저 완료해 주세요."
        )
    if not isinstance(creds, Credentials):
        # google.oauth2.service_account 등도 authorize 가능하지만, 여기선 사용자 OAuth 전제
        pass
    return gspread.authorize(creds)


def _ensure_case_list_worksheet(spreadsheet, log_callback=None):
    """
    '사건 목록' 탭이 없으면 만들고, 1행 헤더가 비어 있으면 채웁니다.
    반환: 워크시트 객체
    """
    target_name = getattr(config, "CASE_LIST_WORKSHEET_NAME", "사건 목록") or "사건 목록"
    worksheet = None
    for ws in spreadsheet.worksheets():
        if target_name in (ws.title or ""):
            worksheet = ws
            break

    if worksheet is None:
        # 기본 Sheet1만 있는 새 파일이면 이름 변경, 아니면 탭 추가
        sheets = spreadsheet.worksheets()
        if len(sheets) == 1 and (sheets[0].title or "").lower() in ("sheet1", "시트1"):
            worksheet = sheets[0]
            worksheet.update_title(target_name)
            if callable(log_callback):
                log_callback(f"시트 탭 이름을 '{target_name}'으로 변경했습니다.")
        else:
            worksheet = spreadsheet.add_worksheet(title=target_name, rows=100, cols=10)
            if callable(log_callback):
                log_callback(f"'{target_name}' 탭을 새로 만들었습니다.")

    # 1행 헤더 확인 — 비어 있거나 사건번호가 없으면 기본 헤더 기록
    try:
        first_row = worksheet.row_values(1)
    except Exception:
        first_row = []
    needs_header = not first_row or "사건번호" not in first_row
    if needs_header:
        worksheet.update("A1:E1", [CASE_LIST_HEADERS])
        if callable(log_callback):
            log_callback("사건 목록 헤더(법원/사건번호/피고/사건명/비고)를 넣었습니다.")

    return worksheet


def create_new_spreadsheet(title=None, log_callback=None):
    """
    새 구글 스프레드시트를 만들고 사건 목록 탭·헤더까지 준비합니다.

    반환: {"id": str, "title": str, "url": str}
    """
    client = _authorize_client(log_callback=log_callback)
    sheet_title = (title or "").strip() or "case-ing"
    spreadsheet = client.create(sheet_title)
    _ensure_case_list_worksheet(spreadsheet, log_callback=log_callback)
    sheet_id = spreadsheet.id
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
    if callable(log_callback):
        log_callback(f"새 시트 생성 완료: {spreadsheet.title} ({sheet_id})")
    return {"id": sheet_id, "title": spreadsheet.title, "url": url}


def verify_and_prepare(sheet_id, log_callback=None):
    """
    기존 시트를 열고, 사건 목록 탭·헤더를 필요 시 자동 준비합니다.

    반환: {"id": str, "title": str, "url": str}
    실패 시 ValueError / PermissionError 등 — 메시지는 한국어로 변환해 재발생.
    """
    sheet_id = extract_sheet_id(sheet_id) if "/" in str(sheet_id) or " " in str(sheet_id) else str(sheet_id).strip()
    # extract 안 거친 순수 ID도 한 번 더 정규화
    if not re.fullmatch(r"[a-zA-Z0-9-_]+", sheet_id):
        sheet_id = extract_sheet_id(sheet_id)

    client = _authorize_client(log_callback=log_callback)
    try:
        spreadsheet = client.open_by_key(sheet_id)
    except gspread.exceptions.SpreadsheetNotFound as e:
        raise ValueError(
            "시트를 찾을 수 없습니다.\n"
            "ID가 맞는지, 로그인한 구글 계정에 편집 권한이 있는지 확인해 주세요."
        ) from e
    except PermissionError as e:
        raise PermissionError(
            "이 시트에 접근할 권한이 없습니다.\n"
            "시트 [공유]에서 내 구글 계정을 '편집자'로 추가해 주세요."
        ) from e
    except Exception as e:
        msg = str(e)
        if "PERMISSION" in msg.upper() or "403" in msg:
            raise PermissionError(
                "이 시트에 접근할 권한이 없습니다.\n"
                "시트 [공유]에서 내 구글 계정을 '편집자'로 추가해 주세요."
            ) from e
        if "404" in msg or "not found" in msg.lower():
            raise ValueError(
                "시트를 찾을 수 없습니다. ID 또는 URL을 다시 확인해 주세요."
            ) from e
        raise RuntimeError(f"시트 연결에 실패했습니다.\n{e}") from e

    _ensure_case_list_worksheet(spreadsheet, log_callback=log_callback)
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}/edit"
    if callable(log_callback):
        log_callback(f"시트 연결 확인: {spreadsheet.title}")
    return {"id": spreadsheet.id, "title": spreadsheet.title, "url": url}


def apply_sheet_to_config(sheet_id, spreadsheet_name=None):
    """
    시트 ID(및 선택적 이름)를 config + user_settings.json에 반영합니다.
    """
    sheet_id = str(sheet_id or "").strip()
    if not sheet_id:
        raise ValueError("시트 ID가 비어 있습니다.")
    partial = {"GOOGLE_SHEET_ID": sheet_id}
    if spreadsheet_name:
        partial["SPREADSHEET_NAME"] = str(spreadsheet_name).strip()
    config.update_user_settings(partial)
