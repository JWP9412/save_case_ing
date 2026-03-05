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
    this_dir = os.path.dirname(os.path.abspath(config.__file__))
    return os.path.join(this_dir, config.UNSENT_EMAILS_FILE)


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


def add_new_update(case_number, updates, sheet_name=""):
    """
    새로 업데이트된 진행내역을 미발송 목록에 추가.
    구글 시트에 적용되는 색상(dateColor, contentColor, resultColor)과 result를 함께 저장.
    sheet_name: 구글 시트 탭 이름(피고_사건명_번호_법원 등). 메일 본문 그룹화에 사용.

    case_number: 사건번호 문자열.
    updates: 진행내역 리스트. 각 항목은 dict with 'date', 'content', 'result',
             'dateColor', 'contentColor', 'resultColor' 등.
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
        })
    save_unsent_emails(data)


def clear_unsent_emails_and_update_last_sent(file_path=None):
    """
    발송 완료 후: updates를 비우고 last_sent를 현재 시간으로 갱신.
    """
    data = load_unsent_emails(file_path)
    data["updates"] = []
    data["last_sent"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_unsent_emails(data, file_path)


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


def get_summary_html():
    """
    미발송 내역을 구글 시트 색상을 반영한 HTML 표로 조합하여 반환.
    시트 이름(sheet_name)별로 그룹화하여 각 그룹마다 소제목(h4)과 표를 생성.
    메일 본문(htmlBody)으로 사용. 반환: (html_string, last_sent_string)
    """
    data = load_unsent_emails()
    updates = data.get("updates", [])
    last_sent = data.get("last_sent", "") or "없음"
    if not updates:
        return "", last_sent

    updates_by_sheet = {}
    for u in updates:
        s_name = u.get("sheet_name") or "기타"
        if s_name not in updates_by_sheet:
            updates_by_sheet[s_name] = []
        updates_by_sheet[s_name].append(u)

    sections = []
    for s_name, sheet_updates in updates_by_sheet.items():
        sections.append(f"<h4>{_esc_html(s_name)}</h4>")
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

    html = f"<html><body><h3>최신 업데이트 내역</h3>{'<br>'.join(sections)}</body></html>"
    return html, last_sent
