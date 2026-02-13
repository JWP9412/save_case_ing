#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
캡차 입력 다이얼로그
====================

역할: 캡차 이미지를 보여주고 6자리 자동입력방지문구를 입력받는 팝업 창.
호출 시점: batch_gui_maker에서 캡차 이미지를 팝업으로 보여주고 입력받을 때 사용 (현재 흐름에서는 인라인 입력을 주로 사용).
반환: show() 가 사용자가 입력한 6자리 문자열 또는 취소 시 None.
"""

import os
import tkinter as tk
from tkinter import messagebox


class CaptchaInputDialog:
    """캡차 입력 다이얼로그"""

    def __init__(self, parent, case_number, image_path):
        self.parent = parent
        self.case_number = case_number
        self.image_path = image_path
        self.result = None
        self.dialog = None

    def show(self):
        """캡차 입력 다이얼로그 표시"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"캡차 입력 - {self.case_number}")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)

        # 모달 다이얼로그로 설정
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 중앙에 배치
        self.dialog.eval("tk::PlaceWindow . center")

        self.create_widgets()

        # 다이얼로그가 닫힐 때까지 대기
        self.dialog.wait_window()

        return self.result

    def create_widgets(self):
        """위젯 생성"""
        # 메인 프레임
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 제목
        title_label = tk.Label(
            main_frame,
            text="자동입력방지문구 입력",
            font=("Arial", 14, "bold"),
            fg="blue",
        )
        title_label.pack(pady=(0, 20))

        # 사건번호
        case_label = tk.Label(
            main_frame,
            text=f"사건번호: {self.case_number}",
            font=("Arial", 12),
            fg="red",
        )
        case_label.pack(pady=(0, 10))

        # 캡차 이미지 영역
        image_frame = tk.Frame(main_frame, relief=tk.SUNKEN, bd=2, bg="white")
        image_frame.pack(fill=tk.X, pady=(0, 20))

        # 이미지 표시
        if self.image_path and os.path.exists(self.image_path):
            try:
                from PIL import Image, ImageTk

                img = Image.open(self.image_path)
                img = img.resize((300, 100), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)

                img_label = tk.Label(image_frame, image=photo, bg="white")
                img_label.image = photo  # 참조 유지
                img_label.pack(pady=10)
            except Exception as e:
                error_label = tk.Label(
                    image_frame, text=f"이미지 로드 실패: {e}", fg="red", bg="white"
                )
                error_label.pack(pady=10)
        else:
            error_label = tk.Label(
                image_frame, text="캡차 이미지를 찾을 수 없습니다", fg="red", bg="white"
            )
            error_label.pack(pady=10)

        # 입력 안내
        instruction_label = tk.Label(
            main_frame,
            text="위 이미지에서 6글자 자동입력방지문구를 입력하세요:",
            font=("Arial", 11),
        )
        instruction_label.pack(pady=(0, 10))

        # 입력 필드
        self.captcha_var = tk.StringVar()
        self.captcha_entry = tk.Entry(
            main_frame,
            textvariable=self.captcha_var,
            font=("Arial", 14),
            width=10,
            justify=tk.CENTER,
        )
        self.captcha_entry.pack(pady=(0, 20))
        self.captcha_entry.focus()

        # 버튼 프레임
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        # 확인 버튼
        ok_btn = tk.Button(
            button_frame,
            text="확인",
            font=("Arial", 12),
            bg="lightgreen",
            width=10,
            command=self.ok_clicked,
        )
        ok_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 취소 버튼
        cancel_btn = tk.Button(
            button_frame,
            text="취소",
            font=("Arial", 12),
            bg="lightcoral",
            width=10,
            command=self.cancel_clicked,
        )
        cancel_btn.pack(side=tk.LEFT)

        # 엔터키로 확인
        self.captcha_entry.bind("<Return>", lambda e: self.ok_clicked())

    def ok_clicked(self):
        """확인 버튼 클릭"""
        captcha_text = self.captcha_var.get().strip()
        if len(captcha_text) == 6:
            self.result = captcha_text
            self.dialog.destroy()
        else:
            messagebox.showwarning("경고", "6글자를 정확히 입력해주세요.")

    def cancel_clicked(self):
        """취소 버튼 클릭"""
        self.result = None
        self.dialog.destroy()
