# -*- coding: utf-8 -*-
"""
Google OAuth 인증 유틸리티
=========================

앱 내 최초 연동(브라우저 로그인)과 토큰 재사용/갱신을 담당합니다.
"""

import os

import config
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/calendar.events",
]


def _abs_path(path_value):
    """상대경로는 배포/프로젝트 루트(BASE_DIR) 기준으로 해석합니다."""
    if not path_value:
        return ""
    if os.path.isabs(path_value):
        return path_value
    return config.path_from_base(path_value)


def _log(log_callback, message):
    if callable(log_callback):
        log_callback(message)


def _get_scopes(scopes=None):
    return list(scopes or getattr(config, "GOOGLE_OAUTH_SCOPES", DEFAULT_SCOPES))


def resolved_oauth_client_secret_path():
    """
    config에 설정된 OAuth 클라이언트 JSON의 절대 경로(정규화).
    주니어: 설정값이 상대경로면 프로젝트 루트(config.py 위치) 기준으로 붙입니다.
    """
    raw = getattr(config, "GOOGLE_OAUTH_CLIENT_SECRET_FILE", "") or ""
    if not str(raw).strip():
        return ""
    return os.path.normpath(_abs_path(raw))


def format_missing_oauth_client_message(resolved_path: str) -> str:
    """클라이언트 파일이 없을 때 사용자에게 보여줄 안내 문구."""
    p = resolved_path.strip() if resolved_path else "(경로 미설정)"
    return (
        "OAuth 클라이언트 파일(JSON)을 찾을 수 없습니다.\n\n"
        f"확인할 경로:\n{p}\n\n"
        "1) Google Cloud Console → 사용자 인증 정보 → OAuth 클라이언트 ID\n"
        "   (애플리케이션 유형: 데스크톱 앱)에서 JSON을 다운로드합니다.\n"
        "2) 위 경로에 파일을 두거나, 설정의 'OAuth 클라이언트 파일 경로'에\n"
        "   실제 JSON 위치를 입력·[찾아보기]로 지정한 뒤 [저장]하세요.\n\n"
        "자세한 절차: api/certification/GOOGLE_AUTH_SETUP.md"
    )


def get_credentials(scopes=None, interactive=False, log_callback=None):
    """
    사용자 OAuth 자격증명을 반환합니다.

    interactive=False:
      - 저장된 토큰 로드/갱신만 시도하고, 없으면 None 반환.
    interactive=True:
      - 토큰이 없거나 만료/갱신불가면 브라우저 연동 플로우를 시작.
    """
    target_scopes = _get_scopes(scopes)
    token_path = _abs_path(getattr(config, "GOOGLE_USER_TOKEN_FILE", ""))
    client_secret_path = resolved_oauth_client_secret_path()

    creds = None
    if token_path and os.path.isfile(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, target_scopes)
        except Exception as e:
            _log(log_callback, f"⚠️ 저장된 Google 토큰 로드 실패: {e}")
            creds = None

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds, token_path)
            _log(log_callback, "✅ Google 토큰 자동 갱신 완료")
            return creds
        except Exception as e:
            _log(log_callback, f"⚠️ Google 토큰 갱신 실패: {e}")
            creds = None

    if not interactive:
        return None

    if not client_secret_path or not os.path.isfile(client_secret_path):
        raise FileNotFoundError(format_missing_oauth_client_message(client_secret_path))
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, target_scopes)
    creds = flow.run_local_server(
        host="localhost",
        port=0,
        authorization_prompt_message="브라우저에서 Google 계정 연동을 완료해 주세요.",
        success_message="Google 연동이 완료되었습니다. 앱으로 돌아가세요.",
        open_browser=True,
    )
    _save_token(creds, token_path)
    _log(log_callback, "✅ Google 계정 연동 완료 (토큰 저장)")
    return creds


def _save_token(creds, token_path):
    if not token_path:
        return
    os.makedirs(os.path.dirname(token_path) or ".", exist_ok=True)
    with open(token_path, "w", encoding="utf-8") as f:
        f.write(creds.to_json())


def clear_token():
    token_path = _abs_path(getattr(config, "GOOGLE_USER_TOKEN_FILE", ""))
    if token_path and os.path.isfile(token_path):
        os.remove(token_path)
        return True
    return False


def has_valid_token(scopes=None):
    return get_credentials(scopes=scopes, interactive=False) is not None


def has_client_secret_file():
    """OAuth 클라이언트 JSON(client_secret.json)이 디스크에 있는지."""
    path = resolved_oauth_client_secret_path()
    return bool(path) and os.path.isfile(path)


def has_sheet_id_configured():
    """구글 시트 ID가 비어 있지 않은지."""
    return bool(str(getattr(config, "GOOGLE_SHEET_ID", "") or "").strip())


def get_setup_status():
    """
    첫 실행 가이드용 세팅 상태 딕셔너리.

    반환 예:
      {
        "client_secret": True/False,
        "token": True/False,
        "sheet_id": True/False,
        "complete": True/False,  # 셋 다 True면 완료
      }
    """
    secret_ok = has_client_secret_file()
    token_ok = has_valid_token()
    sheet_ok = has_sheet_id_configured()
    return {
        "client_secret": secret_ok,
        "token": token_ok,
        "sheet_id": sheet_ok,
        "complete": secret_ok and token_ok and sheet_ok,
    }


def is_setup_complete():
    """인증 파일 + 토큰 + 시트 ID가 모두 준비됐으면 True."""
    return get_setup_status()["complete"]


def should_show_first_run_guide():
    """
    시작 시 첫 실행 가이드를 띄울지 여부.

    - 세팅이 이미 완료면 False
    - SHOW_FIRST_RUN_GUIDE 가 0이면 False ("다시 보지 않기")
    """
    if is_setup_complete():
        return False
    return int(getattr(config, "SHOW_FIRST_RUN_GUIDE", 1) or 0) == 1
