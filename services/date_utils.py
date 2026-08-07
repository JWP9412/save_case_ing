# -*- coding: utf-8 -*-
"""
유연한 날짜 파서
================

주니어 개발자 참고:
사용자가 날짜를 어떻게 쓰든(26.08.06. / 2026/ 8/ 6 / 20260806 등)
datetime.date 로 바꿔 주는 유틸입니다. 실패하면 None 을 반환합니다.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Optional, Tuple


def parse_date(text) -> Optional[date]:
    """
    다양한 형식의 날짜 문자열을 date 로 변환합니다.

    지원 예:
      - 26.08.06. / 26/08/06. / 26-8-6
      - 2026.08.06 / 2026-08-06 / 2026/08/06
      - 2026. 8. 6. / 2026/ 8/ 6 (공백 포함)
      - 20260806 (구분자 없음)

    두 자리 연도: 기본적으로 2000+n.
    다만 그 결과가 '오늘+10년'보다 미래면 1900+n 으로 보정합니다.
    """
    if text is None:
        return None
    s = str(text).strip()
    if not s:
        return None

    # 끝의 마침표·공백 제거 반복
    s = s.strip(" .")
    if not s:
        return None

    # 숫자만 8자리면 YYYYMMDD
    digits_only = re.sub(r"\D", "", s)
    if len(digits_only) == 8 and re.fullmatch(r"\d{8}", digits_only):
        try:
            return date(
                int(digits_only[0:4]),
                int(digits_only[4:6]),
                int(digits_only[6:8]),
            )
        except ValueError:
            return None

    # . - / 공백을 구분자로 통일 → 숫자 토큰 추출
    normalized = re.sub(r"[.\-/\\\s]+", " ", s).strip()
    parts = [p for p in normalized.split(" ") if p]
    if len(parts) != 3:
        return None
    if not all(re.fullmatch(r"\d{1,4}", p) for p in parts):
        return None

    try:
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None

    # 두 자리 연도 보정
    if y < 100:
        y2000 = 2000 + y
        today = date.today()
        if y2000 > today.year + 10:
            y = 1900 + y
        else:
            y = y2000

    try:
        return date(y, m, d)
    except ValueError:
        return None


def format_date(d: date, sep: str = ".") -> str:
    """date → 'YYYY.MM.DD' 형식 문자열."""
    if d is None:
        return ""
    return f"{d.year:04d}{sep}{d.month:02d}{sep}{d.day:02d}"


def yesterday_today() -> Tuple[date, date]:
    """기본 기간: 어제 ~ 오늘."""
    today = date.today()
    return today - timedelta(days=1), today


def last_n_days(n: int = 7) -> Tuple[date, date]:
    """오늘 포함 최근 n일 (시작 = 오늘-(n-1))."""
    today = date.today()
    return today - timedelta(days=max(n, 1) - 1), today


def this_month() -> Tuple[date, date]:
    """이번 달 1일 ~ 오늘."""
    today = date.today()
    return date(today.year, today.month, 1), today


def in_period(row_date_text, start: date, end: date) -> bool:
    """
    진행내용 행의 date 문자열이 [start, end] 구간에 포함되는지 판별.
    파싱 실패 시 False.
    """
    d = parse_date(row_date_text)
    if d is None:
        return False
    return start <= d <= end


def parse_datetime_loose(text) -> Optional[datetime]:
    """'YYYY-MM-DD HH:MM:SS' 등 흔한 타임스탬프 파싱(실패 시 None)."""
    if not text:
        return None
    s = str(text).strip()
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y.%m.%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y.%m.%d",
    ):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    d = parse_date(s)
    if d:
        return datetime(d.year, d.month, d.day)
    return None
