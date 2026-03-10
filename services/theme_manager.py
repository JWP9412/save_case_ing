# -*- coding: utf-8 -*-
"""
테마 관리 서비스
================

테마 설정 로드/저장, CustomTkinter 적용, 현재 모드에 따른 색상·폰트 반환.
GUI는 이 모듈을 사용해 테마를 적용하고 get_theme_color로 색상을 조회합니다.
"""
import os
import json
import customtkinter as ctk
import config
from config import THEME


def load_theme_setting():
    """저장된 테마 설정 로드. 'Dark' / 'Light' / 'System' 중 하나 반환."""
    path = getattr(config, "THEME_CONFIG_FILE", "theme_config.json")
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            mode = data.get("appearance_mode") or data.get("mode")
            if mode in ("Dark", "Light", "System"):
                return mode
    except Exception:
        pass
    return "Dark"


def save_theme_setting(mode):
    """선택한 테마를 파일에 저장."""
    path = getattr(config, "THEME_CONFIG_FILE", "theme_config.json")
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"appearance_mode": mode}, f, indent=2)
    except Exception:
        pass


def apply_theme(mode):
    """
    CustomTkinter에 테마 적용.
    반환: 현재 유효 모드의 THEME 인덱스 (0=라이트, 1=다크).
    """
    ctk.set_appearance_mode(mode)
    effective = ctk.get_appearance_mode()
    return 1 if effective == "Dark" else 0


def get_theme_color(key, theme_index):
    """
    테마 키에 해당하는 색상 또는 폰트 반환.
    THEME 값이 (light, dark) 튜플이면 theme_index(0 또는 1)에 맞는 값 반환.
    """
    v = THEME.get(key)
    if (
        isinstance(v, tuple)
        and len(v) >= 2
        and isinstance(v[0], str)
        and v[0].startswith("#")
    ):
        return v[theme_index]
    return v
