# -*- coding: utf-8 -*-
"""
알림메일 미발송 내역 관리
=========================
이전 발송 이후 수집된 업데이트 내역을 unsent_emails.json에 누적하고,
발송 시 비우는 역할.
"""
import json
import os
from datetime import datetime

import config


def _get_path():
    return config.path_from_base(config.UNSENT_EMAILS_FILE)


def load_unsent_emails(file_path=None):
    """
    미발송 이메일 내역 로드.

    반환: {"last_sent": "YYYY-MM-DD HH:MM:SS", "updates": [...]} 또는 기본 구조.
    """
    path = file_path or _get_path()
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "updates" in data:
                    return data
    except Exception:
        pass
    return {"last_sent": "", "updates": []}


def save_unsent_emails(data, file_path=None):
    """미발송 이메일 내역 저장."""
    path = file_path or _get_path()
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

    매개변수:
        case_number: 사건번호 문자열.
        updates: 진행내역 리스트. 각 항목은 dict with 'date', 'content', 'result',
                 'dateColor', 'contentColor', 'resultColor' 등.
        sheet_name: 구글 시트 탭 이름(피고_사건명_번호_법원 등). 메일 본문 그룹화에 사용.
        sheet_url: 구글 시트 탭의 바로가기 URL(gid 포함). 메일 본문의 "바로가기" 링크로 사용.
                   구버전 호환을 위해 기본값은 빈 문자열이며, 없으면 메일에서 링크를 생략합니다.
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
    발송 완료 후: updates를 비우고 last_sent를 현재 시간으로 갱신.
    마지막 조회 결과(last_run_result)도 초기화합니다.
    """
    data = load_unsent_emails(file_path)
    data["updates"] = []
    data["last_sent"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if "last_run_result" in data:
        del data["last_run_result"]
    save_unsent_emails(data, file_path)
    # 모듈 레벨 캐시도 비움
    _last_run_result_cache.clear()


# GUI용: 마지막 조회 결과 저장 (배치 완료 시 호출). 메모리 캐시 + 파일에 저장하지 않고 메모리만 사용.
_last_run_result_cache = {}


def set_last_run_result(success_cases=None, failed_cases=None, no_update_cases=None, captcha_cases=None):
    """
    마지막 조회 결과를 저장합니다. get_summary_html() 호출 시 인자 없으면 이 값을 사용합니다.
    각 인자는 딕셔너리 리스트 [{"사건번호": ..., "피고": ..., "사건명": ...}, ...] 구조를 가집니다.
    """
    _last_run_result_cache["success_cases"] = list(success_cases) if success_cases else []
    _last_run_result_cache["failed_cases"] = list(failed_cases) if failed_cases else []
    _last_run_result_cache["no_update_cases"] = list(no_update_cases) if no_update_cases else []
    _last_run_result_cache["captcha_cases"] = list(captcha_cases) if captcha_cases else []


def has_last_run_result():
    """저장된 마지막 조회 결과가 하나라도 있으면 True."""
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


def _build_run_result_footer(success_cases=None, failed_cases=None, no_update_cases=None, captcha_cases=None):
    """
    이번 조회 결과 푸터 HTML 조각. 성공/실패/캡차/변경없음 목록을 표로 반환.
    """
    success_cases = success_cases or []
    failed_cases = failed_cases or []
    no_update_cases = no_update_cases or []
    captcha_cases = captcha_cases or []
    if not (success_cases or failed_cases or no_update_cases or captcha_cases):
        return ""

    def _render_case_table(title, case_list):
        if not case_list:
            return ""
        
        table_style = 'border="1" cellpadding="4" cellspacing="0" style="border-collapse:collapse; width: 100%; max-width: 800px; margin-bottom: 20px;"'
        th_style = 'style="background-color: #f2f2f2; text-align: left;"'
        
        rows = [
            f"<h4>{title} ({len(case_list)}건)</h4>",
            f'<table {table_style}>',
            f'<tr><th {th_style} width="40%">사건번호</th><th {th_style} width="60%">피고/사건명</th></tr>'
        ]
        
        for case in case_list:
            if isinstance(case, dict):
                case_num = case.get("사건번호", "")
                defendant = case.get("피고", "")
                case_name = case.get("사건명", "")
                
                # 피고와 사건명을 조합 (둘 다 있으면 슬래시로 연결, 아니면 있는 것만)
                details = []
                if defendant: details.append(defendant)
                if case_name: details.append(case_name)
                detail_str = " / ".join(details)
                
                rows.append(
                    f'<tr>'
                    f'<td>{_esc_html(case_num)}</td>'
                    f'<td>{_esc_html(detail_str)}</td>'
                    f'</tr>'
                )
            else:
                # 문자열 등 구버전 호환용 대비
                rows.append(
                    f'<tr>'
                    f'<td>{_esc_html(str(case))}</td>'
                    f'<td>-</td>'
                    f'</tr>'
                )
        
        rows.append("</table>")
        return "\n".join(rows)

    parts = ["<h3>이번 조회 결과 요약</h3>"]
    parts.append(_render_case_table("성공", success_cases))
    parts.append(_render_case_table("성공(변경없음)", no_update_cases))
    parts.append(_render_case_table("실패", failed_cases))
    parts.append(_render_case_table("캡차(재시도 안 함)", captcha_cases))
    
    return "\n".join(parts)


def get_summary_html(
    success_cases=None,
    failed_cases=None,
    no_update_cases=None,
    captcha_cases=None,
):
    """
    미발송 내역을 구글 시트 색상을 반영한 HTML 표로 조합하여 반환.
    시트 이름(sheet_name)별로 그룹화. 메일 하단에 "이번 조회 결과" 푸터 추가.
    success_cases, failed_cases, no_update_cases, captcha_cases가 넘어오면 사용하고,
    없으면 저장된 last_run_result( set_last_run_result ) 사용.
    업데이트가 없어도 푸터만 있으면 HTML 반환. 반환: (html_string, last_sent_string)
    """
    data = load_unsent_emails()
    updates = data.get("updates", [])
    last_sent = data.get("last_sent", "") or "없음"

    # 푸터용: 인자로 넘어온 값이 없으면 캐시 사용
    use_success = success_cases if success_cases is not None else _last_run_result_cache.get("success_cases") or []
    use_failed = failed_cases if failed_cases is not None else _last_run_result_cache.get("failed_cases") or []
    use_no_update = no_update_cases if no_update_cases is not None else _last_run_result_cache.get("no_update_cases") or []
    use_captcha = captcha_cases if captcha_cases is not None else _last_run_result_cache.get("captcha_cases") or []
    has_footer = bool(use_success or use_failed or use_no_update or use_captcha)

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
            # 같은 사건(탭) 그룹 내 첫 번째로 유효한 sheet_url을 대표로 사용.
            # 구버전 JSON에는 sheet_url 키가 없을 수 있으므로 get()으로 방어적으로 접근.
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
                    f'바로가기 &rarr;</a></div>'
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
                    f'<tr>'
                    f'<td style="color:{dc}">{_esc_html(date)}</td>'
                    f'<td style="color:{cc}">{_esc_html(content)}</td>'
                    f'<td style="color:{rc}">{_esc_html(result)}</td>'
                    f'</tr>'
                )
            table = f'<table border="1" cellpadding="4" cellspacing="0" style="border-collapse:collapse;">{"".join(rows)}</table>'
            sections.append(table)
        body_parts.append(f"<h3>최신 업데이트 내역</h3>{'<br>'.join(sections)}")

    if has_footer:
        body_parts.append(_build_run_result_footer(use_success, use_failed, use_no_update, use_captcha))

    html = f"<html><body>{'<br>'.join(body_parts)}</body></html>"
    return html, last_sent
