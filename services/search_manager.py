# -*- coding: utf-8 -*-
"""
검색 관리 서비스
================

사건 목록(case_list)에서 검색어와 일치하는 행 인덱스 목록을 반환하는 순수 로직.
GUI는 이 결과를 받아 스크롤/하이라이트 등 UI만 담당.
"""


def case_search_text(case):
    """사건 한 건을 검색 대상 문자열(소문자)로 변환."""
    return " ".join(
        [
            str(case.get("법원", "") or ""),
            str(case.get("사건번호", "") or ""),
            str(case.get("피고", "") or ""),
            str(case.get("사건명", "") or ""),
            str(case.get("비고", "") or ""),
        ]
    ).lower()


def find_match_indices(case_list, query):
    """
    검색어와 일치하는 사건 목록의 인덱스 리스트를 반환.

    case_list: 사건 딕셔너리 리스트.
    query: 검색어 문자열.
    반환: 일치하는 인덱스 리스트 (비어 있으면 []).
    """
    if not query or not case_list:
        return []
    q = query.strip().lower()
    return [i for i, c in enumerate(case_list) if q in case_search_text(c)]
