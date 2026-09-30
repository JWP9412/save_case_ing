# -*- coding: utf-8 -*-
"""알림메일 분할/안전절단 스모크 테스트.

사건 단위 패킹:
- 업데이트+결과변경이 작으면 1통 (섹션으로 갈라지지 않음)
- 기록이 많은 사건이 먼저
- 한 사건이 한도를 넘을 때만 '(이어짐 N)', 짧은 사건은 한 통에만
"""
import os
import tempfile

from services import email_manager as em

LONG_NAME = "롯데_부산 부암1구역 입대의_2025가합41096_부산지방법원"
SHORT_NAME = "롯데_부산 부암1구역 조합_2025가합41087_부산지방법원"
MAX_CHARS = 49000


def _use_temp_store():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    em._get_path = lambda: path
    return path


def _update_row(sheet_name, content, case="2025가합41096"):
    return {
        "case": case,
        "date": "2026.09.29",
        "content": content,
        "result": "",
        "dateColor": "rgb(204, 102, 0)",
        "contentColor": "rgb(204, 102, 0)",
        "resultColor": "rgb(0,0,0)",
        "sheet_name": sheet_name,
        "sheet_url": "https://docs.google.com/spreadsheets/d/abc/edit#gid=1",
    }


def _change_row(sheet_name, content, case="2025가합41096"):
    return {
        "case": case,
        "date": "2026.09.28",
        "content": content,
        "old_result": "",
        "result": "위의 '확인' 항목 체크",
        "dateColor": "rgb(204, 102, 0)",
        "contentColor": "rgb(204, 102, 0)",
        "resultColor": "rgb(204, 102, 0)",
        "sheet_name": sheet_name,
        "sheet_url": "https://docs.google.com/spreadsheets/d/abc/edit#gid=1",
    }


def _assert_parts_fit(parts):
    assert parts, "메일이 비어 있으면 안 됩니다"
    for i, part in enumerate(parts, 1):
        assert len(part) <= MAX_CHARS, f"part {i} too long: {len(part)}"
        assert "메일" in part and f"{i}/{len(parts)}" in part
    assert "이번 조회 결과 요약" in parts[-1], "footer는 마지막 메일"
    assert all("이번 조회 결과 요약" not in p for p in parts[:-1])


def test_small_cases_stay_one_mail(path):
    """업데이트·결과변경이 둘 다 있어도, 짧으면 1통이고 긴 사건이 위입니다."""
    updates = []
    changes = []
    for i in range(6):
        updates.append(_update_row(LONG_NAME, f"기일변경 송달 행 {i}", "2025가합41096"))
    for i in range(2):
        updates.append(_update_row(SHORT_NAME, f"보조참가 행 {i}", "2025가합41087"))
    for i in range(3):
        changes.append(_change_row(LONG_NAME, f"감정 통지 {i}", "2025가합41096"))
    changes.append(_change_row(SHORT_NAME, "소송고지 송달", "2025가합41087"))

    em.save_unsent_emails(
        {
            "last_sent": "없음",
            "updates": updates,
            "result_changes": changes,
            "run_results": {
                "2025가합41096": {
                    "상태": em.STATUS_SUCCESS,
                    "피고": "롯데",
                    "사건명": "입대의",
                    "사건번호": "2025가합41096",
                },
                "2025가합41087": {
                    "상태": em.STATUS_RESULT_CHANGED,
                    "피고": "롯데",
                    "사건명": "조합",
                    "사건번호": "2025가합41087",
                },
            },
        },
        path,
    )
    parts, _ = em.get_summary_html_parts(
        all_cases=[
            {"사건번호": "2025가합41096", "피고": "롯데", "사건명": "입대의"},
            {"사건번호": "2025가합41087", "피고": "롯데", "사건명": "조합"},
        ]
    )
    print("small parts:", len(parts), [len(p) for p in parts])
    _assert_parts_fit(parts)
    assert len(parts) == 1, "짧은 두 사건은 업데이트/결과변경으로 갈라지면 안 됩니다"
    html = parts[0]
    assert html.find(LONG_NAME) != -1 and html.find(SHORT_NAME) != -1
    assert html.find(LONG_NAME) < html.find(SHORT_NAME), "기록이 많은 사건이 위"
    # 같은 사건은 카드(시트명) 하나. 업데이트/결과변경을 카드 둘로 나누지 않습니다.
    assert html.count(LONG_NAME) == 1, html.count(LONG_NAME)
    assert html.count(SHORT_NAME) == 1, html.count(SHORT_NAME)
    assert "최신 업데이트" in html and "결과 변경" in html
    assert "font-weight:800" in html
    assert "이어짐" not in html


def test_long_case_continues_short_case_once(path):
    """한 사건만 길면 그 사건만 이어지고, 짧은 사건은 한 통에만 나옵니다."""
    updates = []
    for i in range(80):
        updates.append(
            _update_row(
                LONG_NAME,
                ("피고지인 " + ("O" * 40) + f"에게 송달 부본 발송 테스트 행 {i} ") * 3,
                "2025가합41096",
            )
        )
    updates.append(_update_row(SHORT_NAME, "짧은 내용", "2025가합41087"))
    changes = [
        _change_row(LONG_NAME, f"결과변경 행 {i}", "2025가합41096") for i in range(4)
    ]

    em.save_unsent_emails(
        {
            "last_sent": "없음",
            "updates": updates,
            "result_changes": changes,
            "run_results": {
                "2025가합41096": {
                    "상태": em.STATUS_SUCCESS,
                    "피고": "롯데",
                    "사건명": "입대의",
                    "사건번호": "2025가합41096",
                },
                "2025가합41087": {
                    "상태": em.STATUS_NO_UPDATE,
                    "피고": "홍길동",
                    "사건명": "대여금",
                    "사건번호": "2025가합41087",
                },
            },
        },
        path,
    )
    parts, _ = em.get_summary_html_parts(
        all_cases=[
            {"사건번호": "2025가합41096", "피고": "롯데", "사건명": "입대의"},
            {"사건번호": "2025가합41087", "피고": "홍길동", "사건명": "대여금"},
        ]
    )
    print("long parts:", len(parts), [len(p) for p in parts])
    _assert_parts_fit(parts)
    assert len(parts) >= 2, "긴 사건은 2통 이상"
    assert any("이어짐" in p for p in parts), "한도 초과 사건에만 이어짐 표시"
    assert parts[0].find(LONG_NAME) != -1, "첫 메일은 가장 긴 사건"
    short_hits = [i for i, p in enumerate(parts) if SHORT_NAME in p]
    assert len(short_hits) == 1, f"짧은 사건은 한 통에만: {short_hits}"
    # 긴 사건의 첫 등장보다 짧은 사건이 앞에 오면 안 됩니다.
    first_long = next(i for i, p in enumerate(parts) if LONG_NAME in p)
    assert first_long < short_hits[0] or (
        first_long == short_hits[0] and parts[first_long].find(LONG_NAME) < parts[first_long].find(SHORT_NAME)
    )


def test_safe_trim():
    huge = "<html><body>" + ("가" * 100000) + "</body></html>"
    trimmed, omitted = em.safe_trim_html(huge, 49000)
    assert omitted > 0
    assert "이하" in trimmed and "생략" in trimmed
    idx = trimmed.find("이하")
    before = trimmed[max(0, idx - 150) : idx]
    assert '<td style="padding:10px 6px; font-family' not in before, before
    print("OK safe_trim omitted", omitted, "trim_len", len(trimmed))


def main():
    path = _use_temp_store()
    try:
        test_small_cases_stay_one_mail(path)
        test_long_case_continues_short_case_once(path)
        test_safe_trim()
    finally:
        if os.path.exists(path):
            os.remove(path)
    print("ALL OK")


if __name__ == "__main__":
    main()
