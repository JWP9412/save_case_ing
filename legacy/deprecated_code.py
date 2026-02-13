# -*- coding: utf-8 -*-
"""
참고용, 실제 사용 안 함.
BatchProcessingGUI._deprecated_update_case_list_ui 를 옮겨 둔 것입니다.
현재 batch_gui_maker.py 에서는 호출하지 않습니다.
"""
import tkinter as tk
from config import COL_WIDTHS


def deprecated_update_case_list_ui(self):
    """사건 목록 UI 업데이트 (참고용, 실제 사용 안 함). self는 BatchProcessingGUI 인스턴스."""
    try:
        self.log_message(
            f"🔄 [DEBUG] update_case_list_ui 시작 - 사건 수: {len(self.case_list)}"
        )
        for widget in self.case_list_frame.winfo_children():
            widget.destroy()
        for widget in self.header_container.winfo_children():
            widget.destroy()
        self.case_checkboxes = {}
        self.log_message(f"🔄 [DEBUG] 기존 위젯 제거 완료")
    except Exception as e:
        self.log_message(f"❌ [ERROR] update_case_list_ui 오류: {e}")
        import traceback
        self.log_message(f"❌ [ERROR] 스택 트레이스: {traceback.format_exc()}")
        return

    try:
        self.col_widths = list(COL_WIDTHS)
        col_names = [
            "선택", "사건번호", "피고", "법원", "비고",
            "캡차 이미지", "캡차 입력", "상태", "최근 업데이트",
        ]
        self.log_message(f"🔄 [DEBUG] 헤더 생성 시작")
        header_frame = tk.Frame(self.header_container, bg="#34495E")
        header_frame.pack(fill=tk.BOTH, expand=True)
        for col_idx, (name, width) in enumerate(zip(col_names, self.col_widths)):
            header_cell = tk.Frame(header_frame, bg="#34495E", width=width, height=40)
            header_cell.pack(side=tk.LEFT)
            header_cell.pack_propagate(False)
            label = tk.Label(
                header_cell, text=name,
                font=("맑은 고딕", 10, "bold"), bg="#34495E", fg="white", anchor=tk.CENTER,
            )
            label.pack(fill=tk.BOTH, expand=True)
        self.log_message(f"✅ [DEBUG] 헤더 생성 완료")
    except Exception as e:
        self.log_message(f"❌ [ERROR] 헤더 생성 오류: {e}")
        import traceback
        self.log_message(f"❌ [ERROR] 스택 트레이스: {traceback.format_exc()}")
        return

    self.case_inputs = {}
    self.case_status = {}
    self.case_images = {}
    self.case_image_photos = {}
    self.case_frames = {}
    self.case_start_times = {}
    self.case_update_labels = {}
    self.case_update_date_labels = {}
    self.log_message(f"🔄 [DEBUG] 사건 목록 생성 시작 - {len(self.case_list)}개")
    total_width = sum(self.col_widths)

    for i, case in enumerate(self.case_list):
        if i == 0:
            self.log_message(f"🔄 [DEBUG] 첫 번째 사건 생성 중: {case.get('사건번호', '')}")
        bg_color = "#FFFFFF" if i % 2 == 0 else "#F8F9FA"
        row_container = tk.Frame(self.case_list_frame, bg="white", bd=0, padx=0, pady=0)
        row_container.pack(fill=tk.X, pady=0, padx=0)
        case_frame = tk.Frame(row_container, bg=bg_color, height=60, width=total_width, bd=0)
        case_frame.pack(fill=tk.X, padx=0, pady=0)
        case_frame.pack_propagate(False)
        if i == 0:
            row_container.update_idletasks()
            row_y = row_container.winfo_y()
            self.log_message(f"🔍 [DEBUG] 첫 번째 row_container Y 위치: {row_y}")
        separator = tk.Frame(row_container, bg="#DEE2E6", height=1, width=total_width)
        separator.pack(fill=tk.X)
        var = tk.BooleanVar()
        checkbox_frame = tk.Frame(case_frame, bg=bg_color, width=self.col_widths[0], height=60)
        checkbox_frame.pack(side=tk.LEFT)
        checkbox_frame.pack_propagate(False)
        checkbox = tk.Checkbutton(
            checkbox_frame, variable=var, bg=bg_color,
            command=lambda idx=i: self.on_checkbox_change(idx),
        )
        checkbox.pack(anchor=tk.CENTER, expand=True)
        case_number = case.get("사건번호", "")
        defendant = case.get("피고", "")
        court = case.get("법원", "")
        note = case.get("비고", "")
        history = self.load_update_history()
        case_data = history.get(case_number, {})
        if isinstance(case_data, str):
            last_update_date = case_data
        else:
            last_update_date = case_data.get("last_update", "")
        days_since = self.get_days_since_update(case)
        info_texts = [case_number, defendant, court, note]
        if i == 0:
            self.log_message(f"🔍 [DEBUG] 첫 번째 사건 데이터: {info_texts}")
        for col_idx, text in enumerate(info_texts, start=1):
            info_frame = tk.Frame(case_frame, bg=bg_color, width=self.col_widths[col_idx], height=60)
            info_frame.pack(side=tk.LEFT)
            info_frame.pack_propagate(False)
            label = tk.Label(
                info_frame, text=text,
                font=("맑은 고딕", 10, "bold"), bg=bg_color, fg="black", anchor=tk.W, padx=5, pady=5,
            )
            label.pack(fill=tk.BOTH, expand=True)
            if i == 0 and col_idx == 1:
                label.update_idletasks()
                self.log_message(f"🔍 [DEBUG] Label 실제 크기: {label.winfo_width()}x{label.winfo_height()}")
        image_frame = tk.Frame(case_frame, bg=bg_color, width=self.col_widths[5], height=60)
        image_frame.pack(side=tk.LEFT)
        image_frame.pack_propagate(False)
        image_label = tk.Label(
            image_frame, text="대기중", font=("맑은 고딕", 10, "bold"), fg="black", bg="#E9ECEF",
            anchor=tk.CENTER, relief=tk.SOLID, bd=1,
        )
        image_label.pack(fill=tk.BOTH, expand=True, padx=2, pady=5)
        captcha_frame = tk.Frame(case_frame, bg=bg_color, width=self.col_widths[6], height=60)
        captcha_frame.pack(side=tk.LEFT)
        captcha_frame.pack_propagate(False)
        captcha_var = tk.StringVar()
        captcha_entry = tk.Entry(
            captcha_frame, textvariable=captcha_var, font=("Arial", 10, "bold"),
            justify=tk.CENTER, bg="white", fg="black", relief=tk.SOLID, bd=1,
        )
        captcha_entry.pack(fill=tk.BOTH, expand=True, padx=2, pady=5)

        def validate_captcha_input(char):
            return char.isdigit() and len(captcha_var.get()) < 6
        captcha_entry.config(
            validate="key",
            validatecommand=(captcha_entry.register(validate_captcha_input), "%S"),
        )
        captcha_entry.bind("<Return>", lambda event, idx=i: self.on_captcha_enter(idx))

        status_frame = tk.Frame(case_frame, bg=bg_color, width=self.col_widths[7], height=60)
        status_frame.pack(side=tk.LEFT)
        status_frame.pack_propagate(False)
        status_label = tk.Label(
            status_frame, text="⏸️ 대기", font=("맑은 고딕", 10, "bold"),
            fg="black", bg=bg_color, anchor=tk.CENTER, pady=5,
        )
        status_label.pack(fill=tk.BOTH, expand=True)
        update_frame = tk.Frame(case_frame, bg=bg_color, width=self.col_widths[8], height=60)
        update_frame.pack(side=tk.LEFT)
        update_frame.pack_propagate(False)
        update_container = tk.Frame(update_frame, bg=bg_color)
        update_container.pack(fill=tk.BOTH, expand=True)
        date_label = None
        if last_update_date:
            date_str = last_update_date.split(" ")[0]
            date_label = tk.Label(
                update_container, text=date_str,
                font=("맑은 고딕", 8, "bold"), fg="black", bg=bg_color, anchor=tk.CENTER,
            )
            date_label.pack(pady=(5, 0))
        update_label = tk.Label(
            update_container, text=days_since, font=("맑은 고딕", 11, "bold"),
            fg="blue" if days_since != "-" else "black", bg=bg_color, anchor=tk.CENTER,
        )
        update_label.pack(pady=(0, 5))
        self.case_checkboxes[i] = var
        self.case_inputs[i] = captcha_var
        self.case_status[i] = status_label
        self.case_images[i] = image_label
        self.case_frames[i] = case_frame
        self.case_update_labels[i] = update_label
        self.case_update_date_labels[i] = date_label
        if i == 0:
            self.log_message(f"✅ [DEBUG] 첫 번째 사건 생성 완료")
        self.log_message(f"✅ [DEBUG] 사건 {i+1}/{len(self.case_list)} 생성 완료: {case_number}")

    self.log_message(f"✅ [DEBUG] 전체 사건 목록 생성 완료")
    try:
        self.case_list_frame.update_idletasks()
        self.header_container.update_idletasks()
        frame_width = self.case_list_frame.winfo_width()
        frame_height = self.case_list_frame.winfo_height()
        frame_children = len(self.case_list_frame.winfo_children())
        self.log_message(f"🔍 [DEBUG] case_list_frame 크기: {frame_width}x{frame_height}, 자식: {frame_children}")
        if hasattr(self, "case_canvas"):
            self.case_list_frame.update_idletasks()
            frame_w = self.case_list_frame.winfo_width()
            frame_h = self.case_list_frame.winfo_height()
            if self.case_canvas.find_all():
                window_coords = self.case_canvas.coords(self.case_canvas.find_all()[0])
                self.log_message(f"🔍 [DEBUG] Canvas window 좌표: {window_coords}")
            self.case_canvas.configure(scrollregion=(0, 0, frame_w, frame_h))
            self.case_canvas.yview_moveto(0)
            self.log_message(f"✅ [DEBUG] Canvas scrollregion 업데이트: (0, 0, {frame_w}, {frame_h})")
            self.log_message(f"🔍 [DEBUG] Canvas 크기: {self.case_canvas.winfo_width()}x{self.case_canvas.winfo_height()}")
        self.root.update_idletasks()
        self.log_message(f"✅ [DEBUG] UI 강제 업데이트 완료")
    except Exception as e:
        self.log_message(f"⚠️ [DEBUG] UI 업데이트 오류: {e}")
        import traceback
        self.log_message(f"⚠️ [DEBUG] 스택 트레이스: {traceback.format_exc()}")
