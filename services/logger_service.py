# -*- coding: utf-8 -*-
"""
로거 서비스
===========
표준 logging 모듈을 사용한 전역 로거 설정.
- 파일: logs/app.log (날짜별 순환)
- GUI: BatchProcessingGUI의 status_text 위젯과 연동하는 GuiLogHandler
"""
import glob
import logging
import os
from datetime import datetime

# 앱 전역 로거 이름. 다른 모듈은 getLogger(APP_LOGGER_NAME) 사용 권장
APP_LOGGER_NAME = "case_ing"
LOG_DIR = "logs"
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"
MAX_LOG_FILES = 10

# 모듈이 로드될 때 현재 실행의 로그 파일 이름 생성
current_time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = os.path.join(LOG_DIR, f"app_{current_time_str}.log")

# 하위 호환성을 위해 최근 로그 파일 반환
def get_latest_log_file():
    _ensure_log_dir()
    log_files = glob.glob(os.path.join(LOG_DIR, "app_*.log"))
    if not log_files:
        return LOG_FILE
    return sorted(log_files)[-1]


def _ensure_log_dir():
    if not os.path.isdir(LOG_DIR):
        try:
            os.makedirs(LOG_DIR, exist_ok=True)
        except OSError:
            pass

def _cleanup_old_logs():
    """로그 디렉토리에서 오래된 로그 파일을 삭제하여 MAX_LOG_FILES 개수만 유지합니다."""
    try:
        _ensure_log_dir()
        log_files = glob.glob(os.path.join(LOG_DIR, "app_*.log"))
        log_files.sort() # 이름에 타임스탬프가 있으므로 정렬하면 오래된 순
        
        if len(log_files) > MAX_LOG_FILES:
            files_to_delete = log_files[:-MAX_LOG_FILES]
            for f in files_to_delete:
                try:
                    os.remove(f)
                except OSError:
                    pass
    except Exception:
        pass


def setup_logger():
    """
    전역 로거를 설정합니다. 실행 시마다 새로운 파일 핸들러를 등록합니다.
    GUI 핸들러는 register_gui_handler()로 UI 생성 후 등록하세요.
    """
    _ensure_log_dir()
    _cleanup_old_logs()
    
    logger = logging.getLogger(APP_LOGGER_NAME)
    
    # 이미 파일 핸들러가 있으면 추가하지 않음
    has_file_handler = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
    
    if not has_file_handler:
        logger.setLevel(logging.DEBUG)
        try:
            # FileHandler를 사용하여 매 실행마다 새로운 파일에 기록
            fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
            logger.addHandler(fh)
        except Exception:
            pass
    return logger


class GuiLogHandler(logging.Handler):
    """
    logging.Handler 서브클래스. 로그 메시지를 메인 스레드의 큐에 넣습니다.
    (직접 after를 호출하면 많은 로그가 몰릴 때 프리징 발생)
    """

    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance  # BatchProcessingGUI 인스턴스

    def emit(self, record):
        try:
            msg = self.format(record)
            if hasattr(self.app_instance, "ui_queue"):
                self.app_instance.ui_queue.put(("log", (msg,), {}))
        except Exception:
            self.handleError(record)


def register_gui_handler(app_instance):
    """
    앱 로거에 GuiLogHandler를 등록합니다.
    """
    logger = logging.getLogger(APP_LOGGER_NAME)
    for h in logger.handlers:
        if isinstance(h, GuiLogHandler):
            logger.removeHandler(h)
    gui_handler = GuiLogHandler(app_instance)
    gui_handler.setLevel(logging.INFO)
    gui_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
    logger.addHandler(gui_handler)


def get_logger(name=None):
    """앱 로거를 반환합니다. name이 있으면 자식 로거를 반환합니다."""
    if name:
        return logging.getLogger(f"{APP_LOGGER_NAME}.{name}")
    return logging.getLogger(APP_LOGGER_NAME)


def get_available_log_paths():
    """
    logs/ 디렉터리의 app_YYYYMMDD_HHMMSS.log 목록을 반환합니다.
    반환: [(display_name, absolute_path), ...], 최신 순.
    """
    base = os.path.abspath(LOG_DIR)
    if not os.path.isdir(base):
        return []
    
    # 예전의 app.log 파일도 포함하기 위해 app*.log 패턴 사용
    pattern = os.path.join(base, "app*.log")
    paths = []
    
    # 현재 실행 중인 파일도 표시하기 위함
    current_basename = os.path.basename(LOG_FILE)
    
    for path in glob.glob(pattern):
        if not os.path.isfile(path):
            continue
        name = os.path.basename(path)
        
        # 파일의 수정 시간 기준으로 정렬
        mtime = os.path.getmtime(path)
        
        if name == current_basename:
            display = f"현재 세션 ({name})"
            sort_key = (0, -mtime)  # 항상 맨 위
        elif name == "app.log":
            display = "이전 통합 로그 (app.log)"
            sort_key = (1, -mtime)
        else:
            # app_YYYYMMDD_HHMMSS.log 형식에서 시간 추출 시도
            try:
                # "app_20260305_100000.log" -> "2026-03-05 10:00:00" 포맷으로 변경
                if name.startswith("app_") and name.endswith(".log"):
                    time_part = name[4:-4] # "20260305_100000"
                    date_str = f"{time_part[:4]}-{time_part[4:6]}-{time_part[6:8]} {time_part[9:11]}:{time_part[11:13]}:{time_part[13:15]}"
                    display = f"{date_str} ({name})"
                else:
                    display = name
            except Exception:
                display = name
                
            sort_key = (1, -mtime)  # 최신 수정일자가 먼저 오도록
            
        paths.append((display, path, sort_key))
        
    paths.sort(key=lambda x: x[2])
    return [(d, p) for d, p, _ in paths]
