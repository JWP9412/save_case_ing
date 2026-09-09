# -*- coding: utf-8 -*-
"""
창 종료 처리
============

메인 창 닫기 시 확인 다이얼로그, 우측 패널 너비 저장, Puppeteer 프로세스 종료, root 파괴.

주니어: 조회 중지/완료 시점에 워커는 이미 정리되어야 합니다.
여기에서는 남은 워커가 있을 때만 안전장치로 한 번 더 정리합니다.
"""
import json
from tkinter import messagebox

import config


def handle_window_closing(app):
    """종료 확인 후 우측 패널 너비 저장, 남은 워커 정리, root.destroy."""
    if not messagebox.askokcancel("종료", "프로그램을 종료하시겠습니까?"):
        return
    if getattr(app, "right_panel", None) is not None:
        try:
            # 접힌 상태면 이미 저장된 펼침 폭을 유지 (탭 폭으로 덮어쓰지 않음)
            if not getattr(app, "_progress_hidden", False) and app.right_panel.winfo_exists():
                w = app.right_panel.winfo_width()
                min_w = int(getattr(config, "RIGHT_PANEL_MIN_WIDTH", 280))
                if w >= min_w:
                    path = getattr(
                        config, "RIGHT_PANEL_WIDTH_FILE", "right_panel_width.json"
                    )
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump({"width": w}, f, indent=2)
        except Exception:
            pass

    # 안전장치: 조회 중 강제 종료 등으로 남은 워커 + 고아 Node 정리
    svc = getattr(app, "puppeteer_service", None)
    if svc is not None:
        try:
            if hasattr(svc, "shutdown_all_workers"):
                svc.shutdown_all_workers()
            else:
                for process in list(getattr(svc, "running_processes", {}).values()):
                    try:
                        process.terminate()
                    except Exception:
                        pass
                # svc 가 옛 버전이어도 고아 interactive_runner 는 쓸어냄
                from services.puppeteer import kill_orphan_interactive_runners

                kill_orphan_interactive_runners(
                    log_fn=getattr(app, "log_message", None)
                )
        except Exception:
            try:
                from services.puppeteer import kill_orphan_interactive_runners

                kill_orphan_interactive_runners(
                    log_fn=getattr(app, "log_message", None)
                )
            except Exception:
                pass
    else:
        # puppeteer_service 자체가 없을 때 (비정상 기동)에도 고아 정리
        try:
            from services.puppeteer import kill_orphan_interactive_runners

            kill_orphan_interactive_runners(log_fn=getattr(app, "log_message", None))
        except Exception:
            pass

    app.root.destroy()
