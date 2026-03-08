#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
프로그램 진입점
===============

실행: python main.py
역할: 사용자 설정 로드 후 gui.main_window.run_app()을 호출하여 GUI를 조립·실행합니다.
"""
import config
config.load_user_settings()

from gui.main_window import run_app


def main():
    """진입점: 실행 인자에 따라 CLI 자동 실행 또는 GUI 모드를 시작합니다."""
    import sys
    if "--auto" in sys.argv:
        from auto_runner import run_auto_batch
        run_auto_batch()
    else:
        print("=== 일괄 처리 GUI 시작 ===")
        run_app()


if __name__ == "__main__":
    main()
