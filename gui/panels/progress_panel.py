# -*- coding: utf-8 -*-
"""
진행상황 패널 (Progress Panel)
==============================
진행률 바와 로그 텍스트 영역을 제공합니다.

주니어 개발자 참고:
- 숨기기/보이기를 반복해도 레이아웃이 깨지지 않도록,
  접을 때는 PanedWindow에서 우측 패널을 forget 하고
  얇은 「▶진행상황 보기」 탭만 다시 add 합니다.
- 로그는 CTkTextbox가 아니라 Canvas입니다.
  Windows에서 Text 배경이 불투명이라 로고 위젯을 뒤로 보내면 안 보이고,
  앞으로 올리면 글자를 가립니다. 같은 Canvas에 로고를 먼저 그린 뒤
  글자를 나중에 그려야 「로고 뒤 · 글자 앞」이 됩니다.
"""
import os
import tkinter as tk
import customtkinter as ctk

import config
from gui.dialogs.log_viewer_dialog import LogViewerDialog

LOGO_OPACITY = 0.28
LOGO_MAX_PX = 220
COLLAPSED_RIGHT_WIDTH = 48
MAX_LOG_LINES = 2000
LOG_BG = "#34495E"
LOG_FG = "#ECF0F1"
LOG_SEL_BG = "#1ABC9C"
LOG_SEL_FG = "#FFFFFF"
# 이전 CTkTextbox 체감에 맞춰 11pt
LOG_FONT = ("맑은 고딕", 11)
LINE_HEIGHT = 16
LOG_PAD_X = 8
LOG_PAD_Y = 6


def _load_watermark_photo(master=None):
    """
    앱 아이콘을 반투명 PhotoImage로 만듭니다 (Canvas create_image용).
    CTkImage는 Canvas에 바로 못 쓰므로 ImageTk.PhotoImage를 씁니다.
    """
    try:
        from PIL import Image, ImageTk
    except Exception:
        return None

    try:
        rel = getattr(config, "APP_ICON_PNG", "assets/app_icon.png")
        path = config.path_from_base(rel) if hasattr(config, "path_from_base") else None
        if not path or not os.path.isfile(path):
            path = os.path.normpath(
                os.path.join(getattr(config, "BASE_DIR", "."), rel)
            )
        if not os.path.isfile(path):
            return None

        img = Image.open(path).convert("RGBA")
        w, h = img.size
        scale = min(LOGO_MAX_PX / max(w, 1), LOGO_MAX_PX / max(h, 1), 1.0)
        if scale < 1.0:
            img = img.resize(
                (max(1, int(w * scale)), max(1, int(h * scale))),
                Image.Resampling.LANCZOS,
            )
        r, g, b, a = img.split()
        a = a.point(lambda p: int(p * LOGO_OPACITY))
        img = Image.merge("RGBA", (r, g, b, a))
        return ImageTk.PhotoImage(img, master=master)
    except Exception:
        return None


class StatusLogCanvas:
    """
    CTkTextbox 호환 API를 가진 Canvas 로그 뷰.

    _redraw() 순서: 지우기 → 로고(create_image) → 선택 하이라이트 → 글자(create_text)
    → 글자가 항상 로고 위에 그려집니다.

    주니어:
    - _scroll_y 는 「맨 위 줄 인덱스」(휠로 이동).
    - 드래그 선택은 _sel_anchor / _sel_end (줄 인덱스)로 보관합니다.
    """

    def __init__(self, parent, app=None):
        self.app = app
        self._lines = []
        self._scroll_y = 0
        self._follow_end = True
        self._pending = ""
        self._sel_anchor = None  # 선택 시작 줄
        self._sel_end = None  # 선택 끝 줄
        self._dragging = False
        self._line_layout = []  # redraw 시 [(line_idx, y0, y1), ...]

        # canvas + scrollbar
        self._holder = tk.Frame(parent, bg=LOG_BG, highlightthickness=0)
        self._holder.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            self._holder,
            bg=LOG_BG,
            highlightthickness=0,
            borderwidth=0,
        )
        self._scrollbar = tk.Scrollbar(
            self._holder, orient=tk.VERTICAL, command=self._on_scrollbar
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._photo = _load_watermark_photo(master=self.canvas)
        if app is not None:
            app._progress_logo_photo = self._photo

        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", lambda e: self._scroll_lines(-3))
        self.canvas.bind("<Button-5>", lambda e: self._scroll_lines(3))
        # 부모에도 휠 바인딩 (포커스 없어도 스크롤)
        self._holder.bind("<MouseWheel>", self._on_mousewheel)
        parent.bind("<MouseWheel>", self._on_mousewheel)

        self.canvas.bind("<Button-1>", self._on_btn1)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Control-c>", self._on_copy_sel)
        self.canvas.bind("<Control-C>", self._on_copy_sel)
        self.canvas.focus_set()

        self._redraw()

    def insert(self, index, text):
        """'end'에 텍스트 추가. 개행 기준으로 줄을 나눕니다."""
        if text is None:
            return
        raw = self._pending + str(text)
        self._pending = ""
        parts = raw.split("\n")
        if not raw.endswith("\n"):
            self._pending = parts[-1]
            parts = parts[:-1]
        elif parts and parts[-1] == "":
            parts = parts[:-1]

        for part in parts:
            self._lines.append(part)

        self._trim_lines()
        if self._follow_end:
            self._scroll_to_end()
        self._redraw()

    def winfo_exists(self):
        try:
            return bool(self.canvas.winfo_exists())
        except Exception:
            return False

    def focus_set(self):
        try:
            self.canvas.focus_set()
        except Exception:
            pass

    def configure(self, **kwargs):
        """state= 등은 무시. text= 가 오면 한 줄 로그로 추가."""
        if "text" in kwargs:
            msg = kwargs.get("text")
            if msg:
                self.insert("end", str(msg) + "\n")
                self.see("end")
        return None

    config = configure

    def get(self, start="1.0", end="end-1c"):
        """선택 구간이 있으면 선택만, 없으면 전체(복사 버튼용)."""
        selected = self.get_selected_text()
        if selected is not None:
            return selected
        body = "\n".join(self._lines)
        if self._pending:
            body = (body + "\n" + self._pending) if body else self._pending
        return body

    def get_selected_text(self):
        """드래그 선택 문자열. 선택 없으면 None."""
        if self._sel_anchor is None or self._sel_end is None:
            return None
        a = min(self._sel_anchor, self._sel_end)
        b = max(self._sel_anchor, self._sel_end)
        if a < 0 or b >= len(self._lines) or a > b:
            return None
        return "\n".join(self._lines[a : b + 1])

    def see(self, index="end"):
        if index in ("end", "end-1c", tk.END):
            self._follow_end = True
            self._scroll_to_end()
            self._redraw()

    def pack(self, **kwargs):
        pass

    def _scroll_to_end(self):
        visible = self._visible_line_count()
        self._scroll_y = max(0, len(self._lines) - visible)

    def _visible_line_count(self):
        h = max(1, int(self.canvas.winfo_height() or 1))
        usable = max(LINE_HEIGHT, h - LOG_PAD_Y * 2)
        return max(1, usable // LINE_HEIGHT)

    def _trim_lines(self):
        if len(self._lines) > MAX_LOG_LINES:
            overflow = len(self._lines) - MAX_LOG_LINES
            self._lines = self._lines[overflow:]
            self._scroll_y = max(0, self._scroll_y - overflow)
            if self._sel_anchor is not None:
                self._sel_anchor = max(0, self._sel_anchor - overflow)
            if self._sel_end is not None:
                self._sel_end = max(0, self._sel_end - overflow)

    def _on_configure(self, _event=None):
        if self._follow_end:
            self._scroll_to_end()
        self._redraw()

    def _on_mousewheel(self, event):
        try:
            delta = int(-1 * (event.delta / 120))
        except Exception:
            delta = 0
        # 한 틱에 3줄 — 예전 Text 스크롤감에 가깝게
        self._scroll_lines(delta * 3 if delta else 0)
        return "break"

    def _on_scrollbar(self, *args):
        """Scrollbar 콜백: moveto / scroll."""
        if not args:
            return
        visible = self._visible_line_count()
        max_scroll = max(0, len(self._lines) - visible)
        if args[0] == "moveto":
            try:
                frac = float(args[1])
            except (TypeError, ValueError):
                return
            self._follow_end = False
            self._scroll_y = max(0, min(max_scroll, int(frac * max(1, len(self._lines)))))
            if self._scroll_y >= max_scroll:
                self._follow_end = True
            self._redraw()
        elif args[0] == "scroll":
            try:
                n = int(args[1])
            except (TypeError, ValueError):
                return
            unit = args[2] if len(args) > 2 else "units"
            step = n * (visible if unit == "pages" else 3)
            self._scroll_lines(step)

    def _update_scrollbar(self):
        total = max(1, len(self._lines))
        visible = self._visible_line_count()
        if total <= visible:
            self._scrollbar.set(0.0, 1.0)
            return
        first = self._scroll_y / total
        last = min(1.0, (self._scroll_y + visible) / total)
        self._scrollbar.set(first, last)

    def _scroll_lines(self, delta):
        if not delta:
            return
        self._follow_end = False
        visible = self._visible_line_count()
        max_scroll = max(0, len(self._lines) - visible)
        self._scroll_y = max(0, min(max_scroll, self._scroll_y + int(delta)))
        if self._scroll_y >= max_scroll:
            self._follow_end = True
        self._redraw()

    def _line_index_at_y(self, y):
        """캔버스 y좌표 → 줄 인덱스 (layout 기준)."""
        if not self._line_layout:
            # 대략적 추정
            visible = self._visible_line_count()
            rel = max(0, y - LOG_PAD_Y) // max(1, LINE_HEIGHT)
            return max(0, min(len(self._lines) - 1, self._scroll_y + int(rel)))
        for idx, y0, y1 in self._line_layout:
            if y0 <= y <= y1:
                return idx
        if y < self._line_layout[0][1]:
            return self._line_layout[0][0]
        return self._line_layout[-1][0]

    def _on_btn1(self, event):
        self.canvas.focus_set()
        if not self._lines:
            return
        idx = self._line_index_at_y(event.y)
        self._sel_anchor = idx
        self._sel_end = idx
        self._dragging = True
        self._redraw()

    def _on_drag(self, event):
        if not self._dragging or not self._lines:
            return
        # 위/아래 밖으로 드래그하면 스크롤
        h = max(1, int(self.canvas.winfo_height() or 1))
        if event.y < 0:
            self._scroll_lines(-1)
        elif event.y > h:
            self._scroll_lines(1)
        idx = self._line_index_at_y(event.y)
        self._sel_end = idx
        self._redraw()

    def _on_release(self, _event):
        self._dragging = False

    def _on_copy_sel(self, _event=None):
        text = self.get_selected_text()
        if text is None:
            text = "\n".join(self._lines)
        try:
            root = self.canvas.winfo_toplevel()
            root.clipboard_clear()
            root.clipboard_append(text)
        except Exception:
            pass
        return "break"

    def _sel_range(self):
        if self._sel_anchor is None or self._sel_end is None:
            return None
        return (min(self._sel_anchor, self._sel_end), max(self._sel_anchor, self._sel_end))

    def _redraw(self):
        c = self.canvas
        try:
            c.delete("all")
        except Exception:
            return

        w = max(1, int(c.winfo_width() or 1))
        h = max(1, int(c.winfo_height() or 1))
        self._line_layout = []

        # 1) 로고 먼저 (최하단 중앙)
        if self._photo is not None:
            try:
                c.create_image(
                    w // 2,
                    h - 6,
                    image=self._photo,
                    anchor="s",
                    tags=("watermark",),
                )
            except Exception:
                pass

        if not self._lines:
            self._update_scrollbar()
            return

        visible = self._visible_line_count()
        start = max(0, min(self._scroll_y, max(0, len(self._lines) - 1)))
        end = min(len(self._lines), start + visible + 4)
        y = LOG_PAD_Y
        max_text_w = max(40, w - LOG_PAD_X * 2)
        sel = self._sel_range()

        for i in range(start, end):
            y0 = y
            selected = sel is not None and sel[0] <= i <= sel[1]
            tid = c.create_text(
                LOG_PAD_X,
                y,
                text=self._lines[i],
                anchor="nw",
                fill=LOG_SEL_FG if selected else LOG_FG,
                font=LOG_FONT,
                width=max_text_w,
                tags=("logline", f"line-{i}"),
            )
            y1 = y0 + LINE_HEIGHT
            try:
                bbox = c.bbox(tid)
                if bbox:
                    y1 = bbox[3]
                    if selected:
                        rid = c.create_rectangle(
                            2,
                            bbox[1] - 1,
                            w - 2,
                            bbox[3] + 1,
                            fill=LOG_SEL_BG,
                            outline="",
                            tags=("selbg",),
                        )
                        c.tag_lower(rid, tid)
                    y = y1 + 3
                else:
                    y += LINE_HEIGHT
            except Exception:
                y += LINE_HEIGHT
            self._line_layout.append((i, y0, y1))
            if y > h + LINE_HEIGHT:
                break

        self._update_scrollbar()


def _place_right_sash(app, right_width):
    """우측 패널(또는 접힌 탭) 폭이 right_width 가 되도록 sash 고정."""
    paned = getattr(app, "main_paned", None)
    if paned is None:
        return
    try:
        paned.update_idletasks()
        sashwidth = int(paned.cget("sashwidth") or 8)
        total_w = paned.winfo_width()
        if total_w < 120:
            return
        min_left = 400
        w = max(40, int(right_width))
        w = min(w, max(40, total_w - min_left - sashwidth))
        paned.sash_place(0, total_w - w - sashwidth, 0)
    except Exception:
        pass


def _paned_has(paned, widget):
    """widget 이 paned 자식 panes 목록에 있는지."""
    try:
        return str(widget) in [str(p) for p in paned.panes()]
    except Exception:
        return False


class ProgressPanel:
    """진행률 바 + Canvas 로그 + 숨기기/보이기 토글."""

    @staticmethod
    def create(parent, app):
        """
        parent: 우측 right_panel.
        접힌 탭은 main_paned 에 직접 add/forget 합니다.
        """
        progress_frame = ctk.CTkFrame(
            parent, fg_color=app.get_theme_color("bg_primary")
        )
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        app._progress_outer_frame = progress_frame
        app._progress_right_panel = parent

        title_row = ctk.CTkFrame(progress_frame, fg_color="transparent")
        title_row.pack(fill=tk.X, pady=(0, 8))
        app._progress_title_row = title_row

        # 제목 옆 작은 아이콘
        try:
            icon_path = config.path_from_base(
                getattr(config, "APP_ICON_PNG", "assets/app_icon.png")
            )
            if os.path.isfile(icon_path):
                from PIL import Image

                img = Image.open(icon_path).convert("RGBA")
                img = img.resize((20, 20), Image.Resampling.LANCZOS)
                app._progress_title_icon = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(20, 20)
                )
                ctk.CTkLabel(
                    title_row,
                    text="",
                    image=app._progress_title_icon,
                    width=22,
                ).pack(side=tk.LEFT, padx=(0, 4))
        except Exception:
            pass

        ctk.CTkLabel(
            title_row,
            text="진행상황",
            font=ctk.CTkFont(family="맑은 고딕", size=16, weight="bold"),
            text_color=app.get_theme_color("text_main"),
        ).pack(side=tk.LEFT)

        app._progress_hidden = False
        app._progress_saved_width = None
        app._progress_toggle_busy = False

        def _make_collapsed_strip():
            paned = getattr(app, "main_paned", None)
            if paned is None:
                return None
            strip = getattr(app, "_progress_collapsed_strip", None)
            if strip is not None:
                try:
                    if strip.winfo_exists():
                        return strip
                except Exception:
                    pass
            strip = ctk.CTkFrame(
                paned,
                fg_color=app.get_theme_color("bg_primary"),
                width=COLLAPSED_RIGHT_WIDTH,
            )
            open_tab_btn = ctk.CTkButton(
                strip,
                text="▶\n진\n행\n상\n황\n보\n기",
                font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"),
                fg_color="#1ABC9C",
                hover_color="#16A085",
                text_color="#FFFFFF",
                corner_radius=8,
                width=COLLAPSED_RIGHT_WIDTH - 8,
                command=lambda: _show_expanded(),
            )
            open_tab_btn.pack(fill=tk.BOTH, expand=True, padx=4, pady=8)
            app._progress_collapsed_strip = strip
            app._progress_open_tab_btn = open_tab_btn
            return strip

        def _show_expanded():
            if app._progress_toggle_busy:
                return
            if not app._progress_hidden:
                return
            app._progress_toggle_busy = True
            try:
                paned = getattr(app, "main_paned", None)
                right = getattr(app, "_progress_right_panel", None)
                strip = getattr(app, "_progress_collapsed_strip", None)
                min_w = int(getattr(config, "RIGHT_PANEL_MIN_WIDTH", LOGO_MAX_PX + 40))
                restore = app._progress_saved_width or getattr(
                    config, "RIGHT_PANEL_WIDTH", 400
                )
                restore = max(int(restore), min_w)

                if paned is not None and strip is not None and _paned_has(paned, strip):
                    try:
                        paned.forget(strip)
                    except Exception:
                        pass

                if paned is not None and right is not None and not _paned_has(paned, right):
                    paned.add(
                        right,
                        minsize=min_w,
                        width=restore,
                        stretch="never",
                    )

                app._progress_hidden = False
                app.root.after(30, lambda: _place_right_sash(app, restore))
            finally:
                app._progress_toggle_busy = False

        def _show_collapsed():
            if app._progress_toggle_busy:
                return
            if app._progress_hidden:
                return
            app._progress_toggle_busy = True
            try:
                paned = getattr(app, "main_paned", None)
                right = getattr(app, "_progress_right_panel", None)
                min_w = int(getattr(config, "RIGHT_PANEL_MIN_WIDTH", LOGO_MAX_PX + 40))

                if right is not None:
                    try:
                        if right.winfo_exists():
                            cur = int(right.winfo_width())
                            if cur >= min_w:
                                app._progress_saved_width = cur
                    except Exception:
                        pass
                if not app._progress_saved_width:
                    app._progress_saved_width = getattr(config, "RIGHT_PANEL_WIDTH", 400)

                strip = _make_collapsed_strip()

                if paned is not None and right is not None and _paned_has(paned, right):
                    try:
                        paned.forget(right)
                    except Exception:
                        pass

                if paned is not None and strip is not None and not _paned_has(paned, strip):
                    paned.add(
                        strip,
                        minsize=COLLAPSED_RIGHT_WIDTH,
                        width=COLLAPSED_RIGHT_WIDTH,
                        stretch="never",
                    )

                app._progress_hidden = True
                app.root.after(
                    30, lambda: _place_right_sash(app, COLLAPSED_RIGHT_WIDTH)
                )
            finally:
                app._progress_toggle_busy = False

        def toggle_progress_visibility():
            if app._progress_hidden:
                _show_expanded()
            else:
                _show_collapsed()

        app._progress_toggle_btn = ctk.CTkButton(
            title_row,
            text="숨기기",
            width=64,
            height=26,
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            fg_color="#5D6D7E",
            hover_color="#7F8C8D",
            command=toggle_progress_visibility,
        )
        app._progress_toggle_btn.pack(side=tk.LEFT, padx=(10, 0))

        _make_collapsed_strip()

        body_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
        body_frame.pack(fill=tk.BOTH, expand=True)
        app._progress_body_frame = body_frame

        app.progress_var = tk.DoubleVar()
        app.progress_bar = ctk.CTkProgressBar(body_frame, height=16)
        app.progress_bar.pack(fill=tk.X, padx=0, pady=10)
        app.progress_bar.set(0)

        sep = ctk.CTkFrame(
            body_frame,
            fg_color=app.get_theme_color("border"),
            height=2,
            corner_radius=0,
        )
        sep.pack(fill=tk.X, pady=(0, 8))
        sep.pack_propagate(False)

        log_wrap = ctk.CTkFrame(body_frame, fg_color=LOG_BG, corner_radius=6)
        log_wrap.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 8))
        app._progress_log_wrap = log_wrap

        # Canvas: 로고 뒤 · 글자 앞 (place 오버레이 없음)
        app.status_text = StatusLogCanvas(log_wrap, app=app)
        app._progress_logo_label = None

        def copy_log_to_clipboard():
            try:
                text = app.status_text.get("1.0", "end-1c")
                app.root.clipboard_clear()
                app.root.clipboard_append(text)
            except Exception:
                pass

        def open_log_viewer():
            try:
                LogViewerDialog(app.root)
            except Exception:
                pass

        bottom_row = ctk.CTkFrame(body_frame, fg_color="transparent")
        bottom_row.pack(fill=tk.X, pady=(0, 4))
        ctk.CTkButton(
            bottom_row,
            text="📋 복사",
            width=60,
            command=copy_log_to_clipboard,
        ).pack(side=tk.LEFT, padx=(0, 8))
        ctk.CTkButton(
            bottom_row,
            text="과거 로그",
            width=70,
            command=open_log_viewer,
        ).pack(side=tk.LEFT)

        return progress_frame
