# -*- coding: utf-8 -*-
"""
검색 관련 화면 조작 유틸리티
============================

찾기 하이라이트 제거/적용, 스크롤 이동, 매치 개수 라벨 갱신, 다음/이전 검색 수행.
app_controller에서 위젯 참조(app)를 받아 UI만 조작한다.
"""
import tkinter as tk
from tkinter import messagebox

from services.search_manager import find_match_indices

FIND_HIGHLIGHT_TAG = "find_highlight"


class SearchUI:
    """검색 하이라이트·스크롤·카운트 등 검색 관련 UI 조작. app(메인 GUI) 참조로 위젯 접근."""

    def __init__(self, app):
        self._app = app

    def clear_find_highlights(self):
        if not hasattr(self._app, "case_info_text_widgets"):
            return
        for widgets in self._app.case_info_text_widgets.values():
            for w in widgets:
                if w.winfo_exists():
                    try:
                        w.tag_remove(FIND_HIGHLIGHT_TAG, "1.0", tk.END)
                    except (tk.TclError, AttributeError):
                        pass

    def apply_find_highlight(self, row_index, q):
        if not q or not hasattr(self._app, "case_info_text_widgets"):
            return
        widgets = self._app.case_info_text_widgets.get(row_index, [])
        q_lower = q.lower()
        for w in widgets:
            if not w.winfo_exists():
                continue
            try:
                w.configure(state="normal")
                content = w.get("1.0", tk.END).rstrip("\n")
                content_lower = content.lower()
                pos = 0
                while True:
                    idx = content_lower.find(q_lower, pos)
                    if idx < 0:
                        break
                    w.tag_add(
                        FIND_HIGHLIGHT_TAG,
                        f"1.{idx}",
                        f"1.{idx + len(q)}",
                    )
                    pos = idx + 1
                w.tag_config(
                    FIND_HIGHLIGHT_TAG,
                    background="#FFF176",
                    foreground="#000000",
                )
                w.configure(state="disabled")
            except (tk.TclError, AttributeError):
                pass

    def scroll_to_row_and_highlight(self, row_index, query):
        """주어진 row_index로 스크롤하고, 해당 행 하이라이트 및 검색어 형광펜 적용."""
        if not hasattr(self._app, "case_frames") or row_index not in self._app.case_frames:
            return
        row_frame = self._app.case_frames[row_index]
        row_container = row_frame.master
        self._app.case_canvas.update_idletasks()
        bbox = self._app.case_canvas.bbox("all")
        if not bbox:
            return
        total_h = bbox[3] - bbox[1]
        y_in_canvas = row_container.winfo_y()
        fraction = max(0.0, min(1.0, (y_in_canvas - 20) / total_h))
        self._app.case_canvas.yview_moveto(fraction)
        self.clear_find_highlights()
        self.apply_find_highlight(row_index, query)
        orig_fg = (
            self._app.get_theme_color("row_odd")
            if row_index % 2 == 0
            else self._app.get_theme_color("row_even")
        )
        try:
            row_frame.configure(fg_color="#B3D9FF")
            for c in row_frame.winfo_children():
                try:
                    c.configure(fg_color="#B3D9FF")
                except (tk.TclError, AttributeError):
                    try:
                        c.config(bg="#B3D9FF")
                    except Exception:
                        pass
        except Exception:
            pass

        def restore():
            try:
                row_frame.configure(fg_color=orig_fg)
                for c in row_frame.winfo_children():
                    try:
                        c.configure(fg_color=orig_fg)
                    except (tk.TclError, AttributeError):
                        try:
                            c.config(bg=orig_fg)
                        except Exception:
                            pass
            except Exception:
                pass

        self._app.root.after(800, restore)

    def update_search_count(self):
        """검색창 타이핑 시 매치 개수 라벨 갱신 (0/N)."""
        if not hasattr(self._app, "search_count_label") or not self._app.search_count_label.winfo_exists():
            return
        if not hasattr(self._app, "search_entry") or not self._app.search_entry.winfo_exists():
            return
        query = self._app.search_entry.get().strip()
        if not query:
            self._app.search_count_label.configure(text="0/0")
            return
        case_list = getattr(self._app, "case_list", [])
        match_indices = find_match_indices(case_list, query)
        n = len(match_indices)
        self._app.search_count_label.configure(text=f"0/{n}" if n > 0 else "0/0")

    def perform_search(self, query=None, direction="next"):
        """상단 검색창 또는 팝업에서 호출. direction: 'next' 다음, 'prev' 이전."""
        if query is None and hasattr(self._app, "search_entry") and self._app.search_entry.winfo_exists():
            query = self._app.search_entry.get().strip()
        if not query:
            return
        case_list = getattr(self._app, "case_list", [])
        match_indices = find_match_indices(case_list, query)
        if not match_indices:
            messagebox.showinfo("찾기", "검색어와 일치하는 항목이 없습니다.")
            if hasattr(self._app, "search_count_label") and self._app.search_count_label.winfo_exists():
                self._app.search_count_label.configure(text="0/0")
            return
        n = len(match_indices)
        last_query = getattr(self._app, "_last_search_query", "")
        current_index = getattr(self._app, "_current_search_index", 0)
        query_changed = last_query != query
        if query_changed:
            self._app._last_search_query = query
            self._app._current_search_index = 0
            current_index = 0
        else:
            if direction == "next":
                current_index = (current_index + 1) % n
            else:
                current_index = (current_index - 1 + n) % n
            self._app._current_search_index = current_index
        row_index = match_indices[current_index]
        self.scroll_to_row_and_highlight(row_index, query)
        if hasattr(self._app, "search_count_label") and self._app.search_count_label.winfo_exists():
            self._app.search_count_label.configure(text=f"{current_index + 1}/{n}")
