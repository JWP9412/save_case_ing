# -*- coding: utf-8 -*-
"""
기일 추출 및 Google Calendar 동기화 (HearingMixin)
==================================================
이 파일이 하는 일:
- 크롤링 결과에서 변론/감정/판결선고 기일을 추출합니다.
- 설정이 켜져 있으면 Google Calendar에 기일을 동기화합니다.

이 파일이 하지 않는 일:
- 시트 저장, 캡차 처리 (다른 mixin 담당)

주의:
- 달력 동기화 실패는 로그만 남기고 본 조회 흐름을 막지 않습니다.

"""

import hashlib
import os
import re
import subprocess as sp
import threading
import time
from datetime import datetime

import psutil

import config
from gui.utils import captcha_ui as captcha_ui_module
from services import captcha_ocr_service
from services import email_manager as email_manager_module
from services import google_calendar as google_calendar_module

class HearingMixin:
    """Mixin - self.app 을 통해 GUI/서비스에 접근."""

    @staticmethod
    def _normalize_text(text):
        """비교용: 공백 제거하여 중복 오판 방지."""
        if text is None:
            return ""
        return "".join(str(text).split())

    @staticmethod

    def _extract_hearing_from_result(result_data):
        """
        result_data(크롤링 결과 리스트)에서 최신 변론기일 또는 판결선고기일 하나만 추출.
        UI에는 최신 기일 하나만 표기하므로, 역순 순회 시 첫 매치 하나만 반환.
        반환: "변론기일 YY.MM.DD.(HH:MM)" 또는 "판결선고기일 YY.MM.DD.(HH:MM)" 형식 문자열, 없으면 None.
        """
        if not result_data or not isinstance(result_data, list):
            return None
        for i in range(len(result_data) - 1, -1, -1):
            row = result_data[i]
            if not isinstance(row, dict):
                continue
            raw_date = (row.get("date") or "").strip()
            raw_content = (row.get("content") or "").strip()
            if not raw_content:
                continue
            raw_content = re.sub(r"\s+", " ", raw_content)
            m = re.search(
                r"(변론기일|감정기일|판결선고기일).*?([0-9]{1,2}:[0-9]{2})",
                raw_content,
                re.DOTALL,
            )
            if not m:
                continue
            kind = m.group(1)
            time_str = m.group(2)
            formatted_date = ""
            if raw_date:
                parts = raw_date.replace("-", ".").split(".")
                if len(parts) >= 3:
                    y = parts[0].strip()
                    if len(y) >= 4:
                        y = y[-2:]
                    formatted_date = f"{y}.{parts[1].strip()}.{parts[2].strip()}."
            if formatted_date:
                return f"{kind} {formatted_date}({time_str})"
            return f"{kind}({time_str})"
        return None

    @staticmethod

    def _parse_datetime_from_row(raw_date, time_str):
        raw_date = (raw_date or "").strip()
        if not raw_date:
            return None
        parts = raw_date.replace("-", ".").split(".")
        if len(parts) < 3:
            return None
        try:
            y = int(parts[0].strip())
            mo = int(parts[1].strip())
            d = int(parts[2].strip())
            hh, mm = time_str.split(":")
            hh = int(hh)
            mm = int(mm)
            if y < 10:
                y = 2020 + y
            elif y < 100:
                y = 2000 + y
            return datetime(y, mo, d, hh, mm)
        except (TypeError, ValueError):
            return None

    @classmethod

    def _extract_hearing_events_from_result(cls, result_data):
        """
        result_data에서 캘린더 등록용 기일 이벤트 목록을 추출.
        반환: [{"kind": str, "start_dt": datetime, "label": str}, ...]
        """
        if not isinstance(result_data, list):
            return []
        events = []
        seen = set()
        for row in result_data:
            if not isinstance(row, dict):
                continue
            raw_content = re.sub(r"\s+", " ", (row.get("content") or "").strip())
            if not raw_content:
                continue
            raw_date = (row.get("date") or "").strip()
            for m in re.finditer(
                r"(변론기일|감정기일|판결선고기일).*?([0-9]{1,2}:[0-9]{2})",
                raw_content,
                re.DOTALL,
            ):
                kind = m.group(1)
                time_str = m.group(2)
                start_dt = cls._parse_datetime_from_row(raw_date, time_str)
                if start_dt is None:
                    continue
                key = (kind, start_dt.isoformat())
                if key in seen:
                    continue
                seen.add(key)
                events.append(
                    {
                        "kind": kind,
                        "start_dt": start_dt,
                        "label": f"{kind} {start_dt.strftime('%y.%m.%d.(%H:%M)')}",
                    }
                )
        return events


    def _maybe_sync_hearing_calendar(self, case, result_data):
        if int(getattr(config, "GOOGLE_CALENDAR_ENABLED", 1)) != 1:
            return
        events = self._extract_hearing_events_from_result(result_data)
        if not events:
            return
        try:
            res = google_calendar_module.sync_hearing_events(
                case, events, log_callback=self.app.log_message
            )
            self.app.log_message(
                "📅 캘린더 동기화 완료: 생성 %s / 갱신 %s / 건너뜀 %s"
                % (res.get("created", 0), res.get("updated", 0), res.get("skipped", 0))
            )
        except Exception as e:
            self.app.log_message(f"⚠️ 캘린더 동기화 실패: {e}")

