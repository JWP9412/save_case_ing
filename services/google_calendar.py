# -*- coding: utf-8 -*-
"""
Google Calendar 연동 서비스
==========================

기일 이벤트를 중복 없이 upsert(있으면 갱신, 없으면 생성)합니다.
"""

import hashlib
from datetime import timedelta

import config

from services import google_oauth


def _make_service(log_callback=None):
    try:
        from googleapiclient.discovery import build
    except Exception as e:
        if callable(log_callback):
            log_callback(f"⚠️ Calendar API 모듈 미설치: {e}")
        return None
    creds = google_oauth.get_credentials(interactive=False, log_callback=log_callback)
    if creds is None:
        return None
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _event_key(case_number, kind, start_iso):
    raw = f"{case_number}|{kind}|{start_iso}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()


def _format_template(template_text, context, fallback, log_callback=None):
    try:
        rendered = str(template_text or "").format(**context).strip()
        return rendered or fallback
    except Exception as e:
        if callable(log_callback):
            log_callback(f"⚠️ 캘린더 템플릿 포맷 실패: {e}")
        return fallback


def sync_hearing_events(case, hearing_events, log_callback=None):
    """
    case: 사건 dict
    hearing_events: [{"kind","start_dt","label"}...]
    """
    if not hearing_events:
        return {"created": 0, "updated": 0, "skipped": 0}
    service = _make_service(log_callback=log_callback)
    if service is None:
        return {"created": 0, "updated": 0, "skipped": len(hearing_events)}

    calendar_id = (getattr(config, "GOOGLE_CALENDAR_ID", "primary") or "primary").strip()
    duration_min = max(5, int(getattr(config, "GOOGLE_CALENDAR_EVENT_DURATION_MINUTES", 60)))
    tz = getattr(config, "GOOGLE_CALENDAR_TIMEZONE", "Asia/Seoul")

    case_number = str(case.get("사건번호", "")).strip()
    defendant = str(case.get("피고", "")).strip()
    case_name = str(case.get("사건명", "")).strip()
    court = str(case.get("법원", "")).strip()
    summary_prefix = f"[case-ing] {case_number}".strip()
    desc = f"피고: {defendant}\n사건명: {case_name}\n법원: {court}".strip()

    created = 0
    updated = 0
    skipped = 0
    for ev in hearing_events:
        start_dt = ev["start_dt"]
        end_dt = start_dt + timedelta(minutes=duration_min)
        kind = ev["kind"]
        key = _event_key(case_number, kind, start_dt.isoformat())
        context = {
            "case_number": case_number,
            "defendant": defendant,
            "case_name": case_name,
            "court": court,
            "kind": kind,
            "start_date": start_dt.strftime("%Y-%m-%d"),
            "start_time": start_dt.strftime("%H:%M"),
            "label": str(ev.get("label", "") or "").strip(),
            "start_iso": start_dt.isoformat(),
        }
        fallback_summary = f"{summary_prefix} {kind}".strip()
        fallback_desc = desc
        summary_template = getattr(
            config, "GOOGLE_CALENDAR_SUMMARY_TEMPLATE", fallback_summary
        )
        desc_template = getattr(
            config, "GOOGLE_CALENDAR_DESCRIPTION_TEMPLATE", fallback_desc
        )
        summary = _format_template(
            summary_template, context, fallback_summary, log_callback=log_callback
        )
        final_desc = _format_template(
            desc_template, context, fallback_desc, log_callback=log_callback
        )
        body = {
            "summary": summary.strip() or fallback_summary,
            "description": final_desc,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": tz},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": tz},
            "extendedProperties": {"private": {"case_ing_key": key}},
        }
        try:
            found = (
                service.events()
                .list(
                    calendarId=calendar_id,
                    privateExtendedProperty=[f"case_ing_key={key}"],
                    maxResults=1,
                    singleEvents=True,
                )
                .execute()
            )
            items = found.get("items", []) if isinstance(found, dict) else []
            if items:
                event_id = items[0].get("id")
                service.events().patch(
                    calendarId=calendar_id,
                    eventId=event_id,
                    body=body,
                ).execute()
                updated += 1
            else:
                service.events().insert(calendarId=calendar_id, body=body).execute()
                created += 1
        except Exception as e:
            skipped += 1
            if callable(log_callback):
                log_callback(f"⚠️ 캘린더 등록 실패({kind}): {e}")
    return {"created": created, "updated": updated, "skipped": skipped}
