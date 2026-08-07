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
STATUS_FAIL = "실패"
STATUS_CAPTCHA = "캡차"
STATUS_NOT_QUERIED = "미조회"


def _get_path():
    return config.path_from_base(config.UNSENT_EMAILS_FILE)


def load_unsent_emails(file_path=None):
    """
    미발송 이메일 내역 로드.

    반환: {"last_sent": "...", "updates": [...], "run_results": {...}}
    """
    path = file_path or _get_path()
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "updates" in data:
                    if "run_results" not in data or not isinstance(data.get("run_results"), dict):
                        data["run_results"] = {}
                    return data
    except Exception:
        pass
    return {"last_sent": "", "updates": [], "run_results": {}}


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


def clear_unsent_emails_and_update_last_sent(file_path=None):
    """
    발송 완료 후: updates·run_results를 비우고 last_sent를 현재 시간으로 갱신.
    """
    data = load_unsent_emails(file_path)
    data["updates"] = []
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
    success, failed, no_update, captcha = [], [], [], []
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
        else:
            success.append(item)
    _last_run_result_cache["success_cases"] = success
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
    last_sent = data.get("last_sent", "") or "없음"
    if not updates:
        return "", last_sent
    lines = []
    for u in updates:
        case = u.get("case", "")
        date = u.get("date", "")
        content = u.get("content", "")
        lines.append(f"{case} {date} -{content}-")
    return "\n".join(lines), last_sent


def _esc_html(s):
    """HTML 특수문자 이스케이프."""
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _case_lists_from_run_results(run_results, all_cases=None):
    """
    run_results + (선택) 전체 사건 목록 → 상태별 리스트.
    all_cases가 있으면 run_results에 없는 사건은 '미조회'로 분류합니다.
    """
    success, no_update, failed, captcha, not_queried = [], [], [], [], []
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

    return success, no_update, failed, captcha, not_queried


def _build_run_result_footer(
    success_cases=None,
    failed_cases=None,
    no_update_cases=None,
    captcha_cases=None,
    not_queried_cases=None,
    total_count=None,
):
    """이번 조회 결과 푸터 HTML 조각."""
    success_cases = success_cases or []
    failed_cases = failed_cases or []
    no_update_cases = no_update_cases or []
    captcha_cases = captcha_cases or []
    not_queried_cases = not_queried_cases or []
    if not (
        success_cases
        or failed_cases
        or no_update_cases
        or captcha_cases
        or not_queried_cases
    ):
        return ""

    def _render_case_table(title, case_list):
        if not case_list:
            return ""

        table_style = (
            'border="1" cellpadding="4" cellspacing="0" '
            'style="border-collapse:collapse; width: 100%; max-width: 800px; margin-bottom: 20px;"'
        )
        th_style = 'style="background-color: #f2f2f2; text-align: left;"'

        rows = [
            f"<h4>{title} ({len(case_list)}건)</h4>",
            f"<table {table_style}>",
            f'<tr><th {th_style} width="40%">사건번호</th>'
            f'<th {th_style} width="60%">피고/사건명</th></tr>',
        ]

        for case in case_list:
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
                rows.append(
                    f"<tr>"
                    f"<td>{_esc_html(case_num)}</td>"
                    f"<td>{_esc_html(detail_str)}</td>"
                    f"</tr>"
                )
            else:
                rows.append(
                    f"<tr>"
                    f"<td>{_esc_html(str(case))}</td>"
                    f"<td>-</td>"
                    f"</tr>"
                )

        rows.append("</table>")
        return "\n".join(rows)

    if total_count is None:
        total_count = (
            len(success_cases)
            + len(no_update_cases)
            + len(failed_cases)
            + len(captcha_cases)
            + len(not_queried_cases)
        )
    parts = [f"<h3>이번 조회 결과 요약 (전체 {total_count}건)</h3>"]
    parts.append(_render_case_table("성공", success_cases))
    parts.append(_render_case_table("성공(변경없음)", no_update_cases))
    parts.append(_render_case_table("실패", failed_cases))
    parts.append(_render_case_table("캡차(재시도 안 함)", captcha_cases))
    parts.append(_render_case_table("미조회", not_queried_cases))

    return "\n".join(parts)


def get_summary_html(
    success_cases=None,
    failed_cases=None,
    no_update_cases=None,
    captcha_cases=None,
    all_cases=None,
):
    """
    미발송 내역을 구글 시트 색상을 반영한 HTML 표로 조합하여 반환.

    all_cases: 사건 목록 전체(list of dict). 있으면 run_results에 없는 건을 '미조회'로 표시.
    인자로 success/... 를 넘기면 그 값을 우선 쓰고, 없으면 파일의 run_results를 사용합니다.
    """
    data = load_unsent_emails()
    updates = data.get("updates", [])
    last_sent = data.get("last_sent", "") or "없음"
    run_results = data.get("run_results") or {}

    # 명시 인자가 하나라도 있으면 구버전 경로(리스트 직접 전달)로 취급
    explicit = any(
        x is not None
        for x in (success_cases, failed_cases, no_update_cases, captcha_cases)
    )
    if explicit:
        use_success = success_cases or []
        use_failed = failed_cases or []
        use_no_update = no_update_cases or []
        use_captcha = captcha_cases or []
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
        use_success, use_no_update, use_failed, use_captcha, use_not_queried = (
            _case_lists_from_run_results(run_results, all_cases=all_cases)
        )

    has_footer = bool(
        use_success
        or use_failed
        or use_no_update
        or use_captcha
        or use_not_queried
    )

    if not updates and not has_footer:
        return "", last_sent

    body_parts = []
    if updates:
        updates_by_sheet = {}
        for u in updates:
            s_name = u.get("sheet_name") or "기타"
            if s_name not in updates_by_sheet:
                updates_by_sheet[s_name] = []
            updates_by_sheet[s_name].append(u)
        sections = []
        for s_name, sheet_updates in updates_by_sheet.items():
            sections.append(f"<h4>{_esc_html(s_name)}</h4>")
            rep_url = next(
                (
                    _normalize_sheet_url(u.get("sheet_url"))
                    for u in sheet_updates
                    if u.get("sheet_url")
                ),
                "",
            )
            if rep_url:
                sections.append(
                    f'<div style="margin:-6px 0 8px 0;">'
                    f'<a href="{_esc_html(rep_url)}" target="_blank" '
                    f'style="color:#1a73e8; text-decoration:none; font-size:13px;">'
                    f"바로가기 &rarr;</a></div>"
                )
            rows = ["<tr><th>일자</th><th>내용</th><th>결과</th></tr>"]
            for u in sheet_updates:
                date = u.get("date", "")
                content = u.get("content", "")
                result = u.get("result", "")
                dc = _rgb_to_css(u.get("dateColor"))
                cc = _rgb_to_css(u.get("contentColor"))
                rc = _rgb_to_css(u.get("resultColor"))
                rows.append(
                    f"<tr>"
                    f'<td style="color:{dc}">{_esc_html(date)}</td>'
                    f'<td style="color:{cc}">{_esc_html(content)}</td>'
                    f'<td style="color:{rc}">{_esc_html(result)}</td>'
                    f"</tr>"
                )
            table = (
                '<table border="1" cellpadding="4" cellspacing="0" '
                f'style="border-collapse:collapse;">{"".join(rows)}</table>'
            )
            sections.append(table)
        body_parts.append(f"<h3>최신 업데이트 내역</h3>{'<br>'.join(sections)}")

    if has_footer:
        total = None
        if all_cases is not None:
            total = len(all_cases)
        body_parts.append(
            _build_run_result_footer(
                use_success,
                use_failed,
                use_no_update,
                use_captcha,
                use_not_queried,
                total_count=total,
            )
        )

    html = f"<html><body>{'<br>'.join(body_parts)}</body></html>"
    return html, last_sent
