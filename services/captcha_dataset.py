# -*- coding: utf-8 -*-
"""
캡차 학습 데이터 자동 수집
==========================
제출에 성공한 캡차 이미지를 정답 라벨과 함께 저장합니다.
WRONG_CAPTCHA(오답)도 별도 폴더에 남겨 오독 패턴 분석에 씁니다.

주니어 참고:
- 지금 당장 모델을 학습하지 않습니다. 데이터만 쌓습니다.
- 수백~수천 장이 모이면 scripts/train_captcha_cnn.py 로 경량 CNN을 학습할 수 있습니다.
- screenshots/ 정리와 무관하게 data/captcha_dataset/ 에 복사본을 둡니다.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime
from typing import Optional

import config
from services.logger_service import get_logger

logger = get_logger("captcha_dataset")


def _dataset_dir() -> str:
    rel = getattr(config, "CAPTCHA_DATASET_DIR", "data/captcha_dataset")
    if hasattr(config, "path_from_base"):
        return config.path_from_base(rel)
    return os.path.abspath(rel)


def _labels_path() -> str:
    return os.path.join(_dataset_dir(), "labels.jsonl")


def record_sample(
    image_path: str,
    label: str,
    *,
    source: str = "unknown",
    ocr_guess: Optional[str] = None,
    ocr_confidence: Optional[float] = None,
    ocr_engine: Optional[str] = None,
    is_correct: bool = True,
) -> bool:
    """
    캡차 이미지를 데이터셋에 복사하고 labels.jsonl 에 한 줄 추가합니다.

    Args:
        image_path: 원본 캡차 PNG 경로
        label: 제출에 사용한(또는 실제) 6자리 숫자
        source: "ocr" | "manual" | "wrong" 등
        ocr_guess / ocr_confidence / ocr_engine: OCR 추정값(있으면)
        is_correct: True=정답(성공 제출), False=오답(WRONG_CAPTCHA)

    Returns:
        저장 성공 여부
    """
    if not getattr(config, "CAPTCHA_DATASET_ENABLED", True):
        return False
    if not image_path or image_path == "__CLICK__":
        return False
    if not os.path.isfile(image_path):
        return False
    label = (label or "").strip()
    if not (len(label) == 6 and label.isdigit()):
        return False

    try:
        base = _dataset_dir()
        sub = "correct" if is_correct else "wrong"
        out_dir = os.path.join(base, sub)
        os.makedirs(out_dir, exist_ok=True)

        # 같은 이미지는 해시로 중복 방지
        with open(image_path, "rb") as f:
            raw = f.read()
        digest = hashlib.md5(raw).hexdigest()[:12]
        filename = f"{label}_{digest}.png"
        dest = os.path.join(out_dir, filename)
        if not os.path.isfile(dest):
            shutil.copy2(image_path, dest)

        entry = {
            "file": f"{sub}/{filename}",
            "label": label,
            "source": source,
            "is_correct": is_correct,
            "ocr_guess": ocr_guess,
            "ocr_confidence": ocr_confidence,
            "ocr_engine": ocr_engine,
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(_labels_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        logger.info(
            "캡차 데이터셋 저장: %s (%s, correct=%s)",
            filename,
            source,
            is_correct,
        )
        return True
    except Exception as e:
        logger.warning("캡차 데이터셋 저장 실패: %s", e)
        return False
