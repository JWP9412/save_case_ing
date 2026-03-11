"""
설정 상수 모음
==============

프로그램에서 사용하는 모든 설정값을 한 곳에 모아둡니다.
이렇게 하면 설정을 변경할 때 이 파일만 수정하면 됩니다.

사용법:
    from config import GOOGLE_SHEET_ID, SPREADSHEET_NAME

    spreadsheet = client.open(SPREADSHEET_NAME)
"""

# ============================================================================
# 앱 표시 정보 (창 제목·헤더용, 버전은 여기서만 수정)
# ============================================================================
# 앱 버전 번호 (한 곳만 수정하면 창 제목·부제목에 반영됨)
APP_VERSION = "4.5.0"
# 창 제목 및 헤더 제목에 쓰는 이름
APP_TITLE = "사건 일괄 처리 시스템"
# 부제목에 쓰는 이름 (버전은 코드에서 f-string으로 붙임)
APP_SUBTITLE = "사건 조회 자동화 시스템"
# 제목 배너 이미지 경로 (없으면 텍스트 헤더 사용)
HEADER_IMAGE_PATH = "./assets/title_banner.png"
# 헤더 배경색 (창 리사이즈 시 이미지 양옆 여백 채우는 색, 이미지 배경과 맞추면 됨)
HEADER_BG_COLOR = "#001A33"

# ============================================================================
# 구글 시트 설정
# ============================================================================
# 구글 시트 스프레드시트 ID (URL에 있는 고유 번호)
# 예: https://docs.google.com/spreadsheets/d/[여기가 ID]/edit
GOOGLE_SHEET_ID = "1ShaDTz4pj8SRWvf3ahcVI-gStYK-dFSBPsS6BnDOFzU"

# 구글 시트 스프레드시트 이름
SPREADSHEET_NAME = "case-ing-test"

# 구글 시트 인증 파일 경로
GOOGLE_AUTH_FILE = "./api/certification/service-account.json"

# 구글 시트 "사건 목록" 워크시트 이름
CASE_LIST_WORKSHEET_NAME = "사건 목록"

# ============================================================================
# Puppeteer 설정
# ============================================================================
# Puppeteer 실행 타임아웃 (초)
# 캡차 이미지 캡처: 90초
PUPPETEER_CAPTCHA_TIMEOUT = 90

# 실제 크롤링 처리: 180초 (3분)
PUPPETEER_PROCESSING_TIMEOUT = 180

# 캡차 입력 대기 시간 (초)
CAPTCHA_INPUT_TIMEOUT = 300

# ============================================================================
# 병렬 처리 설정
# ============================================================================
# 기본 병렬 처리 수 (동시에 처리할 수 있는 최대 사건 수)
DEFAULT_MAX_PARALLEL = 3

# 최대 병렬 처리 수 (제한) - cookie_data_for_save/instance_N 폴더 최대 개수
MAX_PARALLEL_LIMIT = 20

# ============================================================================
# 재시도 설정
# ============================================================================
# 기본 캡차 재시도 횟수
DEFAULT_MAX_RETRY = 3

# 재시도 간 대기 시간 (초)
DEFAULT_RETRY_DELAY = 2

# ============================================================================
# 파일 경로 설정
# ============================================================================
# 결과 파일 저장 디렉토리
RESULTS_DIR = "results"

# 스크린샷 저장 디렉토리
SCREENSHOTS_DIR = "screenshots"

# 업데이트 기록 파일
UPDATE_HISTORY_FILE = "data/update_history.json"

# 검색 성공 이력 파일 (캡차 입력 성공한 사건번호 목록, '자동 조회' 열 표시용)
SEARCH_LOG_FILE = "data/search_log.json"

# 상태 열 영구 보존용 JSON (사건번호별 직전 상태: 완료/저장 실패 등)
STATUS_HISTORY_FILE = "data/status_history.json"

# 사건 목록 테이블 열 너비 저장 (사용자 리사이즈 값 복원용)
COLUMN_WIDTHS_FILE = "data/column_widths.json"

# 사건 목록 테이블 열 순서 저장 (사용자 설정 복원용)
COLUMN_ORDER_FILE = "data/column_order.json"

# 숨긴 사건번호 목록 (사건목록 관리 - 숨기기/숨김 해제)
HIDDEN_CASES_FILE = "data/hidden_cases.json"

# 우측(진행상황) 패널 너비 저장 (사용자 조절 값 복원용)
RIGHT_PANEL_WIDTH_FILE = "data/right_panel_width.json"

# 테마 설정 저장 (다크/라이트/시스템 선택 복원용)
THEME_CONFIG_FILE = "data/theme_config.json"

# 알림메일: 미발송 내역 저장 파일, 구글 시트 워크시트명, 수신 주소(GUI 설정)
UNSENT_EMAILS_FILE = "data/unsent_emails.json"
NOTIFICATION_WORKSHEET_NAME = "알림메일"
NOTIFICATION_EMAIL_ADDRESS = ""
NOTIFICATION_GAS_WEBAPP_URL = ""  # 웹 앱 배포 URL (즉시 발송용, 비어 있으면 호출 안 함)

# ============================================================================
# 구글 시트 포맷팅 설정
# ============================================================================
# 업데이트 일시 앞에 추가할 빈 줄 개수
EMPTY_ROWS_BEFORE_UPDATE = 5

# 열 너비 설정 (픽셀)
COLUMN_WIDTH_DATE = 200  # 일자 열
COLUMN_WIDTH_CONTENT = 500  # 내용 열

# ============================================================================
# GUI 설정
# ============================================================================
# 메인 창 크기
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 800

# 우측 패널 너비
RIGHT_PANEL_WIDTH = 400

# 사건 목록 행 높이
CASE_ROW_HEIGHT = 60

# 헤더 높이
HEADER_HEIGHT = 40

# UI 테마 (색상, 폰트 등) - (라이트 모드 값, 다크 모드 값) 튜플로 양쪽 대응
# app_controller에서 현재 모드에 따라 인덱스 0(라이트) 또는 1(다크) 사용
# 다크 모드: 사건 목록 밖 영역을 두 번째 참고 사진처럼 통일된 어두운 톤으로 조정
THEME = {
    "bg_primary": ("#F8F9FA", "#1A1A1A"),
    "bg_white": ("#FFFFFF", "#1A1A1A"),
    "bg_header": ("#2C3E50", "#2C3E50"),
    "text_header": ("#FFFFFF", "#FFFFFF"),
    "text_main": ("#2C3E50", "#FFFFFF"),
    "text_sub": ("#7F8C8D", "#BDC3C7"),
    "accent": ("#3498DB", "#3498DB"),
    "success": ("#27AE60", "#27AE60"),
    "warning": ("#F39C12", "#F39C12"),
    "error": ("#E74C3C", "#E74C3C"),
    "hearing_mint": ("#2DD4BF", "#2DD4BF"),
    "row_odd": ("#FFFFFF", "#242424"),
    "row_even": ("#F8F9FA", "#2B2B2B"),
    "border": ("#E0E0E0", "#333333"),
    "font_main": ("Segoe UI", 12),
    "font_bold": ("Segoe UI", 12, "bold"),
    "font_header": ("Segoe UI", 13, "bold"),
    "font_small": ("Segoe UI", 11),
}

# 사건 목록 테이블 컬럼 이름 (고정 인덱스 0~10, 코드에서 열 식별용)
# 인덱스: 0=선택, 1=법원/사건번호, 2=피고/사건명, 3=기일, 4=비고, 5=캡차이미지, 6=캡차입력, 7=상태, 8=자동조회, 9=최근업데이트, 10=시트
COL_NAMES = [
    "선택",
    "법원/사건번호",
    "피고/사건명",
    "기일",
    "비고",
    "캡차 이미지",
    "캡차 입력",
    "상태",
    "자동 조회",
    "최근 업데이트",
    "시트",
]

# 사건 목록 테이블 기본 표시 순서 (COL_NAMES 인덱스 리스트). 비고=가장 우측, 시트=그 왼쪽.
DEFAULT_COL_ORDER = [0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 4]

# 사건 목록 테이블 컬럼 너비 (픽셀) - 인덱스 0~10 순서: 선택, 법원/사건번호, 피고/사건명, 기일, 비고, 캡차이미지, 캡차입력, 상태, 자동조회, 최근업데이트, 시트
COL_WIDTHS = [160, 210, 260, 150, 110, 180, 90, 90, 80, 120, 60]

# ============================================================================
# 사용자 설정 (GUI 편집기용 JSON)
# ============================================================================
# user_settings.json에 저장 가능한 키 목록. 새 항목 추가 시 이 튜플과
# load_user_settings() 내부 매핑, settings_dialog.py 폼을 함께 수정하세요.
USER_SETTINGS_FILE = "data/user_settings.json"
USER_SETTINGS_OVERRIDABLE = (
    "GOOGLE_SHEET_ID",
    "SPREADSHEET_NAME",
    "GOOGLE_AUTH_FILE",
    "CASE_LIST_WORKSHEET_NAME",
    "NOTIFICATION_EMAIL_ADDRESS",
    "NOTIFICATION_GAS_WEBAPP_URL",
    "PUPPETEER_CAPTCHA_TIMEOUT",
    "PUPPETEER_PROCESSING_TIMEOUT",
    "CAPTCHA_INPUT_TIMEOUT",
    "HEADER_IMAGE_PATH",
    "HEADER_BG_COLOR",
    "MAX_PARALLEL_LIMIT",
)


def load_user_settings():
    """
    user_settings.json을 읽어 전역 변수를 덮어씁니다.
    앱 시작 시 진입점(main.py 등)에서 가장 먼저 호출하세요.
    """
    import json
    import os
    this_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(this_dir, USER_SETTINGS_FILE)
    if not os.path.isfile(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return
    if not isinstance(data, dict):
        return
    g = globals()
    for key in USER_SETTINGS_OVERRIDABLE:
        if key not in data:
            continue
        val = data[key]
        if key in ("PUPPETEER_CAPTCHA_TIMEOUT", "PUPPETEER_PROCESSING_TIMEOUT",
                   "CAPTCHA_INPUT_TIMEOUT", "MAX_PARALLEL_LIMIT"):
            try:
                val = int(val)
            except (TypeError, ValueError):
                continue
        if not isinstance(val, (str, int, float)):
            continue
        if key in g:
            g[key] = val


def save_user_settings(data):
    """
    사용자 설정 딕셔너리를 user_settings.json에 저장합니다.
    data는 USER_SETTINGS_OVERRIDABLE에 있는 키만 포함하면 됩니다.
    """
    import json
    import os
    this_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(this_dir, USER_SETTINGS_FILE)
    out = {}
    for key in USER_SETTINGS_OVERRIDABLE:
        if key in data:
            out[key] = data[key]
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    except Exception:
        raise
