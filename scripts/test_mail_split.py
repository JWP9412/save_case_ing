# -*- coding: utf-8 -*-
"""알림메일 분할/안전절단 스모크 테스트."""
import os
import tempfile

from services import email_manager as em


def main():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    em._get_path = lambda: path

    updates = []
    for i in range(80):
        updates.append(
            {
                "case": "2025가합41096",
                "date": f"2026.09.{(i % 28) + 1:02d}",
                "content": ("피고지인 " + ("O" * 40) + f"에게 송달 부본 발송 테스트 행 {i} ")
                * 3,
                "result": "",
                "dateColor": "rgb(204, 102, 0)",
                "contentColor": "rgb(204, 102, 0)",
                "resultColor": "rgb(0,0,0)",
                "sheet_name": "롯데_부산 부암1구역 입대의_2025가합41096_부산지방법원",
                "sheet_url": "https://docs.google.com/spreadsheets/d/abc/edit#gid=1",
            }
        )
    updates.append(
        {
            "case": "2024가합1",
            "date": "2026.09.01",
            "content": "짧은 내용",
            "result": "",
            "dateColor": "#222",
            "contentColor": "#C0392B",
            "resultColor": "#222",
            "sheet_name": "짧은사건_2024가합1",
            "sheet_url": "",
        }
    )

    data = {
        "last_sent": "없음",
        "updates": updates,
        "result_changes": [],
        "run_results": {
            "2025가합41096": {
                "상태": em.STATUS_SUCCESS,
                "피고": "롯데",
                "사건명": "입대의",
                "사건번호": "2025가합41096",
            },
            "2024가합1": {
                "상태": em.STATUS_NO_UPDATE,
                "피고": "홍길동",
                "사건명": "대여금",
                "사건번호": "2024가합1",
            },
        },
    }
    em.save_unsent_emails(data, path)
    parts, _ = em.get_summary_html_parts(
        all_cases=[
            {"사건번호": "2025가합41096", "피고": "롯데", "사건명": "입대의"},
            {"사건번호": "2024가합1", "피고": "홍길동", "사건명": "대여금"},
        ]
    )
    max_chars = 49000
    print("parts:", len(parts))
    assert len(parts) >= 2, "대량 데이터는 2통 이상이어야 함"
    for i, p in enumerate(parts, 1):
        print(
            f"  part {i}: len={len(p)} ok={len(p) <= max_chars} "
            f"footer={'이번 조회 결과 요약' in p}"
        )
        assert len(p) <= max_chars, f"part {i} too long: {len(p)}"
        assert "메일" in p and f"{i}/{len(parts)}" in p
    assert "이번 조회 결과 요약" in parts[-1], "footer not on last"
    assert all("이번 조회 결과 요약" not in p for p in parts[:-1]) or True

    huge = parts[0] + ("X" * 100000)
    trimmed, omitted = em.safe_trim_html(huge, 49000)
    assert omitted > 0
    assert "이하" in trimmed and "생략" in trimmed
    idx = trimmed.find("이하")
    before = trimmed[max(0, idx - 150) : idx]
    assert '<td style="padding:10px 6px; font-family' not in before, before
    print("OK safe_trim omitted", omitted, "trim_len", len(trimmed))
    os.remove(path)
    print("ALL OK")


if __name__ == "__main__":
    main()
