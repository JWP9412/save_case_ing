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
        """한 사건의 브라우저/Node 프로세스 정리."""
        try:
            if case_number in self.app.browser_processes:
                process = self.app.browser_processes[case_number]
                try:
                    if process.poll() is None:
                        self.app.log_message(f"🔄 프로세스 종료 중: {case_number}")
                        process.kill()
                        try:
                            process.wait(timeout=2)
                        except Exception:
                            pass
                        self.app.log_message(f"✅ 프로세스 종료 완료: {case_number}")
                except Exception as e:
                    self.app.log_message(f"⚠️ 프로세스 종료 실패: {case_number} - {e}")
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
                sp.run(
                    ["taskkill", "/F", "/IM", "chrome.exe"],
                    capture_output=True,
                    timeout=3,
                )
                self.app.log_message("⚠️ taskkill로 Chrome 강제 종료 시도")
            except Exception:
                pass

