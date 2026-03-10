# -*- coding: utf-8 -*-
"""
메인 창 생성 및 서비스 초기화
=============================

CTk 루트 생성, geometry·중앙 배치, WM_DELETE 바인딩, Tk 변수·로거·서비스 객체 생성.
호출 전에 app에서 테마(_load_theme_setting / _apply_theme)는 이미 적용된 상태를 가정.
"""
import threading

import config
import customtkinter as ctk
import tkinter as tk

from services.google_sheets import GoogleSheetsService
from services.puppeteer import PuppeteerService
from services.process_controller import ProcessController
from services.history_manager import HistoryManager
from services.logger_service import setup_logger
from services import update_history as update_history_service


def create_root_and_services(app):
    """
    app.root 생성, 설정, Tk 변수·로거·서비스 초기화 후 app.root 반환.
    테마는 호출 전에 app._load_theme_setting() / app._apply_theme() 로 적용되어 있어야 함.
    """
    app.root = ctk.CTk()
    app.root.title(f"{config.APP_TITLE} v{config.APP_VERSION}")
    w, h = config.WINDOW_WIDTH, config.WINDOW_HEIGHT
    app.root.geometry(f"{w}x{h}")
    app.root.resizable(True, True)

    app.root.protocol("WM_DELETE_WINDOW", app.on_closing)

    app.root.update_idletasks()
    sw = app.root.winfo_screenwidth()
    sh = app.root.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    app.root.geometry(f"{w}x{h}+{x}+{y}")

    app.header_select_all_var = tk.BooleanVar(value=False)
    app.max_parallel = tk.IntVar(value=config.DEFAULT_MAX_PARALLEL)
    app.max_retry = tk.IntVar(value=config.DEFAULT_MAX_RETRY)
    app.retry_delay = tk.IntVar(value=config.DEFAULT_RETRY_DELAY)

    setup_logger()

    app.google_sheets_service = GoogleSheetsService()
    app.puppeteer_service = PuppeteerService()
    app.history_manager = update_history_service.HistoryManager()
    app.log_history_manager = HistoryManager(app)
    max_profiles = getattr(config, "MAX_PARALLEL_LIMIT", 20)
    app.profile_locks = [threading.Lock() for _ in range(max_profiles)]
    app.process_controller = ProcessController(app)

    return app.root
