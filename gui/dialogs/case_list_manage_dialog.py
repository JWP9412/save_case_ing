# -*- coding: utf-8 -*-
"""
사건목록 관리 다이얼로그
========================
사건 추가, 수정, 삭제, 숨기기, 숨김 해제 기능을 탭으로 제공합니다.
"""
import json
import os
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

import config
from gui.utils.google_sheet_ui import load_hidden_cases, save_hidden_cases


def load_case_list_manage_left_width():
    """저장된 사건목록 관리 왼쪽 패널 너비 로드. 180~500 클램프."""
    path = getattr(
        config,
        "CASE_LIST_MANAGE_LEFT_WIDTH_FILE",
        "data/case_list_manage_left_width.json",
    )
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            w = data.get("width")
            if isinstance(w, (int, float)) and 180 <= w <= 500:
                return int(w)
    except Exception:
        pass
    return getattr(config, "CASE_LIST_MANAGE_LEFT_WIDTH", 220)


def save_case_list_manage_left_width(width):
    """사건목록 관리 왼쪽 패널 너비 저장."""
    path = getattr(
        config,
        "CASE_LIST_MANAGE_LEFT_WIDTH_FILE",
        "data/case_list_manage_left_width.json",
    )
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"width": int(width)}, f, indent=2)
    except Exception:
        pass


def load_case_list_manage_geometry():
    """저장된 사건목록 관리 창 크기(및 위치) 로드. (width, height) 또는 (width, height, x, y). 저장값 없으면 기본값."""
    path = getattr(
        config, "CASE_LIST_MANAGE_GEOMETRY_FILE", "data/case_list_manage_geometry.json"
    )
    default_w = getattr(config, "CASE_LIST_MANAGE_DEFAULT_WIDTH", 720)
    default_h = getattr(config, "CASE_LIST_MANAGE_DEFAULT_HEIGHT", 520)
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            w = data.get("width")
            h = data.get("height")
            if (
                isinstance(w, (int, float))
                and isinstance(h, (int, float))
                and int(w) > 0
                and int(h) > 0
            ):
                w, h = int(w), int(h)
                x = data.get("x")
                y = data.get("y")
                if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                    return (w, h, int(x), int(y))
                return (w, h)
    except Exception:
        pass
    return (default_w, default_h)


def save_case_list_manage_geometry(width, height, x=None, y=None):
    """사건목록 관리 창 크기(및 위치) 저장."""
    path = getattr(
        config, "CASE_LIST_MANAGE_GEOMETRY_FILE", "data/case_list_manage_geometry.json"
    )
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        payload = {"width": int(width), "height": int(height)}
        if x is not None and y is not None:
            payload["x"] = int(x)
            payload["y"] = int(y)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception:
        pass


# Form field keys that may exist on the sheet (header-driven)
DEFAULT_HEADER_KEYS = ["법원", "사건번호", "피고", "사건명"]

# 법원 드롭다운 옵션 (사건목록 관리 창)
COURT_NAMES = [
    "서울고등법원",
    "서울고등법원(춘천재판부)",
    "서울고등법원(인천재판부)",
    "대전고등법원",
    "대전고등법원(청주재판부)",
    "대구고등법원",
    "부산고등법원",
    "부산고등법원(창원재판부)",
    "부산고등법원(울산재판부)",
    "광주고등법원",
    "광주고등법원(제주재판부)",
    "광주고등법원(전주재판부)",
    "수원고등법원",
    "특허법원",
    "서울가정법원",
    "서울행정법원",
    "서울회생법원",
    "서울중앙지방법원",
    "서울동부지방법원",
    "서울남부지방법원",
    "서울북부지방법원",
    "서울서부지방법원",
    "의정부지방법원",
    "고양지원",
    "남양주지원",
    "파주시법원",
    "포천시법원",
    "동두천시법원",
    "가평군법원",
    "연천군법원",
    "철원군법원",
    "인천지방법원",
    "인천지방법원 부천지원",
    "김포시법원",
    "강화군법원",
    "인천가정법원",
    "인천가정법원 부천지원",
    "수원지방법원",
    "성남지원",
    "여주지원",
    "평택지원",
    "안산지원",
    "안양지원",
    "용인시법원",
    "오산시법원",
    "광명시법원",
    "안성시법원",
    "광주시법원",
    "양평군법원",
    "이천시법원",
    "수원가정법원",
    "수원가정법원 성남지원",
    "수원가정법원 여주지원",
    "수원가정법원 평택지원",
    "수원가정법원 안산지원",
    "수원가정법원 안양지원",
    "수원회생법원",
    "춘천지방법원",
    "강릉지원",
    "원주지원",
    "속초지원",
    "영월지원",
    "홍천군법원",
    "양구군법원",
    "삼척시법원",
    "동해시법원",
    "정선군법원",
    "평창군법원",
    "태백시법원",
    "횡성군법원",
    "인제군법원",
    "화천군법원",
    "고성군법원",
    "양양군법원",
    "대전지방법원",
    "대전지방법원 홍성지원",
    "대전지방법원 공주지원",
    "대전지방법원 논산지원",
    "대전지방법원 서산지원",
    "대전지방법원 천안지원",
    "금산군법원",
    "세종특별자치시법원",
    "보령시법원",
    "서천군법원",
    "예산군법원",
    "아산시법원",
    "태안군법원",
    "당진시법원",
    "부여군법원",
    "청양군법원",
    "대전가정법원",
    "대전가정법원 홍성지원",
    "대전가정법원 공주지원",
    "대전가정법원 논산지원",
    "대전가정법원 서산지원",
    "대전가정법원 천안지원",
    "청주지방법원",
    "충주지원",
    "제천지원",
    "영동지원",
    "진천군법원",
    "보은군법원",
    "단양군법원",
    "음성군법원",
    "옥천군법원",
    "괴산군법원",
    "대구지방법원",
    "대구지방법원 서부지원",
    "대구지방법원 안동지원",
    "대구지방법원 경주지원",
    "대구지방법원 포항지원",
    "대구지방법원 김천지원",
    "대구지방법원 상주지원",
    "대구지방법원 의성지원",
    "대구지방법원 영덕지원",
    "경산시법원",
    "칠곡군법원",
    "청도군법원",
    "영천시법원",
    "성주군법원",
    "고령군법원",
    "영주시법원",
    "봉화군법원",
    "구미시법원",
    "문경시법원",
    "예천군법원",
    "청송군법원",
    "군위군법원",
    "울진군법원",
    "영양군법원",
    "대구가정법원",
    "대구가정법원 안동지원",
    "대구가정법원 경주지원",
    "대구가정법원 포항지원",
    "대구가정법원 김천지원",
    "대구가정법원 상주지원",
    "대구가정법원 의성지원",
    "대구가정법원 영덕지원",
    "부산지방법원",
    "부산지방법원 동부지원",
    "부산지방법원 서부지원",
    "부산가정법원",
    "부산회생법원",
    "울산지방법원",
    "양산시법원",
    "울산가정법원",
    "창원지방법원",
    "마산지원",
    "진주지원",
    "통영지원",
    "밀양지원",
    "거창지원",
    "창원남부시법원",
    "김해시법원",
    "함안군법원",
    "의령군법원",
    "사천시법원",
    "남해군법원",
    "하동군법원",
    "거제시법원",
    "고성군법원(경)",
    "창녕군법원",
    "합천군법원",
    "함양군법원",
    "산청군법원",
    "광주지방법원",
    "광주지방법원 목포지원",
    "광주지방법원 장흥지원",
    "광주지방법원 순천지원",
    "광주지방법원 해남지원",
    "담양군법원",
    "함평군법원",
    "강진군법원",
    "구례군법원",
    "영광군법원",
    "나주시법원",
    "장성군법원",
    "화순군법원",
    "곡성군법원",
    "광양시법원",
    "고흥군법원",
    "여수시법원",
    "보성군법원",
    "무안군법원",
    "영암군법원",
    "완도군법원",
    "진도군법원",
    "광주가정법원",
    "광주가정법원 목포지원",
    "광주가정법원 장흥지원",
    "광주가정법원 순천지원",
    "광주가정법원 해남지원",
    "전주지방법원",
    "군산지원",
    "정읍지원",
    "남원지원",
    "진안군법원",
    "김제시법원",
    "무주군법원",
    "임실군법원",
    "익산시법원",
    "부안군법원",
    "고창군법원",
    "장수군법원",
    "순창군법원",
    "제주지방법원",
    "서귀포시법원",
    "법원행정처",
]


class CourtAutocomplete(ctk.CTkFrame):
    """입력 시 법원명 목록을 필터링해 보여주는 자동완성 필드 (구글 시트 드롭다운처럼 동작). 목록은 Toplevel 오버레이로 표시해 폼 간격이 벌어지지 않음."""

    def __init__(self, parent, width=280, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._width = width
        self._popup = None
        self._listbox = None
        self._hide_job = None

        row_frm = ctk.CTkFrame(self, fg_color="transparent")
        row_frm.pack(fill=tk.X)
        self.entry = ctk.CTkEntry(row_frm, width=width)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        dropdown_btn = ctk.CTkButton(
            row_frm,
            text="▼",
            width=32,
            height=28,
            fg_color="transparent",
            hover_color="#3D5A6C",
            cursor="hand2",
            command=self._show_list,
        )
        dropdown_btn.pack(side=tk.RIGHT, padx=(4, 0))
        self.entry.bind("<KeyRelease>", self._on_key)
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_entry_focus_out)

    def _ensure_popup(self):
        if self._popup is not None:
            try:
                self._popup.winfo_exists()
            except tk.TclError:
                self._popup = None
        if self._popup is None:
            toplevel = self.winfo_toplevel()
            self._popup = tk.Toplevel(toplevel)
            self._popup.overrideredirect(True)
            self._popup.transient(toplevel)
            app = getattr(toplevel, "app", None)
            if app is not None:
                bg_primary = app.get_theme_color("bg_primary")
                text_main = app.get_theme_color("text_main")
                accent = app.get_theme_color("accent")
                self._popup.configure(bg=bg_primary)
            else:
                bg_primary = "#2B2B2B"
                text_main = "white"
                accent = "#3498DB"
            self._listbox = tk.Listbox(
                self._popup,
                height=8,
                font=("맑은 고딕", 11),
                selectmode=tk.SINGLE,
                activestyle="none",
                bg=bg_primary,
                fg=text_main,
                selectbackground=accent,
                selectforeground="white",
                highlightthickness=0,
                relief=tk.FLAT,
            )
            self._listbox.pack(fill=tk.BOTH, expand=True)
            self._listbox.bind("<<ListboxSelect>>", self._on_select)
            self._listbox.bind("<FocusOut>", self._on_list_focus_out)

    def _fill_listbox(self):
        if self._listbox is None:
            return
        self._listbox.delete(0, tk.END)
        q = (self.entry.get() or "").strip()
        if not q:
            for name in COURT_NAMES[:50]:
                self._listbox.insert(tk.END, name)
        else:
            matched = [c for c in COURT_NAMES if q in c]
            for name in matched[:20]:
                self._listbox.insert(tk.END, name)

    def _show_list(self):
        if self._hide_job:
            self.after_cancel(self._hide_job)
            self._hide_job = None
        self._ensure_popup()
        self._fill_listbox()
        if self._listbox.size() == 0:
            self._hide_list()
            return
        self.entry.update_idletasks()
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        w = max(self._width + 40, 200)
        h = min(220, max(120, self._listbox.size() * 20))
        self._popup.geometry(f"{w}x{h}+{x}+{y}")
        self._popup.deiconify()
        self._popup.lift()

    def _on_focus_in(self, event=None):
        self._show_list()

    def _on_key(self, event=None):
        if self._hide_job:
            self.after_cancel(self._hide_job)
            self._hide_job = None
        q = (self.entry.get() or "").strip()
        if not q:
            self._hide_list()
            return
        self._ensure_popup()
        self._fill_listbox()
        if self._listbox.size() > 0:
            self.entry.update_idletasks()
            x = self.entry.winfo_rootx()
            y = self.entry.winfo_rooty() + self.entry.winfo_height()
            w = max(self._width + 40, 200)
            h = min(220, max(120, self._listbox.size() * 20))
            self._popup.geometry(f"{w}x{h}+{x}+{y}")
            self._popup.deiconify()
            self._popup.lift()
        else:
            self._hide_list()

    def _hide_list(self):
        if self._popup is not None:
            try:
                self._popup.withdraw()
            except tk.TclError:
                pass

    def _on_select(self, event=None):
        if self._listbox is None:
            return
        sel = self._listbox.curselection()
        if sel:
            val = self._listbox.get(sel[0])
            self.entry.delete(0, tk.END)
            self.entry.insert(0, val)
        self._hide_list()

    def _on_entry_focus_out(self, event=None):
        self._hide_job = self.after(150, self._hide_list)

    def _on_list_focus_out(self, event=None):
        self._hide_job = self.after(150, self._hide_list)

    def get(self):
        return (self.entry.get() or "").strip()

    def set(self, value):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, str(value or ""))
        self._hide_list()


def _case_display_text(case):
    """사건 한 줄 표시 문자열 (왼쪽 리스트용)."""
    cn = case.get("사건번호", "") or ""
    cn = str(cn).strip() if cn is not None else ""
    defendant = case.get("피고", "") or ""
    name = case.get("사건명", "") or ""
    name = str(name).strip() if name is not None else ""
    sub = str(defendant).strip() if defendant is not None else ""
    if sub and name:
        sub = f"{sub} / {name}"
    elif name:
        sub = name
    return f"{cn} - {sub}" if sub else cn or "(사건번호 없음)"


class CaseListManageDialog(ctk.CTkToplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("사건목록 관리")
        geom = load_case_list_manage_geometry()
        self.minsize(
            geom[0], geom[1]
        )  # 저장된 크기를 최소값으로 (이보다 더 줄일 수 없음)
        if len(geom) == 4:
            self.geometry(f"{geom[0]}x{geom[1]}+{geom[2]}+{geom[3]}")
        else:
            self.geometry(f"{geom[0]}x{geom[1]}")
        self.transient(parent)
        self.resizable(True, True)
        self._editing_case_number = None
        self._loaded_edit_row = None  # 수정 탭 불러온 직후/저장 직후 스냅샷 (저장 버튼 변경 여부 판단용)
        self.pending_hidden_add = []
        self.pending_hidden_remove = []
        self.pending_adds = []
        self.pending_updates = {}
        self.pending_deletes = []
        self._visible_case_list = []
        self._last_apply_undo = None  # 적용 되돌리기용 스냅샷 (적용 1회분)

        self._create_widgets()
        self._refresh_case_list()
        self._update_apply_button_and_summary()
        self._update_button_states()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _on_close(self):
        """다이얼로그 닫을 때 왼쪽 패널 너비·창 크기 저장 후 destroy."""
        if getattr(self, "left_frm", None) is not None and self.left_frm.winfo_exists():
            try:
                w = self.left_frm.winfo_width()
                if isinstance(w, (int, float)) and w > 0:
                    save_case_list_manage_left_width(w)
            except Exception:
                pass
        try:
            w, h = self.winfo_width(), self.winfo_height()
            x, y = self.winfo_x(), self.winfo_y()
            if w > 0 and h > 0:
                save_case_list_manage_geometry(w, h, x, y)
        except Exception:
            pass
        self.destroy()

    def _create_widgets(self):
        bg_primary = self.app.get_theme_color("bg_primary")
        text_main = self.app.get_theme_color("text_main")
        accent = self.app.get_theme_color("accent")

        main_frm = ctk.CTkFrame(self, fg_color="transparent")
        main_frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_width = load_case_list_manage_left_width()
        paned = tk.PanedWindow(
            main_frm, orient=tk.HORIZONTAL, sashwidth=6, bg=bg_primary
        )
        paned.pack(fill=tk.BOTH, expand=True)

        # 왼쪽: 사건 목록 리스트 (너비 조절 가능)
        self.left_frm = ctk.CTkFrame(paned, fg_color=bg_primary, width=left_width)
        self.left_frm.pack_propagate(False)
        self.case_list_label = ctk.CTkLabel(
            self.left_frm, text="사건 목록 (0)", font=ctk.CTkFont(weight="bold")
        )
        self.case_list_label.pack(anchor="w")
        list_container = ctk.CTkFrame(self.left_frm, fg_color="transparent")
        list_container.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        self.case_listbox = tk.Listbox(
            list_container,
            height=18,
            font=("맑은 고딕", 10),
            selectmode=tk.EXTENDED,
            activestyle="none",
            exportselection=False,
            bg=bg_primary,
            fg=text_main,
            selectbackground=accent,
            selectforeground="white",
            highlightthickness=0,
            relief=tk.FLAT,
        )
        scroll = ctk.CTkScrollbar(list_container, command=self.case_listbox.yview)
        self.case_listbox.configure(yscrollcommand=scroll.set)
        self.case_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.case_listbox.bind("<<ListboxSelect>>", self._on_case_list_select)
        self.case_listbox.bind("<Double-Button-1>", self._on_left_list_double_click)
        ctk.CTkFrame(
            self.left_frm,
            fg_color=self.app.get_theme_color("border"),
            height=2,
            corner_radius=0,
        ).pack(fill=tk.X, pady=(4, 2))
        # 왼쪽 패널 하단: 숨기기 / 숨김 해제 버튼 (가운데 정렬) + 숨긴 사건 리스트
        left_btn_frm = ctk.CTkFrame(self.left_frm, fg_color="transparent")
        left_btn_frm.pack(fill=tk.X, pady=(6, 4))
        inner_btn = ctk.CTkFrame(left_btn_frm, fg_color="transparent")
        inner_btn.pack(anchor="center")
        self.hide_btn = ctk.CTkButton(
            inner_btn, text="숨기기 ▼", width=90, height=28, command=self._on_hide
        )
        self.hide_btn.pack(side=tk.LEFT, padx=(0, 6))
        self.unhide_btn = ctk.CTkButton(
            inner_btn, text="숨김 해제 ▲", width=90, height=28, command=self._on_unhide
        )
        self.unhide_btn.pack(side=tk.LEFT, padx=(0, 6))
        self.delete_btn = ctk.CTkButton(
            inner_btn, text="사건 삭제", width=90, height=28, command=self._on_delete
        )
        self.delete_btn.pack(side=tk.LEFT)
        ctk.CTkFrame(
            self.left_frm,
            fg_color=self.app.get_theme_color("border"),
            height=2,
            corner_radius=0,
        ).pack(fill=tk.X, pady=(2, 4))
        self.unhide_list_label = ctk.CTkLabel(
            self.left_frm, text="숨긴 사건 (0)", font=ctk.CTkFont(weight="bold")
        )
        self.unhide_list_label.pack(anchor="w", pady=(4, 2))
        unhide_container = ctk.CTkFrame(self.left_frm, fg_color="transparent")
        unhide_container.pack(fill=tk.BOTH, expand=True, pady=(0, 0))
        self.unhide_listbox = tk.Listbox(
            unhide_container,
            height=10,
            font=("맑은 고딕", 10),
            selectmode=tk.EXTENDED,
            bg=bg_primary,
            fg=text_main,
            selectbackground=accent,
            selectforeground="white",
            highlightthickness=0,
            relief=tk.FLAT,
        )
        unhide_scroll = ctk.CTkScrollbar(
            unhide_container, command=self.unhide_listbox.yview
        )
        self.unhide_listbox.configure(yscrollcommand=unhide_scroll.set)
        self.unhide_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        unhide_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.unhide_listbox.bind("<<ListboxSelect>>", lambda e: self._update_button_states())
        paned.add(self.left_frm, minsize=180, width=left_width, stretch="never")

        # 오른쪽: 탭뷰 + 변경 예정 사건 목록
        right_frm = ctk.CTkFrame(paned, fg_color=bg_primary)
        ctk.CTkFrame(
            right_frm,
            fg_color=self.app.get_theme_color("border"),
            width=2,
            corner_radius=0,
        ).pack(side=tk.LEFT, fill=tk.Y)
        ctk.CTkFrame(
            right_frm,
            fg_color=self.app.get_theme_color("border"),
            width=2,
            corner_radius=0,
        ).pack(side=tk.RIGHT, fill=tk.Y)
        self.tabview = ctk.CTkTabview(right_frm, width=420, height=240)
        self.tabview.pack(fill=tk.X)

        self.tabview.add("사건 추가")
        self.tabview.add("사건 수정")

        self._build_add_tab(self.tabview.tab("사건 추가"))
        self._build_edit_tab(self.tabview.tab("사건 수정"))

        ctk.CTkFrame(
            right_frm,
            fg_color=self.app.get_theme_color("border"),
            height=2,
            corner_radius=0,
        ).pack(fill=tk.X, pady=(4, 6))
        # 변경 예정 사건 목록 (N) + 변경 취소 버튼 + Listbox
        pending_frm = ctk.CTkFrame(right_frm, fg_color="transparent")
        pending_frm.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        pending_header = ctk.CTkFrame(pending_frm, fg_color="transparent")
        pending_header.pack(fill=tk.X, pady=(0, 4))
        self.pending_list_label = ctk.CTkLabel(
            pending_header,
            text="변경 예정 사건 목록 (0)",
            font=ctk.CTkFont(weight="bold"),
        )
        self.pending_list_label.pack(side=tk.LEFT)
        self.cancel_pending_btn = ctk.CTkButton(
            pending_header,
            text="변경 취소",
            width=90,
            height=28,
            command=self._on_cancel_pending_change,
        )
        self.cancel_pending_btn.pack(side=tk.RIGHT, padx=(0, 10))
        pending_container = ctk.CTkFrame(pending_frm, fg_color="transparent")
        pending_container.pack(fill=tk.BOTH, expand=True)
        self.pending_listbox = tk.Listbox(
            pending_container,
            height=8,
            font=("맑은 고딕", 10),
            selectmode=tk.EXTENDED,
            bg=bg_primary,
            fg=text_main,
            selectbackground=accent,
            selectforeground="white",
            highlightthickness=0,
            relief=tk.FLAT,
        )
        pending_scroll = ctk.CTkScrollbar(
            pending_container, command=self.pending_listbox.yview
        )
        self.pending_listbox.configure(yscrollcommand=pending_scroll.set)
        self.pending_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pending_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.pending_listbox.bind("<<ListboxSelect>>", lambda e: self._update_button_states())

        paned.add(right_frm, minsize=360, stretch="always")

        self._refresh_unhide_list()

        # 하단: 취소, 확인, 적용 버튼
        _pad = 10
        btn_frm = ctk.CTkFrame(self, fg_color="transparent")
        btn_frm.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.apply_btn = ctk.CTkButton(
            btn_frm,
            text="적용",
            width=120,
            height=36,
            command=self._on_apply_with_confirm,
        )
        self.apply_btn.pack(side=tk.RIGHT)
        ctk.CTkButton(
            btn_frm, text="확인", width=120, height=36, command=self._on_confirm_and_close
        ).pack(side=tk.RIGHT, padx=(0, _pad))
        ctk.CTkButton(
            btn_frm, text="취소", width=120, height=36, command=self._on_cancel
        ).pack(side=tk.RIGHT, padx=(0, _pad))

    def _refresh_case_list(self):
        self.case_listbox.delete(0, tk.END)
        effective = self.get_effective_hidden()
        effective_cns = {self._hidden_item_to_case_number(h) for h in effective}
        case_list = getattr(self.app, "case_list", []) or []
        pending_del = set(getattr(self, "pending_deletes", []) or [])

        def _cn(c):
            r = c.get("사건번호", "")
            return str(r).strip() if r is not None else ""

        self._visible_case_list = [
            c
            for c in case_list
            if _cn(c) not in effective_cns and _cn(c) not in pending_del
        ]
        for case in self._visible_case_list:
            self.case_listbox.insert(tk.END, _case_display_text(case))
        if getattr(self, "case_list_label", None) is not None:
            self.case_list_label.configure(
                text=f"사건 목록 ({len(self._visible_case_list)})"
            )

    def _on_case_list_select(self, event=None):
        self._update_button_states()

    def _update_button_states(self):
        """조건에 따라 7개 버튼 활성/비활성."""
        case_sel = self.case_listbox.curselection()
        case_n = len(case_sel)
        unhide_sel = self.unhide_listbox.curselection()
        unhide_n = len(unhide_sel)
        pending_sel = self.pending_listbox.curselection()
        pending_n = len(pending_sel)
        pending_has_items = self.pending_listbox.size() > 0

        self.hide_btn.configure(state="normal" if case_n >= 1 else "disabled")
        self.unhide_btn.configure(state="normal" if unhide_n >= 1 else "disabled")
        self.delete_btn.configure(state="normal" if case_n >= 1 else "disabled")
        self.cancel_pending_btn.configure(
            state="normal" if pending_has_items and pending_n >= 1 else "disabled"
        )

        add_cn = ""
        if getattr(self, "add_entries", None) and "사건번호" in self.add_entries:
            e = self.add_entries["사건번호"]
            add_cn = (e.get() if hasattr(e, "get") else getattr(e, "get", lambda: "")()).strip()
        self.add_btn.configure(state="normal" if add_cn else "disabled")

        self.load_edit_btn.configure(state="normal" if case_n == 1 else "disabled")

        cn = getattr(self, "_editing_case_number", None) or ""
        if not cn:
            self.edit_save_btn.configure(state="disabled")
        else:
            row = getattr(self, "edit_entries", None)
            if not row:
                self.edit_save_btn.configure(state="disabled")
            else:
                current = {k: (e.get() if hasattr(e, "get") else "").strip() for k, e in row.items()}
                baseline = self.pending_updates.get(cn) or getattr(self, "_loaded_edit_row", None)
                if baseline is None:
                    self.edit_save_btn.configure(state="normal")
                else:
                    same = all(str(current.get(k, "")) == str(baseline.get(k, "")) for k in row)
                    self.edit_save_btn.configure(state="disabled" if same else "normal")

    def _on_left_list_double_click(self, event=None):
        """왼쪽 사건 목록 더블클릭 시 수정 탭 입력창에 해당 사건 불러오기."""
        selected = self._get_selected_from_left_list()
        if len(selected) == 1:
            self.tabview.set("사건 수정")
            self._load_edit_case()

    def _on_cancel(self):
        """취소: 적용된 적 있으면 '적용 사항 취소' 확인 후 되돌리기 및 닫기, 없으면 그냥 닫기."""
        if getattr(self, "_last_apply_undo", None):
            if messagebox.askyesno(
                "확인", "적용 사항을 취소하시겠습니까?", parent=self
            ):
                self._revert_last_apply()
        self._on_close()

    def _revert_last_apply(self):
        """마지막 적용 분을 되돌린다 (시트·숨김 복원 후 스냅샷 해제)."""
        u = getattr(self, "_last_apply_undo", None)
        if not u:
            return
        svc = self.app.google_sheets_service
        # 되돌리기 순서: 적용의 역순 — 삭제 복원 → 수정 복원 → 추가 취소 → 숨김 복원
        for row_dict in u.get("deletes_rows", []):
            svc.append_row_to_case_list(row_dict)
        for cn, old_dict in u.get("updates_old", {}).items():
            svc.update_row_by_case_number(cn, old_dict)
        for cn in u.get("added_cns", []):
            svc.delete_row_by_case_number(cn)
        hidden = list(load_hidden_cases())
        add_cns = u.get("hidden_add_cns") or set()
        hidden = [
            h for h in hidden
            if self._hidden_item_to_case_number(h) not in add_cns
        ]
        hidden.extend(u.get("hidden_remove_items") or [])
        save_hidden_cases(hidden)
        self.app.load_google_sheet()
        self._last_apply_undo = None
        self._refresh_case_list()
        self._refresh_unhide_list()
        self._update_apply_button_and_summary()

    def _on_apply_with_confirm(self):
        """적용 버튼: 확인 다이얼로그 후 적용 실행."""
        if messagebox.askyesno("확인", "적용을 완료하시겠습니까?", parent=self):
            self._on_apply()

    def _on_confirm_and_close(self):
        """확인 버튼: 적용할 항목이 있으면 적용, 그 다음 새로고침 후 창 닫기."""
        self._on_apply()
        self.app.load_google_sheet()
        self._on_close()

    def _hidden_item_to_case_number(self, s):
        """저장 항목(표시 문자열 또는 사건번호)에서 사건번호만 추출."""
        s = str(s).strip()
        return s.split(" - ")[0].strip() if " - " in s else s

    def get_effective_hidden(self):
        """화면용 숨김 목록: 저장된 hidden + pending_hidden_add - pending_hidden_remove."""
        hidden = list(load_hidden_cases())
        remove_cns = set(self.pending_hidden_remove)
        for item in self.pending_hidden_add:
            hidden.append(item)
        hidden = [
            h for h in hidden if self._hidden_item_to_case_number(h) not in remove_cns
        ]
        return hidden

    def _has_pending_changes(self):
        """변경사항이 하나라도 있으면 True."""
        return bool(
            self.pending_hidden_add
            or self.pending_hidden_remove
            or self.pending_adds
            or self.pending_updates
            or self.pending_deletes
        )

    def _get_change_summary_text(self):
        """변경 요약 문자열 (▶ 숨김 처리 N건 : ... 형식). 항목 많으면 처음 5건 + 외 N건."""
        _max_show = 5
        lines = []

        if self.pending_hidden_add:
            parts = self.pending_hidden_add[:_max_show]
            suffix = (
                f" 외 {len(self.pending_hidden_add) - _max_show}건"
                if len(self.pending_hidden_add) > _max_show
                else ""
            )
            lines.append(
                f"▶ 숨김 처리 {len(self.pending_hidden_add)}건 : {', '.join(parts)}{suffix}"
            )

        remove_cns = set(self.pending_hidden_remove)
        if remove_cns:
            hidden_src = list(load_hidden_cases()) + list(self.pending_hidden_add)
            unhide_displays = [
                item
                for item in hidden_src
                if self._hidden_item_to_case_number(item) in remove_cns
            ]
            parts = unhide_displays[:_max_show]
            suffix = (
                f" 외 {len(unhide_displays) - _max_show}건"
                if len(unhide_displays) > _max_show
                else ""
            )
            lines.append(
                f"▶ 숨김 해제 {len(unhide_displays)}건 : {', '.join(parts)}{suffix}"
            )

        if self.pending_deletes:
            parts = self.pending_deletes[:_max_show]
            suffix = (
                f" 외 {len(self.pending_deletes) - _max_show}건"
                if len(self.pending_deletes) > _max_show
                else ""
            )
            lines.append(
                f"▶ 사건 삭제 {len(self.pending_deletes)}건 : {', '.join(parts)}{suffix}"
            )

        if self.pending_updates:
            displays = [_case_display_text(d) for d in self.pending_updates.values()]
            parts = displays[:_max_show]
            suffix = (
                f" 외 {len(displays) - _max_show}건"
                if len(displays) > _max_show
                else ""
            )
            lines.append(
                f"▶ 사건 수정 {len(self.pending_updates)}건 : {', '.join(parts)}{suffix}"
            )

        if self.pending_adds:
            displays = [_case_display_text(d) for d in self.pending_adds]
            parts = displays[:_max_show]
            suffix = (
                f" 외 {len(displays) - _max_show}건"
                if len(displays) > _max_show
                else ""
            )
            lines.append(
                f"▶ 사건 추가 {len(self.pending_adds)}건 : {', '.join(parts)}{suffix}"
            )

        return "\n".join(lines) if lines else ""

    def _get_pending_change_list_lines(self):
        """변경 예정 목록용 한 줄씩 전체 목록 (말줄임 없음). [숨김 처리] ... 형식."""
        lines, _ = self._get_pending_change_list_lines_and_meta()
        return lines

    def _get_pending_change_list_lines_and_meta(self):
        """(lines, meta) 반환. meta[i] = (kind, key)로 인덱스→pending 항목 매핑."""
        lines = []
        meta = []
        for item in self.pending_hidden_add:
            lines.append(f"[숨김 처리] {item}")
            meta.append(("hidden_add", item))
        remove_cns = set(self.pending_hidden_remove)
        if remove_cns:
            hidden_src = list(load_hidden_cases()) + list(self.pending_hidden_add)
            for item in hidden_src:
                if self._hidden_item_to_case_number(item) in remove_cns:
                    lines.append(f"[숨김 해제] {item}")
                    meta.append(
                        ("hidden_remove", self._hidden_item_to_case_number(item))
                    )
        for cn in self.pending_deletes:
            lines.append(f"[사건 삭제] {cn}")
            meta.append(("delete", cn))
        for cn, row_dict in self.pending_updates.items():
            lines.append(f"[사건 수정] {_case_display_text(row_dict)}")
            meta.append(("update", cn))
        for i, row_dict in enumerate(self.pending_adds):
            lines.append(f"[사건 추가] {_case_display_text(row_dict)}")
            meta.append(("add", i))
        return lines, meta

    def _refresh_pending_list(self):
        """변경 예정 사건 목록 Listbox, 라벨 N, _pending_list_meta 갱신."""
        lines, meta = self._get_pending_change_list_lines_and_meta()
        self._pending_list_meta = meta
        self.pending_listbox.delete(0, tk.END)
        for line in lines:
            self.pending_listbox.insert(tk.END, line)
        n = len(lines)
        self.pending_list_label.configure(text=f"변경 예정 사건 목록 ({n})")

    def _update_apply_button_and_summary(self):
        """변경 여부에 따라 적용 버튼 활성/비활성 및 변경 예정 목록 VIEW 갱신."""
        has_changes = self._has_pending_changes()
        self.apply_btn.configure(state="normal" if has_changes else "disabled")
        self._refresh_pending_list()
        self._update_button_states()

    def _on_cancel_pending_change(self):
        """변경 예정 목록에서 선택한 항목을 pending에서 제거(되돌리기)."""
        sel = self.pending_listbox.curselection()
        if not sel:
            messagebox.showwarning(
                "선택", "되돌릴 항목을 목록에서 선택하세요.", parent=self
            )
            return
        meta = getattr(self, "_pending_list_meta", []) or []
        to_remove = [meta[i] for i in sel if i < len(meta)]
        if not to_remove:
            return
        add_indices = sorted(
            [key for kind, key in to_remove if kind == "add"], reverse=True
        )
        for idx in add_indices:
            if 0 <= idx < len(self.pending_adds):
                self.pending_adds.pop(idx)
        for kind, key in to_remove:
            if kind == "hidden_add" and key in self.pending_hidden_add:
                self.pending_hidden_add.remove(key)
            elif kind == "hidden_remove" and key in self.pending_hidden_remove:
                self.pending_hidden_remove.remove(key)
            elif kind == "delete" and key in self.pending_deletes:
                self.pending_deletes.remove(key)
            elif kind == "update" and key in self.pending_updates:
                del self.pending_updates[key]
        self._refresh_case_list()
        self._refresh_unhide_list()
        self._update_apply_button_and_summary()

    def _get_selected_from_left_list(self):
        """왼쪽 리스트에서 선택된 (인덱스, case) 리스트 반환."""
        sel = self.case_listbox.curselection()
        visible = getattr(self, "_visible_case_list", []) or []
        return [(i, visible[i]) for i in sel if 0 <= i < len(visible)]

    def _on_apply(self):
        """대기 중인 모든 변경을 구글 시트·숨김 목록에 한꺼번에 반영."""
        svc = self.app.google_sheets_service
        has_work = (
            self.pending_hidden_add
            or self.pending_hidden_remove
            or self.pending_adds
            or self.pending_updates
            or self.pending_deletes
        )
        if not has_work:
            return
        case_list = getattr(self.app, "case_list", []) or []

        def _cn(c):
            r = c.get("사건번호", "")
            return str(r).strip() if r is not None else ""

        # 되돌리기용 스냅샷 (적용 전 현재 상태)
        undo_added_cns = [d.get("사건번호") for d in self.pending_adds]
        undo_updates_old = {}
        for cn in self.pending_updates:
            for c in case_list:
                if _cn(c) == cn:
                    undo_updates_old[cn] = dict(c)
                    break
        undo_deletes_rows = []
        for cn in self.pending_deletes:
            for c in case_list:
                if _cn(c) == cn:
                    undo_deletes_rows.append(dict(c))
                    break
        hidden_now = list(load_hidden_cases())
        remove_cns = set(self.pending_hidden_remove)
        undo_hidden_remove_items = [
            h for h in hidden_now
            if self._hidden_item_to_case_number(h) in remove_cns
        ]
        undo_hidden_add_cns = {
            self._hidden_item_to_case_number(x) for x in self.pending_hidden_add
        }

        # 1. 숨김 반영
        hidden = list(hidden_now)
        existing_cns = {self._hidden_item_to_case_number(h) for h in hidden}
        for item in self.pending_hidden_add:
            cn = self._hidden_item_to_case_number(item)
            if cn and cn not in existing_cns:
                hidden.append(item)
                existing_cns.add(cn)
        hidden = [
            h for h in hidden if self._hidden_item_to_case_number(h) not in remove_cns
        ]
        save_hidden_cases(hidden)
        # 2. 시트 추가
        for row_dict in self.pending_adds:
            svc.append_row_to_case_list(row_dict)
        # 3. 시트 수정
        for cn, row_dict in self.pending_updates.items():
            svc.update_row_by_case_number(cn, row_dict)
        # 4. 시트 삭제
        for cn in self.pending_deletes:
            svc.delete_row_by_case_number(cn)
        # 5. 대기 비우기
        self.pending_hidden_add = []
        self.pending_hidden_remove = []
        self.pending_adds = []
        self.pending_updates = {}
        self.pending_deletes = []
        # 6. 되돌리기용 스냅샷 저장
        self._last_apply_undo = {
            "added_cns": undo_added_cns,
            "updates_old": undo_updates_old,
            "deletes_rows": undo_deletes_rows,
            "hidden_add_cns": undo_hidden_add_cns,
            "hidden_remove_items": undo_hidden_remove_items,
        }
        # 7. UI 갱신
        self._refresh_case_list()
        self._refresh_unhide_list()
        self._update_apply_button_and_summary()

    # 법원 행 = 입력창(280) + 드롭다운 버튼(32) + 간격(4) → 모든 입력창 이 길이로 통일
    _FORM_ENTRY_WIDTH = 280
    _FORM_ENTRY_TOTAL = 280 + 32 + 4

    def _form_frame(self, parent, keys):
        frm = ctk.CTkFrame(parent, fg_color="transparent")
        frm.pack(fill=tk.X)
        entries = {}
        for i, key in enumerate(keys):
            ctk.CTkLabel(frm, text=key, width=100, anchor="w").grid(
                row=i, column=0, padx=(0, 8), pady=4, sticky="w"
            )
            if key == "법원":
                ent = CourtAutocomplete(frm, width=self._FORM_ENTRY_WIDTH)
            else:
                ent = ctk.CTkEntry(frm, width=self._FORM_ENTRY_TOTAL)
            ent.grid(row=i, column=1, padx=0, pady=4, sticky="ew")
            entries[key] = ent
        frm.grid_columnconfigure(1, weight=0, minsize=self._FORM_ENTRY_TOTAL)
        return entries

    def _build_add_tab(self, tab):
        self.add_entries = self._form_frame(tab, DEFAULT_HEADER_KEYS)
        self.add_btn = ctk.CTkButton(
            tab, text="추가", width=120, height=32, command=self._on_add
        )
        self.add_btn.pack(pady=10)
        add_cn_ent = self.add_entries.get("사건번호")
        if add_cn_ent is not None:
            add_cn_ent.bind("<KeyRelease>", lambda e: self._update_button_states())

    def _on_add(self):
        row_dict = {k: (e.get() or "").strip() for k, e in self.add_entries.items()}
        if not row_dict.get("사건번호"):
            messagebox.showwarning("입력", "사건번호를 입력하세요.", parent=self)
            return
        self.pending_adds.append(row_dict)
        for key, e in self.add_entries.items():
            if key == "법원":
                e.set("")
            else:
                e.delete(0, tk.END)
        self._update_apply_button_and_summary()

    def _build_edit_tab(self, tab):
        ctk.CTkLabel(
            tab, text="왼쪽 목록에서 수정할 사건 1건 선택 후 불러오기 → 수정 후 적용"
        ).pack(anchor="w", pady=(0, 4))
        self.edit_entries = self._form_frame(tab, DEFAULT_HEADER_KEYS)
        btn_row = ctk.CTkFrame(tab, fg_color="transparent")
        btn_row.pack(pady=10)
        self.load_edit_btn = ctk.CTkButton(
            btn_row,
            text="선택 사건 불러오기",
            width=140,
            height=32,
            command=self._load_edit_case,
        )
        self.load_edit_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.edit_save_btn = ctk.CTkButton(
            btn_row, text="저장", width=100, height=32, command=self._on_edit_save
        )
        self.edit_save_btn.pack(side=tk.LEFT)
        for ent in self.edit_entries.values():
            w = getattr(ent, "entry", ent)
            w.bind("<KeyRelease>", lambda e: self._update_button_states())

    def _load_edit_case(self):
        selected = self._get_selected_from_left_list()
        if len(selected) != 1:
            messagebox.showwarning(
                "선택", "왼쪽 목록에서 수정할 사건을 1건만 선택하세요.", parent=self
            )
            return
        _, case = selected[0]
        raw = case.get("사건번호", "")
        self._editing_case_number = str(raw).strip() if raw is not None else ""
        for key, ent in self.edit_entries.items():
            val = str(case.get(key, "") or "")
            if key == "법원":
                ent.set(val)
            else:
                ent.delete(0, tk.END)
                ent.insert(0, val)
        self._loaded_edit_row = {k: str(case.get(k, "") or "") for k in self.edit_entries}
        self.app.log_message(f"수정 대상: {self._editing_case_number}")
        self._update_button_states()

    def _on_edit_save(self):
        if not self._editing_case_number:
            messagebox.showwarning(
                "선택",
                "먼저 '선택 사건 불러오기'로 수정할 사건을 불러오세요.",
                parent=self,
            )
            return
        row_dict = {k: (e.get() or "").strip() for k, e in self.edit_entries.items()}
        self.pending_updates[self._editing_case_number] = row_dict
        self._loaded_edit_row = dict(row_dict)
        self._refresh_case_list()
        self._update_apply_button_and_summary()
        self._update_button_states()

    def _on_delete(self):
        selected = self._get_selected_from_left_list()
        if not selected:
            messagebox.showwarning(
                "선택", "삭제할 사건을 목록에서 선택하세요.", parent=self
            )
            return
        n = len(selected)
        if not messagebox.askyesno(
            "확인", f"선택한 {n}건을 구글 시트에서 삭제할까요?", parent=self
        ):
            return
        for _, case in selected:
            raw = case.get("사건번호", "")
            cn = str(raw).strip() if raw is not None else ""
            if cn:
                self.pending_deletes.append(cn)
        self._refresh_case_list()
        self._update_apply_button_and_summary()

    def _on_hide(self):
        selected = self._get_selected_from_left_list()
        if not selected:
            messagebox.showwarning(
                "선택", "숨길 사건을 목록에서 선택하세요.", parent=self
            )
            return
        effective = self.get_effective_hidden()
        existing_cns = {self._hidden_item_to_case_number(h) for h in effective}
        added = 0
        for _, case in selected:
            raw = case.get("사건번호", "")
            cn = str(raw).strip() if raw is not None else ""
            if cn and cn not in existing_cns:
                self.pending_hidden_add.append(_case_display_text(case))
                existing_cns.add(cn)
                added += 1
        if added == 0:
            messagebox.showinfo("알림", "추가로 숨길 사건이 없습니다.", parent=self)
            return
        self._refresh_case_list()
        self._refresh_unhide_list()
        self._update_apply_button_and_summary()

    def _refresh_unhide_list(self):
        self.unhide_listbox.delete(0, tk.END)
        effective = self.get_effective_hidden()
        for item in effective:
            self.unhide_listbox.insert(tk.END, item)
        if getattr(self, "unhide_list_label", None) is not None:
            self.unhide_list_label.configure(text=f"숨긴 사건 ({len(effective)})")

    def _on_unhide(self):
        sel = self.unhide_listbox.curselection()
        if not sel:
            messagebox.showwarning(
                "선택", "숨김 해제할 사건을 선택하세요.", parent=self
            )
            return
        effective = self.get_effective_hidden()
        to_remove = [effective[i] for i in sel]
        for item in to_remove:
            self.pending_hidden_remove.append(self._hidden_item_to_case_number(item))
        self._refresh_unhide_list()
        self._refresh_case_list()
        self._update_apply_button_and_summary()
