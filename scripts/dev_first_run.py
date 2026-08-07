# -*- coding: utf-8 -*-
"""
첫 실행 UX 테스트용 개발 스크립트
==================================

이미 세팅된 개발 PC에서 "처음 사용자" 상태를 안전하게 재현·복원합니다.
파일을 삭제하지 않고 `.dev_backup/` 으로 이동했다가 되돌립니다.

사용법 (프로젝트 루트에서):
  python scripts/dev_first_run.py status
  python scripts/dev_first_run.py backup              # 토큰·user_settings 이동
  python scripts/dev_first_run.py backup --with-secret  # 인증 파일도 함께
  python scripts/dev_first_run.py restore             # 원위치 복원

중요 — 이 스크립트가 건드리는 것 / 안 건드리는 것:
  [이동 대상]
    - data/google_user_token.json   (구글 로그인 토큰)
    - data/user_settings.json       (시트 ID 등 설정)
    - api/certification/client_secret.json  (--with-secret 일 때만)
  [절대 안 건드림 — 삭제·이동 없음]
    - data/case_list_cache.json     (사건 목록 캐시)
    - data/hidden_cases.json        (숨긴 사건)
    - 구글 시트에 있는 실제 사건 데이터
    - cookie_data_for_save/, logs/ 등

주니어 개발자:
- backup 후 앱을 실행하면 첫 실행 가이드가 떠야 합니다.
- 사건 목록이 화면에 그대로 보이는 것은 정상입니다(캐시를 지우지 않기 때문).
- 테스트가 끝나면 반드시 restore 하세요.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys

# 프로젝트 루트를 import 경로에 추가
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

BACKUP_DIR = os.path.join(ROOT, ".dev_backup")

# (백업 파일명, 원본 상대경로)
TRACKED = [
    ("google_user_token.json", os.path.join("data", "google_user_token.json")),
    ("user_settings.json", os.path.join("data", "user_settings.json")),
]
SECRET = ("client_secret.json", os.path.join("api", "certification", "client_secret.json"))


def _abs(rel: str) -> str:
    return os.path.join(ROOT, rel)


def _ensure_backup_dir():
    os.makedirs(BACKUP_DIR, exist_ok=True)


def cmd_status(with_secret: bool = False):
    print("=== 첫 실행 테스트 상태 ===")
    print(f"프로젝트 루트: {ROOT}")
    print(f"백업 폴더: {BACKUP_DIR} ({'있음' if os.path.isdir(BACKUP_DIR) else '없음'})")
    print()
    items = list(TRACKED)
    if with_secret or True:
        # status는 항상 secret도 함께 보여줌
        items = list(TRACKED) + [SECRET]
    for name, rel in items:
        src = _abs(rel)
        bak = os.path.join(BACKUP_DIR, name)
        print(f"- {rel}")
        print(f"    원본: {'있음' if os.path.isfile(src) else '없음'}")
        print(f"    백업: {'있음' if os.path.isfile(bak) else '없음'}")

    print()
    print("참고: case_list_cache / hidden_cases 는 이 스크립트가 절대 이동·삭제하지 않습니다.")
    print("      (backup 후에도 사건 목록이 화면에 보이면 정상입니다.)")

    # config 기준 세팅 판정 (가능하면)
    try:
        import config
        from services import google_oauth

        config.load_user_settings()
        st = google_oauth.get_setup_status()
        print()
        print("세팅 판정:")
        print(f"  client_secret: {st['client_secret']}")
        print(f"  token:         {st['token']}")
        print(f"  sheet_id:      {st['sheet_id']}")
        print(f"  complete:      {st['complete']}")
        print(f"  SHOW_FIRST_RUN_GUIDE: {getattr(config, 'SHOW_FIRST_RUN_GUIDE', '?')}")
        print(f"  should_show_guide: {google_oauth.should_show_first_run_guide()}")
    except Exception as e:
        print()
        print(f"(세팅 판정 생략: {e})")


def cmd_backup(with_secret: bool = False):
    _ensure_backup_dir()
    # 덮어쓰기 방지: 이미 백업이 있으면 거부
    existing = [
        name
        for name, _ in (TRACKED + ([SECRET] if with_secret else []))
        if os.path.isfile(os.path.join(BACKUP_DIR, name))
    ]
    if existing:
        print("오류: 이미 백업이 있습니다. 덮어쓰지 않습니다.")
        print("  기존 백업:", ", ".join(existing))
        print("  먼저 `python scripts/dev_first_run.py restore` 후 다시 시도하세요.")
        sys.exit(1)

    moved = []
    targets = list(TRACKED)
    if with_secret:
        targets.append(SECRET)

    for name, rel in targets:
        src = _abs(rel)
        bak = os.path.join(BACKUP_DIR, name)
        if not os.path.isfile(src):
            print(f"건너뜀 (원본 없음): {rel}")
            continue
        shutil.move(src, bak)
        moved.append(rel)
        print(f"이동 → 백업: {rel}")

    if not moved:
        print("이동할 파일이 없었습니다. (이미 첫 사용자 상태일 수 있음)")
    else:
        print()
        print("완료: 첫 사용자 상태로 전환했습니다.")
        print("이제 `python main.py` 로 앱을 실행해 가이드 창을 확인하세요.")
        print("테스트 후 `python scripts/dev_first_run.py restore` 로 복원하세요.")


def cmd_restore():
    if not os.path.isdir(BACKUP_DIR):
        print("오류: .dev_backup/ 폴더가 없습니다. 복원할 백업이 없습니다.")
        sys.exit(1)

    restored = []
    for name, rel in TRACKED + [SECRET]:
        bak = os.path.join(BACKUP_DIR, name)
        dest = _abs(rel)
        if not os.path.isfile(bak):
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.isfile(dest):
            # 테스트 중 새로 생긴 파일은 덮어쓰기 전 안내
            print(f"주의: 원본 위치에 파일이 있어 덮어씁니다 → {rel}")
        shutil.move(bak, dest)
        restored.append(rel)
        print(f"복원: {rel}")

    if not restored:
        print("복원할 백업 파일이 없습니다.")
    else:
        print()
        print("완료: 원래 개발 환경으로 복원했습니다.")

    # 빈 백업 폴더 정리(선택)
    try:
        if os.path.isdir(BACKUP_DIR) and not os.listdir(BACKUP_DIR):
            os.rmdir(BACKUP_DIR)
            print(".dev_backup/ 빈 폴더를 삭제했습니다.")
    except OSError:
        pass


def main():
    parser = argparse.ArgumentParser(
        description="첫 실행 UX 테스트: 세팅 파일을 백업/복원합니다."
    )
    parser.add_argument(
        "command",
        choices=["status", "backup", "restore"],
        help="status | backup | restore",
    )
    parser.add_argument(
        "--with-secret",
        action="store_true",
        help="backup 시 client_secret.json 도 함께 이동 (1단계 테스트용)",
    )
    args = parser.parse_args()

    if args.command == "status":
        cmd_status(with_secret=args.with_secret)
    elif args.command == "backup":
        cmd_backup(with_secret=args.with_secret)
    elif args.command == "restore":
        cmd_restore()


if __name__ == "__main__":
    main()
