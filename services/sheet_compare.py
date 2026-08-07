# -*- coding: utf-8 -*-
"""
시트 ↔ 대법원 진행내용 대조
===========================

주니어 개발자 참고:
- google_sheets._sheet_row_dedup_key(일자·내용·결과·공시문 4열)로 '완전 일치' 판별
- _sheet_row_dc_key(일자+내용)로 '유사(결과만 다름)' 판별
- 기간 리포트용: 각 행이 시트에 있는지 표시 (있음/유사/없음)
- 전체 대조용: 시트에만 / 대법원에만 / 일치 / 결과만 다름
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from services.google_sheets import GoogleSheetsService


Presence = str  # "있음" | "유사" | "없음"


def _sheet_progress_rows(all_values: List[List[str]]) -> List[List[str]]:
    """헤더·업데이트 일시 행을 제외한 진행내용 행만."""
    if not all_values:
        return []
    rows = []
    for row in all_values[1:]:
        if GoogleSheetsService._is_progress_data_row(row):
            rows.append(row)
    return rows


def build_sheet_key_sets(all_values: List[List[str]]):
    """
    시트 값에서 4열 키 / (일자+내용) 키 집합을 만듭니다.
    반환: (full_keys: set, dc_keys: set, full_counter: Counter, rows_by_full, rows_by_dc)
    """
    full_keys = set()
    dc_keys = set()
    full_counter = Counter()
    rows_by_full = {}
    rows_by_dc = {}
    for row in _sheet_progress_rows(all_values):
        fk = GoogleSheetsService._sheet_row_dedup_key(row)
        dk = GoogleSheetsService._sheet_row_dc_key(row)
        full_keys.add(fk)
        dc_keys.add(dk)
        full_counter[fk] += 1
        rows_by_full.setdefault(fk, []).append(row)
        rows_by_dc.setdefault(dk, []).append(row)
    return full_keys, dc_keys, full_counter, rows_by_full, rows_by_dc


def classify_row_presence(row_dict: dict, full_keys, dc_keys) -> Presence:
    """크롤링 dict 한 행이 시트에 있는지 분류."""
    fk = GoogleSheetsService._dict_row_dedup_key(row_dict)
    if fk in full_keys:
        return "있음"
    dk = GoogleSheetsService._dict_row_dc_key(row_dict)
    if dk in dc_keys:
        return "유사"
    return "없음"


def annotate_rows_with_sheet_presence(
    rows: List[dict], all_values: List[List[str]]
) -> Tuple[List[dict], Dict[str, int]]:
    """
    기간 리포트 행에 sheet_presence 필드를 붙입니다.
    반환: (annotated_rows, summary_counts)
    """
    full_keys, dc_keys, *_ = build_sheet_key_sets(all_values)
    counts = {"있음": 0, "유사": 0, "없음": 0}
    out = []
    for r in rows:
        presence = classify_row_presence(r, full_keys, dc_keys)
        counts[presence] = counts.get(presence, 0) + 1
        nr = dict(r)
        nr["sheet_presence"] = presence
        out.append(nr)
    return out, counts


def compare_court_and_sheet(
    court_rows: List[dict], all_values: List[List[str]]
) -> Dict[str, Any]:
    """
    대법원 크롤링 결과와 시트 전체 진행내용을 대조합니다.

    반환 예:
    {
      "matched": N,
      "sheet_only": [...],   # 시트에만 있는 행(리스트 of list)
      "court_only": [...],   # 대법원에만 있는 행(dict)
      "result_diff": [...],  # 일자+내용은 같지만 결과가 다른 쌍
      "verdict": "완전 일치" | "불일치 (차이 N건)",
      "diff_count": N,
    }
    """
    full_keys, dc_keys, sheet_counter, rows_by_full, rows_by_dc = build_sheet_key_sets(
        all_values
    )

    court_counter = Counter()
    court_by_full = {}
    court_by_dc = {}
    for r in court_rows or []:
        fk = GoogleSheetsService._dict_row_dedup_key(r)
        dk = GoogleSheetsService._dict_row_dc_key(r)
        court_counter[fk] += 1
        court_by_full.setdefault(fk, []).append(r)
        court_by_dc.setdefault(dk, []).append(r)

    # 일치: 양쪽에 같은 4열 키가 있는 개수(min)
    matched = 0
    all_full = set(sheet_counter.keys()) | set(court_counter.keys())
    sheet_only_keys = []
    court_only_keys = []
    for fk in all_full:
        sc = sheet_counter.get(fk, 0)
        cc = court_counter.get(fk, 0)
        matched += min(sc, cc)
        if sc > cc:
            for _ in range(sc - cc):
                sheet_only_keys.append(fk)
        elif cc > sc:
            for _ in range(cc - sc):
                court_only_keys.append(fk)

    sheet_only = []
    for fk in sheet_only_keys:
        rows = rows_by_full.get(fk) or []
        if rows:
            sheet_only.append(rows[0])

    court_only = []
    for fk in court_only_keys:
        rows = court_by_full.get(fk) or []
        if rows:
            court_only.append(rows[0])

    # 결과만 다름: 대법원 행의 dc 키가 시트에 있고, 4열 키는 시트에 없을 때
    result_diff = []
    seen_dc = set()
    for r in court_rows or []:
        fk = GoogleSheetsService._dict_row_dedup_key(r)
        dk = GoogleSheetsService._dict_row_dc_key(r)
        if fk in full_keys:
            continue
        if dk in dc_keys and dk not in seen_dc:
            seen_dc.add(dk)
            sheet_row = (rows_by_dc.get(dk) or [None])[0]
            result_diff.append({"court": r, "sheet": sheet_row})

    # court_only 에서 result_diff 로 빠진 것은 이미 '유사'로 분류된 것 — 중복 카운트 방지 위해
    # diff_count 는 sheet_only + court_only(유사 제외) + result_diff
    similar_court_fks = set()
    for item in result_diff:
        similar_court_fks.add(GoogleSheetsService._dict_row_dedup_key(item["court"]))
    court_only_strict = [
        r for r in court_only
        if GoogleSheetsService._dict_row_dedup_key(r) not in similar_court_fks
    ]

    diff_count = len(sheet_only) + len(court_only_strict) + len(result_diff)
    if diff_count == 0:
        verdict = "완전 일치"
    else:
        verdict = f"불일치 (차이 {diff_count}건)"

    return {
        "matched": matched,
        "sheet_only": sheet_only,
        "court_only": court_only_strict,
        "result_diff": result_diff,
        "verdict": verdict,
        "diff_count": diff_count,
        "sheet_count": sum(sheet_counter.values()),
        "court_count": sum(court_counter.values()),
    }


def fetch_sheet_values(gs: GoogleSheetsService, case: dict) -> List[List[str]]:
    """사건 탭 전체 값 읽기(없으면 [])."""
    try:
        return gs.get_full_sheet_data(case) or []
    except Exception:
        return []
