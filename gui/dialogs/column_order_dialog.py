# -*- coding: utf-8 -*-
"""
열 순서 설정 다이얼로그
======================

역할: 사건 목록 테이블의 열 표시 순서를 위/아래로 이동하여 변경합니다.
호출: 사건 목록 헤더의 설정(톱니바퀴) 버튼 클릭 시 BatchProcessingGUI에서 띄웁니다.
적용 시 col_order가 바뀌고 UI가 해당 순서로 다시 그려집니다.
"""
import tkinter as tk
import customtkinter as ctk
from config import COL_NAMES


class ColumnOrderDialog(ctk.CTkToplevel):
    def __init__(self, parent, current_order, theme_color_getter, on_apply_callback):
        super().__init__(parent)
        self.title("사건 목록 열 순서")
        self.geometry("320x380")
        self.transient(parent)
        self.resizable(False, False)
        
        self.theme_color_getter = theme_color_getter
        self.on_apply_callback = on_apply_callback
        self.order = list(current_order)
        
        self._create_widgets()
        
    def _create_widgets(self):
        frm = ctk.CTkFrame(self, fg_color="transparent")
        frm.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        # 제목 라벨
        ctk.CTkLabel(
            frm,
            text="표시 순서 (위에서 아래가 왼쪽에서 오른쪽)",
            font=ctk.CTkFont(family="맑은 고딕", size=13),
        ).pack(anchor=tk.W, pady=(0, 6))

        # 리스트 영역
        list_frame = ctk.CTkFrame(frm, fg_color=("#2B2B2B", "#2B2B2B"))
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        self.listbox = tk.Listbox(
            list_frame,
            font=("맑은 고딕", 13),
            selectbackground=self.theme_color_getter("accent"),
            selectforeground="white",
            bg="#2B2B2B",
            fg="white",
            relief=tk.FLAT,
            highlightthickness=0,
            height=12,
        )
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        self._refresh_list()
        if self.order:
            self.listbox.selection_set(0)

        # 구분선
        sep_line = ctk.CTkFrame(
            frm, fg_color=self.theme_color_getter("border"), height=2, corner_radius=0
        )
        sep_line.pack(side=tk.BOTTOM, fill=tk.X, pady=(12, 0))
        sep_line.pack_propagate(False)

        # 버튼 행
        btn_row = ctk.CTkFrame(frm, fg_color="transparent")
        btn_row.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 4))
        btn_row.grid_columnconfigure(2, weight=1)

        BTN_PAD = 8
        ctk.CTkButton(
            btn_row, text="위로", width=70, height=36, text_color="#FFFFFF",
            command=self._move_up
        ).grid(row=0, column=0, padx=(0, BTN_PAD), sticky="w")
        
        ctk.CTkButton(
            btn_row, text="아래로", width=70, height=36, text_color="#FFFFFF",
            command=self._move_down
        ).grid(row=0, column=1, padx=(0, 0), sticky="w")
        
        ctk.CTkButton(
            btn_row, text="취소", width=70, height=36, text_color="#FFFFFF",
            command=self.destroy
        ).grid(row=0, column=3, padx=(BTN_PAD * 2, BTN_PAD), sticky="e")
        
        ctk.CTkButton(
            btn_row, text="적용", width=70, height=36, text_color="#FFFFFF",
            command=self._apply_and_close
        ).grid(row=0, column=4, padx=(0, 0), sticky="e")

        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        for internal_idx in self.order:
            self.listbox.insert(tk.END, COL_NAMES[internal_idx])

    def _move_up(self):
        sel = self.listbox.curselection()
        if not sel or sel[0] == 0:
            return
        i = sel[0]
        self.order[i], self.order[i - 1] = self.order[i - 1], self.order[i]
        self._refresh_list()
        self.listbox.selection_set(i - 1)

    def _move_down(self):
        sel = self.listbox.curselection()
        if not sel or sel[0] >= len(self.order) - 1:
            return
        i = sel[0]
        self.order[i], self.order[i + 1] = self.order[i + 1], self.order[i]
        self._refresh_list()
        self.listbox.selection_set(i + 1)

    def _apply_and_close(self):
        if self.on_apply_callback:
            self.on_apply_callback(self.order)
        self.destroy()
