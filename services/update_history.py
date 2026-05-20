#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
업데이트 기록 서비스
====================

역할: 사건별 "마지막 업데이트 일시"와 "행 개수"를 JSON 파일에 저장/불러오기.
호출 시점: app_controller에서 사건 처리 완료 시 기록 저장, 사건 목록 UI에서 D+n 표시 시 load + get_days_since_update 로 조회.
파일 위치: config.UPDATE_HISTORY_FILE (기본 update_history.json).
"""

import re
import json
import os
from datetime import datetime, date

import config


def load_update_history(file_path=None):
    """
    로컬 업데이트 기록 파일에서 딕셔너리 로드.

    file_path: 기록 파일 경로. None이면 config.UPDATE_HISTORY_FILE 사용.
    반환: { 사건번호: {"last_update": "YYYY-MM-DD HH:MM:SS", "row_count": N }, ... } 또는 {}
    """
    path = file_path or config.UPDATE_HISTORY_FILE
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception:
        return {}


def save_update_history(history, file_path=None):
    """
    로컬 업데이트 기록을 파일에 저장.

    history: load_update_history()와 같은 형식의 딕셔너리.
    file_path: None이면 config.UPDATE_HISTORY_FILE 사용.
    """
    path = file_path or config.UPDATE_HISTORY_FILE
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_days_since_update(case, history):
    """
    해당 사건의 마지막 업데이트 이후 경과 일수.

    case: {"사건번호": "..."} 형태의 딕셔너리.
    history: load_update_history()로 얻은 딕셔너리.
    반환: 경과 일수 (int). 기록 없거나 오류 시 -1.
    """
    try:
        case_number = case.get("사건번호", "")
        if case_number not in history:
            return -1

        data = history[case_number]
        if isinstance(data, str):
            last_update_str = data
        else:
            last_update_str = data.get("last_update", "")

        if not last_update_str:
            return -1

        last_update = datetime.strptime(last_update_str, "%Y-%m-%d %H:%M:%S")
        days_diff = (datetime.now() - last_update).days
        return days_diff
    except Exception:
        return -1


def get_days_until_hearing(hearing_info):
    """
    기일 문자열에서 날짜를 파싱하여 오늘로부터 기일까지의 일수 반환.

    hearing_info: "변론기일 26.03.11.(14:00)" 또는 "판결선고기일 26.03.11.(14:00)" 형식.
    반환: (hearing_date - today).days. 미래면 양수, 당일 0, 과거면 음수. 파싱 실패 시 None.
    """
    if not hearing_info or not isinstance(hearing_info, str):
        return None
    s = hearing_info.strip()
    # Y.MM.DD, YY.MM.DD 또는 YYYY.MM.DD 패턴 추출 (괄호 앞까지)
    m = re.search(r"(\d{1,4})\.(\d{1,2})\.(\d{1,2})\.?", s)
    if not m:
        return None
    try:
        y_str, mo_str, d_str = m.group(1), m.group(2), m.group(3)
        y = int(y_str)
        mo = int(mo_str)
        d = int(d_str)
        if y < 10:
            y = 2020 + y
        elif y < 100:
            y = 2000 + y
        if not (1 <= mo <= 12 and 1 <= d <= 31):
            return None
        hearing_date = date(y, mo, d)
        return (hearing_date - date.today()).days
    except (ValueError, TypeError):
        return None


def update_case_record(case_number, row_count, history, is_auto=False, hearing_info=None):
    """
    사건번호에 대한 업데이트 기록(시간 + 행 개수 + 자동여부 + 기일정보)을 갱신한 새 딕셔너리 반환.

    case_number: 사건번호 문자열.
    row_count: 저장된 진행내용 행 개수.
    history: load_update_history()로 얻은 딕셔너리 (수정하지 않음).
    is_auto: 자동 조회 여부 (기본 False).
    hearing_info: 기일 정보 문자열 (예: "판결선고기일 26.03.11.(14:00)"). None이면 기존 값 유지.
    반환: 갱신된 새 딕셔너리 (원본 history와 동일 참조가 아닌 복사본).
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_history = dict(history)
    existing = new_history.get(case_number) if isinstance(new_history.get(case_number), dict) else {}
    keep_keys = ("last_entry", "hearing_info")
    merged = {k: v for k, v in existing.items() if k in keep_keys}
    record = {
        "last_update": current_time,
        "row_count": row_count,
        "is_auto": is_auto,
        **merged,
    }
    if hearing_info is not None:
        record["hearing_info"] = hearing_info
    new_history[case_number] = record
    return new_history


# =============================================================================
# HistoryManager: 증분 업데이트용 "마지막 저장 항목" 저장/로드
# =============================================================================


class HistoryManager:
    """
    로컬 캐시(update_history.json)를 이용해 사건별 마지막 저장 항목을 관리.
    증분 업데이트 시 '그 다음 행부터' 필터링하기 위해 사용.
    """

    def __init__(self, file_path=None):
        self.file_path = file_path or config.UPDATE_HISTORY_FILE

    def load_history(self):
        """
        기록 파일에서 전체 딕셔너리 로드.
        파일이 없거나 오류 시 빈 딕셔너리 반환.
        """
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def get_last_entry(self, case_number):
        """
        해당 사건의 마지막 저장된 항목(일자, 내용 등) 반환.
        증분 필터링 시 기준점으로 사용.

        case_number: 사건번호 문자열.
        반환: {"date": "...", "content": "...", "result": "...", "document": "..."} 또는 None
        """
        history = self.load_history()
        case_data = history.get(case_number)
        if not case_data or not isinstance(case_data, dict):
            return None
        return case_data.get("last_entry")

    def update_last_entry(self, case_number, last_row_data):
        """
        저장 성공 시 해당 사건의 마지막 항목을 파일에 기록.

        case_number: 사건번호 문자열.
        last_row_data: 마지막 행 데이터 딕셔너리 (date, content, result, document 키 포함).
        """
        history = self.load_history()
        if case_number not in history or not isinstance(history[case_number], dict):
            history[case_number] = {}
        history[case_number]["last_entry"] = {
            "date": last_row_data.get("date", ""),
            "content": last_row_data.get("content", ""),
            "result": last_row_data.get("result", ""),
            "document": last_row_data.get("document", ""),
        }
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def clear_last_entry(self, case_number):
        """
        해당 사건의 증분 저장 기준점(last_entry)과 행 개수(row_count)를 초기화합니다.

        주니어 개발자 참고:
        - '기록 초기화 및 재수집' 시 호출하여, 다음 저장이 처음부터 전체 데이터로
          인식되도록 합니다.
        - update_history.json의 같은 사건 키에 last_entry·row_count가 함께 있을 수 있습니다.
        """
        history = self.load_history()
        if case_number not in history:
            return
        case_data = history.get(case_number)
        if not isinstance(case_data, dict):
            history.pop(case_number, None)
        else:
            case_data.pop("last_entry", None)
            case_data.pop("row_count", None)
            if not case_data:
                history.pop(case_number, None)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
