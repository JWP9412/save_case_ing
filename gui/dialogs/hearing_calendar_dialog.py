# -*- coding: utf-8 -*-
"""
미어캣싱 · 기일 달력
====================

등록된 사건의 변론기일·감정기일·판결선고기일을 월간 달력으로 보여 줍니다.
구글 캘린더가 아니라 미어캣싱 앱 안의 창입니다.

주니어 개발자 참고:
- 데이터는 update_history.json 의 hearing_events (조회 성공 시 저장)입니다.
- 외부 달력 패키지 없이 calendar 모듈 + CTk 그리드로 그립니다.
"""
from __future__ import annotations

import calendar
import tkinter as tk
from collections import defaultdict
from datetime import date, datetime

import customtkinter as ctk

import config
from services.date_utils import parse_datetime_loose


# 기일 종류별 점/강조 색
KIND_COLORS = {
    "변론기일": "#3498DB",
    "감정기일": "#9B59B6",
    "판결선고기일": "#E67E22",
}
DEFAULT_KIND_COLOR = "#7F8C8D"


def _parse_event_day(start_val):
    """hearing_events.start(ISO 등) → date | None"""
    if isinstance(start_val, datetime):
        return start_val.date()
    if isinstance(start_val, date):
        return start_val
    dt = parse_datetime_loose(start_val)
    return dt.date() if dt else None


def collect_hearing_items(history, case_list):
    """
    history + case_list → 달력용 항목 리스트.

    각 항목: {
      "day": date, "kind", "label", "start",
      "사건번호", "피고", "사건명", "time_str"
    }
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
        events = rec.get("hearing_events") or []
        if not isinstance(events, list):
            continue
        meta = case_map.get(str(case_number), {})
        defendant = meta.get("피고", "") if isinstance(meta, dict) else ""
        case_name = meta.get("사건명", "") if isinstance(meta, dict) else ""
        for ev in events:
            if not isinstance(ev, dict):
                continue
            kind = (ev.get("kind") or "").strip()
            if kind not in ("변론기일", "감정기일", "판결선고기일"):
                continue
            day = _parse_event_day(ev.get("start"))
            if day is None:
                continue
            start_raw = ev.get("start") or ""
            time_str = ""
            dt = parse_datetime_loose(start_raw)
            if dt:
                time_str = dt.strftime("%H:%M")
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
    return items


class HearingCalendarDialog(ctk.CTkToplevel):
    """미어캣싱 기일 월간 달력."""

    WEEKDAYS = ("월", "화", "수", "목", "금", "토", "일")

    def __init__(self, parent, items=None, title=None):
        super().__init__(parent)
        app_name = getattr(config, "APP_TITLE", "미어캣싱")
        self.title(title or f"{app_name} · 기일 달력")
        self.geometry("720x560")
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
            self, height=140, font=ctk.CTkFont(family="맑은 고딕", size=12)
        )
        self.detail_box.pack(fill=tk.X, padx=12, pady=(0, 12))

        hint = ctk.CTkLabel(
            self,
            text="안내: 조회가 끝난 사건의 기일만 표시됩니다. (hearing_events 없는 사건은 비어 있음)",
            font=ctk.CTkFont(family="맑은 고딕", size=11),
            text_color="#7F8C8D",
            anchor="w",
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

    def _render_month(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()

        self.month_label.configure(text=f"{self.view_year}년 {self.view_month}월")

        for i, name in enumerate(self.WEEKDAYS):
            ctk.CTkLabel(
                self.grid_frame,
                text=name,
                width=90,
                font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"),
            ).grid(row=0, column=i, padx=2, pady=2)

        # calendar.setfirstweekday(월요일)
        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdayscalendar(self.view_year, self.view_month)
        today = date.today()

        for r, week in enumerate(weeks, start=1):
            for c, day_num in enumerate(week):
                if day_num == 0:
                    ctk.CTkLabel(self.grid_frame, text="", width=90, height=48).grid(
                        row=r, column=c, padx=2, pady=2
                    )
                    continue
                d = date(self.view_year, self.view_month, day_num)
                day_items = self.by_day.get(d, [])
                kinds = sorted({it["kind"] for it in day_items})
                dots = " ".join(
                    "●" for _ in kinds[:3]
                )  # 개수만; 색은 버튼 텍스트로 표현이 어려워 하단 범례 참고
                mark = ""
                if kinds:
                    # 첫 종류 색으로 요약 문자
                    color = KIND_COLORS.get(kinds[0], DEFAULT_KIND_COLOR)
                    mark = f"\n{len(day_items)}건"
                else:
                    color = "#B0B0B0"

                is_today = d == today
                is_sel = d == self.selected_day
                fg = "#1ABC9C" if is_today else ("#2980B9" if is_sel else "#2C3E50")
                text = f"{day_num}{mark}"
                btn = ctk.CTkButton(
                    self.grid_frame,
                    text=text,
                    width=90,
                    height=48,
                    fg_color=fg if (is_today or is_sel or day_items) else "#3D3D3D",
                    hover_color="#34495E",
                    text_color=color if day_items and not (is_today or is_sel) else "#FFFFFF",
                    font=ctk.CTkFont(family="맑은 고딕", size=12),
                    command=lambda dd=d: self._on_day_click(dd),
                )
                btn.grid(row=r, column=c, padx=2, pady=2)

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
