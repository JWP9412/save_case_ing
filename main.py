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
    """진입점: run_app()으로 창 생성·패널 조립·이벤트 루프 시작."""
    print("=== 일괄 처리 GUI 시작 ===")
    run_app()


if __name__ == "__main__":
    main()
