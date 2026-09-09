# -*- coding: utf-8 -*-
"""
사건 목록 한 행(CaseRow)
========================
행 생성 + 배경색 재귀 적용.

주니어 참고:
- 표시용 글자는 CTkTextbox 대신 tk.Text 를 씁니다 (스크롤 가볍게).
- 버튼·캡차 입력(CTkEntry)은 그대로 둡니다.
- 상태 색(처리중 노랑 등)은 apply_row_background 로 칸까지 채웁니다.
"""
import re
from datetime import datetime
import tkinter as tk
import customtkinter as ctk
import config
from config import COL_NAMES
from gui.utils.bind_utils import bind_entry_return


def _list_font_size():
    """설정(CASE_LIST_FONT_SIZE) 기준 pt. 기본 9."""
    try:
        return max(8, min(16, int(getattr(config, "CASE_LIST_FONT_SIZE", 9) or 9)))
    except (TypeError, ValueError):
        return 9


# 완료 계열 상태 글씨색 (행 연두 배경과 구분)
STATUS_COMPLETE_FG = "#3498DB"
# accent 버튼(보기/시트) 글씨 — 파란 배경과 대비
BUTTON_TEXT_FG = "#FFFFFF"


def _is_complete_status(status):
    """완료·입력완료·기간조회 완료 등 성공 계열 상태인지."""
    if not status:
        return False
    return (
        status.startswith("완료")
        or status.startswith("기간조회 완료")
        or status.startswith("재수집 완료")
        or status.startswith("중복 정리 완료")
        or status.startswith("입력완료")
        or status.startswith("대조")
    )


def apply_row_background(root, color, text_color=None, skip_buttons=True):
    """
    행 루트부터 자손까지 배경색을 채웁니다.

    - tk 위젯: bg
    - CTk 위젯: fg_color (버튼은 파란 accent 유지 → 건너뜀)
    - 밝은 상태색(처리중/완료/실패)이면 글자는 검은색으로 (가독성)
    - text_color 를 넘기면 Label/Text 기본 글자색을 그걸로 맞춤
    - CTkButton 은 자식 재귀를 하지 않고 text_color 를 흰색으로 고정
    """
    if root is None or color is None:
        return
    try:
        if not root.winfo_exists():
            return
    except tk.TclError:
        return

    # 밝은 행 배경 → 기본 글자 검정 (테마 흰색이 안 보이게)
    _LIGHT_BGS = {
        "#FFF3CD",  # 처리중
        "#D4EDDA",  # 완료
        "#F8D7DA",  # 실패
        "#B3D9FF",  # 검색 하이라이트
    }
    if text_color is None and isinstance(color, str) and color.upper() in {
        c.upper() for c in _LIGHT_BGS
    }:
        text_color = "#000000"

    # 시트/보기 버튼: 배경은 유지, 글씨만 흰색. 자식 재귀 금지(내부 라벨이 검게 됨)
    if skip_buttons and isinstance(root, ctk.CTkButton):
        try:
            root.configure(text_color=BUTTON_TEXT_FG)
        except (tk.TclError, AttributeError, ValueError):
            pass
        return

    if isinstance(root, ctk.CTkCheckBox):
        try:
            root.configure(bg_color=color)
        except (tk.TclError, AttributeError, ValueError):
            pass
    elif isinstance(root, ctk.CTkEntry):
        # 입력창 배경은 행색에 맞추되, 글자는 검정(밝은 행) 또는 기본
        try:
            cfg = {"fg_color": color}
            if text_color is not None:
                cfg["text_color"] = text_color
            root.configure(**cfg)
        except (tk.TclError, AttributeError, ValueError):
            try:
                root.configure(fg_color=color)
            except Exception:
                pass
    elif isinstance(root, (ctk.CTkFrame, ctk.CTkLabel, ctk.CTkTextbox)):
        try:
            root.configure(fg_color=color)
        except (tk.TclError, AttributeError, ValueError):
            pass
    elif isinstance(root, tk.Text):
        try:
            root.configure(bg=color)
            if text_color is not None:
                root.configure(fg=text_color)
        except (tk.TclError, AttributeError):
            pass
    elif isinstance(root, tk.Label):
        try:
            cfg = {"bg": color}
            # 상태 라벨은 완료 파란 글씨를 유지 (검정 강제 덮어쓰기 금지)
            is_status = getattr(root, "_case_ing_status_label", False)
            if text_color is not None and not is_status:
                cfg["fg"] = text_color
            root.configure(**cfg)
        except (tk.TclError, AttributeError):
            pass
    else:
        # tk.Frame / Canvas 등
        try:
            root.configure(bg=color)
        except (tk.TclError, AttributeError):
            try:
                root.config(bg=color)
            except Exception:
                pass

    try:
        children = root.winfo_children()
    except tk.TclError:
        return
    for child in children:
        apply_row_background(
            child, color, text_color=text_color, skip_buttons=skip_buttons
        )


def _status_bg_from_text(status):
    """상태 문자열 → 행 배경색 (ui_queue_manager 와 동일 규칙)."""
    if not status:
        return None
    if status.startswith("처리중"):
        return "#FFF3CD"
    if _is_complete_status(status):
        return "#D4EDDA"
    if status.startswith("실패") or status.startswith("오류"):
        return "#F8D7DA"
    return None


def _make_plain_text(parent, bg_color, text_color, width, height, font_size=None, wrap=True):
    """가벼운 표시용 tk.Text (복사·태그 가능). 글씨체=맑은 고딕."""
    if font_size is None:
        font_size = _list_font_size()
    t = tk.Text(
        parent,
        font=("맑은 고딕", font_size),
        bg=bg_color,
        fg=text_color,
        width=1,
        height=1,
        bd=0,
        highlightthickness=0,
        relief=tk.FLAT,
        # 한글 긴 사건명은 공백이 없어 CHAR 줄바꿈이 잘림을 막습니다
        wrap=tk.CHAR if wrap else tk.NONE,
        cursor="arrow",
        selectbackground="#5DADE2",
        selectforeground="#FFFFFF",
        insertwidth=0,
    )
    t.configure(width=max(8, width // 8), height=max(2, height // 16))
    return t


class CaseRow:
    """
    단일 사건 행(Row) 생성을 전담하는 클래스.
    CaseListPanel의 create_case_row 메서드에서 분리됨.
    """

    @staticmethod
    def create(app, parent, case, index, total_width, initial_status=None):
        """
        단일 사건 행 위젯을 생성하고 반환합니다.

        Returns
        -------
        tuple
            (row_container, components, cell_frames)
        """
        bg_color = (
            app.get_theme_color("row_odd")
            if index % 2 == 0
            else app.get_theme_color("row_even")
        )
        text_main = app.get_theme_color("text_main")
        text_sub = app.get_theme_color("text_sub")
        fs = _list_font_size()

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
            width=24,
            command=lambda idx=index: app.on_checkbox_change(idx),
        ).place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        components["checkbox_var"] = var

        # 1,2,4. 법원/사건번호, 피고/사건명, 비고 — tk.Text
        info_indices = [1, 2, 4]
        court_and_num = "\n".join(
            filter(
                None,
                [
                    str(case.get("법원", "") or "").strip(),
                    str(case.get("사건번호", "") or "").strip(),
                ],
            )
        ) or " "
        defendant_and_name = "\n".join(
            filter(
                None,
                [
                    str(case.get("피고", "") or "").strip(),
                    str(case.get("사건명", "") or "").strip(),
                ],
            )
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
            frames_by_internal[internal_idx] = fi
            cw = _cell_width(internal_idx) - 8
            # 피고 칸은 아래 「보기」 버튼 자리 확보 → 텍스트를 약간 위, 버튼은 아래
            text_h = 40 if internal_idx == 2 else 48
            tb = _make_plain_text(fi, bg_color, text_main, cw, text_h, font_size=fs)
            # relwidth=1 로 칸이 넓어지면 Text 도 같이 넓어짐 (고정 width 금지)
            tb.place(
                relx=0.5,
                rely=0.42 if internal_idx == 2 else 0.5,
                anchor=tk.CENTER,
                relwidth=1.0,
                width=-8,
                height=text_h,
            )
            tb.insert("1.0", text)
            if internal_idx != 4:
                tb.tag_configure("center", justify=tk.CENTER)
                tb.tag_add("center", "1.0", tk.END)
            else:
                tb.tag_configure("left", justify="left")
                tb.tag_add("left", "1.0", tk.END)
            tb.configure(state=tk.DISABLED)
            components[f"label_info_{internal_idx}"] = tb

            if internal_idx == 2:
                from gui.utils.glyphs import sanitize as _sanitize_glyph

                mag_text = _sanitize_glyph("🔍") or "보기"
                if not mag_text.strip():
                    mag_text = "보기"
                ctk.CTkButton(
                    fi,
                    text=mag_text,
                    font=ctk.CTkFont(family="맑은 고딕", size=max(9, fs)),
                    fg_color=app.get_theme_color("accent"),
                    hover_color=app.get_theme_color("accent"),
                    text_color=BUTTON_TEXT_FG,
                    width=40,
                    height=20,
                    cursor="hand2",
                    command=lambda idx=index: app._open_general_info(idx),
                ).place(relx=0.5, rely=0.82, anchor=tk.CENTER)

        # 3. 기일
        f3 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(3),
            height=90,
            bd=0,
            highlightthickness=0,
        )
        f3.pack_propagate(False)
        frames_by_internal[3] = f3
        cn = case.get("사건번호", "")
        history = app.load_update_history()
        c_data = history.get(cn, {}) if isinstance(history.get(cn), dict) else {}
        hearing_info_raw = (c_data.get("hearing_info") or "").strip()
        hearing_text = hearing_info_raw or "기일 미정"
        days_until = (
            app.get_days_until_hearing(hearing_info_raw) if hearing_info_raw else None
        )
        if days_until is not None:
            if days_until > 0:
                d_day_str = f"D-{days_until}"
            elif days_until == 0:
                d_day_str = "D+0"
            else:
                d_day_str = f"D+{abs(days_until)}"
            if days_until < 0:
                d_day_fg = app.get_theme_color("success")
            else:
                d_day_fg = app.get_theme_color("error")
        else:
            d_day_str = "-"
            d_day_fg = text_sub

        if hearing_text.startswith("변론기일"):
            kind_line = "변론기일\n"
            rest_line = hearing_text[len("변론기일") :].strip()
        elif hearing_text.startswith("감정기일"):
            kind_line = "감정기일\n"
            rest_line = hearing_text[len("감정기일") :].strip()
        elif hearing_text.startswith("판결선고기일"):
            kind_line = "판결선고기일\n"
            rest_line = hearing_text[len("판결선고기일") :].strip()
        else:
            kind_line = None
            rest_line = hearing_text

        date_time_match = re.match(
            r"^(\d{1,4})\.(\d{1,2})\.(\d{1,2})\.?\s*(?:\((\d{1,2}:\d{2})\))?\s*$",
            rest_line.strip(),
        )
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
            rest_line = f"{display_yy}.{mm}.{dd}" + (
                f" ({time_part})" if time_part else ""
            )

        cw3 = _cell_width(3) - 8
        ht = _make_plain_text(f3, bg_color, text_main, cw3, 64, font_size=fs)
        ht.place(
            relx=0.5,
            rely=0.5,
            anchor=tk.CENTER,
            relwidth=1.0,
            width=-8,
            height=64,
        )
        mint_color = app.get_theme_color("hearing_mint")
        ht.tag_configure("mint", foreground=mint_color)
        ht.tag_configure("center", justify=tk.CENTER)
        ht.tag_configure(
            "dday",
            foreground=d_day_fg,
            font=("맑은 고딕", fs, "bold"),
        )
        ht.configure(state=tk.NORMAL)
        if kind_line is not None:
            ht.insert(tk.END, kind_line, "mint")
            ht.insert(tk.END, rest_line)
            if d_day_str:
                ht.insert(tk.END, "\n" + d_day_str, "dday")
        else:
            ht.insert(tk.END, rest_line)
            if d_day_str:
                ht.insert(tk.END, "\n" + d_day_str, "dday")
        ht.tag_add("center", "1.0", tk.END)
        ht.configure(state=tk.DISABLED)
        components["hearing_label"] = ht

        # 5. 캡차 이미지 — 대기중은 행색과 동일
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
            font=("맑은 고딕", fs),
            fg=text_sub,
            bg=bg_color,
            relief=tk.FLAT,
        )
        il.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        components["image_label"] = il

        # 6. 캡차 입력 (기능 유지: CTkEntry)
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
            font=ctk.CTkFont(family="맑은 고딕", size=max(10, fs + 1), weight="bold"),
            justify=tk.CENTER,
            width=70,
            height=26,
        )
        captcha_entry.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        captcha_entry.bind(
            "<KeyRelease>", lambda e, idx=index: app._validate_captcha_entry(idx)
        )
        bind_entry_return(
            captcha_entry, lambda e, idx=index: app.on_captcha_enter(idx)
        )
        components["captcha_var"] = captcha_var
        components["captcha_entry"] = captcha_entry

        # 7. 상태 — tk.Label (배경 따라감)
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
            # 완료 계열은 history 색(green/회색) 무시 → 파란색
            if _is_complete_status(st):
                status_fg = STATUS_COMPLETE_FG
            else:
                status_fg = initial_status.get("color", text_sub)
        else:
            status_text, status_fg = "⏸️ 대기", text_sub
        sl = tk.Label(
            f7,
            text=status_text,
            font=("맑은 고딕", fs),
            fg=status_fg,
            bg=bg_color,
            justify=tk.CENTER,
        )
        # apply_row_background 가 검정으로 덮지 않도록 표시
        sl._case_ing_status_label = True
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
        search_log = app.log_history_manager.load_search_log()
        if cn in search_log:
            record_text, record_fg = "자동 가능", app.get_theme_color("success")
        else:
            record_text, record_fg = "최초 조회 필요", text_sub
        rl = tk.Label(
            f8,
            text=record_text,
            font=("맑은 고딕", fs),
            fg=record_fg,
            bg=bg_color,
            justify=tk.CENTER,
        )
        rl.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        components["record_label"] = rl

        # 9. 최근 업데이트
        f9 = tk.Frame(
            case_frame,
            bg=bg_color,
            width=_cell_width(9),
            height=90,
            bd=0,
            highlightthickness=0,
        )
        f9.pack_propagate(False)
        frames_by_internal[9] = f9
        u_container = tk.Frame(f9, bg=bg_color)
        u_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        history = app.load_update_history()
        c_data = history.get(cn, {}) if isinstance(history.get(cn), dict) else {}
        last_update_raw = c_data.get("last_update", "-")
        last_date_display = "-"
        if last_update_raw and last_update_raw != "-":
            try:
                dt = datetime.strptime(last_update_raw, "%Y-%m-%d %H:%M:%S")
                last_date_display = dt.strftime("%y.%m.%d.\n%H:%M:%S")
            except Exception:
                last_date_display = last_update_raw

        days_since = app.get_days_since_update(case)
        date_label = tk.Label(
            u_container,
            text=last_date_display,
            font=("맑은 고딕", fs),
            fg=text_sub,
            bg=bg_color,
            justify=tk.CENTER,
        )
        date_label.pack(anchor=tk.CENTER)
        is_auto = c_data.get("is_auto", False)
        d_suffix = " (자동 조회)" if is_auto else ""
        d_text = "-" if days_since < 0 else f"D+{days_since}{d_suffix}"
        d_fg = text_sub if days_since < 0 else app.get_theme_color("success")
        d_label = tk.Label(
            u_container,
            text=d_text,
            font=("맑은 고딕", fs, "bold"),
            fg=d_fg,
            bg=bg_color,
            justify=tk.CENTER,
        )
        d_label.pack(anchor=tk.CENTER)
        components["update_date_label"] = date_label
        components["update_d_label"] = d_label

        # 10. 시트 버튼 (기능 유지)
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
            text_color=BUTTON_TEXT_FG,
            width=50,
            height=28,
            cursor="hand2",
            command=lambda idx=index: app._open_sheet_viewer(idx),
        ).place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        cell_frames = []
        for _disp_idx, internal_idx in enumerate(app.col_order):
            frame = frames_by_internal[internal_idx]
            frame.pack(side=tk.LEFT)
            frame.pack_propagate(False)
            cell_frames.append(frame)

        app.case_frames[index] = case_frame

        # 목록 재구성(시작·F5) 시에는 테마 줄무늬만 사용.
        # 완료 연두(#D4EDDA) 등 상태 행색은 조회 중 실시간 갱신에서만 칠함.
        apply_row_background(case_frame, bg_color)
        # 상태 라벨 글씨색 복원 (줄무늬 칠한 뒤에도 완료=파란 유지)
        try:
            if sl.winfo_exists():
                sl.configure(fg=status_fg, bg=bg_color)
        except tk.TclError:
            pass

        return row_container, components, cell_frames
