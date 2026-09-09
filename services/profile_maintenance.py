# -*- coding: utf-8 -*-
"""
Chrome 프로필 캐시 · 스크린샷 자동 정리 · 프로필 zip 백업/복원
=============================================================
스마트 스킵에 필요한 Cookies/History 는 남기고,
Cache·Code Cache 등만 삭제해 디스크·메모리를 줄입니다.

백업: cookie_data_for_save/instance_* 를 zip 으로 보관 (캐시 폴더는 제외).
복원: zip 을 다시 instance_* 로 풀어 스마트 스킵 프로필을 되살립니다.
"""
from __future__ import annotations

import json
import os
import shutil
import time
import zipfile
from datetime import datetime
from typing import Callable, Optional

import config

LogFn = Optional[Callable[[str], None]]

# zip 안에 넣는 메타데이터 파일명 (복원 시 이 앱 백업인지 확인)
_MANIFEST_NAME = "caseing_profile_backup.json"


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


def _backup_root() -> str:
    rel = getattr(config, "PROFILE_BACKUP_DIR", "data/profile_backups")
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


def list_profile_instances() -> list[str]:
    """cookie 루트 아래 instance_* 폴더명 목록 (정렬)."""
    root = _cookie_root()
    if not os.path.isdir(root):
        return []
    names = []
    for name in os.listdir(root):
        path = os.path.join(root, name)
        if os.path.isdir(path) and name.startswith("instance_"):
            names.append(name)
    names.sort(key=lambda n: (len(n), n))
    return names


def _path_has_cache_dir(rel_parts: list[str]) -> bool:
    """상대경로 조각 중 캐시 폴더가 있으면 True (백업에서 제외)."""
    return any(p in _CACHE_DIR_NAMES for p in rel_parts)


def default_backup_zip_path() -> str:
    """
    기본 저장 경로: data/profile_backups/profiles_YYYYMMDD_HHMMSS.zip
    폴더가 없으면 만듭니다.
    """
    folder = _backup_root()
    os.makedirs(folder, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(folder, f"profiles_{stamp}.zip")


def backup_cookie_profiles(
    dest_zip: str | None = None,
    log_fn: LogFn = None,
) -> dict:
    """
    프로필(instance_*)을 zip 파일로 백업합니다.

    주니어:
    - Cache 등은 빼고 Cookies/History 등만 담아 용량을 줄입니다.
    - Chrome/워커가 프로필을 쓰는 중이면 일부 파일이 잠겨 건너뛸 수 있습니다.
      가능하면 조회를 멈춘 뒤 백업하세요.

    Returns:
        {"ok": bool, "path": str, "instances": int, "files": int, "skipped": int, "error": str|None}
    """
    root = _cookie_root()
    instances = list_profile_instances()
    if not instances:
        msg = f"백업할 프로필이 없습니다: {root}"
        _log(log_fn, f"⚠️ {msg}")
        return {
            "ok": False,
            "path": dest_zip or "",
            "instances": 0,
            "files": 0,
            "skipped": 0,
            "error": msg,
        }

    out_path = dest_zip or default_backup_zip_path()
    out_dir = os.path.dirname(os.path.abspath(out_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    files_ok = 0
    skipped = 0
    try:
        with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            manifest = {
                "app": "case-ing",
                "kind": "cookie_profiles",
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "cookie_dir_name": os.path.basename(root.rstrip("\\/")),
                "instances": instances,
                "profile_count_config": int(getattr(config, "PROFILE_COUNT", 0) or 0),
            }
            zf.writestr(
                _MANIFEST_NAME,
                json.dumps(manifest, ensure_ascii=False, indent=2),
            )

            for inst_name in instances:
                inst_path = os.path.join(root, inst_name)
                for dirpath, dirnames, filenames in os.walk(inst_path):
                    # 캐시 폴더는 하위로 내려가지 않음
                    dirnames[:] = [d for d in dirnames if d not in _CACHE_DIR_NAMES]
                    for fname in filenames:
                        abs_file = os.path.join(dirpath, fname)
                        rel = os.path.relpath(abs_file, root)
                        rel_parts = rel.replace("\\", "/").split("/")
                        if _path_has_cache_dir(rel_parts):
                            continue
                        arcname = rel.replace("\\", "/")
                        try:
                            zf.write(abs_file, arcname)
                            files_ok += 1
                        except OSError:
                            # Windows에서 Cookies DB 잠금 등
                            skipped += 1
                        except Exception:
                            skipped += 1
    except Exception as e:
        _log(log_fn, f"❌ 프로필 백업 실패: {e}")
        return {
            "ok": False,
            "path": out_path,
            "instances": len(instances),
            "files": files_ok,
            "skipped": skipped,
            "error": str(e),
        }

    size_mb = 0.0
    try:
        size_mb = os.path.getsize(out_path) / (1024 * 1024)
    except OSError:
        pass
    _log(
        log_fn,
        f"💾 프로필 백업 완료: {out_path} "
        f"({len(instances)}개 프로필, {files_ok}파일, "
        f"건너뜀 {skipped}, {size_mb:.1f}MB)",
    )
    return {
        "ok": True,
        "path": out_path,
        "instances": len(instances),
        "files": files_ok,
        "skipped": skipped,
        "error": None,
    }


def _zip_looks_like_profile_backup(zf: zipfile.ZipFile) -> tuple[bool, str]:
    names = zf.namelist()
    if _MANIFEST_NAME in names:
        try:
            raw = zf.read(_MANIFEST_NAME).decode("utf-8")
            data = json.loads(raw)
            if data.get("kind") == "cookie_profiles" or data.get("app") == "case-ing":
                return True, "manifest"
        except Exception:
            pass
    # 구형/수동 zip: instance_*/ 가 있으면 허용
    for n in names:
        part = n.replace("\\", "/").split("/")[0]
        if part.startswith("instance_"):
            return True, "instance_prefix"
    return False, "unknown"


def restore_cookie_profiles(
    zip_path: str,
    *,
    replace_existing: bool = True,
    log_fn: LogFn = None,
) -> dict:
    """
    백업 zip 을 cookie_data_for_save 로 복원합니다.

    Args:
        replace_existing: True면 같은 이름 instance_* 를 지우고 덮어씁니다.
    """
    if not zip_path or not os.path.isfile(zip_path):
        msg = f"백업 파일이 없습니다: {zip_path}"
        _log(log_fn, f"⚠️ {msg}")
        return {"ok": False, "restored": [], "error": msg}

    root = _cookie_root()
    os.makedirs(root, exist_ok=True)

    restored: list[str] = []
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            ok, _how = _zip_looks_like_profile_backup(zf)
            if not ok:
                msg = "이 zip은 case-ing 프로필 백업이 아닌 것 같습니다."
                _log(log_fn, f"⚠️ {msg}")
                return {"ok": False, "restored": [], "error": msg}

            # 복원 대상 instance 목록
            inst_set = set()
            for name in zf.namelist():
                top = name.replace("\\", "/").split("/")[0]
                if top.startswith("instance_"):
                    inst_set.add(top)
            if not inst_set:
                msg = "zip 안에 instance_* 폴더가 없습니다."
                _log(log_fn, f"⚠️ {msg}")
                return {"ok": False, "restored": [], "error": msg}

            if replace_existing:
                for inst in sorted(inst_set):
                    target = os.path.join(root, inst)
                    if os.path.isdir(target):
                        shutil.rmtree(target, ignore_errors=True)

            for info in zf.infolist():
                name = info.filename.replace("\\", "/")
                if name.endswith("/") or name == _MANIFEST_NAME:
                    continue
                top = name.split("/")[0]
                if not top.startswith("instance_"):
                    continue
                # zip-slip 방지: root 밖으로 못 나가게
                dest = os.path.normpath(os.path.join(root, name))
                if not dest.startswith(os.path.normpath(root) + os.sep):
                    continue
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with zf.open(info, "r") as src, open(dest, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                if top not in restored:
                    restored.append(top)
    except Exception as e:
        _log(log_fn, f"❌ 프로필 복원 실패: {e}")
        return {"ok": False, "restored": restored, "error": str(e)}

    restored.sort(key=lambda n: (len(n), n))
    _log(
        log_fn,
        f"📥 프로필 복원 완료: {len(restored)}개 ← {zip_path}",
    )
    return {"ok": True, "restored": restored, "error": None}


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
