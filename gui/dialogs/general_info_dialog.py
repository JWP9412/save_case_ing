# -*- coding: utf-8 -*-
"""
일반내용 뷰어 다이얼로그
========================

역할: 대법원 '일반내용' 화면(기본내용·최근기일·최근제출서류·당사자·대리인)을
      CaseIng 안에서 스크롤 가능한 창으로 보여줍니다.
호출: 사건 목록 '피고/사건명' 칸의 돋보기 버튼 → app._open_general_info(idx)

주니어 개발자 참고:
- 데이터는 구글시트가 아니라 data/general_info.json (로컬 캐시)에서 읽습니다.
- 조회한 적 없는 사건이면 안내 문구만 보여줍니다.
- "당사자·대리인 내용 변경시 클릭" 버튼은 해당 사건만 선택해 기존 조회 파이프라인을
  다시 태웁니다. 캡차는 메인 화면 행에서 평소처럼 입력합니다.
"""
import tkinter as tk
from tkinter import messagebox
import threading
import customtkinter as ctk

from gui.utils.glyphs import sanitize
from services.general_info_store import get_case_general_info


class GeneralInfoDialog(tk.Toplevel):
    def __init__(self, parent, case_data, theme_color_getter, app=None):
        """
        parent: 메인 창
        case_data: {"법원","사건번호","피고","사건명",...}
        theme_color_getter: app.get_theme_color
        app: AppController (당사자 새로고침 시 조회 파이프라인 호출용, 선택)
        """
        super().__init__(parent)
        self.case_data = case_data or {}
        self.theme_color_getter = theme_color_getter
        self.app = app

        case_number = self.case_data.get("사건번호", "")
        self.case_number = str(case_number).strip()
        self.title(f"일반내용: {self.case_number}")
        # 2열 기본내용(긴 라벨 포함)이 잘리지 않도록 최소 폭을 넉넉히 잡습니다.
        self.geometry("820x640")
        self.minsize(720, 500)

        bg = self._c("bg_primary")
        try:
            self.configure(bg=bg)
        except Exception:
            pass

        self._status_var = tk.StringVar(value="불러오는 중...")
        self._create_widgets()
        self.reload_from_store()

    def _c(self, key, fallback="#333333"):
        try:
            return self.theme_color_getter(key)
        except Exception:
            return fallback

    def _create_widgets(self):
        bg = self._c("bg_primary")
        text_main = self._c("text_main", "#FFFFFF")
        accent = self._c("accent", "#3498DB")

        # 상단: 제목 + 새로고침 버튼
        top = tk.Frame(self, bg=bg)
        top.pack(fill=tk.X, padx=10, pady=(10, 4))

        title_lbl = tk.Label(
            top,
            text=f"기본내용 ({self.case_data.get('법원', '')})",
            font=("맑은 고딕", 13, "bold"),
            fg=text_main,
            bg=bg,
            anchor="w",
        )
        title_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        refresh_text = sanitize("당사자·대리인 내용 변경시 클릭")
        self.refresh_btn = ctk.CTkButton(
            top,
            text=refresh_text or "당사자·대리인 새로고침",
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            fg_color=accent,
            hover_color=accent,
            width=220,
            height=28,
            cursor="hand2",
            command=self._on_refresh_parties,
        )
        self.refresh_btn.pack(side=tk.RIGHT, padx=(8, 0))

        # 상태 줄
        status = tk.Label(
            self,
            textvariable=self._status_var,
            font=("맑은 고딕", 10),
            fg=self._c("text_sub", "#AAAAAA"),
            bg=bg,
            anchor="w",
        )
        status.pack(fill=tk.X, padx=10, pady=(0, 4))

        # 스크롤 영역
        outer = tk.Frame(self, bg=bg)
        outer.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        self.canvas = tk.Canvas(outer, bg=bg, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.content = tk.Frame(self.canvas, bg=bg)
        self._content_win = self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.content.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        # 마우스 휠: add="+" 로 다른 창 바인딩을 지우지 않음
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        self.canvas.bind("<MouseWheel>", self._on_mousewheel, add="+")
        self.content.bind("<MouseWheel>", self._on_mousewheel, add="+")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_content_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self._content_win, width=event.width)

    def _on_mousewheel(self, event):
        try:
            if not self.winfo_exists():
                return
            # 이 창 위에 있을 때만 스크롤 (전역 바인딩이어도 다른 창 방해 안 함)
            w = event.widget
            under = False
            while w is not None:
                if w is self or w is self.canvas or w is self.content:
                    under = True
                    break
                try:
                    w = w.master
                except Exception:
                    break
            if not under:
                return
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def _on_close(self):
        # unbind_all 금지: 다른 창(수동 캡차 등) 휠까지 사라짐
        # 새로고침 대기 등록 해제
        if self.app is not None:
            refresh = getattr(self.app, "_general_info_dialog_refresh", None)
            if refresh and refresh.get("dialog") is self:
                self.app._general_info_dialog_refresh = None
        self.destroy()

    def reload_from_store(self):
        """로컬 JSON에서 다시 읽어 화면을 다시 그립니다 (스레드 안전)."""
        self._status_var.set("불러오는 중...")

        def fetch():
            try:
                data = get_case_general_info(self.case_number)
                err = None
            except Exception as e:
                data = None
                err = str(e)
            try:
                self.after(0, lambda: self._apply_data(data, err))
            except Exception:
                pass

        threading.Thread(target=fetch, daemon=True).start()

    def _clear_content(self):
        for child in self.content.winfo_children():
            child.destroy()

    def _apply_data(self, data, err):
        if not self.winfo_exists():
            return
        self._clear_content()
        # 재조회 후 버튼 다시 활성화
        try:
            self.refresh_btn.configure(state="normal")
        except Exception:
            pass
        bg = self._c("bg_primary")
        text_main = self._c("text_main", "#FFFFFF")

        if err:
            self._status_var.set(f"오류: {err}")
            tk.Label(
                self.content,
                text=f"불러오기 실패\n{err}",
                font=("맑은 고딕", 11),
                fg=self._c("error", "#E74C3C"),
                bg=bg,
                justify="left",
            ).pack(anchor="w", padx=8, pady=20)
            return

        if not data:
            self._status_var.set("저장된 일반내용 없음")
            tk.Label(
                self.content,
                text=(
                    "아직 조회한 적이 없습니다.\n"
                    "사건을 조회하면 일반내용이 자동으로 저장됩니다."
                ),
                font=("맑은 고딕", 12),
                fg=text_main,
                bg=bg,
                justify="left",
            ).pack(anchor="w", padx=12, pady=24)
            return

        updated = data.get("updated_at") or "-"
        parties_updated = data.get("parties_updated_at") or "-"
        self._status_var.set(
            f"저장 시각: {updated}  |  당사자·대리인: {parties_updated}"
        )

        # 1) 기본내용
        self._section_title("ㅇ 기본내용")
        self._render_basic(data.get("basic") or {})

        # 2) 최근기일내용
        self._section_title("ㅇ 최근기일내용")
        self._render_table(
            ["일자", "시각", "기일구분", "기일장소", "결과"],
            data.get("recent_hearings") or [],
            empty_msg="지정된 기일내용이 없습니다.",
        )

        # 3) 최근 제출서류 접수내용
        self._section_title("ㅇ 최근 제출서류 접수내용")
        self._render_table(
            ["일자", "내용"],
            data.get("recent_documents") or [],
            empty_msg="제출서류 접수내용이 없습니다.",
        )

        # 4) 당사자내용
        # 이름 열은 넓게 표시함. 예전 조회에서 이름이 잘렸다면
        # 「당사자·대리인 내용 변경시 클릭」으로 재조회해 캐시를 갱신하세요.
        self._section_title("ㅇ 당사자내용")
        self._render_table(
            ["구분", "이름", "종국결과", "판결도달일", "확정일"],
            data.get("parties") or [],
            empty_msg="당사자내용이 없습니다.",
        )

        # 5) 대리인내용
        self._section_title("ㅇ 대리인내용")
        self._render_table(
            ["구분", "이름"],
            data.get("attorneys") or [],
            empty_msg="대리인내용이 없습니다.",
        )

        self._on_content_configure()

    def _section_title(self, text):
        bg = self._c("bg_primary")
        tk.Label(
            self.content,
            text=text,
            font=("맑은 고딕", 12, "bold"),
            fg=self._c("text_main", "#FFFFFF"),
            bg=bg,
            anchor="w",
        ).pack(fill=tk.X, padx=8, pady=(14, 4))

    def _render_basic(self, basic):
        """기본내용: 라벨-값 2열 표 형태로 표시 (드래그 복사 가능)."""
        bg = self._c("bg_primary")
        row_bg = self._c("bg_white", "#1E1E1E")
        text_main = self._c("text_main", "#FFFFFF")
        text_sub = self._c("text_sub", "#AAAAAA")
        border = self._c("border", "#444444")

        if not basic:
            tk.Label(
                self.content,
                text="기본내용이 없습니다.",
                font=("맑은 고딕", 10),
                fg=text_sub,
                bg=bg,
            ).pack(anchor="w", padx=12, pady=4)
            return

        # 표시 순서 힌트 (없으면 나머지 키를 뒤에 붙임)
        preferred = [
            "사건번호", "사건명", "원고", "피고", "재판부",
            "접수일", "종국결과", "원고소가", "피고소가",
            "수리구분", "병합구분", "상소인", "상소일", "상소각하일",
            "인지액", "판결도달일", "확정일",
        ]
        keys = [k for k in preferred if k in basic]
        for k in basic.keys():
            if k not in keys:
                keys.append(k)

        frame = tk.Frame(self.content, bg=border, bd=0)
        frame.pack(fill=tk.X, padx=8, pady=2)

        # 2개씩 짝지어 한 줄에 배치
        pairs = []
        i = 0
        while i < len(keys):
            pairs.append((keys[i], keys[i + 1] if i + 1 < len(keys) else None))
            i += 2

        for r, (k1, k2) in enumerate(pairs):
            row = tk.Frame(frame, bg=row_bg)
            row.pack(fill=tk.X, padx=1, pady=1)
            # 주니어: pack(expand)는 글자 길이에 따라 좌·우 열 폭이 달라짐.
            # grid + uniform 으로 좌·우를 항상 50:50 맞춥니다.
            row.grid_columnconfigure(0, weight=1, uniform="basic_cols")
            row.grid_columnconfigure(1, weight=1, uniform="basic_cols")
            self._basic_cell(
                row, k1, basic.get(k1, ""), text_sub, text_main, row_bg, col=0
            )
            if k2:
                self._basic_cell(
                    row, k2, basic.get(k2, ""), text_sub, text_main, row_bg, col=1
                )
            else:
                tk.Frame(row, bg=row_bg).grid(row=0, column=1, sticky="nsew")

    def _basic_cell(self, parent, label, value, label_fg, value_fg, bg, col=0):
        """
        기본내용 한 칸(라벨+값).

        주니어: 창을 줄여도 글이 잘리지 않게
        - 라벨은 wraplength로 여러 줄
        - 값은 Text height를 글자 수에 맞게 늘림
        - col: 부모 row 그리드에서 왼쪽(0)/오른쪽(1)
        """
        cell = tk.Frame(parent, bg=bg)
        cell.grid(row=0, column=col, sticky="nsew", padx=4, pady=3)
        lbl = tk.Label(
            cell,
            text=str(label),
            font=("맑은 고딕", 9),
            fg=label_fg,
            bg=bg,
            anchor="w",
            justify="left",
            wraplength=300,
        )
        lbl.pack(fill=tk.X)

        val = str(value) if value is not None else ""
        # 대략 28자당 1줄, 최대 8줄 (원고·피고 마스킹 긴 이름 대비)
        lines = max(1, min(8, (len(val) // 28) + 1)) if val else 1
        tb = tk.Text(
            cell,
            height=lines,
            wrap="word",
            font=("맑은 고딕", 10),
            fg=value_fg,
            bg=bg,
            bd=0,
            highlightthickness=0,
            relief="flat",
        )
        tb.insert("1.0", val)
        tb.configure(state="disabled")
        tb.pack(fill=tk.X)

        # 칸 폭이 바뀌면 라벨 줄바꿈 폭도 맞춤
        def _on_cell_cfg(event, label_w=lbl):
            w = max(60, int(event.width) - 8)
            try:
                label_w.configure(wraplength=w)
            except Exception:
                pass

        cell.bind("<Configure>", _on_cell_cfg)

    def _cell_value_for_header(self, row, header, col_index):
        """
        행 dict에서 헤더에 맞는 값을 찾습니다.

        주니어 참고:
        1) 키 정확 일치
        2) 공백 제거한 키 / 부분 일치
        3) 그래도 없으면 행 값을 열 인덱스 순으로 사용 (스크래핑 키가 깨진 경우)
        """
        if not isinstance(row, dict):
            return ""
        if header in row:
            return str(row.get(header) or "")
        norm_h = "".join(str(header).split())
        for k, v in row.items():
            nk = "".join(str(k).split())
            if nk == norm_h or (norm_h and (norm_h in nk or nk in norm_h)):
                return str(v or "")
        values = list(row.values())
        if 0 <= col_index < len(values):
            return str(values[col_index] or "")
        return ""

    def _render_table(self, preferred_headers, rows, empty_msg="내용이 없습니다."):
        """
        표 렌더: pack이 아니라 grid로 열을 고정합니다.

        주니어 참고:
        pack(expand=True)는 글자 길이에 따라 칸 시작 폭이 달라져
        헤더 행과 데이터 행의 열 경계가 어긋납니다.
        grid + uniform 을 쓰면 같은 표 안에서는 열이 항상 맞습니다.
        """
        bg = self._c("bg_primary")
        row_bg = self._c("bg_white", "#1E1E1E")
        header_bg = self._c("bg_header", "#2C3E50")
        text_main = self._c("text_main", "#FFFFFF")
        text_sub = self._c("text_sub", "#AAAAAA")
        border = self._c("border", "#444444")

        if not rows:
            tk.Label(
                self.content,
                text=empty_msg,
                font=("맑은 고딕", 10),
                fg=text_sub,
                bg=bg,
            ).pack(anchor="w", padx=12, pady=4)
            return

        # 열 순서는 preferred_headers로 고정 (키 불일치여도 빈 칸으로 유지)
        headers = list(preferred_headers) if preferred_headers else []
        if not headers and rows:
            headers = list(rows[0].keys())

        n = max(len(headers), 1)
        # 열 비중: 표 종류마다 다르게 (5열 공통 [1,5,...] 쓰면 기일표 '시각'이 비대해짐)
        header_set = {str(h).strip() for h in headers}
        if n == 2:
            # 서류·대리인: 앞 좁게, 내용/이름 넓게
            weights = [1, 4]
        elif n == 5 and "이름" in header_set:
            # 당사자: 구분 | 이름 | 종국결과 | 판결도달일 | 확정일
            weights = [1, 5, 1, 1, 1]
        elif n == 5 and "시각" in header_set:
            # 최근기일: 일자 | 시각(짧음) | 기일구분 | 기일장소 | 결과
            weights = [2, 1, 2, 2, 2]
        elif n == 5:
            weights = [1, 1, 1, 1, 1]
        else:
            weights = [1] * n

        wrap = tk.Frame(self.content, bg=border)
        wrap.pack(fill=tk.X, padx=8, pady=2)

        # 헤더 행
        hrow = tk.Frame(wrap, bg=header_bg)
        hrow.pack(fill=tk.X, padx=1, pady=1)
        for i, h in enumerate(headers):
            hrow.grid_columnconfigure(i, weight=weights[i], uniform="gi_cols")
            tk.Label(
                hrow,
                text=h,
                font=("맑은 고딕", 9, "bold"),
                fg="#FFFFFF",
                bg=header_bg,
                anchor="center",
            ).grid(row=0, column=i, sticky="nsew", padx=2, pady=3)

        for row in rows:
            rframe = tk.Frame(wrap, bg=row_bg)
            rframe.pack(fill=tk.X, padx=1, pady=1)
            for i, h in enumerate(headers):
                rframe.grid_columnconfigure(i, weight=weights[i], uniform="gi_cols")
                val = self._cell_value_for_header(row, h, i)
                # 이름 열은 마스킹·여러 줄이 길어 줄 수를 더 넉넉히 (12자당 1줄, 최대 6)
                # 그 외 열은 대략 22자당 1줄, 최대 4
                if val:
                    if str(h).strip() == "이름":
                        lines = max(1, min(6, (len(val) // 12) + 1))
                    else:
                        lines = max(1, min(4, (len(val) // 22) + 1))
                else:
                    lines = 1
                tb = tk.Text(
                    rframe,
                    height=lines,
                    wrap="word",
                    font=("맑은 고딕", 9),
                    fg=text_main,
                    bg=row_bg,
                    bd=0,
                    highlightthickness=0,
                    relief="flat",
                )
                tb.insert("1.0", val)
                tb.configure(state="disabled")
                tb.grid(row=0, column=i, sticky="nsew", padx=2, pady=2)

    def _on_refresh_parties(self):
        """
        당사자·대리인만 최신화가 필요할 때:
        해당 사건만 선택하고 기존 조회 파이프라인을 시작합니다.
        캡차는 메인 화면 행에서 평소처럼 입력합니다.
        """
        if self.app is None:
            messagebox.showinfo(
                "안내",
                "앱 연결이 없어 재조회를 시작할 수 없습니다.\n"
                "메인 화면에서 해당 사건을 조회해 주세요.",
                parent=self,
            )
            return

        if getattr(self.app, "processing", False):
            messagebox.showwarning(
                "처리 중",
                "이미 사건 조회가 진행 중입니다.\n끝난 뒤 다시 시도해 주세요.",
                parent=self,
            )
            return

        # case_list에서 인덱스 찾기
        case_index = None
        for i, c in enumerate(getattr(self.app, "case_list", []) or []):
            if str(c.get("사건번호", "")).strip() == self.case_number:
                case_index = i
                break

        if case_index is None:
            messagebox.showwarning(
                "사건 없음",
                f"목록에서 사건 {self.case_number} 을(를) 찾지 못했습니다.",
                parent=self,
            )
            return

        # 해당 사건만 체크
        try:
            from gui.utils import selection_manager as selection_manager_module

            selection_manager_module.deselect_all_cases(self.app)
            if case_index in self.app.case_checkboxes:
                self.app.case_checkboxes[case_index].set(True)
                selection_manager_module.on_checkbox_change(self.app, case_index)
        except Exception:
            # 체크박스 직접 설정 폴백
            try:
                if case_index in self.app.case_checkboxes:
                    self.app.case_checkboxes[case_index].set(True)
            except Exception:
                pass

        # 완료 시 이 창을 다시 그리도록 등록
        self.app._general_info_dialog_refresh = {
            "case_number": self.case_number,
            "dialog": self,
        }
        self._status_var.set(
            "조회 중... 메인 화면에서 캡차를 입력한 뒤 '캡차 입력 완료'를 눌러 주세요."
        )
        try:
            self.refresh_btn.configure(state="disabled")
        except Exception:
            pass

        try:
            self.app.start_batch_processing()
            messagebox.showinfo(
                "재조회 시작",
                f"{self.case_number} 사건만 선택해 조회를 시작했습니다.\n\n"
                "메인 화면에서 캡차(또는 자동 스킵)를 처리해 주세요.\n"
                "조회가 끝나면 이 창이 자동으로 갱신됩니다.",
                parent=self,
            )
        except Exception as e:
            self.app._general_info_dialog_refresh = None
            self._status_var.set(f"재조회 시작 실패: {e}")
            try:
                self.refresh_btn.configure(state="normal")
            except Exception:
                pass
