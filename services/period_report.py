# -*- coding: utf-8 -*-
"""
기간 조회 / 시트 대조 리포트 렌더러
===================================

HTML·Markdown 문자열을 만들어 미리보기·메일 발송에 사용합니다.
외부 템플릿 엔진 없이 순수 문자열 조합만 사용합니다.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from services.date_utils import format_date


def _esc(s) -> str:
    return (
        (s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _rgb(color) -> str:
    if not color or not isinstance(color, str):
        return "#000000"
    return color.strip()


def _case_title(case: dict) -> str:
    defendant = (case or {}).get("피고", "")
    name = (case or {}).get("사건명", "")
    cn = (case or {}).get("사건번호", "")
    parts = [p for p in (defendant, name, cn) if p]
    return " / ".join(parts) if parts else cn or "사건"


def render_period_html(
    period_results: Dict[str, dict],
    start: date,
    end: date,
    *,
    presence_summary: Optional[Dict[str, int]] = None,
) -> str:
    """
    period_results: {
      사건번호: {
        "case": {...},
        "rows": [ {date, content, result, ... sheet_presence?}, ... ],
        "sheet_url": optional,
      }, ...
    }
    """
    head = (
        f"<h3>[기간 조회] {format_date(start)} ~ {format_date(end)}</h3>"
    )
    if presence_summary:
        head += (
            "<p>시트 대조: "
            f"있음 {presence_summary.get('있음', 0)}건 / "
            f"유사 {presence_summary.get('유사', 0)}건 / "
            f"없음 {presence_summary.get('없음', 0)}건"
            "</p>"
        )

    sections = []
    for cn, payload in (period_results or {}).items():
        case = payload.get("case") or {"사건번호": cn}
        rows = payload.get("rows") or []
        title = _case_title(case)
        sections.append(f"<h4>{_esc(title)}</h4>")
        url = payload.get("sheet_url") or ""
        if url:
            sections.append(
                f'<div style="margin:-6px 0 8px 0;">'
                f'<a href="{_esc(url)}" target="_blank" '
                f'style="color:#1a73e8; text-decoration:none; font-size:13px;">'
                f"바로가기 &rarr;</a></div>"
            )
        if not rows:
            sections.append("<p>(해당 기간 기록 없음)</p>")
            continue
        has_presence = any("sheet_presence" in r for r in rows)
        hdr = "<tr><th>일자</th><th>내용</th><th>결과</th>"
        if has_presence:
            hdr += "<th>시트</th>"
        hdr += "</tr>"
        body = [hdr]
        for u in rows:
            dc = _rgb(u.get("dateColor"))
            cc = _rgb(u.get("contentColor"))
            rc = _rgb(u.get("resultColor"))
            line = (
                f"<tr>"
                f'<td style="color:{dc}">{_esc(u.get("date", ""))}</td>'
                f'<td style="color:{cc}">{_esc(u.get("content", ""))}</td>'
                f'<td style="color:{rc}">{_esc(u.get("result", ""))}</td>'
            )
            if has_presence:
                line += f"<td>{_esc(u.get('sheet_presence', ''))}</td>"
            line += "</tr>"
            body.append(line)
        sections.append(
            '<table border="1" cellpadding="4" cellspacing="0" '
            f'style="border-collapse:collapse;">{"".join(body)}</table>'
        )

    if not sections:
        sections.append("<p>조회된 기록이 없습니다.</p>")

    return f"<html><body>{head}<br>{'<br>'.join(sections)}</body></html>"


def render_period_markdown(
    period_results: Dict[str, dict],
    start: date,
    end: date,
    *,
    presence_summary: Optional[Dict[str, int]] = None,
) -> str:
    lines = [f"# [기간 조회] {format_date(start)} ~ {format_date(end)}", ""]
    if presence_summary:
        lines.append(
            f"- 시트 있음: {presence_summary.get('있음', 0)} / "
            f"유사: {presence_summary.get('유사', 0)} / "
            f"없음: {presence_summary.get('없음', 0)}"
        )
        lines.append("")
    for cn, payload in (period_results or {}).items():
        case = payload.get("case") or {"사건번호": cn}
        rows = payload.get("rows") or []
        lines.append(f"## {_case_title(case)}")
        lines.append("")
        if not rows:
            lines.append("(해당 기간 기록 없음)")
            lines.append("")
            continue
        has_presence = any("sheet_presence" in r for r in rows)
        if has_presence:
            lines.append("| 일자 | 내용 | 결과 | 시트 |")
            lines.append("| --- | --- | --- | --- |")
            for u in rows:
                lines.append(
                    f"| {u.get('date', '')} | {u.get('content', '')} | "
                    f"{u.get('result', '')} | {u.get('sheet_presence', '')} |"
                )
        else:
            lines.append("| 일자 | 내용 | 결과 |")
            lines.append("| --- | --- | --- |")
            for u in rows:
                lines.append(
                    f"| {u.get('date', '')} | {u.get('content', '')} | {u.get('result', '')} |"
                )
        lines.append("")
    return "\n".join(lines)


def _row_list_as_dict(row: list) -> dict:
    return {
        "date": row[0] if len(row) > 0 else "",
        "content": row[1] if len(row) > 1 else "",
        "result": row[2] if len(row) > 2 else "",
        "document": row[3] if len(row) > 3 else "",
    }


def render_compare_html(compare_results: Dict[str, dict]) -> str:
    """
    compare_results: {
      사건번호: {
        "case": {...},
        "diff": compare_court_and_sheet() 결과,
        "sheet_url": optional,
      }
    }
    """
    head = "<h3>[시트 대조] 시트 ↔ 대법원 전체 일치 여부</h3>"
    sections = []
    for cn, payload in (compare_results or {}).items():
        case = payload.get("case") or {"사건번호": cn}
        diff = payload.get("diff") or {}
        title = _case_title(case)
        verdict = diff.get("verdict", "")
        sections.append(f"<h4>{_esc(title)} — {_esc(verdict)}</h4>")
        sections.append(
            "<p>"
            f"시트 {diff.get('sheet_count', 0)}행 / "
            f"대법원 {diff.get('court_count', 0)}행 / "
            f"일치 {diff.get('matched', 0)}행"
            "</p>"
        )
        url = payload.get("sheet_url") or ""
        if url:
            sections.append(
                f'<div><a href="{_esc(url)}" target="_blank">바로가기 &rarr;</a></div>'
            )

        def _table(title_s, rows_dicts):
            if not rows_dicts:
                return f"<p><b>{_esc(title_s)}</b>: 없음</p>"
            body = ["<tr><th>일자</th><th>내용</th><th>결과</th></tr>"]
            for u in rows_dicts:
                body.append(
                    "<tr>"
                    f"<td>{_esc(u.get('date', ''))}</td>"
                    f"<td>{_esc(u.get('content', ''))}</td>"
                    f"<td>{_esc(u.get('result', ''))}</td>"
                    "</tr>"
                )
            return (
                f"<p><b>{_esc(title_s)}</b></p>"
                '<table border="1" cellpadding="4" cellspacing="0" '
                f'style="border-collapse:collapse;">{"".join(body)}</table>'
            )

        sheet_only = [_row_list_as_dict(r) for r in (diff.get("sheet_only") or [])]
        court_only = list(diff.get("court_only") or [])
        sections.append(_table("시트에만 있음", sheet_only))
        sections.append(_table("대법원에만 있음", court_only))

        result_diff = diff.get("result_diff") or []
        if result_diff:
            body = [
                "<tr><th>구분</th><th>일자</th><th>내용</th><th>결과</th></tr>"
            ]
            for item in result_diff:
                court = item.get("court") or {}
                sheet = item.get("sheet")
                body.append(
                    "<tr><td>대법원</td>"
                    f"<td>{_esc(court.get('date', ''))}</td>"
                    f"<td>{_esc(court.get('content', ''))}</td>"
                    f"<td>{_esc(court.get('result', ''))}</td></tr>"
                )
                if sheet:
                    sd = _row_list_as_dict(sheet)
                    body.append(
                        "<tr><td>시트</td>"
                        f"<td>{_esc(sd.get('date', ''))}</td>"
                        f"<td>{_esc(sd.get('content', ''))}</td>"
                        f"<td>{_esc(sd.get('result', ''))}</td></tr>"
                    )
            sections.append(
                "<p><b>결과값만 다름</b></p>"
                '<table border="1" cellpadding="4" cellspacing="0" '
                f'style="border-collapse:collapse;">{"".join(body)}</table>'
            )

    if not sections:
        sections.append("<p>대조 결과가 없습니다.</p>")
    return f"<html><body>{head}<br>{'<br>'.join(sections)}</body></html>"


def render_compare_markdown(compare_results: Dict[str, dict]) -> str:
    lines = ["# [시트 대조] 시트 ↔ 대법원 전체 일치 여부", ""]
    for cn, payload in (compare_results or {}).items():
        case = payload.get("case") or {"사건번호": cn}
        diff = payload.get("diff") or {}
        lines.append(f"## {_case_title(case)} — {diff.get('verdict', '')}")
        lines.append(
            f"- 시트 {diff.get('sheet_count', 0)}행 / "
            f"대법원 {diff.get('court_count', 0)}행 / "
            f"일치 {diff.get('matched', 0)}행"
        )
        lines.append("")
        for label, rows in (
            ("시트에만 있음", [_row_list_as_dict(r) for r in (diff.get("sheet_only") or [])]),
            ("대법원에만 있음", list(diff.get("court_only") or [])),
        ):
            lines.append(f"### {label}")
            if not rows:
                lines.append("(없음)")
            else:
                lines.append("| 일자 | 내용 | 결과 |")
                lines.append("| --- | --- | --- |")
                for u in rows:
                    lines.append(
                        f"| {u.get('date', '')} | {u.get('content', '')} | {u.get('result', '')} |"
                    )
            lines.append("")
    return "\n".join(lines)
