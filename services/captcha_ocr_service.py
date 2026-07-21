# -*- coding: utf-8 -*-
"""
캡차 OCR 서비스 (ocr_export 래퍼)
==================================

ocr_export/captcha_ocr.py를 case-ing 앱에서 안전하게 호출하기 위한 얇은 래퍼입니다.

주니어 개발자 참고:
- EasyOCR·opencv 등이 설치되지 않았거나 import에 실패해도 앱 전체가 죽지 않도록
  try/except로 감싸고, 실패 시 None을 반환합니다(수동 입력 폴백).
- image_path는 Puppeteer가 저장한 디스크 경로(str)입니다. bytes로 읽어 OCR에 넘깁니다.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional

import config

# ocr_export 폴더를 import 경로에 추가 (독립 모듈 captcha_ocr.py)
_OCR_EXPORT_DIR = config.path_from_base("ocr_export")
if _OCR_EXPORT_DIR not in sys.path:
    sys.path.insert(0, _OCR_EXPORT_DIR)

_recognize_captcha = None
_OcrResult = None
_import_error: Optional[str] = None

try:
    from captcha_ocr import OcrResult as _OcrResultCls
    from captcha_ocr import recognize_captcha as _recognize_captcha_fn

    _recognize_captcha = _recognize_captcha_fn
    _OcrResult = _OcrResultCls
except Exception as exc:  # ImportError, DLL 오류 등
    _import_error = str(exc)


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

    try:
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
    except Exception:
        return None
    return None
