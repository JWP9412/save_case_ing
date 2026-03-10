# -*- coding: utf-8 -*-
"""
정렬 관리 서비스
================

사건 목록(case_list)을 정렬 기준(열 인덱스, 오름차/내림차)과
history, search_log 데이터에 따라 정렬한 새 리스트를 반환하는 순수 로직.
GUI는 반환된 목록으로 case_list를 갱신한 뒤 UI만 다시 그린다.
"""


def sort_cases(case_list, sort_column_index, sort_reverse, history, search_log):
    """
    case_list를 정렬한 새 리스트를 반환.

    case_list: 사건 딕셔너리 리스트.
    sort_column_index: 정렬 기준 열 (1=법원/사건번호, 2=피고/사건명, 3=비고, 7=기록, 8=최근 업데이트).
    sort_reverse: True면 내림차순.
    history: load_update_history() 결과 딕셔너리.
    search_log: load_search_log() 결과 (사건번호 존재 여부 등).

    반환: 정렬된 새 리스트. 비어 있으면 입력 case_list의 복사본(그대로) 반환.
    """
    if not case_list:
        return list(case_list)

    def sort_key(case):
        cn = case.get("사건번호", "")
        if sort_column_index == 1:
            return f"{case.get('법원', '')} {case.get('사건번호', '')}".strip()
        if sort_column_index == 2:
            return f"{case.get('피고', '')} {case.get('사건명', '')}".strip()
        if sort_column_index == 3:
            return case.get("비고", "")
        if sort_column_index == 7:
            return 1 if cn in search_log else 0
        if sort_column_index == 8:
            data = history.get(cn, {})
            if isinstance(data, dict):
                return data.get("last_update", "1900-01-01 00:00:00")
            return data if isinstance(data, str) else "1900-01-01 00:00:00"
        return ""

    return sorted(case_list, key=sort_key, reverse=sort_reverse)
