import re
from datetime import datetime
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
            height=90,
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
            height=90,
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
        
        # 1,2,4. 사건 정보 (법원/사건번호 줄바꿈+가운데, 피고/사건명 줄바꿈+가운데, 비고)
        info_indices = [1, 2, 4]
        court_and_num = "\n".join(
            filter(None, [str(case.get("법원", "") or "").strip(), str(case.get("사건번호", "") or "").strip()])
        ) or " "
        defendant_and_name = "\n".join(
            filter(None, [str(case.get("피고", "") or "").strip(), str(case.get("사건명", "") or "").strip()])
        ) or " "
        info_texts = [
            court_and_num,
            defendant_and_name,
            str(case.get("비고", "") or ""),
        ]
        for internal_idx, text in zip(info_indices, info_texts):
            fi = tk.Frame(
                case_frame,
                bg=bg_color,
                width=_cell_width(internal_idx),
                height=90,
                bd=0,
                highlightthickness=0,
            )
            fi.pack_propagate(False)
            fi.grid_propagate(False)
            frames_by_internal[internal_idx] = fi
            # 수직 가운데 정렬: grid로 상·하 공간 균등 배분 후 텍스트박스를 중간 행에 배치
            fi.grid_rowconfigure(0, weight=1)
            fi.grid_rowconfigure(1, weight=0)
            fi.grid_rowconfigure(2, weight=1)
            fi.grid_columnconfigure(0, weight=1)
            _spacer_top = tk.Frame(fi, height=1, bg=bg_color)
            _spacer_top.grid(row=0, column=0, sticky="nsew")
            _spacer_bot = tk.Frame(fi, height=1, bg=bg_color)
            _spacer_bot.grid(row=2, column=0, sticky="nsew")
            tb = ctk.CTkTextbox(
                fi,
                font=ctk.CTkFont(family="맑은 고딕", size=13),
                fg_color=bg_color,
                text_color=app.get_theme_color("text_main"),
                width=_cell_width(internal_idx) - 8,
                height=52,
                activate_scrollbars=False,
                wrap=tk.NONE,
                border_width=0,
            )
            tb.grid(row=1, column=0, sticky="nsew", padx=4, pady=2)
            tb.insert("1.0", text)
            # 수평 가운데 정렬: 법원/사건번호, 피고/사건명만. 비고는 좌측 정렬
            try:
                tbox = tb._textbox
                if internal_idx != 4:
                    tbox.tag_configure("center", justify=tk.CENTER)
                    tbox.tag_add("center", "1.0", tk.END)
                else:
                    tbox.tag_configure("left", justify="left")
                    tbox.tag_add("left", "1.0", tk.END)
            except Exception:
                pass
            tb.configure(state="disabled")
            components[f"label_info_{internal_idx}"] = tb
            
        # 3. 기일 (update_history.json 캐시에서 읽음)
        # 기일 정보가 없을 경우 '기일 미정'으로 표기. 드래그 선택 후 복사 가능.
        # 표기: 첫 줄에 '변론기일' 또는 '판결선고기일'(민트색), 그 다음 줄에 일시, 마지막에 디데이.
        f3 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(3),
            height=90,
            bd=0,
            highlightthickness=0,
        )
        f3.pack_propagate(False)
        f3.grid_propagate(False)
        f3.grid_rowconfigure(0, weight=1)
        f3.grid_rowconfigure(1, weight=0)
        f3.grid_rowconfigure(2, weight=1)
        f3.grid_columnconfigure(0, weight=1)
        _s3_top = tk.Frame(f3, height=1, bg=bg_color)
        _s3_top.grid(row=0, column=0, sticky="nsew")
        _s3_bot = tk.Frame(f3, height=1, bg=bg_color)
        _s3_bot.grid(row=2, column=0, sticky="nsew")
        frames_by_internal[3] = f3
        cn = case.get("사건번호", "")
        history = app.load_update_history()
        c_data = history.get(cn, {}) if isinstance(history.get(cn), dict) else {}
        hearing_info_raw = (c_data.get("hearing_info") or "").strip()
        hearing_text = hearing_info_raw or "기일 미정"
        # 디데이: 최근 업데이트 열과 동일 양식. "-" 또는 "D+숫자"(당일 D+0, 과거 D+n, 미래 D-n), 색상 0~2 success·3+ error
        days_until = app.get_days_until_hearing(hearing_info_raw) if hearing_info_raw else None
        if days_until is not None:
            if days_until > 0:
                d_day_str = f"D-{days_until}"
            elif days_until == 0:
                d_day_str = "D+0"
            else:
                d_day_str = f"D+{abs(days_until)}"
            # 색상: D+ (과거)는 초록색, D- (미래/오늘)는 빨간색
            if days_until < 0:
                d_day_fg = app.get_theme_color("success")
            else:
                d_day_fg = app.get_theme_color("error")
        else:
            d_day_str = "-"
            d_day_fg = app.get_theme_color("text_sub")
        # '변론기일' / '판결선고기일' 뒤로 줄바꿈하여 일시 표기. 일시는 연도 4자리로 표기.
        if hearing_text.startswith("변론기일 "):
            kind_line = "변론기일\n"
            rest_line = hearing_text[6:].strip()
        elif hearing_text.startswith("판결선고기일 "):
            kind_line = "판결선고기일\n"
            rest_line = hearing_text[8:].strip()
        else:
            kind_line = None
            rest_line = hearing_text
        # 로우 데이터 정제: 연도 해석은 D-day와 동일하게. 06/6→2026, 26→2026, 2025→2025. 표기는 2자리(YY).
        date_time_match = re.match(r"^(\d{1,4})\.(\d{1,2})\.(\d{1,2})\.?\s*(?:\((\d{1,2}:\d{2})\))?\s*$", rest_line.strip())
        if date_time_match:
            y_str, mm, dd, time_part = date_time_match.groups()
            y_int = int(y_str)
            if y_int >= 2000:
                full_year = y_int
            elif y_int >= 1900:
                full_year = y_int
            elif y_int < 10:
                full_year = 2020 + y_int
            elif y_int < 100:
                full_year = 2000 + y_int
            else:
                full_year = y_int
            display_yy = str(full_year)[-2:]
            rest_line = f"{display_yy}.{mm}.{dd}" + (f" ({time_part})" if time_part else "")
        ht = ctk.CTkTextbox(
            f3,
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            fg_color=bg_color,
            text_color=app.get_theme_color("text_main"),
            width=_cell_width(3) - 8,
            height=70,
            activate_scrollbars=False,
            wrap=tk.NONE,
            border_width=0,
        )
        ht.grid(row=1, column=0, sticky="nsew", padx=4, pady=2)
        mint_color = app.get_theme_color("hearing_mint")
        try:
            textbox = ht._textbox
            textbox.tag_configure("mint", foreground=mint_color)
            textbox.tag_configure("center", justify=tk.CENTER)
            dday_font = ctk.CTkFont(family="맑은 고딕", size=13, weight="bold")
            textbox.tag_configure("dday", foreground=d_day_fg, font=dday_font)
        except Exception:
            textbox = None
        if kind_line is not None:
            if textbox is not None:
                textbox.insert(tk.END, kind_line, "mint")
                textbox.insert(tk.END, rest_line)
                if d_day_str:
                    textbox.insert(tk.END, "\n" + d_day_str, "dday")
                textbox.tag_add("center", "1.0", tk.END)
            else:
                ht.insert("1.0", kind_line + rest_line + ("\n" + d_day_str if d_day_str else ""))
        else:
            if textbox is not None:
                textbox.insert(tk.END, rest_line)
                if d_day_str:
                    textbox.insert(tk.END, "\n" + d_day_str, "dday")
                textbox.tag_add("center", "1.0", tk.END)
            else:
                ht.insert("1.0", rest_line + ("\n" + d_day_str if d_day_str else ""))
        ht.configure(state="disabled")
        components["hearing_label"] = ht
            
        # 5. 캡차 이미지
        f5 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(5),
            height=90,
            bd=0,
            highlightthickness=0,
        )
        f5.pack_propagate(False)
        frames_by_internal[5] = f5
        il = tk.Label(
            f5,
            text="대기중",
            font=app.get_theme_color("font_small"),
            fg=app.get_theme_color("text_sub"),
            bg=app.get_theme_color("bg_primary"),
            relief=tk.FLAT,
        )
        il.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        components["image_label"] = il
        
        # 6. 캡차 입력
        f6 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(6),
            height=90,
            bd=0,
            highlightthickness=0,
        )
        f6.pack_propagate(False)
        frames_by_internal[6] = f6
        captcha_var = tk.StringVar()
        captcha_entry = ctk.CTkEntry(
            f6,
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
        
        # 7. 상태
        f7 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(7),
            height=90,
            bd=0,
            highlightthickness=0,
        )
        f7.pack_propagate(False)
        frames_by_internal[7] = f7
        if initial_status and isinstance(initial_status, dict):
            st = initial_status.get("status", "대기")
            em = initial_status.get("emoji", "⏸️")
            status_text = f"{em} {st}" if em else st
            status_fg = initial_status.get("color", app.get_theme_color("text_sub"))
        else:
            status_text, status_fg = "⏸️ 대기", app.get_theme_color("text_sub")
        sl = ctk.CTkLabel(
            f7,
            text=status_text,
            font=ctk.CTkFont(family="맑은 고딕", size=13),
            text_color=status_fg,
        )
        sl.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        components["status_label"] = sl
        
        # 8. 자동 조회
        f8 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(8),
            height=90,
            bd=0,
            highlightthickness=0,
        )
        f8.pack_propagate(False)
        frames_by_internal[8] = f8
        cn = case.get("사건번호", "")
        search_log = app.log_history_manager.load_search_log()
        if cn in search_log:
            record_text, record_fg = "자동 가능", app.get_theme_color("success")
        else:
            record_text, record_fg = "최초 조회 필요", app.get_theme_color("text_sub")
        rl = ctk.CTkLabel(
            f8,
            text=record_text,
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            text_color=record_fg,
        )
        rl.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        components["record_label"] = rl
        
        # 9. 최근 업데이트 (수직 가운데 정렬: grid + 스페이서)
        f9 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(9),
            height=90,
            bd=0,
            highlightthickness=0,
        )
        f9.pack_propagate(False)
        f9.grid_propagate(False)
        f9.grid_rowconfigure(0, weight=1)
        f9.grid_rowconfigure(1, weight=0)
        f9.grid_rowconfigure(2, weight=1)
        f9.grid_columnconfigure(0, weight=1)
        _s9_top = tk.Frame(f9, height=1, bg=bg_color)
        _s9_top.grid(row=0, column=0, sticky="nsew")
        _s9_bot = tk.Frame(f9, height=1, bg=bg_color)
        _s9_bot.grid(row=2, column=0, sticky="nsew")
        frames_by_internal[9] = f9
        u_container = tk.Frame(f9, bg=bg_color)
        u_container.grid(row=1, column=0, sticky="nsew", padx=4, pady=2)
        history = app.load_update_history()
        c_data = history.get(cn, {})
        last_update_raw = c_data.get("last_update", "-")
        # 'YY.MM.DD.' + 줄바꿈 + 'HH:MM:SS' 형식으로 정제
        last_date_display = "-"
        if last_update_raw and last_update_raw != "-":
            try:
                # 저장된 형식: YYYY-MM-DD HH:MM:SS
                dt = datetime.strptime(last_update_raw, "%Y-%m-%d %H:%M:%S")
                last_date_display = dt.strftime("%y.%m.%d.\n%H:%M:%S")
            except:
                last_date_display = last_update_raw
        
        days_since = app.get_days_since_update(case)
        date_label = ctk.CTkLabel(
            u_container,
            text=last_date_display,
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            text_color=app.get_theme_color("text_sub"),
        )
        date_label.pack(anchor=tk.CENTER)
        is_auto = c_data.get("is_auto", False)
        d_suffix = " (자동 조회)" if is_auto else ""
        # 최근 업데이트: D+ (0 이상)는 초록색, 기록 없으면(-) 회색
        d_text = "-" if days_since < 0 else f"D+{days_since}{d_suffix}"
        d_fg = (
            app.get_theme_color("text_sub")
            if days_since < 0
            else app.get_theme_color("success")
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
        
        # 10. 시트 버튼
        f10 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(10),
            height=90,
            bd=0,
            highlightthickness=0,
        )
        f10.pack_propagate(False)
        frames_by_internal[10] = f10
        ctk.CTkButton(
            f10,
            text="📝",
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
