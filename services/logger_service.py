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
from logging.handlers import TimedRotatingFileHandler

# 앱 전역 로거 이름. 다른 모듈은 getLogger(APP_LOGGER_NAME) 사용 권장
APP_LOGGER_NAME = "case_ing"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"


def _ensure_log_dir():
    if not os.path.isdir(LOG_DIR):
        try:
            os.makedirs(LOG_DIR, exist_ok=True)
        except OSError:
            pass


def setup_logger():
    """
    전역 로거를 설정합니다. 파일 핸들러만 등록합니다.
    GUI 핸들러는 register_gui_handler()로 UI 생성 후 등록하세요.
    """
    _ensure_log_dir()
    logger = logging.getLogger(APP_LOGGER_NAME)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    try:
        fh = TimedRotatingFileHandler(
            LOG_FILE,
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8",
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
        logger.addHandler(fh)
    except Exception:
        pass
    return logger


class GuiLogHandler(logging.Handler):
    """
    logging.Handler 서브클래스. 로그 메시지를 메인 스레드에서
    status_text 위젯에 추가합니다. root.after(0, ...)로 스레드 세이프하게 동작합니다.
    """

    def __init__(self, root, status_text_getter):
        super().__init__()
        self.root = root
        self.status_text_getter = status_text_getter  # callable that returns CTkTextbox

    def emit(self, record):
        try:
            msg = self.format(record)
            widget = self.status_text_getter() if callable(self.status_text_getter) else self.status_text_getter
            if widget is None:
                return

            def _append():
                try:
                    if widget.winfo_exists():
                        widget.insert("end", msg + "\n")
                        widget.see("end")
                except Exception:
                    pass

            self.root.after(0, _append)
        except Exception:
            self.handleError(record)


def register_gui_handler(root, status_text_getter):
    """
    앱 로거에 GuiLogHandler를 등록합니다.
    status_text_getter: status_text 위젯을 반환하는 callable 또는 위젯 자체.
    """
    logger = logging.getLogger(APP_LOGGER_NAME)
    for h in logger.handlers:
        if isinstance(h, GuiLogHandler):
            logger.removeHandler(h)
    gui_handler = GuiLogHandler(root, status_text_getter)
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
    logs/ 디렉터리의 app.log 및 app.log.* (날짜 suffix) 목록을 반환합니다.
    반환: [(display_name, absolute_path), ...], 최신 순.
    """
    base = os.path.abspath(LOG_DIR)
    if not os.path.isdir(base):
        return []
    pattern = os.path.join(base, "app.log*")
    paths = []
    for path in glob.glob(pattern):
        if not os.path.isfile(path):
            continue
        name = os.path.basename(path)
        if name == "app.log":
            display = "오늘 (app.log)"
            sort_key = (0, 0)  # current first
        else:
            suffix = name[8:] if name.startswith("app.log.") else ""
            display = suffix if suffix else name
            try:
                from datetime import datetime
                dt = datetime.strptime(suffix, "%Y-%m-%d")
                sort_key = (1, -dt.timestamp())  # rotated, newer first
            except (ValueError, TypeError):
                sort_key = (1, 0)
        paths.append((display, path, sort_key))
    paths.sort(key=lambda x: x[2])
    return [(d, p) for d, p, _ in paths]
