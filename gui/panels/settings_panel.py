# -*- coding: utf-8 -*-
"""
설정 패널 (Settings Panel)
==========================
병렬 처리 수, 캡차 재시도 횟수, 재시도 대기시간, 테마(다크/라이트/시스템)를 설정합니다.
Why: 사용자가 처리 강도와 재시도 정책, 화면 테마를 코드 수정 없이 변경할 수 있게 합니다.
"""
import tkinter as tk
import customtkinter as ctk
import config


class SettingsPanel:
    """
    처리 설정 및 테마 선택 UI만 생성하는 클래스.
    값은 app의 IntVar/StringVar에 바인딩되며, FocusOut 시 app._sync_spin으로 범위가 보정됩니다.
    """

    @staticmethod
    def create(parent, app):
        """
        설정 패널 프레임을 생성하고, app에 _settings_parallel_entry, _theme_option_var 를 저장한 뒤 반환합니다.

        Parameters
        ----------
        parent : tk.Widget
            부모 위젯.
        app : object
            메인 윈도우. 필요 속성/메서드:
            - get_theme_color(key)
            - max_parallel, max_retry, retry_delay (tk.IntVar)
            - _appearance_mode (str: "Dark"|"Light"|"System")
            - _sync_spin(entry_widget, int_var, low, high)
            - _apply_theme(mode), _save_theme_setting(mode)
            - update_case_list_ui()
            생성 후 app._settings_parallel_entry, app._theme_option_var 가 설정됩니다.

        Returns
        -------
        ctk.CTkFrame
            설정 패널 프레임.
        """
        # 구분선: 제어 패널과 설정 패널 시각적 구분
        sep = ctk.CTkFrame(
            parent, fg_color=app.get_theme_color("border"), height=2, corner_radius=0
        )
        sep.pack(fill=tk.X, padx=10, pady=(0, 4))
        sep.pack_propagate(False)

        settings_frame = ctk.CTkFrame(
            parent, fg_color=app.get_theme_color("bg_primary")
        )
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        ctk.CTkLabel(
            settings_frame,
            text="⚙️ 처리 설정",
            font=ctk.CTkFont(family="맑은 고딕", size=16, weight="bold"),
            text_color=app.get_theme_color("text_main"),
        ).pack(anchor=tk.W, pady=(0, 8))

        settings_inner = ctk.CTkFrame(
            settings_frame, fg_color=app.get_theme_color("bg_primary")
        )
        settings_inner.pack(fill=tk.X, padx=0, pady=8)

        # ---- 병렬 처리 수 ----
        ctk.CTkLabel(
            settings_inner,
            text="⚡ 병렬 처리 수:",
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
            text_color=app.get_theme_color("text_main"),
        ).grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=2)
        max_limit = getattr(config, "MAX_PARALLEL_LIMIT", 20)
        parallel_entry = ctk.CTkEntry(
            settings_inner,
            width=80,
            height=28,
            font=ctk.CTkFont(family="맑은 고딕", size=13),
        )
        parallel_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 25))
        parallel_entry.insert(0, str(app.max_parallel.get()))
        parallel_entry.bind(
            "<FocusOut>",
            lambda e: app._sync_spin(parallel_entry, app.max_parallel, 1, max_limit),
        )
        app._settings_parallel_entry = parallel_entry

        # ---- 캡차 재시도 횟수 ----
        ctk.CTkLabel(
            settings_inner,
            text="🔄 캡차 재시도 횟수:",
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
            text_color=app.get_theme_color("text_main"),
        ).grid(row=0, column=2, sticky=tk.W, padx=(0, 10), pady=2)
        retry_entry = ctk.CTkEntry(
            settings_inner,
            width=80,
            height=28,
            font=ctk.CTkFont(family="맑은 고딕", size=13),
        )
        retry_entry.grid(row=0, column=3, sticky=tk.W, padx=(0, 25))
        retry_entry.insert(0, str(app.max_retry.get()))
        retry_entry.bind(
            "<FocusOut>",
            lambda e: app._sync_spin(retry_entry, app.max_retry, 1, 10),
        )

        # ---- 재시도 간 대기시간 ----
        ctk.CTkLabel(
            settings_inner,
            text="⏱️ 재시도 간 대기시간(초):",
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
            text_color=app.get_theme_color("text_main"),
        ).grid(row=0, column=4, sticky=tk.W, padx=(0, 10), pady=2)
        delay_entry = ctk.CTkEntry(
            settings_inner,
            width=80,
            height=28,
            font=ctk.CTkFont(family="맑은 고딕", size=13),
        )
        delay_entry.grid(row=0, column=5, sticky=tk.W, pady=2)
        delay_entry.insert(0, str(app.retry_delay.get()))
        delay_entry.bind(
            "<FocusOut>",
            lambda e: app._sync_spin(delay_entry, app.retry_delay, 1, 10),
        )

        # ---- 테마 선택 ----
        theme_display = {
            "Dark": "다크(Dark)",
            "Light": "라이트(Light)",
            "System": "시스템(System)",
        }
        theme_options = ["다크(Dark)", "라이트(Light)", "시스템(System)"]
        current_display = theme_display.get(app._appearance_mode, "다크(Dark)")

        ctk.CTkLabel(
            settings_inner,
            text="🎨 테마:",
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
            text_color=app.get_theme_color("text_main"),
        ).grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(12, 2))

        def on_theme_change(choice):
            mode = (
                "Dark"
                if choice == "다크(Dark)"
                else ("Light" if choice == "라이트(Light)" else "System")
            )
            app._apply_theme(mode)
            app._save_theme_setting(mode)
            if hasattr(app, "case_list") and app.case_list:
                app.update_case_list_ui()

        theme_var = ctk.StringVar(value=current_display)
        theme_menu = ctk.CTkOptionMenu(
            settings_inner,
            values=theme_options,
            variable=theme_var,
            width=140,
            command=on_theme_change,
        )
        theme_menu.grid(row=1, column=1, sticky=tk.W, padx=(0, 25), pady=(12, 2))
        app._theme_option_var = theme_var

        return settings_frame
