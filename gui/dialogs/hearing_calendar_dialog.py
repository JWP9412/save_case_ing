# -*- coding: utf-8 -*-
"""
미어캣싱 · 기일 달력
====================

등록된 사건의 변론기일·감정기일·판결선고기일을 월간 달력으로 보여 줍니다.
구글 캘린더가 아니라 미어캣싱 앱 안의 창입니다.

주니어 개발자 참고:
- 데이터: update_history.json 의 hearing_events (조회 성공 시 저장).
- hearing_events가 없으면 hearing_info(목록용 최신 1건)를 폴백으로 사용합니다.
- 날짜 칸 안에 「• 이름 종류」요약을 바로 보여, 클릭 없이도 한눈에 볼 수 있습니다.
"""
from __future__ import annotations

import calendar
import tkinter as tk
from collections import defaultdict
from datetime import date, datetime

import customtkinter as ctk

import config
from services.date_utils import parse_datetime_loose
from services.update_history import parse_hearing_info_to_event


# 기일 종류별 점/강조 색
KIND_COLORS = {
    "변론기일": "#3498DB",
    "감정기일": "#9B59B6",
    "판결선고기일": "#E67E22",
}
DEFAULT_KIND_COLOR = "#7F8C8D"

# 칸 안 짧은 종류 표기
KIND_SHORT = {
    "변론기일": "변론",
    "감정기일": "감정",
    "판결선고기일": "판결",
}

CELL_W = 100
CELL_H = 82
NAME_MAX = 8  # 칸 안 이름 최대 글자 수
MAX_LINES_IN_CELL = 2


def _parse_event_day(start_val):
    """hearing_events.start(ISO 등) → date | None"""
    if isinstance(start_val, datetime):
        return start_val.date()
    if isinstance(start_val, date):
        return start_val
    dt = parse_datetime_loose(start_val)
    return dt.date() if dt else None


def _short_name(item):
    """칸 표시용 짧은 이름: 피고 > 사건명 > 사건번호."""
    for key in ("피고", "사건명", "사건번호"):
        val = (item.get(key) or "").strip()
        if val:
            if len(val) > NAME_MAX:
                return val[: NAME_MAX - 1] + "…"
            return val
    return "?"


def _cell_line(item):
    """칸 한 줄: '• 이름 변론'"""
    kind = item.get("kind") or ""
    short_kind = KIND_SHORT.get(kind, kind.replace("기일", "") or "?")
    return f"• {_short_name(item)} {short_kind}"


def _append_event_item(items, case_number, meta, ev):
    """이벤트 dict 하나를 달력 항목으로 추가. 성공 시 True."""
    if not isinstance(ev, dict):
        return False
    kind = (ev.get("kind") or "").strip()
    if kind not in ("변론기일", "감정기일", "판결선고기일"):
        return False
    day = _parse_event_day(ev.get("start"))
    if day is None:
        return False
    start_raw = ev.get("start") or ""
    time_str = ""
    dt = parse_datetime_loose(start_raw)
    if dt:
        time_str = dt.strftime("%H:%M")
    defendant = meta.get("피고", "") if isinstance(meta, dict) else ""
    case_name = meta.get("사건명", "") if isinstance(meta, dict) else ""
    items.append(
        {
            "day": day,
            "kind": kind,
            "label": (ev.get("label") or f"{kind}").strip(),
            "start": start_raw,
            "time_str": time_str,
            "사건번호": str(case_number),
            "피고": defendant or "",
            "사건명": case_name or "",
        }
    )
    return True


def collect_hearing_items(history, case_list):
    """
    history + case_list → 달력용 항목 리스트.

    hearing_events가 비어 있으면 hearing_info(최신 1건)를 폴백으로 넣습니다.
    """
    case_map = {}
    for c in case_list or []:
        if not isinstance(c, dict):
            continue
        cn = str(c.get("사건번호", "")).strip()
        if cn:
            case_map[cn] = c

    items = []
    for case_number, rec in (history or {}).items():
        if not isinstance(rec, dict):
            continue
        meta = case_map.get(str(case_number), {})
        events = rec.get("hearing_events") or []
        added = 0
        if isinstance(events, list):
            for ev in events:
                if _append_event_item(items, case_number, meta, ev):
                    added += 1
        # 조회 전 이력: hearing_info만 있는 경우 달력에도 보이도록
        if added == 0:
            fallback = parse_hearing_info_to_event(rec.get("hearing_info") or "")
            if fallback:
                _append_event_item(items, case_number, meta, fallback)
    return items


class HearingCalendarDialog(ctk.CTkToplevel):
    """미어캣싱 기일 월간 달력 (칸 안 요약 표시)."""

    WEEKDAYS = ("월", "화", "수", "목", "금", "토", "일")

    def __init__(self, parent, items=None, title=None):
        super().__init__(parent)
        app_name = getattr(config, "APP_TITLE", "미어캣싱")
        self.title(title or f"{app_name} · 기일 달력")
        self.geometry("820x640")
        self.transient(parent)

        self.items = list(items or [])
        self.by_day = defaultdict(list)
        for it in self.items:
            self.by_day[it["day"]].append(it)

        today = date.today()
        self.view_year = today.year
        self.view_month = today.month
        self.selected_day = today

        self._build()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        try:
            self.focus_force()
        except Exception:
            pass

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill=tk.X, padx=12, pady=10)

        ctk.CTkButton(top, text="◀", width=40, command=self._prev_month).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        self.month_label = ctk.CTkLabel(
            top,
            text="",
            font=ctk.CTkFont(family="맑은 고딕", size=16, weight="bold"),
        )
        self.month_label.pack(side=tk.LEFT, padx=8)
        ctk.CTkButton(top, text="▶", width=40, command=self._next_month).pack(
            side=tk.LEFT, padx=(6, 0)
        )
        ctk.CTkButton(top, text="오늘", width=60, command=self._goto_today).pack(
            side=tk.LEFT, padx=(12, 0)
        )

        legend = ctk.CTkFrame(top, fg_color="transparent")
        legend.pack(side=tk.RIGHT)
        for kind, color in KIND_COLORS.items():
            ctk.CTkLabel(
                legend,
                text=f"● {kind.replace('기일', '')}",
                text_color=color,
                font=ctk.CTkFont(family="맑은 고딕", size=11),
            ).pack(side=tk.LEFT, padx=4)

        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))

        self.detail_title = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
            anchor="w",
        )
        self.detail_title.pack(fill=tk.X, padx=12, pady=(0, 4))

        self.detail_box = ctk.CTkTextbox(
            self, height=120, font=ctk.CTkFont(family="맑은 고딕", size=12)
        )
        self.detail_box.pack(fill=tk.X, padx=12, pady=(0, 8))

        hint = ctk.CTkLabel(
            self,
            text=(
                "안내: 칸 안 「• 이름 종류」는 클릭 없이 보입니다. "
                "hearing_events가 없으면 목록의 최신 기일(hearing_info)을 표시합니다."
            ),
            font=ctk.CTkFont(family="맑은 고딕", size=11),
            text_color="#7F8C8D",
            anchor="w",
            wraplength=780,
            justify="left",
        )
        hint.pack(fill=tk.X, padx=12, pady=(0, 10))

        self._render_month()
        self._show_day(self.selected_day)

    def _prev_month(self):
        if self.view_month == 1:
            self.view_year -= 1
            self.view_month = 12
        else:
            self.view_month -= 1
        self._render_month()

    def _next_month(self):
        if self.view_month == 12:
            self.view_year += 1
            self.view_month = 1
        else:
            self.view_month += 1
        self._render_month()

    def _goto_today(self):
        today = date.today()
        self.view_year = today.year
        self.view_month = today.month
        self.selected_day = today
        self._render_month()
        self._show_day(today)

    def _cell_colors(self, d, day_items, today):
        """
        칸 배경/테두리/글자색.
        - 기일 없는 날은 어두운 기본색 (선택만으로 '기일 칸'처럼 보이지 않음)
        - 기일 있는 날은 살짝 밝은 강조
        - 오늘/선택은 테두리로 구분
        """
        has = bool(day_items)
        is_today = d == today
        is_sel = d == self.selected_day
        if has:
            fg = "#2C3E50"
        else:
            fg = "#3D3D3D"
        if is_today:
            border = "#1ABC9C"
        elif is_sel:
            border = "#2980B9"
        elif has:
            border = KIND_COLORS.get(day_items[0]["kind"], "#5D6D7E")
        else:
            border = fg
        return fg, border, has, is_today, is_sel

    def _make_day_cell(self, parent, d, day_items, row, col):
        """날짜 + 인라인 요약이 있는 클릭 가능 칸."""
        today = date.today()
        fg, border, has, is_today, is_sel = self._cell_colors(d, day_items, today)

        # 바깥 프레임 = 테두리 역할
        outer = ctk.CTkFrame(
            parent,
            width=CELL_W,
            height=CELL_H,
            fg_color=border,
            corner_radius=6,
            cursor="hand2",
        )
        outer.grid(row=row, column=col, padx=2, pady=2)
        outer.grid_propagate(False)

        inner = ctk.CTkFrame(
            outer,
            width=CELL_W - 4,
            height=CELL_H - 4,
            fg_color=fg,
            corner_radius=4,
            cursor="hand2",
        )
        inner.place(relx=0.5, rely=0.5, anchor="center")
        inner.pack_propagate(False)

        day_label = ctk.CTkLabel(
            inner,
            text=str(d.day),
            font=ctk.CTkFont(
                family="맑은 고딕",
                size=12,
                weight="bold" if (is_today or is_sel or has) else "normal",
            ),
            text_color="#FFFFFF" if not is_today else "#1ABC9C",
            anchor="w",
        )
        day_label.pack(fill=tk.X, padx=4, pady=(2, 0))

        # 칸 안 요약: 최대 2줄, 넘치면 +N
        sorted_items = sorted(
            day_items,
            key=lambda x: (x.get("time_str") or "", x.get("사건번호") or ""),
        )
        lines = [_cell_line(it) for it in sorted_items[:MAX_LINES_IN_CELL]]
        extra = len(sorted_items) - MAX_LINES_IN_CELL
        if extra > 0:
            if len(lines) >= MAX_LINES_IN_CELL:
                lines[-1] = f"+{extra + 1}건 더"
            else:
                lines.append(f"+{extra}건 더")

        summary_text = "\n".join(lines) if lines else ""
        if summary_text:
            # 첫 기일 색으로 요약 글자색
            first_color = KIND_COLORS.get(
                sorted_items[0]["kind"], DEFAULT_KIND_COLOR
            )
            sum_label = ctk.CTkLabel(
                inner,
                text=summary_text,
                font=ctk.CTkFont(family="맑은 고딕", size=10),
                text_color=first_color,
                anchor="nw",
                justify="left",
                wraplength=CELL_W - 12,
            )
            sum_label.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 2))

        def _click(_event=None, dd=d):
            self._on_day_click(dd)

        for w in (outer, inner, day_label):
            w.bind("<Button-1>", _click)
        if summary_text:
            sum_label.bind("<Button-1>", _click)

    def _render_month(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()

        self.month_label.configure(text=f"{self.view_year}년 {self.view_month}월")

        for i, name in enumerate(self.WEEKDAYS):
            ctk.CTkLabel(
                self.grid_frame,
                text=name,
                width=CELL_W,
                font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"),
            ).grid(row=0, column=i, padx=2, pady=2)

        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdayscalendar(self.view_year, self.view_month)

        for r, week in enumerate(weeks, start=1):
            for c, day_num in enumerate(week):
                if day_num == 0:
                    ctk.CTkLabel(
                        self.grid_frame, text="", width=CELL_W, height=CELL_H
                    ).grid(row=r, column=c, padx=2, pady=2)
                    continue
                d = date(self.view_year, self.view_month, day_num)
                day_items = self.by_day.get(d, [])
                self._make_day_cell(self.grid_frame, d, day_items, r, c)

    def _on_day_click(self, d: date):
        self.selected_day = d
        self._render_month()
        self._show_day(d)

    def _show_day(self, d: date):
        items = sorted(
            self.by_day.get(d, []),
            key=lambda x: (x.get("time_str") or "", x.get("사건번호") or ""),
        )
        self.detail_title.configure(
            text=f"{d.year}.{d.month:02d}.{d.day:02d} 기일 ({len(items)}건)"
        )
        self.detail_box.delete("1.0", "end")
        if not items:
            self.detail_box.insert("end", "이 날짜에 등록된 기일이 없습니다.")
            return
        lines = []
        for it in items:
            title_bits = [it.get("사건번호", "")]
            if it.get("피고"):
                title_bits.append(it["피고"])
            if it.get("사건명"):
                title_bits.append(it["사건명"])
            head = " / ".join(title_bits)
            time_s = it.get("time_str") or "--:--"
            lines.append(f"[{it.get('kind')}] {time_s}  {head}")
            if it.get("label"):
                lines.append(f"    {it['label']}")
        self.detail_box.insert("end", "\n".join(lines))
