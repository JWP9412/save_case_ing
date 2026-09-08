# -*- coding: utf-8 -*-
"""
캡차 OCR 서비스 (ocr_export 래퍼)
==================================

ocr_export/captcha_ocr.py를 case-ing 앱에서 안전하게 호출하기 위한 얇은 래퍼입니다.

주니어 개발자 참고:
- EasyOCR·opencv 등이 설치되지 않았거나 import에 실패해도 앱 전체가 죽지 않도록
  try/except로 감싸고, 실패 시 None을 반환합니다(수동 입력 폴백).
- image_path는 Puppeteer가 저장한 디스크 경로(str)입니다. bytes로 읽어 OCR에 넘깁니다.
- 병렬 레인이 동시에 OCR을 호출해도 `_ocr_call_lock`으로 한 번에 하나만 실행합니다.
  (EasyOCR/Torch 동시 초기화 → Windows access violation 방지)
"""
from __future__ import annotations

import os
import sys
import threading
from dataclasses import dataclass
from typing import Optional

import config
from services.logger_service import get_logger

logger = get_logger("captcha_ocr_service")

# ocr_export 폴더를 import 경로에 추가 (독립 모듈 captcha_ocr.py)
_OCR_EXPORT_DIR = config.path_from_base("ocr_export")
if _OCR_EXPORT_DIR not in sys.path:
    sys.path.insert(0, _OCR_EXPORT_DIR)

_recognize_captcha = None
_OcrResult = None
_is_easyocr_loaded = None
_ensure_easyocr_loaded = None
_import_error: Optional[str] = None
# 앱 경로에서도 OCR 호출을 직렬화 (ocr_export 락과 이중 안전)
_ocr_call_lock = threading.Lock()

try:
    from captcha_ocr import OcrResult as _OcrResultCls
    from captcha_ocr import ensure_easyocr_loaded as _ensure_easyocr_loaded_fn
    from captcha_ocr import is_easyocr_loaded as _is_easyocr_loaded_fn
    from captcha_ocr import recognize_captcha as _recognize_captcha_fn
    from captcha_ocr import unload_easyocr as _unload_easyocr_fn

    _recognize_captcha = _recognize_captcha_fn
    _OcrResult = _OcrResultCls
    _is_easyocr_loaded = _is_easyocr_loaded_fn
    _ensure_easyocr_loaded = _ensure_easyocr_loaded_fn
    _unload_easyocr = _unload_easyocr_fn
except Exception as exc:  # ImportError, DLL 오류 등
    _import_error = str(exc)
    _unload_easyocr = None


@dataclass
class CaptchaOcrSuccess:
    """OCR 성공 시 process_controller에 넘기는 결과."""

    text: str
    confidence: float
    engine: str


def ocr_import_available() -> bool:
    """OCR 의존성 import 가능 여부."""
    return _recognize_captcha is not None


def ocr_import_error_message() -> Optional[str]:
    return _import_error


def recognize_from_path(image_path: str) -> Optional[CaptchaOcrSuccess]:
    """
    캡차 PNG 경로에서 숫자를 인식합니다.

    반환:
    - CaptchaOcrSuccess: 자릿수·신뢰도 조건 통과
    - None: 비활성, CLICK, 파일 없음, import 실패, 인식 실패
    """
    if not getattr(config, "OCR_ENABLED", False):
        return None
    if not image_path or image_path == "__CLICK__":
        return None
    if not os.path.isfile(image_path):
        return None
    if _recognize_captcha is None:
        return None

    digit_count = getattr(config, "OCR_DIGIT_COUNT", 6)
    threshold = getattr(config, "OCR_CONFIDENCE_THRESHOLD", 0.7)

    with _ocr_call_lock:
        try:
            # 최초 1회: 모델 로딩은 수 초~수십 초·메모리 많이 씀 → 안내 로그
            if _is_easyocr_loaded is not None and _ensure_easyocr_loaded is not None:
                if not _is_easyocr_loaded():
                    logger.info("EasyOCR 모델 로딩 중(최초 1회, 잠시 기다려 주세요)...")
                    _ensure_easyocr_loaded()
                    logger.info("EasyOCR 모델 로딩 완료")

            with open(image_path, "rb") as f:
                image_bytes = f.read()
            result = _recognize_captcha(
                image_bytes,
                digit_count=digit_count,
                confidence_threshold=threshold,
            )
            if result.is_valid_length and result.is_confident:
                return CaptchaOcrSuccess(
                    text=result.text,
                    confidence=float(result.confidence),
                    engine=str(result.engine),
                )
        except Exception as e:
            logger.warning(f"OCR 인식 실패(수동 폴백): {e}")
            return None
    return None


def warmup_easyocr_async() -> None:
    """
    EasyOCR 모델을 백그라운드 스레드에서 미리 로드합니다.
    GUI 시작 직후 호출하면 첫 사건 OCR 대기(약 20초)를 없앱니다.
    """
    if not getattr(config, "OCR_ENABLED", False):
        return
    if _ensure_easyocr_loaded is None:
        return

    def _run():
        try:
            if _is_easyocr_loaded is not None and _is_easyocr_loaded():
                return
            logger.info("EasyOCR 백그라운드 워밍업 시작...")
            with _ocr_call_lock:
                _ensure_easyocr_loaded()
            logger.info("EasyOCR 백그라운드 워밍업 완료")
        except Exception as e:
            logger.warning("EasyOCR 워밍업 실패(무시, 첫 OCR 시 재시도): %s", e)

    threading.Thread(target=_run, daemon=True, name="easyocr-warmup").start()


def unload_easyocr_model() -> None:
    """유휴 시 EasyOCR 메모리 해제."""
    if _unload_easyocr is None:
        return
    try:
        with _ocr_call_lock:
            _unload_easyocr()
        logger.info("EasyOCR 모델 언로드 완료")
    except Exception as e:
        logger.warning("EasyOCR 언로드 실패: %s", e)
