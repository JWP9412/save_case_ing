# -*- coding: utf-8 -*-
"""
알림메일 미발송 내역 관리
=========================
이전 발송 이후 수집된 업데이트 내역을 unsent_emails.json에 누적하고,
발송 시 비우는 역할.

주니어 개발자 참고 (v4.10.0):
- updates: 신규 진행내용 행(메일 상단 '최신 업데이트 내역')
- run_results: 사건별 조회 결과 누적(메일 하단 '이번 조회 결과 요약')
  → 여러 번 나눠 조회해도 덮어쓰지 않고 병합합니다.
  → GUI / --auto 가 같은 파일을 공유하므로 자동 실행 결과도 GUI 메일에 포함됩니다.
"""
import json
import os
from datetime import datetime

import config

# 상태 상수 (run_results 값)
STATUS_SUCCESS = "성공"
STATUS_NO_UPDATE = "변경없음"
STATUS_RESULT_CHANGED = "결과변경"
STATUS_FAIL = "실패"
STATUS_CAPTCHA = "캡차"
STATUS_NOT_QUERIED = "미조회"


def _get_path():
    return config.path_from_base(config.UNSENT_EMAILS_FILE)


def load_unsent_emails(file_path=None):
    """
    미발송 이메일 내역 로드.

    반환: {"last_sent": "...", "updates": [...], "result_changes": [...], "run_results": {...}}
    """
    path = file_path or _get_path()
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "updates" in data:
                    if "run_results" not in data or not isinstance(data.get("run_results"), dict):
                        data["run_results"] = {}
                    if "result_changes" not in data or not isinstance(data.get("result_changes"), list):
                        data["result_changes"] = []
                    return data
    except Exception:
        pass
    return {"last_sent": "", "updates": [], "result_changes": [], "run_results": {}}


def save_unsent_emails(data, file_path=None):
    """미발송 이메일 내역 저장."""
    path = file_path or _get_path()
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _normalize_sheet_url(url):
    """
    메일 링크용 시트 URL을 사용자 브라우저용 형식으로 정규화합니다.

    주니어 개발자 참고:
    - 과거 데이터에는 `https://sheets.googleapis.com/v4/spreadsheets/...#gid=...`
      형태(API 엔드포인트)가 저장되어 있을 수 있습니다.
    - 이 주소를 메일에서 클릭하면 인증 없는 API 호출이 되어 403이 납니다.
    - 따라서 `https://docs.google.com/spreadsheets/d/.../edit#gid=...` 형식으로 변환합니다.
    """
    s = (url or "").strip()
    if not s:
        return ""
    bad_prefix = "https://sheets.googleapis.com/v4/spreadsheets/"
    if s.startswith(bad_prefix):
        rest = s[len(bad_prefix):]
        spreadsheet_id, _, fragment = rest.partition("#")
        if not spreadsheet_id:
            return ""
        base = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
        return f"{base}#{fragment}" if fragment else base
    return s


def add_new_update(case_number, updates, sheet_name="", sheet_url=""):
    """
    새로 업데이트된 진행내역을 미발송 목록에 추가.
    구글 시트에 적용되는 색상(dateColor, contentColor, resultColor)과 result를 함께 저장.
    """
    data = load_unsent_emails()
    if "updates" not in data:
        data["updates"] = []
    for u in updates:
        if not isinstance(u, dict):
            u = {"date": "", "content": str(u), "result": ""}
        data["updates"].append({
            "case": case_number,
            "date": u.get("date", ""),
            "content": u.get("content", ""),
            "result": u.get("result", ""),
            "dateColor": u.get("dateColor") or "",
            "contentColor": u.get("contentColor") or "",
            "resultColor": u.get("resultColor") or "",
            "sheet_name": sheet_name or "",
            "sheet_url": _normalize_sheet_url(sheet_url),
        })
    save_unsent_emails(data)


def add_result_changes(case_number, changes, sheet_name="", sheet_url=""):
    """
    송달 '결과' 칸만 바뀐 행을 미발송 목록에 추가합니다.

    주니어 개발자 참고:
    - updates(최신 업데이트)와 별도로 result_changes에 쌓습니다.
    - old_result: 시트에 있던 이전 결과, result: 대법원에서 가져온 새 결과
    """
    data = load_unsent_emails()
    if "result_changes" not in data:
        data["result_changes"] = []
    for ch in changes or []:
        if not isinstance(ch, dict):
            continue
        data["result_changes"].append({
            "case": case_number,
            "date": ch.get("date", ""),
            "content": ch.get("content", ""),
            "old_result": ch.get("old_result", ""),
            "result": ch.get("result", ""),
            "dateColor": ch.get("dateColor") or "",
            "contentColor": ch.get("contentColor") or "",
            "resultColor": ch.get("resultColor") or "",
            "sheet_name": sheet_name or "",
            "sheet_url": _normalize_sheet_url(sheet_url),
        })
    save_unsent_emails(data)


def clear_unsent_emails_and_update_last_sent(file_path=None):
    """
    발송 완료 후: updates·run_results를 비우고 last_sent를 현재 시간으로 갱신.
    """
    data = load_unsent_emails(file_path)
    data["updates"] = []
    data["result_changes"] = []
    data["run_results"] = {}
    data["last_sent"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if "last_run_result" in data:
        del data["last_run_result"]
    save_unsent_emails(data, file_path)
    _last_run_result_cache.clear()


# 하위호환용 메모리 캐시 (record_run_results가 파일에도 쓰므로 보조)
_last_run_result_cache = {}


def record_run_results(results):
    """
    사건별 조회 결과를 파일에 누적 병합합니다.

    Parameters
    ----------
    results : dict
        {사건번호: {"상태": "성공"|"변경없음"|"실패"|"캡차", "피고": ..., "사건명": ...}, ...}
        같은 사건번호가 이미 있으면 새 값으로 덮어씁니다(사건 단위 최신 상태 유지).
        다른 사건번호는 그대로 둡니다(배치마다 전체 덮어쓰지 않음).
    """
    if not results:
        return
    data = load_unsent_emails()
    run_results = data.get("run_results") or {}
    if not isinstance(run_results, dict):
        run_results = {}
    for case_number, info in results.items():
        if not case_number:
            continue
        if not isinstance(info, dict):
            continue
        run_results[str(case_number)] = {
            "상태": info.get("상태", STATUS_SUCCESS),
            "피고": info.get("피고", ""),
            "사건명": info.get("사건명", ""),
            "사건번호": str(case_number),
        }
    data["run_results"] = run_results
    save_unsent_emails(data)

    # 메모리 캐시도 동기화(구버전 호출 경로용)
    _sync_cache_from_run_results(run_results)


def _sync_cache_from_run_results(run_results):
    """run_results dict → 구버전 success/fail/... 리스트 캐시."""
    success, result_changed, failed, no_update, captcha = [], [], [], [], []
    for cn, info in (run_results or {}).items():
        item = {
            "사건번호": info.get("사건번호") or cn,
            "피고": info.get("피고", ""),
            "사건명": info.get("사건명", ""),
        }
        st = info.get("상태", "")
        if st == STATUS_NO_UPDATE:
            no_update.append(item)
        elif st == STATUS_FAIL:
            failed.append(item)
        elif st == STATUS_CAPTCHA:
            captcha.append(item)
        elif st == STATUS_RESULT_CHANGED:
            result_changed.append(item)
        else:
            success.append(item)
    _last_run_result_cache["success_cases"] = success
    _last_run_result_cache["result_changed_cases"] = result_changed
    _last_run_result_cache["failed_cases"] = failed
    _last_run_result_cache["no_update_cases"] = no_update
    _last_run_result_cache["captcha_cases"] = captcha


def load_run_results():
    """파일에 저장된 run_results dict 반환."""
    data = load_unsent_emails()
    rr = data.get("run_results") or {}
    return rr if isinstance(rr, dict) else {}


def set_last_run_result(success_cases=None, failed_cases=None, no_update_cases=None, captcha_cases=None):
    """
    하위호환 래퍼: 리스트들을 record_run_results 형식으로 변환해 누적 저장합니다.
    """
    merged = {}

    def _ingest(lst, status):
        for case in lst or []:
            if isinstance(case, dict):
                cn = case.get("사건번호", "")
                if not cn:
                    continue
                merged[cn] = {
                    "상태": status,
                    "피고": case.get("피고", ""),
                    "사건명": case.get("사건명", ""),
                    "사건번호": cn,
                }
            else:
                cn = str(case)
                merged[cn] = {"상태": status, "피고": "", "사건명": "", "사건번호": cn}

    _ingest(success_cases, STATUS_SUCCESS)
    _ingest(no_update_cases, STATUS_NO_UPDATE)
    _ingest(failed_cases, STATUS_FAIL)
    _ingest(captcha_cases, STATUS_CAPTCHA)
    record_run_results(merged)


def has_last_run_result():
    """저장된 조회 결과(파일 또는 캐시)가 하나라도 있으면 True."""
    if load_run_results():
        return True
    s = _last_run_result_cache.get("success_cases") or []
    f = _last_run_result_cache.get("failed_cases") or []
    n = _last_run_result_cache.get("no_update_cases") or []
    c = _last_run_result_cache.get("captcha_cases") or []
    return bool(s or f or n or c)


def _rgb_to_css(color):
    """gspread/시트에서 오는 rgb(255,0,0) 형태를 CSS color로 그대로 사용."""
    if not color or not isinstance(color, str):
        return "#000000"
    return color.strip()


def get_summary_text():
    """
    미발송 내역을 "사건번호 날짜 -내용-" 형식 평문 문자열로 조합하여 반환.
    반환: (summary_string, last_sent_string)
    """
    data = load_unsent_emails()
    updates = data.get("updates", [])
    result_changes = data.get("result_changes", [])
    last_sent = data.get("last_sent", "") or "없음"
    if not updates and not result_changes:
        return "", last_sent
    lines = []
    for u in updates:
        case = u.get("case", "")
        date = u.get("date", "")
        content = u.get("content", "")
        lines.append(f"{case} {date} -{content}-")
    for ch in result_changes:
        case = ch.get("case", "")
        date = ch.get("date", "")
        content = ch.get("content", "")
        old_r = ch.get("old_result", "")
        new_r = ch.get("result", "")
        lines.append(f"{case} {date} -{content}- [결과변경: {old_r} → {new_r}]")
    return "\n".join(lines), last_sent


def _esc_html(s):
    """HTML 특수문자 이스케이프."""
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# 메일 HTML 공통 스타일 (인라인만 사용 — Gmail/Outlook 호환)
_MAIL_FONT = "'Apple SD Gothic Neo','Malgun Gothic',Arial,sans-serif"
_TH_STYLE = (
    "text-align:left; padding:8px 6px; font-size:12px; color:#6B7280; "
    f"font-family:Arial,sans-serif; border-bottom:1px solid #EEEEEE;"
)
_TD_BASE = (
    f"padding:10px 6px; font-family:{_MAIL_FONT}; font-size:13px;"
)


def _case_lists_from_run_results(run_results, all_cases=None):
    """
    run_results + (선택) 전체 사건 목록 → 상태별 리스트.
    all_cases가 있으면 run_results에 없는 사건은 '미조회'로 분류합니다.
    """
    success, no_update, failed, captcha, result_changed, not_queried = [], [], [], [], [], []
    seen = set()

    for cn, info in (run_results or {}).items():
        item = {
            "사건번호": info.get("사건번호") or cn,
            "피고": info.get("피고", ""),
            "사건명": info.get("사건명", ""),
        }
        seen.add(str(cn))
        st = info.get("상태", "")
        if st == STATUS_NO_UPDATE:
            no_update.append(item)
        elif st == STATUS_FAIL:
            failed.append(item)
        elif st == STATUS_CAPTCHA:
            captcha.append(item)
        elif st == STATUS_RESULT_CHANGED:
            result_changed.append(item)
        else:
            success.append(item)

    if all_cases:
        for case in all_cases:
            if not isinstance(case, dict):
                continue
            cn = case.get("사건번호", "")
            if not cn or str(cn) in seen:
                continue
            not_queried.append({
                "사건번호": cn,
                "피고": case.get("피고", ""),
                "사건명": case.get("사건명", ""),
            })

    return success, no_update, failed, captcha, result_changed, not_queried


def _mail_section_title(title, padding="18px 0 12px 0"):
    """섹션 제목 HTML (최신 업데이트 / 결과 변경 / 조회 요약)."""
    return (
        f'<div style="padding:{padding}; font-family:{_MAIL_FONT}; '
        f'font-size:18px; font-weight:700; color:#111827;">{_esc_html(title)}</div>'
    )


def _mail_card(header_html, body_html):
    """
    사건(또는 상태 그룹) 1개를 흰 카드로 감쌉니다.
    주니어: 메일 클라이언트는 border-radius를 무시할 수 있어도, 테두리·여백은 유지됩니다.
    """
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        'style="background-color:#FFFFFF; border:1px solid #E5E7EB; border-radius:10px; '
        'overflow:hidden; margin:0 0 14px 0;">'
        f'<tr><td style="padding:16px 18px 12px 18px; border-bottom:1px solid #EEF0F3;">{header_html}</td></tr>'
        f'<tr><td style="padding:8px 12px 12px 12px;">{body_html}</td></tr>'
        "</table>"
    )


def _mail_shortcut_link(sheet_url):
    """시트 바로가기 링크. URL 없으면 빈 문자열."""
    rep_url = _normalize_sheet_url(sheet_url) if sheet_url else ""
    if not rep_url:
        return ""
    return (
        f'<div style="margin-top:8px;">'
        f'<a href="{_esc_html(rep_url)}" target="_blank" '
        f'style="color:#1a73e8; text-decoration:none; font-size:13px; font-family:Arial,sans-serif;">'
        f"바로가기 &rarr;</a></div>"
    )


def _mail_card_header(title, sheet_url=""):
    """카드 상단: 시트명 + 바로가기."""
    return (
        f'<div style="font-family:{_MAIL_FONT}; font-size:14px; font-weight:700; '
        f'color:#111827; line-height:1.45;">{_esc_html(title)}</div>'
        f"{_mail_shortcut_link(sheet_url)}"
    )


def _mail_td(text, color=None, with_border=False):
    """표 셀. color는 시트에서 온 글자색을 그대로 씁니다."""
    css_color = _rgb_to_css(color) if color is not None else "#222222"
    border = " border-bottom:1px solid #F3F4F6;" if with_border else ""
    return (
        f'<td style="{_TD_BASE} color:{css_color};{border}">{_esc_html(text)}</td>'
    )


def _render_update_card(s_name, sheet_updates, sheet_url="", title_suffix=""):
    """업데이트 행 묶음 1개를 카드 HTML로 렌더."""
    title = f"{s_name}{title_suffix}" if title_suffix else s_name
    header = _mail_card_header(title, sheet_url)
    rows = [
        "<tr>"
        f'<th style="{_TH_STYLE} width:18%;">일자</th>'
        f'<th style="{_TH_STYLE} width:52%;">내용</th>'
        f'<th style="{_TH_STYLE} width:30%;">결과</th>'
        "</tr>"
    ]
    last_i = len(sheet_updates) - 1
    for i, u in enumerate(sheet_updates):
        border = i < last_i
        rows.append(
            "<tr>"
            f"{_mail_td(u.get('date', ''), u.get('dateColor'), border)}"
            f"{_mail_td(u.get('content', ''), u.get('contentColor'), border)}"
            f"{_mail_td(u.get('result', ''), u.get('resultColor'), border)}"
            "</tr>"
        )
    body = (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="border-collapse:collapse; width:100%;">{"".join(rows)}</table>'
    )
    return _mail_card(header, body)


def _render_result_change_card(s_name, sheet_changes, sheet_url="", title_suffix=""):
    """결과 변경 행 묶음 1개를 카드 HTML로 렌더."""
    title = f"{s_name}{title_suffix}" if title_suffix else s_name
    header = _mail_card_header(title, sheet_url)
    rows = [
        "<tr>"
        f'<th style="{_TH_STYLE}">일자</th>'
        f'<th style="{_TH_STYLE}">내용</th>'
        f'<th style="{_TH_STYLE}">이전 결과</th>'
        f'<th style="{_TH_STYLE}">변경 결과</th>'
        "</tr>"
    ]
    last_i = len(sheet_changes) - 1
    for i, ch in enumerate(sheet_changes):
        border = i < last_i
        rows.append(
            "<tr>"
            f"{_mail_td(ch.get('date', ''), ch.get('dateColor'), border)}"
            f"{_mail_td(ch.get('content', ''), ch.get('contentColor'), border)}"
            f"{_mail_td(ch.get('old_result', ''), None, border)}"
            f"{_mail_td(ch.get('result', ''), ch.get('resultColor'), border)}"
            "</tr>"
        )
    body = (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="border-collapse:collapse; width:100%;">{"".join(rows)}</table>'
    )
    return _mail_card(header, body)


def _chunk_items_to_cards(s_name, items, sheet_url, render_fn, max_card_chars):
    """
    한 사건 행이 너무 많으면 여러 카드로 나눕니다.
    render_fn(s_name, chunk, sheet_url, title_suffix) -> html
    """
    if not items:
        return []
    cards = []
    chunk = []
    part_idx = 0
    for item in items:
        trial = chunk + [item]
        suffix = f" (이어짐 {part_idx + 1})" if part_idx > 0 else ""
        trial_html = render_fn(s_name, trial, sheet_url, suffix)
        if chunk and len(trial_html) > max_card_chars:
            # 지금까지 모은 행으로 카드 확정
            suffix = f" (이어짐 {part_idx + 1})" if part_idx > 0 else ""
            cards.append(render_fn(s_name, chunk, sheet_url, suffix))
            part_idx += 1
            chunk = [item]
        else:
            chunk = trial
    if chunk:
        suffix = f" (이어짐 {part_idx + 1})" if part_idx > 0 else ""
        cards.append(render_fn(s_name, chunk, sheet_url, suffix))
    return cards


def _build_update_card_list(updates_by_sheet, max_card_chars=None):
    """최신 업데이트: 시트별 카드 HTML 리스트 (거대 카드는 행 분할)."""
    if max_card_chars is None:
        max_card_chars = int(getattr(config, "GOOGLE_SHEET_CELL_MAX_CHARS", 49000)) - 2500
    cards = []
    for s_name, sheet_updates in updates_by_sheet.items():
        rep_url = next(
            (u.get("sheet_url") for u in sheet_updates if u.get("sheet_url")),
            "",
        )
        cards.extend(
            _chunk_items_to_cards(
                s_name,
                sheet_updates,
                rep_url,
                _render_update_card,
                max_card_chars,
            )
        )
    return cards


def _build_result_change_card_list(changes_by_sheet, max_card_chars=None):
    """결과 변경: 시트별 카드 HTML 리스트 (거대 카드는 행 분할)."""
    if max_card_chars is None:
        max_card_chars = int(getattr(config, "GOOGLE_SHEET_CELL_MAX_CHARS", 49000)) - 2500
    cards = []
    for s_name, sheet_changes in changes_by_sheet.items():
        rep_url = next(
            (ch.get("sheet_url") for ch in sheet_changes if ch.get("sheet_url")),
            "",
        )
        cards.extend(
            _chunk_items_to_cards(
                s_name,
                sheet_changes,
                rep_url,
                _render_result_change_card,
                max_card_chars,
            )
        )
    return cards


def _build_update_cards(updates_by_sheet):
    """하위 호환: 시트별 카드를 이어 붙인 문자열."""
    return "".join(_build_update_card_list(updates_by_sheet))


def _build_result_change_cards(changes_by_sheet):
    """하위 호환: 시트별 카드를 이어 붙인 문자열."""
    return "".join(_build_result_change_card_list(changes_by_sheet))


def _build_run_result_footer(
    success_cases=None,
    failed_cases=None,
    no_update_cases=None,
    captcha_cases=None,
    result_changed_cases=None,
    not_queried_cases=None,
    total_count=None,
):
    """이번 조회 결과 요약 — 상태별 카드 HTML."""
    success_cases = success_cases or []
    failed_cases = failed_cases or []
    no_update_cases = no_update_cases or []
    captcha_cases = captcha_cases or []
    result_changed_cases = result_changed_cases or []
    not_queried_cases = not_queried_cases or []
    if not (
        success_cases
        or failed_cases
        or no_update_cases
        or captcha_cases
        or result_changed_cases
        or not_queried_cases
    ):
        return ""

    def _render_status_card(title, case_list):
        if not case_list:
            return ""
        header = (
            f'<div style="font-family:{_MAIL_FONT}; font-size:14px; font-weight:700; '
            f'color:#111827;">{_esc_html(title)} ({len(case_list)}건)</div>'
        )
        rows = [
            "<tr>"
            f'<th style="{_TH_STYLE} width:40%;">사건번호</th>'
            f'<th style="{_TH_STYLE} width:60%;">피고/사건명</th>'
            "</tr>"
        ]
        last_i = len(case_list) - 1
        for i, case in enumerate(case_list):
            border = i < last_i
            if isinstance(case, dict):
                case_num = case.get("사건번호", "")
                defendant = case.get("피고", "")
                case_name = case.get("사건명", "")
                details = []
                if defendant:
                    details.append(defendant)
                if case_name:
                    details.append(case_name)
                detail_str = " / ".join(details)
            else:
                case_num = str(case)
                detail_str = "-"
            rows.append(
                "<tr>"
                f"{_mail_td(case_num, None, border)}"
                f"{_mail_td(detail_str, None, border)}"
                "</tr>"
            )
        body = (
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
            f'style="border-collapse:collapse; width:100%;">{"".join(rows)}</table>'
        )
        return _mail_card(header, body)

    if total_count is None:
        total_count = (
            len(success_cases)
            + len(no_update_cases)
            + len(failed_cases)
            + len(captcha_cases)
            + len(result_changed_cases)
            + len(not_queried_cases)
        )
    parts = [_mail_section_title(f"이번 조회 결과 요약 (전체 {total_count}건)")]
    parts.append(_render_status_card("성공", success_cases))
    parts.append(_render_status_card("성공(결과 변경)", result_changed_cases))
    parts.append(_render_status_card("성공(변경없음)", no_update_cases))
    parts.append(_render_status_card("실패", failed_cases))
    parts.append(_render_status_card("캡차(재시도 안 함)", captcha_cases))
    parts.append(_render_status_card("미조회", not_queried_cases))
    return "".join(parts)


def _wrap_mail_body(inner_html):
    """회색 배경 + 680px 컨테이너로 본문을 감쌉니다."""
    return (
        '<div style="margin:0; padding:0; background-color:#F3F4F6;">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        'style="background-color:#F3F4F6; padding:24px 12px;">'
        "<tr><td align=\"center\">"
        '<table role="presentation" width="680" cellpadding="0" cellspacing="0" border="0" '
        'style="width:680px; max-width:680px;">'
        f"<tr><td>{inner_html}</td></tr>"
        "</table></td></tr></table></div>"
    )


def _mail_part_banner(part_no, total):
    """메일 상단: CASE-ING NOTIFICATION · 메일 N/M"""
    label = f"CASE-ING NOTIFICATION · 메일 {part_no}/{total}"
    return (
        '<div style="padding:0 0 4px 0;">'
        '<div style="font-family:Arial,sans-serif; font-size:11px; letter-spacing:0.08em; '
        f'color:#6B7280; margin-bottom:6px;">{_esc_html(label)}</div>'
        "</div>"
    )


def _finalize_mail_html(inner_html):
    """완성된 메일 HTML 문서."""
    return f"<html><body>{_wrap_mail_body(inner_html)}</body></html>"


def _estimate_wrapper_overhead():
    """래퍼+배너 대략 길이 (예산 계산용)."""
    sample = _finalize_mail_html(_mail_part_banner(99, 99))
    return len(sample)


def safe_trim_html(html, max_chars, omitted_hint="다음 메일에서 이어집니다"):
    """
    셀 한도 초과 시 깨진 태그 조각을 남기지 않고 자릅니다.
    반환: (잘린_html, 생략된_글자_수) — 생략 없으면 omitted=0.
    """
    if not html:
        return "", 0
    if len(html) <= max_chars:
        return html, 0

    omitted = len(html) - max_chars
    notice = (
        f'<p style="margin:16px 0 0 0; padding:12px 14px; background:#F9FAFB; '
        f'border:1px solid #E5E7EB; border-radius:8px; font-family:{_MAIL_FONT}; '
        f'font-size:13px; color:#6B7280;">'
        f"(이하 {omitted}자 생략"
        f"{(' — ' + omitted_hint) if omitted_hint else ''})"
        f"</p>"
    )
    # 안내 문구·닫는 태그를 넣을 여유를 확보
    reserve = len(notice) + len("</td></tr></table></td></tr></table></div></body></html>") + 80
    budget = max(500, max_chars - reserve)
    cut = html[:budget]

    # 미완성 태그 제거: 마지막 '<' 가 '>' 보다 뒤에 있으면 그 앞까지
    last_lt = cut.rfind("<")
    last_gt = cut.rfind(">")
    if last_lt > last_gt:
        cut = cut[:last_lt]

    # 가능하면 행/카드 경계에서 끊기
    for marker in ("</table>", "</tr>", "</td>", "</div>"):
        idx = cut.rfind(marker)
        if idx != -1 and idx > budget // 2:
            cut = cut[: idx + len(marker)]
            break

    # 열린 래퍼를 최소한으로 닫아 메일 클라이언트가 깨지지 않게 함
    closers = ""
    lower = cut.lower()
    for tag, open_pat, close_pat in (
        ("table", "<table", "</table"),
        ("tr", "<tr", "</tr"),
        ("td", "<td", "</td"),
        ("div", "<div", "</div"),
    ):
        opens = lower.count(open_pat) - lower.count(close_pat)
        if opens > 0:
            closers += f"</{tag}>" * opens

    # html/body 가 잘렸으면 보충
    if "<html" in lower and "</html" not in lower:
        if "<body" in lower and "</body" not in lower:
            closers += "</body></html>"
        else:
            closers += "</html>"
    elif "<body" in lower and "</body" not in lower:
        closers += "</body>"

    result = cut + notice + closers
    if len(result) > max_chars:
        # 최후: 안내만 남기고 본문은 더 짧게
        mini_notice = (
            f'<html><body><p style="font-family:{_MAIL_FONT}; font-size:13px; color:#6B7280;">'
            f"(이하 {omitted}자 생략"
            f"{(' — ' + omitted_hint) if omitted_hint else ''})"
            f"</p></body></html>"
        )
        if len(mini_notice) <= max_chars:
            return mini_notice, omitted
        return mini_notice[:max_chars], omitted
    return result, omitted


def _pack_mail_parts(content_blocks, footer_html, max_chars):
    """
    content_blocks: [{'kind': 'update'|'change'|'title', 'html': '...'}, ...]
    카드/제목을 한도 내로 묶어 완성 HTML 리스트를 반환. footer는 마지막에만.
    """
    overhead = _estimate_wrapper_overhead()
    budget = max(2000, max_chars - overhead - 200)

    batches = []  # list of list of html snippets
    current = []
    current_len = 0

    def flush():
        nonlocal current, current_len
        if current:
            batches.append(current)
            current = []
            current_len = 0

    for block in content_blocks:
        html = block.get("html") or ""
        if not html:
            continue
        # 단일 블록이 예산 초과면 그대로 한 배치(이후 safe_trim 폴백)
        if len(html) > budget:
            flush()
            batches.append([html])
            continue
        if current and current_len + len(html) > budget:
            flush()
        current.append(html)
        current_len += len(html)
    flush()

    if not batches:
        if footer_html:
            batches = [[]]
        else:
            return []

    # footer를 마지막 배치에 붙일 수 있는지 확인
    if footer_html:
        last = batches[-1]
        last_len = sum(len(x) for x in last)
        if last_len + len(footer_html) <= budget:
            last.append(footer_html)
        else:
            batches.append([footer_html])

    total = len(batches)
    parts = []
    for i, snippets in enumerate(batches, start=1):
        inner = _mail_part_banner(i, total) + "".join(snippets)
        html = _finalize_mail_html(inner)
        if len(html) > max_chars:
            html, _ = safe_trim_html(html, max_chars)
        parts.append(html)
    return parts


def _resolve_case_lists(
    success_cases=None,
    failed_cases=None,
    no_update_cases=None,
    captcha_cases=None,
    all_cases=None,
):
    """get_summary_html / parts 공통: 상태별 리스트와 last_sent, updates, changes 반환."""
    data = load_unsent_emails()
    updates = data.get("updates", [])
    result_changes = data.get("result_changes", [])
    last_sent = data.get("last_sent", "") or "없음"
    run_results = data.get("run_results") or {}

    explicit = any(
        x is not None
        for x in (success_cases, failed_cases, no_update_cases, captcha_cases)
    )
    if explicit:
        use_success = success_cases or []
        use_failed = failed_cases or []
        use_no_update = no_update_cases or []
        use_captcha = captcha_cases or []
        use_result_changed = []
        use_not_queried = []
        if all_cases:
            seen = set()
            for lst in (use_success, use_failed, use_no_update, use_captcha):
                for c in lst:
                    cn = c.get("사건번호", "") if isinstance(c, dict) else str(c)
                    if cn:
                        seen.add(cn)
            for case in all_cases:
                cn = case.get("사건번호", "") if isinstance(case, dict) else ""
                if cn and cn not in seen:
                    use_not_queried.append({
                        "사건번호": cn,
                        "피고": case.get("피고", ""),
                        "사건명": case.get("사건명", ""),
                    })
    else:
        use_success, use_no_update, use_failed, use_captcha, use_result_changed, use_not_queried = (
            _case_lists_from_run_results(run_results, all_cases=all_cases)
        )

    return {
        "updates": updates,
        "result_changes": result_changes,
        "last_sent": last_sent,
        "use_success": use_success,
        "use_failed": use_failed,
        "use_no_update": use_no_update,
        "use_captcha": use_captcha,
        "use_result_changed": use_result_changed,
        "use_not_queried": use_not_queried,
    }


def get_summary_html_parts(
    success_cases=None,
    failed_cases=None,
    no_update_cases=None,
    captcha_cases=None,
    all_cases=None,
    max_chars=None,
):
    """
    알림메일 HTML을 셀 한도 내로 나눈 리스트로 반환.
    반환: (html_parts:list[str], last_sent:str)
    성공/실패 요약은 마지막 파트에만 포함됩니다.
    """
    if max_chars is None:
        max_chars = int(getattr(config, "GOOGLE_SHEET_CELL_MAX_CHARS", 49000))

    ctx = _resolve_case_lists(
        success_cases, failed_cases, no_update_cases, captcha_cases, all_cases
    )
    updates = ctx["updates"]
    result_changes = ctx["result_changes"]
    last_sent = ctx["last_sent"]

    has_footer = bool(
        ctx["use_success"]
        or ctx["use_failed"]
        or ctx["use_no_update"]
        or ctx["use_captcha"]
        or ctx["use_result_changed"]
        or ctx["use_not_queried"]
    )

    if not updates and not result_changes and not has_footer:
        return [], last_sent

    # 카드 1개 예산: 전체 한도에서 래퍼·footer 여유를 뺀 값
    max_card = max(3000, max_chars - _estimate_wrapper_overhead() - 1500)
    blocks = []

    if updates:
        blocks.append({
            "kind": "title",
            "html": _mail_section_title("최신 업데이트 내역", padding="0 0 12px 0"),
        })
        updates_by_sheet = {}
        for u in updates:
            s_name = u.get("sheet_name") or "기타"
            updates_by_sheet.setdefault(s_name, []).append(u)
        for card in _build_update_card_list(updates_by_sheet, max_card_chars=max_card):
            blocks.append({"kind": "update", "html": card})

    if result_changes:
        blocks.append({
            "kind": "title",
            "html": _mail_section_title("결과 변경 내역"),
        })
        changes_by_sheet = {}
        for ch in result_changes:
            s_name = ch.get("sheet_name") or "기타"
            changes_by_sheet.setdefault(s_name, []).append(ch)
        for card in _build_result_change_card_list(changes_by_sheet, max_card_chars=max_card):
            blocks.append({"kind": "change", "html": card})

    footer_html = ""
    if has_footer:
        total = len(all_cases) if all_cases is not None else None
        footer_html = _build_run_result_footer(
            ctx["use_success"],
            ctx["use_failed"],
            ctx["use_no_update"],
            ctx["use_captcha"],
            ctx["use_result_changed"],
            ctx["use_not_queried"],
            total_count=total,
        )

    parts = _pack_mail_parts(blocks, footer_html, max_chars)
    return parts, last_sent


def get_summary_html(
    success_cases=None,
    failed_cases=None,
    no_update_cases=None,
    captcha_cases=None,
    all_cases=None,
):
    """
    미발송 내역을 사건별 카드형 HTML로 조합하여 반환.
    미리보기용: 분할 파트를 순서대로 이어 붙입니다(시트 저장은 get_summary_html_parts 사용).
    """
    parts, last_sent = get_summary_html_parts(
        success_cases=success_cases,
        failed_cases=failed_cases,
        no_update_cases=no_update_cases,
        captcha_cases=captcha_cases,
        all_cases=all_cases,
    )
    if not parts:
        return "", last_sent
    if len(parts) == 1:
        return parts[0], last_sent
    # 미리보기: 파트들을 구분선과 함께 합침
    joined_inners = []
    for i, p in enumerate(parts, start=1):
        joined_inners.append(
            f'<div style="margin:0 0 24px 0; padding:0 0 16px 0; '
            f'border-bottom:2px dashed #D1D5DB;">'
            f'<div style="font-size:12px; color:#9CA3AF; margin-bottom:8px;">'
            f'[미리보기 파트 {i}/{len(parts)}]</div>{p}</div>'
        )
    return "".join(joined_inners), last_sent
