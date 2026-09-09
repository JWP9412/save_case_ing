# -*- coding: utf-8 -*-
"""
브라우저·Chrome 프로세스 정리 (CleanupMixin)
============================================
한 사건 처리 후 Puppeteer/Chrome 프로세스를 정리합니다.
배치 종료 시 원격 디버깅 Chrome 일괄 종료도 담당합니다.

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

class CleanupMixin:
    """Mixin - self.app 을 통해 GUI/서비스에 접근."""

    def cleanup_case_process(self, case_number):
        """
        한 사건의 브라우저/Node 매핑 정리.

        주니어: 레인 워커는 여러 사건이 공유합니다.
        여기서 process.kill() 하면 같은 레인의 뒤 사건까지 죽습니다.
        → app.browser_processes 에서 매핑만 제거하고, 실제 종료는
          배치 끝의 shutdown_all_workers / _kill_chrome_debug_processes 에서 합니다.
        """
        try:
            # PuppeteerService 사건 매핑만 해제 (워커 유지)
            svc = getattr(self.app, "puppeteer_service", None)
            if svc is not None and hasattr(svc, "unbind_case"):
                svc.unbind_case(case_number)
            elif svc is not None and hasattr(svc, "cleanup_process"):
                svc.cleanup_process(case_number)

            if case_number in self.app.browser_processes:
                del self.app.browser_processes[case_number]
            if case_number in self.app.browser_ws_urls:
                del self.app.browser_ws_urls[case_number]
        except Exception as e:
            self.app.log_message(f"⚠️ 프로세스 정리 오류: {case_number} - {e}")

    # -------------------------------------------------------------------------
    # 실제 실행 루프
    # -------------------------------------------------------------------------


    def _kill_chrome_debug_processes(self):
        """원격 디버깅 포트 사용 중인 Chrome 프로세스 종료."""
        try:
            self.app.log_message("🔄 [DEBUG] Chrome 프로세스 정리 중...")
            chrome_killed = 0
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if (
                        proc.info.get("name")
                        and "chrome.exe" in (proc.info.get("name") or "").lower()
                    ):
                        cmdline = proc.info.get("cmdline", []) or []
                        if any(
                            "--remote-debugging-port" in str(arg)
                            for arg in cmdline
                        ):
                            self.app.log_message(
                                f"🔄 [DEBUG] Chrome 프로세스 종료: PID {proc.info.get('pid')}"
                            )
                            proc.kill()
                            chrome_killed += 1
                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    pass
            if chrome_killed > 0:
                self.app.log_message(f"✅ Chrome 프로세스 {chrome_killed}개 종료 완료")
            else:
                self.app.log_message("ℹ️ 종료할 Chrome 프로세스 없음")
        except Exception as e:
            self.app.log_message(f"⚠️ Chrome 프로세스 정리 오류: {e}")
            try:
                # 주니어: CREATE_NO_WINDOW 없으면 taskkill 때문에 CMD 창이 번쩍입니다.
                # Chrome 을 보이게 하는 설정이 아닙니다. 콘솔 창만 숨깁니다.
                kill_kwargs = dict(capture_output=True, timeout=3)
                if os.name == "nt":
                    kill_kwargs["creationflags"] = sp.CREATE_NO_WINDOW
                sp.run(
                    ["taskkill", "/F", "/IM", "chrome.exe"],
                    **kill_kwargs,
                )
                self.app.log_message("⚠️ taskkill로 Chrome 강제 종료 시도")
            except Exception:
                pass

