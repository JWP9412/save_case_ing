#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
일반내용 로컬 저장소
====================

역할: 대법원 '일반내용' 화면에서 긁어온 데이터를 data/general_info.json 에 저장/조회.
호출: ProcessController가 사건 조회 직후 저장, GeneralInfoDialog가 돋보기 창에서 조회.

주니어 개발자 참고:
- update_history.json 은 진행내용 이력 전용이라 스키마를 섞지 않고 파일을 분리합니다.
- include_parties=False 이면 당사자/대리인 필드는 건드리지 않습니다
  (평소 자동 저장과 '당사자·대리인만 새로고침'을 구분하기 위함).
"""

import json
import os
from datetime import datetime
from copy import deepcopy

import config


def _file_path(file_path=None):
    return file_path or config.GENERAL_INFO_FILE


def load_general_info(file_path=None):
    """
    일반내용 JSON 전체를 읽어옵니다.

    반환: { 사건번호: { updated_at, basic, recent_hearings, ... }, ... }
    파일이 없거나 깨졌으면 빈 dict.
    """
    path = _file_path(file_path)
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        return {}
    except Exception:
        return {}


def save_general_info(store, file_path=None):
    """일반내용 JSON 전체를 파일에 씁니다."""
    path = _file_path(file_path)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)


def get_case_general_info(case_number, file_path=None):
    """
    사건 하나분의 일반내용을 반환합니다.

    case_number: 사건번호 문자열
    반환: dict 또는 None (없으면)
    """
    if not case_number:
        return None
    store = load_general_info(file_path)
    entry = store.get(str(case_number).strip())
    return entry if isinstance(entry, dict) else None


def save_case_general_info(case_number, data, include_parties=False, file_path=None):
    """
    사건 하나분의 일반내용을 저장합니다.

    case_number: 사건번호
    data: Node에서 받은 generalInfo dict
          (basic, recent_hearings, recent_documents, parties, attorneys)
    include_parties:
      - True  → parties / attorneys / parties_updated_at 도 덮어씀
      - False → 기존 당사자·대리인 정보는 보존하고
                basic / recent_hearings / recent_documents 만 갱신

    반환: 저장된 entry dict. 실패 시 None.
    """
    if not case_number or not isinstance(data, dict):
        return None

    cn = str(case_number).strip()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        store = load_general_info(file_path)
        prev = store.get(cn) if isinstance(store.get(cn), dict) else {}

        entry = {
            "updated_at": now,
            "basic": data.get("basic") if isinstance(data.get("basic"), dict) else {},
            "recent_hearings": (
                data.get("recent_hearings")
                if isinstance(data.get("recent_hearings"), list)
                else []
            ),
            "recent_documents": (
                data.get("recent_documents")
                if isinstance(data.get("recent_documents"), list)
                else []
            ),
        }

        if include_parties:
            entry["parties"] = (
                data.get("parties") if isinstance(data.get("parties"), list) else []
            )
            entry["attorneys"] = (
                data.get("attorneys") if isinstance(data.get("attorneys"), list) else []
            )
            entry["parties_updated_at"] = now
        else:
            # 기존 당사자·대리인 보존
            entry["parties"] = deepcopy(prev.get("parties") or [])
            entry["attorneys"] = deepcopy(prev.get("attorneys") or [])
            entry["parties_updated_at"] = prev.get("parties_updated_at") or ""

        store[cn] = entry
        save_general_info(store, file_path)
        return entry
    except Exception:
        return None
