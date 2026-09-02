# -*- coding: utf-8 -*-
"""
바인딩 유틸리티
===============

위젯 트리에 마우스 휠 이벤트를 재귀적으로 바인딩하는 순수 로직.
CTkEntry Enter 키 바인딩(내부 _entry 포함)도 여기서 처리합니다.
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


def bind_entry_return(widget, callback):
    """
    CTkEntry / tk.Entry 에 Enter·키패드 Enter 바인딩.

    주니어 개발자 참고:
    - CustomTkinter CTkEntry 는 실제 키 입력을 내부 tk.Entry(`_entry`)가 받습니다.
      바깥 위젯에만 bind 하면 Enter 가 무시되는 경우가 많아 `_entry`에도 같이 겁니다.
    - 콜백이 무엇을 반환하든 이벤트 전파를 막기 위해 항상 "break" 를 반환합니다.
    """

    def _wrapped(event):
        try:
            callback(event)
        except Exception:
            pass
        return "break"

    targets = [widget]
    inner = getattr(widget, "_entry", None)
    if inner is not None and inner not in targets:
        targets.append(inner)

    for target in targets:
        for seq in ("<Return>", "<KP_Enter>"):
            try:
                target.bind(seq, _wrapped)
            except tk.TclError:
                pass
