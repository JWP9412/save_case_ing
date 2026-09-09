# -*- coding: utf-8 -*-
"""
종국(판결로 사건 종료) 감지 · 숨김 확인
======================================

역할:
- 조회 성공 후 일반내용(기본내용) 표의 '종국결과' 칸만으로 종국 여부를 판별합니다.
- GUI 배치: 끝날 때까지 모아 두었다가 한 번만 "숨김 처리할까요?"를 묻습니다.
- CLI(자동 조회): 대화상자 없이 감지만 하고 data/pending_finalized_cases.json 에 저장합니다.
  → 사용자가 GUI 프로그램을 실행하면 안내창으로 정리(숨김) 여부를 묻습니다.

주니어 개발자 참고:
- 사건마다 바로 물으면 병렬 조회 시 확인창이 여러 개 겹칩니다 → 배치 끝에 한 번만.
- askyesno / 목록 UI 갱신은 반드시 메인(UI) 스레드에서 해야 합니다.
- 숨김 저장 형식은 사건목록 관리와 동일: "사건번호 - 피고 / 사건명" 또는 사건번호만.
- 진행내용·대리인 본문을 훑지 않습니다. (이름 '박종국' 안의 '종국' 오탐 방지)
"""

from __future__ import annotations

import json
import os
from datetime import datetime

import config
from gui.utils.google_sheet_ui import (
    _hidden_item_to_case_number,
    load_hidden_cases,
    save_hidden_cases,
)
from services.general_info_store import get_case_general_info

# 종국결과 칸이 비어 있거나 의미 없는 placeholder 로 올 때 무시
_EMPTY_JONGGUK = frozenset({
    "",
    "-",
    "없음",
    "해당없음",
    "해당 없음",
    "—",
    "–",
    ".",
    "없음.",
})
# 컬럼 헤더/라벨 자체. 값으로 오면 종국이 아님.
# 예: 파서가 헤더 문자열 "종국결과" 를 값처럼 넣는 경우.
_JONGGUK_LABELS = frozenset({"종국결과", "종국 결과", "종국"})


def case_display_text(case):
    """
    숨김 목록·확인창에 쓸 한 줄 표시 문자열.
    gui/dialogs/case_list_manage_dialog._case_display_text 와 동일 규칙.
    """
    if not isinstance(case, dict):
        return "(사건 없음)"
    cn = case.get("사건번호", "") or ""
    cn = str(cn).strip() if cn is not None else ""
    defendant = case.get("피고", "") or ""
    name = case.get("사건명", "") or ""
    name = str(name).strip() if name is not None else ""
    sub = str(defendant).strip() if defendant is not None else ""
    if sub and name:
        sub = f"{sub} / {name}"
    elif name:
        sub = name
    return f"{cn} - {sub}" if sub else cn or "(사건번호 없음)"


def _is_jongguk_label(text):
    """컬럼명·헤더 문자열인지. '종국결과' 라벨은 종국이 아닙니다."""
    return str(text or "").strip() in _JONGGUK_LABELS


def _meaningful_jongguk(value):
    """
    기본내용 '종국결과' 칸의 실제 값이 채워져 있는지 판별.

    주니어 개발자 참고:
    - 대법원 화면: 진행 중이면 칸이 비고, 종국이면 '2026.08.28 항소기각' 처럼 실값이 옵니다.
    - 사이트/파서가 헤더 문자열 "종국결과" 를 값처럼 넣는 경우가 있습니다 → 라벨은 False.
    - 빈칸·placeholder(-, 없음 등)도 False (진행 중).
    - 이름 '박종국' 등은 이 함수에 들어오지 않습니다. (기본내용 칸만 호출)
    """
    text = str(value or "").strip()
    if not text:
        return False
    if text in _EMPTY_JONGGUK:
        return False
    if _is_jongguk_label(text):
        return False
    return True


def is_case_finalized(general_info, progress_data=None):
    """
    종국 여부 판별.

    오직 일반내용(기본내용) 표의 basic['종국결과'] 실값만 봅니다.
    - 칸에 실값(예: '2026.08.28 항소기각') → 종국
    - 빈칸 / '-' / 라벨 '종국결과' → 진행 중
    - 진행내용·당사자·대리인 본문은 보지 않음
      (이름 '박종국' 안의 '종국' 글자 오탐 방지)

    progress_data 인자는 호출부 호환용으로 남겨 두며 사용하지 않습니다.

    반환: (is_finalized: bool, reason: str)
    """
    # progress_data 는 의도적으로 무시 (하위 호환)
    _ = progress_data

    info = general_info if isinstance(general_info, dict) else {}
    basic = info.get("basic") if isinstance(info.get("basic"), dict) else {}

    basic_jong = basic.get("종국결과")
    if _meaningful_jongguk(basic_jong):
        return True, str(basic_jong).strip()

    return False, ""


def _pending_file_path():
    rel = getattr(
        config, "PENDING_FINALIZED_CASES_FILE", "data/pending_finalized_cases.json"
    )
    if os.path.isabs(rel):
        return rel
    return config.path_from_base(rel)


def load_persisted_finalized():
    """
    CLI가 남겨 둔 종국 후보 목록 로드.
    반환: [{case_number, display, reason, detected_at}, ...]
    """
    path = _pending_file_path()
    try:
        if not os.path.isfile(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            out = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                cn = str(item.get("case_number") or "").strip()
                if not cn:
                    continue
                out.append(
                    {
                        "case_number": cn,
                        "display": str(item.get("display") or cn).strip(),
                        "reason": str(item.get("reason") or "종국").strip(),
                        "detected_at": str(item.get("detected_at") or "").strip(),
                    }
                )
            return out
    except Exception:
        pass
    return []


def save_persisted_finalized(items):
    """종국 후보 목록을 JSON으로 저장. 빈 리스트면 파일 삭제."""
    path = _pending_file_path()
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    clean = []
    seen = set()
    for item in items or []:
        if not isinstance(item, dict):
            continue
        cn = str(item.get("case_number") or "").strip()
        if not cn or cn in seen:
            continue
        seen.add(cn)
        clean.append(
            {
                "case_number": cn,
                "display": str(item.get("display") or cn).strip(),
                "reason": str(item.get("reason") or "종국").strip(),
                "detected_at": str(item.get("detected_at") or "").strip(),
            }
        )
    if not clean:
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception:
            pass
        return
    with open(path, "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)


def merge_persisted_finalized(new_items):
    """기존 파일 + 새 감지 건을 사건번호 기준 병합 저장. 반환: 저장 후 전체 건수."""
    existing = load_persisted_finalized()
    by_cn = {p["case_number"]: p for p in existing}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for item in new_items or []:
        if not isinstance(item, dict):
            continue
        cn = str(item.get("case_number") or "").strip()
        if not cn:
            continue
        by_cn[cn] = {
            "case_number": cn,
            "display": str(item.get("display") or cn).strip(),
            "reason": str(item.get("reason") or "종국").strip(),
            "detected_at": str(item.get("detected_at") or now).strip() or now,
        }
    merged = list(by_cn.values())
    save_persisted_finalized(merged)
    return len(merged)


def clear_pending_finalized(app):
    """새 조회 배치 시작 시 메모리 종국 후보 목록을 비웁니다. (파일은 유지)"""
    app._pending_finalized_for_hide = []
    app._pending_finalized_case_numbers = set()


def queue_finalized_for_hide(app, case, case_number, result_data):
    """
    조회 성공 직후 호출: 종국이면 pending 리스트에 적재.

    - 이미 hidden_cases 에 있으면 스킵
    - 같은 배치에서 같은 사건번호 중복 스킵
    """
    cn = str(case_number or "").strip()
    if not cn:
        return

    pending_cns = getattr(app, "_pending_finalized_case_numbers", None)
    if pending_cns is None:
        app._pending_finalized_case_numbers = set()
        pending_cns = app._pending_finalized_case_numbers
    if cn in pending_cns:
        return

    try:
        hidden_set = {
            _hidden_item_to_case_number(x) for x in load_hidden_cases()
        }
    except Exception:
        hidden_set = set()
    if cn in hidden_set:
        return

    general_info = None
    try:
        general_info = get_case_general_info(cn)
    except Exception:
        general_info = None

    finalized, reason = is_case_finalized(general_info, result_data)
    if not finalized:
        return

    pending = getattr(app, "_pending_finalized_for_hide", None)
    if pending is None:
        app._pending_finalized_for_hide = []
        pending = app._pending_finalized_for_hide

    display = case_display_text(case if isinstance(case, dict) else {"사건번호": cn})
    pending.append(
        {
            "case_number": cn,
            "display": display,
            "reason": reason or "종국",
        }
    )
    pending_cns.add(cn)

    try:
        app.log_message(f"⚖️ 종국 감지: {cn} ({reason})")
    except Exception:
        pass


def _is_gui_app(app):
    """Tk root 가 살아 있으면 GUI. CLI MockApp 은 root 가 없거나 동작하지 않음."""
    root = getattr(app, "root", None)
    if root is None:
        return False
    try:
        return bool(root.winfo_exists())
    except Exception:
        return False


def _filter_not_already_hidden(pending):
    """이미 숨긴 사건은 후보에서 제외."""
    try:
        hidden_set = {
            _hidden_item_to_case_number(x) for x in load_hidden_cases()
        }
    except Exception:
        hidden_set = set()
    return [
        p
        for p in pending
        if str(p.get("case_number") or "").strip() not in hidden_set
    ]


def _build_hide_message(pending, *, from_cli_persist=False):
    """확인창 본문 문자열."""
    n = len(pending)
    prefix = (
        "자동 조회(CLI)에서 종국된 사건이 발견되어 두었습니다.\n"
        "목록에서 정리(숨김)할까요?\n\n"
        if from_cli_persist
        else ""
    )
    if n == 1:
        p = pending[0]
        body = (
            "종국된 사건이 발견되었습니다.\n\n"
            f"{p.get('display') or p.get('case_number')}\n"
            f"(종국: {p.get('reason') or '종국'})\n\n"
            "사건 숨김 처리 할까요?"
        )
        if from_cli_persist:
            body = (
                prefix
                + f"{p.get('display') or p.get('case_number')}\n"
                + f"(종국: {p.get('reason') or '종국'})\n\n"
                + "사건 숨김 처리 할까요?"
            )
        return body

    lines = []
    for p in pending[:8]:
        lines.append(
            f"· {p.get('display') or p.get('case_number')} ({p.get('reason') or '종국'})"
        )
    if n > 8:
        lines.append(f"· … 외 {n - 8}건")
    if from_cli_persist:
        return (
            f"자동 조회(CLI)에서 종국된 사건이 {n}건 발견되어 두었습니다.\n"
            "목록에서 정리(숨김)할까요?\n\n"
            + "\n".join(lines)
            + "\n\n사건 숨김 처리 할까요?"
        )
    return (
        f"종국된 사건이 {n}건 발견되었습니다.\n\n"
        + "\n".join(lines)
        + "\n\n사건 숨김 처리 할까요?"
    )


def _ask_and_maybe_hide(app, pending, *, from_cli_persist=False):
    """
    GUI에서 숨김 여부를 묻고 적용.
    예/아니오 모두 호출 측에서 파일 정리할 수 있도록 yes 여부 반환.
    """
    pending = _filter_not_already_hidden(pending)
    if not pending:
        return False, []

    n = len(pending)
    message = _build_hide_message(pending, from_cli_persist=from_cli_persist)
    ask = getattr(app, "ask_yesno", None)
    yes = False
    if callable(ask):
        try:
            yes = bool(ask("종국 사건", message))
        except Exception:
            yes = False

    if not yes:
        try:
            app.log_message(f"⚖️ 종국 {n}건 — 숨김 안 함")
        except Exception:
            pass
        return False, pending

    _apply_hide_finalized(app, pending)
    return True, pending


def prompt_hide_finalized_cases(app):
    """
    메인(UI) 스레드에서만 호출하세요. (배치 종료 직후 메모리 pending)

    - GUI: 숨김 여부 확인
    - CLI: 파일에 저장만 하고, GUI 실행 시 안내하도록 로그
    """
    pending = list(getattr(app, "_pending_finalized_for_hide", None) or [])
    # 한 번 처리했으면 메모리 비워 중복 다이얼로그 방지
    app._pending_finalized_for_hide = []
    app._pending_finalized_case_numbers = set()

    if not pending:
        return

    n = len(pending)
    if not _is_gui_app(app):
        # CLI: 질문 없이 파일에 남겨 두고, 다음 GUI 실행 때 안내
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for p in pending:
            p["detected_at"] = now
        try:
            total = merge_persisted_finalized(pending)
        except Exception as e:
            try:
                app.log_message(f"⚠️ 종국 후보 저장 실패: {e}")
            except Exception:
                pass
            total = n
        names = ", ".join(p.get("display") or p.get("case_number") for p in pending[:5])
        extra = f" 외 {n - 5}건" if n > 5 else ""
        try:
            app.log_message(
                f"⚖️ 종국 {n}건 감지·저장 (누적 {total}건, GUI 실행 시 숨김 안내): "
                f"{names}{extra}"
            )
        except Exception:
            pass
        return

    _ask_and_maybe_hide(app, pending, from_cli_persist=False)


def prompt_persisted_finalized_on_startup(app):
    """
    GUI 프로그램 시작 시 호출 (메인 스레드).

    CLI가 남겨 둔 pending_finalized_cases.json 이 있으면
    안내창으로 숨김(정리) 여부를 묻고, 예/아니오 후 파일을 비웁니다.
    세션당 한 번만 묻도록 플래그를 둡니다.
    """
    if getattr(app, "_finalized_startup_prompt_done", False):
        return
    if not _is_gui_app(app):
        return

    pending = _filter_not_already_hidden(load_persisted_finalized())
    if not pending:
        # 이미 숨긴 것만 남아 있으면 파일만 정리
        try:
            if load_persisted_finalized():
                save_persisted_finalized([])
        except Exception:
            pass
        app._finalized_startup_prompt_done = True
        return

    app._finalized_startup_prompt_done = True
    try:
        _ask_and_maybe_hide(app, pending, from_cli_persist=True)
    finally:
        # 예/아니오 모두 '이번 안내는 처리됨' → 파일 비워 매 실행마다 반복 질문 방지
        try:
            save_persisted_finalized([])
        except Exception:
            pass


def schedule_persisted_finalized_prompt(app, delay_ms=800):
    """
    목록 로드 직후 등에서 호출. root.after 로 시작 안내를 예약합니다.
    첫 실행 가이드와 겹치지 않도록 약간의 지연을 둡니다.
    """
    if getattr(app, "_finalized_startup_prompt_done", False):
        return
    root = getattr(app, "root", None)
    if root is None:
        return
    try:
        if not root.winfo_exists():
            return
    except Exception:
        return

    def _run():
        try:
            prompt_persisted_finalized_on_startup(app)
        except Exception as e:
            try:
                app.log_message(f"⚠️ 종국 시작 안내 실패: {e}")
            except Exception:
                pass

    try:
        root.after(int(delay_ms), _run)
    except Exception:
        pass


def _apply_hide_finalized(app, pending):
    """Yes 선택 시 hidden_cases 저장 + 목록에서 제거 + UI 갱신."""
    if not pending:
        return

    hide_cns = {
        str(p.get("case_number") or "").strip()
        for p in pending
        if str(p.get("case_number") or "").strip()
    }
    if not hide_cns:
        return

    try:
        hidden = list(load_hidden_cases())
    except Exception:
        hidden = []

    existing = {_hidden_item_to_case_number(x) for x in hidden}
    for p in pending:
        cn = str(p.get("case_number") or "").strip()
        if not cn or cn in existing:
            continue
        display = (p.get("display") or cn).strip()
        hidden.append(display)
        existing.add(cn)

    try:
        save_hidden_cases(hidden)
    except Exception as e:
        try:
            app.log_message(f"⚠️ 종국 숨김 저장 실패: {e}")
        except Exception:
            pass
        return

    case_list = getattr(app, "case_list", None)
    if isinstance(case_list, list):
        app.case_list = [
            c
            for c in case_list
            if str((c or {}).get("사건번호") or "").strip() not in hide_cns
        ]

    update_ui = getattr(app, "update_case_list_ui", None)
    if callable(update_ui):
        try:
            update_ui()
        except Exception as e:
            try:
                app.log_message(f"⚠️ 종국 숨김 후 목록 갱신 실패: {e}")
            except Exception:
                pass

    names = ", ".join(
        (p.get("display") or p.get("case_number") or "") for p in pending[:5]
    )
    extra = f" 외 {len(pending) - 5}건" if len(pending) > 5 else ""
    try:
        app.log_message(f"🙈 종국 사건 {len(pending)}건 숨김 처리: {names}{extra}")
    except Exception:
        pass
