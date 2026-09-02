# -*- coding: utf-8 -*-
"""
ProcessController 본체 - mixin 조합 + Puppeteer 래퍼
==================================================
외부에서는 `from services.process_controller import ProcessController` 만 사용합니다.

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

from .captcha_ocr import CaptchaOcrMixin
from .case_runner import CaseRunnerMixin
from .cleanup import CleanupMixin
from .hearing import HearingMixin
from .result_handler import ResultHandlerMixin

class ProcessController(
    CleanupMixin,
    HearingMixin,
    ResultHandlerMixin,
    CaptchaOcrMixin,
    CaseRunnerMixin,
):
    """사건 조회·캡차·저장 통합 컨트롤러 (mixin 조합)."""

    def __init__(self, app):
        """
        Args:
            app: AppController 또는 MockApp. log_message, update_case_status, ui_queue, show_warning 등에 접근.
        """
        self.app = app
        # OCR 자동 제출(웨이브) 중복 호출 방지
        self._auto_submit_lock = threading.Lock()

    # -------------------------------------------------------------------------
    # 캡차 OCR (EasyOCR + Tesseract, ocr_export)
    # -------------------------------------------------------------------------


    def capture_captcha_image(
        self,
        case_number,
        defendant,
        court,
        instance_index=0,
        smart_skip_enabled=True,
    ):
        """캡차 이미지 캡처. PuppeteerService 사용, ws_url/process는 app에 저장."""
        try:
            image_path, ws_url, process = self.app.puppeteer_service.capture_captcha_image(
                case_number,
                defendant,
                court,
                instance_index,
                smart_skip_enabled=smart_skip_enabled,
            )
            if ws_url:
                self.app.browser_ws_urls[case_number] = ws_url
            if process:
                self.app.browser_processes[case_number] = process
            return image_path
        except Exception as e:
            self.app.log_message(f"❌ 캡차 이미지 캡처 오류: {e}")
            return None


    def execute_case_processing_with_captcha(
        self, case, case_index, instance_index=0, smart_skip_enabled=True
    ):
        """캡차 이미지 캡처 후 GUI 표시 및 완료 버튼 활성화."""
        try:
            case_number = case.get("사건번호", "")
            defendant = case.get("피고", "")
            court = case.get("법원", "")
            self.app.log_message(f"🔄 처리 시작: {case_number} (법원: {court})")
            self.app.log_message(f"📸 캡차 이미지 캡처 중: {case_number}")
            image_path = self.capture_captcha_image(
                case_number,
                defendant,
                court,
                instance_index,
                smart_skip_enabled=smart_skip_enabled,
            )
            if image_path:
                self.app.update_captcha_image(case_index, image_path)
                self.app.update_case_status(case_index, "캡차입력", "blue")
                self.app.log_message(f"🔐 캡차 입력 대기: {case_number}")
                # OCR 자동 제출 모드면 여기서 완료 버튼을 켜지 않음.
                # (OCR 실패/수동 폴백·웨이브 미완일 때만 나중에 활성화)
                ocr_auto = (
                    getattr(config, "OCR_ENABLED", False)
                    and getattr(config, "OCR_AUTO_SUBMIT", False)
                )
                if not ocr_auto:
                    self.app.ui_queue.put(
                        (
                            "function",
                            (self.app._set_control_btn_state, self.app.complete_btn, True),
                            {},
                        )
                    )
                    self.app.log_message("✅ 캡차 입력 완료 버튼 활성화됨")
                return image_path
            self.app.log_message(f"❌ 캡차 이미지 캡처 실패: {case_number}")
            return False
        except Exception as e:
            case_number = case.get("사건번호", "")
            self.app.log_message(f"❌ 처리 오류: {case_number} - {e}")
            return False


    def execute_case_processing(self, case, captcha_input):
        """Puppeteer로 사건 처리 실행. 반환: 진행내용 리스트 또는 False 또는 WRONG_CAPTCHA 딕셔너리."""
        try:
            case_number = case.get("사건번호", "")
            browser_ws_url = self.app.browser_ws_urls.get(case_number)
            result = self.app.puppeteer_service.execute_case_processing(
                case, captcha_input, browser_ws_url
            )
            # 진행내용 리스트를 받은 직후, 별도 보관함의 일반내용도 저장 시도
            # (실패해도 본 흐름에 영향 없음)
            if isinstance(result, list):
                self._persist_general_info(case_number)
            return result
        except Exception as e:
            case_number = case.get("사건번호", "")
            self.app.log_message(f"❌ Puppeteer 실행 오류: {case_number} - {e}")
            return False


    def _persist_general_info(self, case_number):
        """
        PuppeteerService.last_general_info 에 담아둔 일반내용을
        data/general_info.json 에 저장합니다.

        주니어 참고:
        - 당사자·대리인도 같은 화면에 이미 있어 비용이 0이므로
          평소 조회 때 include_parties=True 로 함께 저장합니다.
        - 돋보기 창의 새로고침 버튼도 같은 경로를 타므로 자동으로 갱신됩니다.
        """
        try:
            svc = getattr(self.app, "puppeteer_service", None)
            if not svc:
                return
            info = None
            if hasattr(svc, "last_general_info"):
                info = svc.last_general_info.pop(case_number, None)
            if not info:
                return
            from services.general_info_store import save_case_general_info

            # 1단계 실측: 당사자·대리인도 같은 화면에 이미 있음 → 평소 조회 때 함께 저장
            saved = save_case_general_info(case_number, info, include_parties=True)
            if saved:
                self.app.log_message(f"📋 일반내용 저장: {case_number}")
                # 돋보기 창이 새로고침을 기다리는 중이면 UI 스레드에서 다시 그리기
                refresh = getattr(self.app, "_general_info_dialog_refresh", None)
                if refresh and refresh.get("case_number") == case_number:
                    dlg = refresh.get("dialog")
                    try:
                        if dlg is not None and dlg.winfo_exists():
                            dlg.after(0, dlg.reload_from_store)
                    except Exception:
                        pass
                    self.app._general_info_dialog_refresh = None
            else:
                self.app.log_message(f"⚠️ 일반내용 저장 실패: {case_number}")
        except Exception as e:
            try:
                self.app.log_message(f"⚠️ 일반내용 저장 예외(무시): {e}")
            except Exception:
                pass

    # -------------------------------------------------------------------------
    # 배치 시작/중지
    # -------------------------------------------------------------------------

