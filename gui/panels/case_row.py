import tkinter as tk
import customtkinter as ctk
from config import COL_NAMES

class CaseRow:
    """
    단일 사건 행(Row) 생성을 전담하는 클래스.
    CaseListPanel의 create_case_row 메서드에서 분리됨.
    """
    @staticmethod
    def create(app, parent, case, index, total_width, initial_status=None):
        """
        단일 사건 행 위젯을 생성하고 반환합니다.

        Parameters
        ----------
        app : BatchProcessingGUI
            메인 윈도우 인스턴스 (테마 색상, 콜백 등 사용).
        parent : tk.Widget
            부모 위젯 (CaseListPanel의 case_frame).
        case : dict
            사건 데이터.
        index : int
            사건 인덱스.
        total_width : int
            행 전체 너비.
        initial_status : dict, optional
            초기 상태 정보 (status, color, emoji 등).

        Returns
        -------
        tuple
            (row_container, components, cell_frames)
            - row_container: 행 전체를 감싸는 컨테이너 프레임
            - components: 행 내부의 주요 위젯들 (체크박스, 텍스트박스, 버튼 등)을 담은 딕셔너리
            - cell_frames: 각 열(Column)의 프레임 리스트
        """
        bg_color = (
            app.get_theme_color("row_odd")
            if index % 2 == 0
            else app.get_theme_color("row_even")
        )
        row_container = ctk.CTkFrame(parent, fg_color="transparent")
        row_container.pack(fill=tk.X, pady=0, padx=0)
        
        case_frame = ctk.CTkFrame(
            row_container,
            fg_color=bg_color,
            height=60,
            width=total_width,
            corner_radius=0,
        )
        case_frame.pack(fill=tk.X)
        case_frame.pack_propagate(False)
        
        separator = tk.Frame(
            row_container,
            bg=app.get_theme_color("border"),
            height=1,
            width=total_width,
            bd=0,
            highlightthickness=0,
        )
        separator.pack(fill=tk.X)
        separator.pack_propagate(False)
        app.case_separators[index] = separator
        
        components = {}
        extra_last = getattr(app, "_extra_width_last_col", 0)
        last_internal = app.col_order[-1] if app.col_order else None

        def _cell_width(internal_idx):
            return app.col_widths[internal_idx] + (
                extra_last if internal_idx == last_internal else 0
            )

        frames_by_internal = [None] * len(COL_NAMES)
        
        # 0. 체크박스
        f0 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(0),
            height=60,
            bd=0,
            highlightthickness=0,
        )
        f0.pack_propagate(False)
        frames_by_internal[0] = f0
        var = tk.BooleanVar()
        ctk.CTkCheckBox(
            f0,
            variable=var,
            text="",
            fg_color=bg_color,
            width=24,
            command=lambda idx=index: app.on_checkbox_change(idx),
        ).place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        components["checkbox_var"] = var
        
        # 1~3. 사건 정보 (법원+사건번호, 피고+사건명, 비고)
        info_parts = [
            f"{case.get('법원', '')} {case.get('사건번호', '')}".strip(),
            f"{case.get('피고', '')} {case.get('사건명', '')}".strip(),
            str(case.get("비고", "") or ""),
        ]
        for i, text in enumerate(info_parts, start=1):
            fi = tk.Frame(
                case_frame,
                bg=bg_color,
                width=_cell_width(i),
                height=60,
                bd=0,
                highlightthickness=0,
            )
            fi.pack_propagate(False)
            frames_by_internal[i] = fi
            tb = ctk.CTkTextbox(
                fi,
                font=ctk.CTkFont(family="맑은 고딕", size=13),
                fg_color=bg_color,
                text_color=app.get_theme_color("text_main"),
                height=36,
                activate_scrollbars=False,
                wrap=tk.NONE,
                border_width=0,
            )
            tb.pack(fill=tk.X, expand=True, padx=6, pady=12)
            tb.insert("1.0", text)
            tb.configure(state="disabled")
            components[f"label_info_{i}"] = tb
            
        # 4. 캡차 이미지
        f4 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(4),
            height=60,
            bd=0,
            highlightthickness=0,
        )
        f4.pack_propagate(False)
        frames_by_internal[4] = f4
        il = tk.Label(
            f4,
            text="대기중",
            font=app.get_theme_color("font_small"),
            fg=app.get_theme_color("text_sub"),
            bg=app.get_theme_color("bg_primary"),
            relief=tk.FLAT,
        )
        il.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        components["image_label"] = il
        
        # 5. 캡차 입력
        f5 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(5),
            height=60,
            bd=0,
            highlightthickness=0,
        )
        f5.pack_propagate(False)
        frames_by_internal[5] = f5
        captcha_var = tk.StringVar()
        captcha_entry = ctk.CTkEntry(
            f5,
            textvariable=captcha_var,
            font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold"),
            justify=tk.CENTER,
            width=70,
            height=28,
        )
        captcha_entry.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        captcha_entry.bind(
            "<KeyRelease>", lambda e, idx=index: app._validate_captcha_entry(idx)
        )
        try:
            captcha_entry.bind(
                "<Return>", lambda e, idx=index: app.on_captcha_enter(idx)
            )
        except Exception:
            pass
        components["captcha_var"] = captcha_var
        components["captcha_entry"] = captcha_entry
        
        # 6. 상태
        f6 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(6),
            height=60,
            bd=0,
            highlightthickness=0,
        )
        f6.pack_propagate(False)
        frames_by_internal[6] = f6
        if initial_status and isinstance(initial_status, dict):
            st = initial_status.get("status", "대기")
            em = initial_status.get("emoji", "⏸️")
            status_text = f"{em} {st}" if em else st
            status_fg = initial_status.get("color", app.get_theme_color("text_sub"))
        else:
            status_text, status_fg = "⏸️ 대기", app.get_theme_color("text_sub")
        sl = ctk.CTkLabel(
            f6,
            text=status_text,
            font=ctk.CTkFont(family="맑은 고딕", size=13),
            text_color=status_fg,
        )
        sl.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        components["status_label"] = sl
        
        # 7. 기록(쿠키)
        f7 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(7),
            height=60,
            bd=0,
            highlightthickness=0,
        )
        f7.pack_propagate(False)
        frames_by_internal[7] = f7
        cn = case.get("사건번호", "")
        search_log = app.log_history_manager.load_search_log()
        if cn in search_log:
            record_text, record_fg = "🍪 검색함", app.get_theme_color("success")
        else:
            record_text, record_fg = "-", app.get_theme_color("text_sub")
        rl = ctk.CTkLabel(
            f7,
            text=record_text,
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            text_color=record_fg,
        )
        rl.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        components["record_label"] = rl
        
        # 8. 최근 업데이트
        f8 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(8),
            height=60,
            bd=0,
            highlightthickness=0,
        )
        f8.pack_propagate(False)
        frames_by_internal[8] = f8
        u_container = tk.Frame(f8, bg=bg_color)
        u_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        history = app.load_update_history()
        c_data = history.get(cn, {})
        last_date = (
            c_data.get("last_update", "-") if isinstance(c_data, dict) else c_data
        )
        days_since = app.get_days_since_update(case)
        date_label = ctk.CTkLabel(
            u_container,
            text=last_date,
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            text_color=app.get_theme_color("text_sub"),
        )
        date_label.pack(anchor=tk.CENTER)
        is_auto = c_data.get("is_auto", False)
        d_suffix = " (자동 조회)" if is_auto else ""
        d_text = "-" if days_since < 0 else f"D+{days_since}{d_suffix}"
        d_fg = (
            app.get_theme_color("text_sub")
            if days_since < 0
            else (
                app.get_theme_color("error")
                if days_since >= 3
                else app.get_theme_color("success")
            )
        )
        d_label = ctk.CTkLabel(
            u_container,
            text=d_text,
            font=ctk.CTkFont(family="맑은 고딕", size=13, weight="bold"),
            text_color=d_fg,
        )
        d_label.pack(anchor=tk.CENTER)
        components["update_date_label"] = date_label
        components["update_d_label"] = d_label
        
        # 9. 시트 버튼
        f9 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(9),
            height=60,
            bd=0,
            highlightthickness=0,
        )
        f9.pack_propagate(False)
        frames_by_internal[9] = f9
        ctk.CTkButton(
            f9,
            text="📝 시트",
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            fg_color=app.get_theme_color("accent"),
            hover_color=app.get_theme_color("accent"),
            width=50,
            height=28,
            cursor="hand2",
            command=lambda idx=index: app._open_sheet_viewer(idx),
        ).place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        cell_frames = []
        for disp_idx, internal_idx in enumerate(app.col_order):
            frame = frames_by_internal[internal_idx]
            frame.pack(side=tk.LEFT)
            frame.pack_propagate(False)
            cell_frames.append(frame)
            
        app.case_frames[index] = case_frame
        return row_container, components, cell_frames
