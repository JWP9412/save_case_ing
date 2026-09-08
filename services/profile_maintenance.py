# -*- coding: utf-8 -*-
"""
Chrome 프로필 캐시 · 스크린샷 자동 정리
======================================
스마트 스킵에 필요한 Cookies/History 는 남기고,
Cache·Code Cache 등만 삭제해 디스크·메모리를 줄입니다.
"""
from __future__ import annotations

import os
import shutil
import time
from typing import Callable, Optional

import config

LogFn = Optional[Callable[[str], None]]


def _log(log_fn: LogFn, msg: str) -> None:
    if log_fn:
        try:
            log_fn(msg)
            return
        except Exception:
            pass
    # fallback
    try:
        from services.logger_service import get_logger

        get_logger("profile_maintenance").info(msg)
    except Exception:
        pass


def _cookie_root() -> str:
    rel = getattr(config, "COOKIE_DATA_DIR", "cookie_data_for_save")
    if hasattr(config, "path_from_base"):
        return config.path_from_base(rel)
    return os.path.abspath(rel)


def _screenshots_dir() -> str:
    rel = getattr(config, "SCREENSHOTS_DIR", "screenshots")
    if hasattr(config, "path_from_base"):
        return config.path_from_base(rel)
    return os.path.abspath(rel)


# 스마트 스킵에 영향 없는 캐시 폴더명
_CACHE_DIR_NAMES = {
    "Cache",
    "Code Cache",
    "GPUCache",
    "DawnCache",
    "GrShaderCache",
    "ShaderCache",
}


def prune_profile_caches(log_fn: LogFn = None) -> int:
    """
    cookie_data_for_save/instance_*/ 아래 캐시 디렉터리를 삭제합니다.
    반환: 삭제한 디렉터리 수
    """
    if not getattr(config, "PROFILE_CACHE_PRUNE_ENABLED", True):
        return 0
    root = _cookie_root()
    if not os.path.isdir(root):
        return 0
    removed = 0
    freed = 0
    for name in os.listdir(root):
        inst = os.path.join(root, name)
        if not os.path.isdir(inst) or not name.startswith("instance_"):
            continue
        # instance_N 바로 아래 + Default/ 아래
        candidates = [inst, os.path.join(inst, "Default")]
        for base in candidates:
            if not os.path.isdir(base):
                continue
            for entry in list(os.listdir(base)):
                if entry not in _CACHE_DIR_NAMES:
                    continue
                path = os.path.join(base, entry)
                if not os.path.isdir(path):
                    continue
                try:
                    size = _dir_size(path)
                    shutil.rmtree(path, ignore_errors=True)
                    removed += 1
                    freed += size
                except Exception:
                    pass
    if removed:
        _log(log_fn, f"🧹 프로필 캐시 정리: {removed}개 폴더, 약 {freed / (1024*1024):.1f}MB 확보")
    return removed


def _dir_size(path: str) -> int:
    total = 0
    try:
        for root, _dirs, files in os.walk(path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
    except Exception:
        pass
    return total


def prune_screenshots(log_fn: LogFn = None) -> int:
    """
    screenshots/ 오래된 PNG 삭제.
    - 일반 캡차: SCREENSHOT_KEEP_DAYS / SCREENSHOT_KEEP_MAX
    - 디버그(grid_not_found_*, tab_not_found_*): SCREENSHOT_DEBUG_KEEP_DAYS
    """
    folder = _screenshots_dir()
    if not os.path.isdir(folder):
        return 0
    keep_days = int(getattr(config, "SCREENSHOT_KEEP_DAYS", 3) or 3)
    keep_max = int(getattr(config, "SCREENSHOT_KEEP_MAX", 200) or 200)
    debug_days = int(getattr(config, "SCREENSHOT_DEBUG_KEEP_DAYS", 7) or 7)
    now = time.time()

    files = []
    for name in os.listdir(folder):
        if not name.lower().endswith(".png"):
            continue
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            continue
        is_debug = name.startswith("grid_not_found_") or name.startswith("tab_not_found_")
        files.append((path, mtime, is_debug, name))

    removed = 0
    # 1) 기간 초과 삭제
    for path, mtime, is_debug, _name in files:
        limit = debug_days if is_debug else keep_days
        if (now - mtime) > limit * 86400:
            try:
                os.remove(path)
                removed += 1
            except OSError:
                pass

    # 2) 개수 상한 (최신 keep_max 개만 유지, 디버그는 기간만 적용)
    remaining = []
    for path, mtime, is_debug, name in files:
        if not os.path.isfile(path):
            continue
        if is_debug:
            continue
        remaining.append((path, mtime))
    remaining.sort(key=lambda x: x[1], reverse=True)
    for path, _mtime in remaining[keep_max:]:
        try:
            os.remove(path)
            removed += 1
        except OSError:
            pass

    if removed:
        _log(log_fn, f"🧹 스크린샷 정리: {removed}개 삭제")
    return removed


def prune_on_app_start(log_fn: LogFn = None) -> None:
    prune_profile_caches(log_fn)
    prune_screenshots(log_fn)


def prune_after_batch(log_fn: LogFn = None) -> None:
    prune_profile_caches(log_fn)
    prune_screenshots(log_fn)
