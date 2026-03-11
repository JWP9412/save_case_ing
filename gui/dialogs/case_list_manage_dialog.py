# -*- coding: utf-8 -*-
"""
사건목록 관리 다이얼로그
========================
사건 추가, 수정, 삭제, 숨기기, 숨김 해제 기능을 탭으로 제공합니다.
"""
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from gui.utils.google_sheet_ui import load_hidden_cases, save_hidden_cases


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
            self._listbox = tk.Listbox(
                self._popup,
                height=8,
                font=("맑은 고딕", 11),
                selectmode=tk.SINGLE,
                activestyle="none",
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


class CaseListManageDialog(ctk.CTkToplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("사건목록 관리")
        self.geometry("520x480")
        self.minsize(400, 400)
        self.transient(parent)
        self.resizable(True, True)

        self._create_widgets()

    def _create_widgets(self):
        tabview = ctk.CTkTabview(self, width=500, height=440)
        tabview.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tabview.add("사건 추가")
        tabview.add("사건 수정")
        tabview.add("사건 삭제")
        tabview.add("숨기기")
        tabview.add("숨김 해제")

        self._build_add_tab(tabview.tab("사건 추가"))
        self._build_edit_tab(tabview.tab("사건 수정"))
        self._build_delete_tab(tabview.tab("사건 삭제"))
        self._build_hide_tab(tabview.tab("숨기기"))
        self._build_unhide_tab(tabview.tab("숨김 해제"))

    # 법원 행 = 입력창(280) + 드롭다운 버튼(32) + 간격(4) → 모든 입력창 이 길이로 통일
    _FORM_ENTRY_WIDTH = 280
    _FORM_ENTRY_TOTAL = 280 + 32 + 4

    def _form_frame(self, parent, keys):
        frm = ctk.CTkFrame(parent, fg_color="transparent")
        frm.pack(fill=tk.BOTH, expand=True)
        entries = {}
        for i, key in enumerate(keys):
            ctk.CTkLabel(frm, text=key, width=100, anchor="w").grid(row=i, column=0, padx=(0, 8), pady=4, sticky="w")
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
        btn = ctk.CTkButton(tab, text="추가", width=120, height=32, command=self._on_add)
        btn.pack(pady=10)

    def _on_add(self):
        row_dict = {k: (e.get() or "").strip() for k, e in self.add_entries.items()}
        if not row_dict.get("사건번호"):
            messagebox.showwarning("입력", "사건번호를 입력하세요.", parent=self)
            return
        svc = self.app.google_sheets_service
        if not svc.append_row_to_case_list(row_dict):
            messagebox.showerror("오류", "시트에 행 추가에 실패했습니다.", parent=self)
            return
        messagebox.showinfo("완료", "사건을 추가했습니다. 목록을 새로고침합니다.", parent=self)
        self.app.load_google_sheet()
        for key, e in self.add_entries.items():
            if key == "법원":
                e.set("")
            else:
                e.delete(0, tk.END)

    def _build_edit_tab(self, tab):
        ctk.CTkLabel(tab, text="수정할 사건 선택 (목록에서 1건 선택 후 아래에서 수정)").pack(anchor="w", pady=(0, 4))
        self.edit_entries = self._form_frame(tab, DEFAULT_HEADER_KEYS)
        btn_row = ctk.CTkFrame(tab, fg_color="transparent")
        btn_row.pack(pady=10)
        ctk.CTkButton(btn_row, text="선택 사건 불러오기", width=140, height=32, command=self._load_edit_case).pack(side=tk.LEFT, padx=(0, 8))
        ctk.CTkButton(btn_row, text="저장", width=100, height=32, command=self._on_edit_save).pack(side=tk.LEFT)
        self._editing_case_number = None

    def _load_edit_case(self):
        selected = self.app.get_selected_cases()
        if len(selected) != 1:
            messagebox.showwarning("선택", "수정할 사건을 목록에서 1건만 선택하세요.", parent=self)
            return
        _, case = selected[0]
        raw = case.get("사건번호", "")
        self._editing_case_number = (str(raw).strip() if raw is not None else "")
        for key, ent in self.edit_entries.items():
            val = str(case.get(key, "") or "")
            if key == "법원":
                ent.set(val)
            else:
                ent.delete(0, tk.END)
                ent.insert(0, val)
        self.app.log_message(f"수정 대상: {self._editing_case_number}")

    def _on_edit_save(self):
        if not self._editing_case_number:
            messagebox.showwarning("선택", "먼저 '선택 사건 불러오기'로 수정할 사건을 불러오세요.", parent=self)
            return
        row_dict = {k: (e.get() or "").strip() for k, e in self.edit_entries.items()}
        svc = self.app.google_sheets_service
        if not svc.update_row_by_case_number(self._editing_case_number, row_dict):
            messagebox.showerror("오류", "시트 행 갱신에 실패했습니다.", parent=self)
            return
        messagebox.showinfo("완료", "수정했습니다. 목록을 새로고침합니다.", parent=self)
        self.app.load_google_sheet()
        self._editing_case_number = None

    def _build_delete_tab(self, tab):
        ctk.CTkLabel(tab, text="목록에서 삭제할 사건을 선택한 뒤 아래 버튼을 누르세요.").pack(anchor="w", pady=(0, 8))
        self.delete_btn = ctk.CTkButton(tab, text="선택한 사건을 시트에서 삭제", width=220, height=36, command=self._on_delete)
        self.delete_btn.pack(pady=10)

    def _on_delete(self):
        selected = self.app.get_selected_cases()
        if not selected:
            messagebox.showwarning("선택", "삭제할 사건을 목록에서 선택하세요.", parent=self)
            return
        n = len(selected)
        if not messagebox.askyesno("확인", f"선택한 {n}건을 구글 시트에서 삭제할까요?", parent=self):
            return
        svc = self.app.google_sheets_service
        failed = []
        for _, case in selected:
            raw = case.get("사건번호", "")
            cn = (str(raw).strip() if raw is not None else "")
            if not cn:
                continue
            if not svc.delete_row_by_case_number(cn):
                failed.append(cn)
        if failed:
            messagebox.showwarning("일부 실패", f"삭제 실패: {', '.join(failed)}", parent=self)
        else:
            messagebox.showinfo("완료", f"{n}건 삭제했습니다. 목록을 새로고침합니다.", parent=self)
        self.app.load_google_sheet()

    def _build_hide_tab(self, tab):
        ctk.CTkLabel(tab, text="숨길 사건을 목록에서 선택한 뒤 아래 버튼을 누르세요.").pack(anchor="w", pady=(0, 8))
        ctk.CTkButton(tab, text="선택한 사건 숨기기", width=180, height=36, command=self._on_hide).pack(pady=10)

    def _on_hide(self):
        selected = self.app.get_selected_cases()
        if not selected:
            messagebox.showwarning("선택", "숨길 사건을 목록에서 선택하세요.", parent=self)
            return
        hidden = load_hidden_cases()
        added = 0
        for _, case in selected:
            raw = case.get("사건번호", "")
            cn = (str(raw).strip() if raw is not None else "")
            if cn and cn not in hidden:
                hidden.append(cn)
                added += 1
        if added == 0:
            messagebox.showinfo("알림", "추가로 숨길 사건이 없습니다.", parent=self)
            return
        save_hidden_cases(hidden)
        def _cn(c):
            r = c.get("사건번호", "")
            return (str(r).strip() if r is not None else "")
        self.app.case_list = [c for c in self.app.case_list if _cn(c) not in hidden]
        self.app.update_case_list_ui()
        messagebox.showinfo("완료", f"{added}건 숨겼습니다.", parent=self)

    def _build_unhide_tab(self, tab):
        ctk.CTkLabel(tab, text="숨긴 사건을 선택한 뒤 '숨김 해제'를 누르세요.").pack(anchor="w", pady=(0, 4))
        list_frm = ctk.CTkFrame(tab, fg_color="transparent")
        list_frm.pack(fill=tk.BOTH, expand=True)
        self.unhide_listbox = tk.Listbox(list_frm, height=10, font=("맑은 고딕", 11), selectmode=tk.EXTENDED)
        self.unhide_listbox.pack(fill=tk.BOTH, expand=True)
        ctk.CTkButton(tab, text="숨김 해제", width=120, height=32, command=self._on_unhide).pack(pady=10)
        self._refresh_unhide_list()

    def _refresh_unhide_list(self):
        self.unhide_listbox.delete(0, tk.END)
        for cn in load_hidden_cases():
            self.unhide_listbox.insert(tk.END, cn)

    def _on_unhide(self):
        sel = self.unhide_listbox.curselection()
        if not sel:
            messagebox.showwarning("선택", "숨김 해제할 사건을 선택하세요.", parent=self)
            return
        hidden = load_hidden_cases()
        to_remove = [hidden[i] for i in sel]
        hidden = [c for c in hidden if c not in to_remove]
        save_hidden_cases(hidden)
        self._refresh_unhide_list()
        messagebox.showinfo("완료", f"{len(to_remove)}건 숨김 해제했습니다. 목록을 새로고침합니다.", parent=self)
        self.app.load_google_sheet()
