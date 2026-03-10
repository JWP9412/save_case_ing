# -*- coding: utf-8 -*-
"""
창 종료 처리
============

메인 창 닫기 시 확인 다이얼로그, 우측 패널 너비 저장, Puppeteer 프로세스 종료, root 파괴.
"""
import json
from tkinter import messagebox

import config


def handle_window_closing(app):
    """종료 확인 후 우측 패널 너비 저장, 실행 중 프로세스 종료, root.destroy."""
    if not messagebox.askokcancel("종료", "프로그램을 종료하시겠습니까?"):
        return
    if getattr(app, "right_panel", None) is not None:
        try:
            if app.right_panel.winfo_exists():
                w = app.right_panel.winfo_width()
                path = getattr(
                    config, "RIGHT_PANEL_WIDTH_FILE", "right_panel_width.json"
                )
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"width": w}, f, indent=2)
        except Exception:
            pass
    if hasattr(app, "puppeteer_service"):
        for process in list(app.puppeteer_service.running_processes.values()):
            try:
                process.terminate()
            except Exception:
                pass
    app.root.destroy()
