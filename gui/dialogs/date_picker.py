# -*- coding: utf-8 -*-
"""
달력 팝업 (외부 패키지 없이)
===========================

주니어 개발자 참고:
- tkcalendar / babel 을 쓰면 PyInstaller 포터블 빌드에서 로케일 데이터 hidden-import
  문제가 자주 납니다. 그래서 표준 calendar 모듈 + CTk 버튼 그리드로 직접 만듭니다.
- 날짜를 고르면 on_select(date) 콜백을 호출하고 창을 닫습니다.
"""
from __future__ import annotations

import calendar
import tkinter as tk
from datetime import date

import customtkinter as ctk

from services.date_utils import format_date


class DatePickerPopup(ctk.CTkToplevel):
    """월 단위 달력 팝업. 날짜 클릭 시 on_select(date) 호출."""

    WEEKDAYS = ("월", "화", "수", "목", "금", "토", "일")

    def __init__(self, parent, initial=None, on_select=None, title="날짜 선택"):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.on_select = on_select
        self.selected = initial or date.today()
        self.view_year = self.selected.year
        self.view_month = self.selected.month
        self.transient(parent)
        self.grab_set()

        self._build()
        self._place_near_parent(parent)
        self.focus_force()

    def _place_near_parent(self, parent):
        try:
            self.update_idletasks()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty() + parent.winfo_height() + 4
            self.geometry(f"+{px}+{py}")
        except Exception:
            pass

    def _build(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill=tk.X, padx=8, pady=(8, 4))

        ctk.CTkButton(
            self.header, text="◀", width=36, command=self._prev_month
        ).pack(side=tk.LEFT)
        self.month_label = ctk.CTkLabel(
            self.header,
            text="",
            font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold"),
        )
        self.month_label.pack(side=tk.LEFT, expand=True)
        ctk.CTkButton(
            self.header, text="▶", width=36, command=self._next_month
        ).pack(side=tk.RIGHT)

        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(padx=8, pady=4)

        for i, name in enumerate(self.WEEKDAYS):
            ctk.CTkLabel(
                self.grid_frame,
                text=name,
                width=36,
                font=ctk.CTkFont(family="맑은 고딕", size=11),
            ).grid(row=0, column=i, padx=1, pady=1)

        self.day_buttons = []
        for r in range(6):
            row_btns = []
            for c in range(7):
                btn = ctk.CTkButton(
                    self.grid_frame,
                    text="",
                    width=36,
                    height=28,
                    fg_color="transparent",
                    text_color=("gray10", "gray90"),
                    hover_color=("gray80", "gray30"),
                    command=lambda rr=r, cc=c: self._on_day_click(rr, cc),
                )
                btn.grid(row=r + 1, column=c, padx=1, pady=1)
                row_btns.append(btn)
            self.day_buttons.append(row_btns)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill=tk.X, padx=8, pady=(4, 8))
        ctk.CTkButton(
            footer, text="오늘", width=70, command=self._pick_today
        ).pack(side=tk.LEFT)
        ctk.CTkButton(
            footer, text="닫기", width=70, command=self.destroy
        ).pack(side=tk.RIGHT)

        self._refresh()

    def _prev_month(self):
        if self.view_month == 1:
            self.view_year -= 1
            self.view_month = 12
        else:
            self.view_month -= 1
        self._refresh()

    def _next_month(self):
        if self.view_month == 12:
            self.view_year += 1
            self.view_month = 1
        else:
            self.view_month += 1
        self._refresh()

    def _pick_today(self):
        self._choose(date.today())

    def _refresh(self):
        self.month_label.configure(text=f"{self.view_year}년 {self.view_month}월")
        cal = calendar.Calendar(firstweekday=0)  # 월요일 시작
        weeks = cal.monthdayscalendar(self.view_year, self.view_month)
        today = date.today()
        # 최대 6주 그리드
        while len(weeks) < 6:
            weeks.append([0] * 7)

        self._day_map = {}  # (r,c) -> day int
        for r in range(6):
            for c in range(7):
                day = weeks[r][c] if r < len(weeks) else 0
                self._day_map[(r, c)] = day
                btn = self.day_buttons[r][c]
                if day == 0:
                    btn.configure(text="", state="disabled", fg_color="transparent")
                else:
                    d = date(self.view_year, self.view_month, day)
                    is_today = d == today
                    is_selected = d == self.selected
                    fg = "#3498DB" if is_selected else ("#1ABC9C" if is_today else "transparent")
                    btn.configure(
                        text=str(day),
                        state="normal",
                        fg_color=fg,
                        text_color="#FFFFFF" if (is_today or is_selected) else ("gray10", "gray90"),
                    )

    def _on_day_click(self, r, c):
        day = self._day_map.get((r, c), 0)
        if day:
            self._choose(date(self.view_year, self.view_month, day))

    def _choose(self, d):
        self.selected = d
        if callable(self.on_select):
            self.on_select(d)
        self.destroy()


def attach_date_entry(parent, entry_widget, initial=None):
    """
    입력칸 옆에 달력 버튼을 붙입니다.
    entry_widget 는 CTkEntry (문자열로 YYYY.MM.DD 를 담음).
    반환: 달력 버튼 위젯.
    """
    def _open():
        cur = None
        try:
            from services.date_utils import parse_date
            cur = parse_date(entry_widget.get()) or initial
        except Exception:
            cur = initial

        def _on_pick(d):
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, format_date(d))

        DatePickerPopup(parent, initial=cur, on_select=_on_pick)

    btn = ctk.CTkButton(parent, text="달력", width=56, command=_open)
    return btn
