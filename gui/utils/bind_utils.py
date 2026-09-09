# -*- coding: utf-8 -*-
"""
바인딩 유틸리티
===============

위젯에 마우스 휠·Enter 키를 거는 로직.

주니어 참고:
- 예전에는 행의 모든 자식에 MouseWheel 을 재귀 bind 해서 위젯이 많을수록 느렸습니다.
- 지금은 목록 위에 커서가 있을 때만 bind_all 로 한 번만 겁니다.
"""
import tkinter as tk


def bind_mousewheel_recursive(widget, handler):
    """(레거시) 위젯과 자손 모두에 휠 바인딩. 사건 목록은 bind_all 방식을 쓰세요."""
    try:
        widget.bind("<MouseWheel>", handler)
    except tk.TclError:
        pass
    for child in widget.winfo_children():
        bind_mousewheel_recursive(child, handler)


def _is_descendant(widget, ancestors):
    """widget 이 ancestors 중 하나의 자손(또는 본인)인지."""
    w = widget
    while w is not None:
        if w in ancestors:
            return True
        try:
            w = w.master
        except Exception:
            break
    return False


def bind_mousewheel_to_case_list(case_list_frame, handler):
    """
    사건 목록 영역 위에 커서가 있을 때만 목록을 스크롤합니다.

    중요: unbind_all 을 쓰지 않습니다.
    unbind_all 하면 CTkScrollableFrame 등 다른 창의 휠 바인딩까지 사라져
    수동 캡차 창 등에서 스크롤이 안 됩니다.
    """
    if case_list_frame is None:
        return
    if not case_list_frame.winfo_exists():
        return

    root = case_list_frame.winfo_toplevel()
    canvas = None
    try:
        parent = case_list_frame.master
        if parent is not None and parent.winfo_exists():
            canvas = parent
    except Exception:
        canvas = None

    ancestors = {case_list_frame}
    if canvas is not None:
        ancestors.add(canvas)

    def _wrapped(event):
        w = event.widget
        try:
            if not _is_descendant(w, ancestors):
                # 이벤트 위젯이 목록이 아니면 포인터 위치도 확인
                containing = root.winfo_containing(event.x_root, event.y_root)
                if not _is_descendant(containing, ancestors):
                    return
        except Exception:
            return
        try:
            return handler(event)
        except Exception:
            return

    # add="+" 로 기존(CTk 등) 휠 핸들러를 지우지 않음
    try:
        root.bind_all("<MouseWheel>", _wrapped, add="+")
    except tk.TclError:
        pass
    for t in (case_list_frame, canvas):
        if t is None:
            continue
        try:
            t.bind("<MouseWheel>", _wrapped, add="+")
        except tk.TclError:
            pass


def bind_mousewheel_to_scrollable(scrollable_frame, window=None):
    """
    CTkScrollableFrame 이 있는 창에서 마우스 휠이 항상 동작하도록 연결합니다.

    창을 만들 때 기본으로 호출하세요.
    - 포인터가 해당 창 위에 있을 때만 스크롤합니다.
    - bind_all 을 덮어쓰지 않고 add="+" 로 추가합니다.
    """
    if scrollable_frame is None:
        return
    canvas = getattr(scrollable_frame, "_parent_canvas", None)
    if canvas is None:
        return

    window = window or scrollable_frame.winfo_toplevel()
    ancestors = {window, scrollable_frame, canvas}

    def _handler(event):
        try:
            if not window.winfo_exists():
                return
            w = event.widget
            if not _is_descendant(w, ancestors):
                containing = window.winfo_containing(event.x_root, event.y_root)
                if not _is_descendant(containing, ancestors):
                    return
            # 스크롤할 내용이 없으면 무시
            if canvas.yview() == (0.0, 1.0):
                return
            # Windows: delta 보통 ±120
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def _bind_tree(widget):
        """자식 위젯에도 직접 휠을 겁니다(입력칸 위에서 먹게)."""
        try:
            widget.bind("<MouseWheel>", _handler, add="+")
        except tk.TclError:
            pass
        try:
            children = widget.winfo_children()
        except Exception:
            return
        for child in children:
            _bind_tree(child)

    try:
        window.bind_all("<MouseWheel>", _handler, add="+")
    except tk.TclError:
        pass
    _bind_tree(window)

    # 행이 나중에 추가되어도 다시 걸 수 있게 보관
    scrollable_frame._case_ing_wheel_rebind = lambda: _bind_tree(scrollable_frame)


def rebind_scrollable_mousewheel(scrollable_frame):
    """스크롤 프레임에 행을 추가한 뒤 휠 바인딩을 갱신합니다."""
    rebind = getattr(scrollable_frame, "_case_ing_wheel_rebind", None)
    if callable(rebind):
        try:
            rebind()
        except Exception:
            pass


def bind_entry_return(widget, callback):
    """
    CTkEntry / tk.Entry 에 Enter·키패드 Enter 바인딩.

    CustomTkinter CTkEntry 는 내부 tk.Entry(`_entry`)에도 같이 겁니다.
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
