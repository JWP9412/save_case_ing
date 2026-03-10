# -*- coding: utf-8 -*-
"""
바인딩 유틸리티
===============

위젯 트리에 마우스 휠 이벤트를 재귀적으로 바인딩하는 순수 로직.
"""
import tkinter as tk


def bind_mousewheel_recursive(widget, handler):
    """위젯과 그 자손 모두에 마우스 휠 핸들러를 바인딩 (사건 목록 내 어디서나 휠 스크롤 가능)."""
    try:
        widget.bind("<MouseWheel>", handler)
    except tk.TclError:
        pass
    for child in widget.winfo_children():
        bind_mousewheel_recursive(child, handler)


def bind_mousewheel_to_case_list(case_list_frame, handler):
    """사건 목록 프레임 및 모든 하위 위젯에 마우스 휠 스크롤 바인딩."""
    if case_list_frame is None:
        return
    if not case_list_frame.winfo_exists():
        return
    bind_mousewheel_recursive(case_list_frame, handler)
