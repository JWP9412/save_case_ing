# -*- coding: utf-8 -*-
"""
수동 캡차 입력 모아보기 창
==========================
OCR 실패·수동 입력이 필요한 사건만 모아 보여 주는 비모달 창입니다.

주니어 개발자 참고:
- grab_set() 을 쓰지 않아 메인 창을 계속 조작할 수 있습니다.
- 입력칸은 app.case_inputs[idx] StringVar 를 그대로 공유합니다.
  → 메인 목록 행과 값이 자동으로 같고, 워커가 읽는 값과도 동일합니다.
- Enter 로 다음 행으로 이동하고, 마지막 칸이면 자동 제출을 시도합니다.
"""
from __future__ import annotations

import os
import tkinter as tk

import customtkinter as ctk

from gui.utils.bind_utils import bind_entry_return


def ensure_manual_captcha_dialog(app):
    """
    이미 열려 있으면 그 인스턴스를, 없으면 새로 만들어 반환합니다.
    메인 스레드에서만 호출하세요.
    """
    dlg = getattr(app, "_manual_captcha_dialog", None)
    if dlg is not None:
        try:
            if dlg.winfo_exists():
                dlg.lift()
                return dlg
        except Exception:
            pass
    dlg = ManualCaptchaDialog(app)
    app._manual_captcha_dialog = dlg
    return dlg


class ManualCaptchaDialog(ctk.CTkToplevel):
    """OCR 실패 건만 모은 비모달 캡차 입력 창."""

    def __init__(self, app):
        parent = getattr(app, "root", None)
        super().__init__(parent)
        self.app = app
        self.title("수동 캡차 입력")
        self.geometry("520x420")
        self.minsize(420, 280)
        # 비모달: grab_set 하지 않음
        try:
            if parent is not None:
                self.transient(parent)
        except Exception:
            pass

        # case_index -> {frame, image_label, photo, entry, case_number}
        self._rows = {}
        self._photos = {}  # GC 방지용 PhotoImage 참조

        self._build_ui()
        self._place_near_main()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill=tk.X, padx=12, pady=(12, 4))
        ctk.CTkLabel(
            header,
            text="OCR이 실패한 사건만 모았습니다. 6자리 입력 후 Enter.",
            font=ctk.CTkFont(family="맑은 고딕", size=13),
            wraplength=480,
            justify=tk.LEFT,
        ).pack(anchor=tk.W)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill=tk.X, padx=12, pady=(0, 12))
        ctk.CTkButton(
            footer,
            text="입력된 건 제출",
            width=140,
            height=32,
            command=self._submit_if_ready,
        ).pack(side=tk.RIGHT)
        ctk.CTkButton(
            footer,
            text="닫기",
            width=80,
            height=32,
            fg_color="#7F8C8D",
            hover_color="#5D6D7E",
            command=self._on_close,
        ).pack(side=tk.RIGHT, padx=(0, 8))

    def _place_near_main(self):
        """메인 창 오른쪽에 배치."""
        try:
            self.update_idletasks()
            root = getattr(self.app, "root", None)
            if root is None:
                return
            rx = int(root.winfo_rootx())
            ry = int(root.winfo_rooty())
            rw = int(root.winfo_width())
            rh = int(root.winfo_height())
            sw = int(root.winfo_screenwidth())
            sh = int(root.winfo_screenheight())
            dw = max(420, int(self.winfo_width() or 520))
            dh = max(280, int(self.winfo_height() or 420))

            # 주니어 참고:
            # - 우선순위는 "메인 창 오른쪽 바깥".
            # - 화면을 넘기면 "메인 창 안쪽 우측"으로 되돌려, 창이 안 보이는 상황을 막습니다.
            x_preferred = rx + rw + 12
            x_inside = rx + max(0, rw - dw - 12)
            x = x_preferred if (x_preferred + dw) <= sw else x_inside
            x = max(0, min(x, max(0, sw - dw - 8)))

            y_preferred = ry + 80
            y = max(0, min(y_preferred, max(0, sh - dh - 40)))
            # 메인 창이 아주 작을 때도 최소한 일부는 메인 창 근처에 보이게 보정
            if rh > 0 and y > (ry + rh - 40):
                y = max(0, ry + 20)
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def add_case(self, case_index, case_number, image_path=None):
        """수동 입력 행을 추가합니다. 이미 있으면 이미지만 갱신."""
        if case_index in self._rows:
            if image_path:
                self.update_image(case_index, image_path)
            self._place_near_main()
            self._bring_to_front()
            return

        var = getattr(self.app, "case_inputs", {}).get(case_index)
        if var is None:
            var = tk.StringVar()
            if not hasattr(self.app, "case_inputs"):
                self.app.case_inputs = {}
            self.app.case_inputs[case_index] = var

        row = ctk.CTkFrame(self.scroll, corner_radius=8)
        row.pack(fill=tk.X, padx=4, pady=6)

        top = ctk.CTkFrame(row, fg_color="transparent")
        top.pack(fill=tk.X, padx=8, pady=(8, 4))
        ctk.CTkLabel(
            top,
            text=str(case_number or f"#{case_index}"),
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
        ).pack(side=tk.LEFT)

        img_label = tk.Label(
            row,
            text="이미지 없음",
            width=28,
            height=3,
            bg="#2C3E50",
            fg="#ECF0F1",
            font=("맑은 고딕", 10),
        )
        img_label.pack(padx=8, pady=4)

        entry = ctk.CTkEntry(
            row,
            textvariable=var,
            width=120,
            height=32,
            justify=tk.CENTER,
            font=ctk.CTkFont(family="맑은 고딕", size=16, weight="bold"),
        )
        entry.pack(pady=(4, 10))

        # 숫자만 남기기 + Enter 로 다음/제출
        def _on_key(_event=None, idx=case_index):
            from gui.utils import captcha_ui as captcha_ui_module

            captcha_ui_module.validate_captcha_entry(self.app, idx)

        entry.bind("<KeyRelease>", _on_key)
        bind_entry_return(entry, lambda e, idx=case_index: self._on_enter(idx))

        self._rows[case_index] = {
            "frame": row,
            "image_label": img_label,
            "entry": entry,
            "case_number": case_number,
        }
        if image_path:
            self.update_image(case_index, image_path)

        try:
            entry.focus_set()
            entry.icursor("end")
        except Exception:
            pass
        self._place_near_main()
        self._bring_to_front()

    def _bring_to_front(self):
        """다이얼로그를 사용자 눈앞으로 가져옵니다."""
        try:
            self.deiconify()
        except Exception:
            pass
        try:
            self.lift()
        except Exception:
            pass
        try:
            self.attributes("-topmost", True)
            self.after(120, lambda: self.attributes("-topmost", False))
        except Exception:
            pass

    def update_image(self, case_index, image_path):
        """행의 캡차 이미지를 교체합니다."""
        info = self._rows.get(case_index)
        if not info:
            return
        label = info["image_label"]
        if not image_path or not os.path.isfile(image_path):
            try:
                label.config(image="", text="이미지 없음")
            except Exception:
                pass
            return
        try:
            from PIL import Image, ImageTk

            img = Image.open(image_path)
            img = img.resize((220, 66), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._photos[case_index] = photo
            label.config(image=photo, text="", width=220, height=66)
            label.image = photo
        except Exception as e:
            try:
                label.config(image="", text=f"오류: {e}")
            except Exception:
                pass

    def remove_case(self, case_index):
        """처리 완료된 행을 제거합니다. 행이 없으면 창을 닫습니다."""
        info = self._rows.pop(case_index, None)
        self._photos.pop(case_index, None)
        if info:
            try:
                info["frame"].destroy()
            except Exception:
                pass
        if not self._rows:
            self._on_close()

    def refresh(self):
        """열려 있는 동안 포커스만 다시 줍니다."""
        try:
            self.lift()
        except Exception:
            pass

    def _ordered_indices(self):
        return list(self._rows.keys())

    def _on_enter(self, case_index):
        """Enter: 6자리면 다음 행, 마지막이면 제출 시도."""
        from gui.utils import captcha_ui as captcha_ui_module

        captcha_ui_module.validate_captcha_entry(self.app, case_index)
        val = captcha_ui_module.get_captcha_input(self.app, case_index) or ""
        if not (len(val) == 6 and val.isdigit()):
            try:
                self.app.log_message(
                    f"⚠️ 수동 캡차 형식 오류: '{val}' (사건 인덱스 {case_index})"
                )
            except Exception:
                pass
            return

        try:
            self.app.update_case_status(case_index, "입력완료", "blue")
        except Exception:
            pass

        indices = self._ordered_indices()
        try:
            pos = indices.index(case_index)
        except ValueError:
            pos = -1
        next_idx = indices[pos + 1] if 0 <= pos < len(indices) - 1 else None
        if next_idx is not None:
            entry = self._rows[next_idx]["entry"]
            try:
                entry.focus_set()
                entry.icursor("end")
            except Exception:
                pass
            return

        # 마지막 칸 → 자동 제출
        self._submit_if_ready()

    def _submit_if_ready(self):
        """채워진 수동 건이 있으면 웨이브 자동 제출을 재시도합니다."""
        try:
            pc = getattr(self.app, "process_controller", None)
            if pc is None:
                return
            wave = getattr(pc, "_wave_cases", None) or []
            if not wave:
                # 웨이브 정보가 없어도 완료 버튼과 동일하게 처리
                if hasattr(self.app, "start_processing_thread"):
                    self.app.start_processing_thread()
                return
            started = pc._try_auto_submit_captcha_wave(wave)
            if not started and hasattr(self.app, "start_processing_thread"):
                # 자동 제출 조건 미충족(플래그 등)이면 보조로 직접 제출
                # (수동만 남은 경우 ready_count>0 이면 위에서 True)
                filled = 0
                for idx in self._rows:
                    v = (self.app.get_captcha_input(idx) or "").strip()
                    if len(v) == 6 and v.isdigit():
                        filled += 1
                if filled > 0:
                    # 주니어 참고:
                    # 배치가 이미 돌고 있을 때 플래그를 강제로 내리면 중복 제출 스레드가 생깁니다.
                    if getattr(self.app, "_captcha_batch_running", False):
                        return
                    if not pc._try_auto_submit_captcha_wave(wave):
                        self.app.start_processing_thread()
        except Exception as e:
            try:
                self.app.log_message(f"⚠️ 수동 캡차 제출 실패: {e}")
            except Exception:
                pass

    def _on_close(self):
        try:
            if getattr(self.app, "_manual_captcha_dialog", None) is self:
                self.app._manual_captcha_dialog = None
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass
