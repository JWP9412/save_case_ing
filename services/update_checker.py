#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
앱 버전 업데이트 확인
====================

역할: GitHub 최신 릴리스(또는 태그)와 로컬 APP_VERSION을 비교합니다.
호출: 제어 패널 '버전 업데이트 확인' 버튼 → app.check_app_update()

주니어 개발자 참고:
- 추가 패키지 없이 urllib.request 만 사용합니다.
- GitHub은 User-Agent가 비어 있으면 거절할 수 있어 헤더를 넣습니다.
- Releases/latest 와 tags 목록을 둘 다 보고, 버전 번호가 더 높은 쪽을 씁니다.
  (태그만 푸시하고 Release를 안 만든 경우에도 맞는 최신을 보여 줍니다.)
"""

import json
import re
import urllib.error
import urllib.request

import config


def _normalize_version(version_str):
    """
    'v4.12.1' / '4.12.1' → (4, 12, 1) 튜플.
    숫자가 아닌 부분은 무시하고, 부족하면 0으로 채웁니다.
    """
    if not version_str:
        return (0, 0, 0)
    s = str(version_str).strip()
    if s.lower().startswith("v"):
        s = s[1:]
    parts = re.findall(r"\d+", s)
    nums = [int(p) for p in parts[:3]]
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums)


def compare_versions(local_version, remote_version):
    """
    로컬 vs 원격 버전 비교.

    반환:
      -1 : 로컬이 더 낮음 (업데이트 가능)
       0 : 같음
       1 : 로컬이 더 높음 (개발 빌드 등)
    """
    a = _normalize_version(local_version)
    b = _normalize_version(remote_version)
    if a < b:
        return -1
    if a > b:
        return 1
    return 0


def _github_get_json(url, timeout=12):
    """GitHub API GET → JSON (dict 또는 list)."""
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"CaseIng/{getattr(config, 'APP_VERSION', '0')}",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def _tag_html_url(tag_name):
    """태그 페이지 URL (Release가 없어도 열 수 있음)."""
    repo = getattr(config, "GITHUB_REPO", "JWP9412/save_case_ing")
    tag = str(tag_name).strip()
    return f"https://github.com/{repo}/releases/tag/{tag}"


def fetch_latest_from_tags(timeout=12):
    """
    GitHub tags 목록에서 버전 번호가 가장 큰 태그를 고릅니다.
    """
    url = getattr(
        config,
        "GITHUB_TAGS_URL",
        "https://api.github.com/repos/JWP9412/save_case_ing/tags?per_page=30",
    )
    data = _github_get_json(url, timeout=timeout)
    if not isinstance(data, list) or not data:
        raise ValueError("태그 목록이 비어 있습니다")

    best = None
    best_key = None
    for item in data:
        if not isinstance(item, dict):
            continue
        name = (item.get("name") or "").strip()
        if not name:
            continue
        key = _normalize_version(name)
        if best_key is None or key > best_key:
            best_key = key
            best = name

    if not best:
        raise ValueError("유효한 버전 태그를 찾지 못했습니다")

    return {
        "tag_name": best,
        "html_url": _tag_html_url(best),
        "name": best,
        "source": "tags",
    }


def _fetch_releases_latest_only(timeout=12):
    """
    /releases/latest 만 조회합니다. 없거나 실패하면 None.
    (폴백은 호출측에서 tags와 비교합니다.)
    """
    url = getattr(
        config,
        "GITHUB_RELEASES_LATEST_URL",
        "https://api.github.com/repos/JWP9412/save_case_ing/releases/latest",
    )
    try:
        data = _github_get_json(url, timeout=timeout)
        if not isinstance(data, dict):
            return None
        tag = (data.get("tag_name") or "").strip()
        if not tag:
            return None
        return {
            "tag_name": tag,
            "html_url": (data.get("html_url") or "").strip() or _tag_html_url(tag),
            "name": (data.get("name") or tag).strip(),
            "source": "releases",
        }
    except urllib.error.HTTPError as e:
        if e.code in (404, 403):
            return None
        raise
    except Exception:
        return None


def fetch_latest_release(timeout=12):
    """
    Release 최신과 Tags 최신 중 버전 번호가 더 높은 쪽을 반환합니다.

    주니어: 예전에 Releases만 보면 태그만 올린 v5.3.x가 무시되고
    오래된 Release(v5.1.1)가 '최신'으로 나오던 문제를 막습니다.
    """
    from_release = _fetch_releases_latest_only(timeout=timeout)
    from_tags = None
    try:
        from_tags = fetch_latest_from_tags(timeout=timeout)
    except Exception:
        from_tags = None

    if from_release and from_tags:
        if compare_versions(from_release["tag_name"], from_tags["tag_name"]) >= 0:
            chosen = dict(from_release)
            chosen["source"] = "releases+tags"
            return chosen
        chosen = dict(from_tags)
        chosen["source"] = "tags+releases"
        return chosen
    if from_tags:
        return from_tags
    if from_release:
        return from_release
    raise ValueError("GitHub에서 최신 버전을 찾지 못했습니다 (releases/tags)")


def check_for_update(local_version=None):
    """
    업데이트 확인 결과 dict를 반환합니다.

    성공 시:
      {
        "ok": True,
        "status": "update_available" | "up_to_date" | "ahead",
        "local": "4.12.1",
        "remote": "4.12.2",
        "html_url": "...",
      }
    실패 시:
      {"ok": False, "error": "메시지"}
    """
    local = local_version or getattr(config, "APP_VERSION", "0.0.0")
    try:
        release = fetch_latest_release()
        remote = release["tag_name"]
        cmp = compare_versions(local, remote)
        if cmp < 0:
            status = "update_available"
        elif cmp > 0:
            status = "ahead"
        else:
            status = "up_to_date"
        return {
            "ok": True,
            "status": status,
            "local": str(local).lstrip("vV"),
            "remote": str(remote).lstrip("vV"),
            "html_url": release.get("html_url") or "",
            "tag_name": remote,
            "source": release.get("source", ""),
        }
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}: {e.reason}"}
    except urllib.error.URLError as e:
        return {"ok": False, "error": f"네트워크 오류: {e.reason}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
