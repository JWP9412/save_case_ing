# -*- coding: utf-8 -*-
"""
크래시 / 미처리 예외 가드
========================
프로그램이 로그 없이 종료되는 문제를 줄이기 위해,
네이티브 크래시·메인/워커 스레드 예외·Tk after 콜백 예외를 파일 로그에 남깁니다.

주니어 개발자 참고:
- faulthandler: C 확장/네이티브(세그폴트 등) 크래시 시 스택을 파일에 덤프합니다.
- sys.excepthook: 메인 스레드에서 잡히지 않은 예외
- threading.excepthook: 워커(daemon) 스레드에서 잡히지 않은 예외
- Tk.report_callback_exception: root.after / 이벤트 콜백에서 난 예외
"""
from __future__ import annotations

import faulthandler
import logging
import os
import sys
import threading
import traceback
from datetime import datetime

_installed = False
_faulthandler_fp = None  # 파일 핸들을 유지해야 faulthandler가 계속 기록함


def _get_logger():
    """로거가 아직 없으면 표준 로깅으로라도 남깁니다."""
    try:
        from services.logger_service import get_logger

        return get_logger("crash_guard")
    except Exception:
        return logging.getLogger("case_ing.crash_guard")


def _log_dir():
    try:
        import config

        return os.path.join(config.get_base_dir(), "logs")
    except Exception:
        return os.path.join(os.getcwd(), "logs")


def install_crash_guard():
    """
    프로세스 시작 직후 한 번 호출합니다 (main.py).
    GUI root가 아직 없어도 faulthandler / excepthook 은 먼저 설치합니다.
    """
    global _installed, _faulthandler_fp
    if _installed:
        return
    _installed = True

    log_dir = _log_dir()
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception:
        pass

    # --- faulthandler: 네이티브 크래시 스택 ---
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fh_path = os.path.join(log_dir, f"faulthandler_{stamp}.log")
    try:
        _faulthandler_fp = open(fh_path, "a", encoding="utf-8", buffering=1)
        faulthandler.enable(file=_faulthandler_fp, all_threads=True)
        _get_logger().info(f"faulthandler 활성화: {fh_path}")
    except Exception as e:
        # 파일 열기 실패 시 stderr로라도 켭니다.
        try:
            faulthandler.enable(all_threads=True)
        except Exception:
            pass
        _get_logger().warning(f"faulthandler 파일 열기 실패, stderr 사용: {e}")

    # --- 메인 스레드 미처리 예외 ---
    previous_excepthook = sys.excepthook

    def _sys_excepthook(exc_type, exc_value, exc_tb):
        try:
            _get_logger().critical(
                "미처리 예외 (메인 스레드)",
                exc_info=(exc_type, exc_value, exc_tb),
            )
        except Exception:
            pass
        # 기본 동작(stderr 출력)도 유지
        try:
            previous_excepthook(exc_type, exc_value, exc_tb)
        except Exception:
            pass

    sys.excepthook = _sys_excepthook

    # --- 워커 스레드 미처리 예외 (Python 3.8+) ---
    if hasattr(threading, "excepthook"):
        previous_thread_hook = threading.excepthook

        def _thread_excepthook(args):
            # args: threading.ExceptHookArgs (exc_type, exc_value, exc_traceback, thread)
            try:
                name = getattr(args.thread, "name", "?")
                _get_logger().critical(
                    f"미처리 예외 (스레드: {name})",
                    exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
                )
            except Exception:
                pass
            try:
                previous_thread_hook(args)
            except Exception:
                pass

        threading.excepthook = _thread_excepthook


def attach_tk_callback_guard(root):
    """
    Tk root 생성 후 호출합니다 (window_bootstrap).
    after / 이벤트 콜백에서 난 예외를 파일 로그에 남깁니다.
    """
    if root is None:
        return

    def _report_callback_exception(exc, val, tb):
        try:
            _get_logger().critical(
                "Tk 콜백 예외 (after/이벤트)",
                exc_info=(exc, val, tb),
            )
        except Exception:
            # 로거조차 실패하면 stderr에라도
            try:
                traceback.print_exception(exc, val, tb)
            except Exception:
                pass

    try:
        root.report_callback_exception = _report_callback_exception
    except Exception as e:
        _get_logger().warning(f"Tk report_callback_exception 설치 실패: {e}")
