"""숫자 캡차(자동입력방지문자) 이미지 OCR 인식 모듈 (독립 실행형).

court_monitor 프로젝트의 captcha_ocr.py에서 config.py 의존성을 제거하고
다른 프로젝트에 그대로 옮겨 쓸 수 있게 만든 버전입니다.

처리 순서: 전처리 -> EasyOCR 시도 -> 신뢰도 부족/실패 시 Tesseract로 폴백.

설치:
    pip install easyocr opencv-python-headless pillow numpy pytesseract
    (Tesseract 폴백을 쓰려면 Tesseract OCR 엔진도 별도 설치 후 PATH 등록)
    https://github.com/UB-Mannheim/tesseract/wiki

사용 예:
    from captcha_ocr import recognize_captcha

    with open("captcha.png", "rb") as f:
        image_bytes = f.read()

    result = recognize_captcha(image_bytes, digit_count=6)
    if result.is_valid_length and result.is_confident:
        print(result.text, result.confidence, result.engine)
"""
import re
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image

_DIGIT_RE = re.compile(r"\d")
_easyocr_reader = None


@dataclass
class OcrResult:
    text: str
    confidence: float
    engine: str          # "easyocr" | "tesseract"
    digit_count: int = 6
    confidence_threshold: float = 0.7

    @property
    def is_valid_length(self) -> bool:
        return len(self.text) == self.digit_count

    @property
    def is_confident(self) -> bool:
        return self.confidence >= self.confidence_threshold


def _get_easyocr_reader():
    """EasyOCR Reader는 초기화가 느리므로 최초 1회만 생성해 재사용합니다."""
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr  # 지연 임포트

        _easyocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    return _easyocr_reader


def preprocess(image_bytes: bytes) -> np.ndarray:
    """흑백 변환 -> 3배 확대 -> 노이즈 제거 -> 대비 강화.

    숫자 캡차처럼 왜곡이 심하지 않은 이미지에서 OCR 정확도를 크게 높여줍니다.
    """
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("이미지를 디코딩할 수 없습니다. 유효한 이미지 바이트인지 확인하세요.")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    h, w = gray.shape
    resized = cv2.resize(gray, (w * 3, h * 3), interpolation=cv2.INTER_CUBIC)

    denoised = cv2.fastNlMeansDenoising(resized, h=10)

    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrasted = clahe.apply(denoised)

    return contrasted


def _extract_digits(text: str) -> str:
    return "".join(_DIGIT_RE.findall(text))


def recognize_with_easyocr(processed_img: np.ndarray) -> tuple[str, float]:
    """반환: (인식된 숫자 문자열, 평균 신뢰도 0~1)"""
    reader = _get_easyocr_reader()
    results = reader.readtext(
        processed_img,
        allowlist="0123456789",
        detail=1,
        paragraph=False,
    )

    if not results:
        return "", 0.0

    text = _extract_digits("".join(r[1] for r in results))
    avg_conf = sum(r[2] for r in results) / len(results)
    return text, avg_conf


def recognize_with_tesseract(processed_img: np.ndarray) -> str:
    """반환: 인식된 숫자 문자열. (Tesseract는 신뢰도를 신뢰성 있게 안 주므로 별도 반환 안 함)"""
    import pytesseract

    pil_img = Image.fromarray(processed_img)
    config_str = "--psm 7 -c tessedit_char_whitelist=0123456789"
    text = pytesseract.image_to_string(pil_img, config=config_str)
    return _extract_digits(text)


def recognize_captcha(
    image_bytes: bytes,
    digit_count: int = 6,
    confidence_threshold: float = 0.7,
) -> OcrResult:
    """숫자 캡차 이미지를 인식합니다.

    Args:
        image_bytes: 캡차 이미지 원본 바이트 (png/jpg 등, cv2.imdecode가 지원하는 포맷)
        digit_count: 캡차 자릿수 (기본 6자리)
        confidence_threshold: 이 값 이상이면 EasyOCR 결과를 신뢰(0~1, 기본 0.7)

    Returns:
        OcrResult(text, confidence, engine, ...). text가 빈 문자열이면 두 엔진 모두 실패한 것.
        호출 측에서 result.is_valid_length / result.is_confident로 재시도 여부를 판단하면 됩니다.
    """
    processed = preprocess(image_bytes)

    easy_text, easy_conf = "", 0.0
    try:
        easy_text, easy_conf = recognize_with_easyocr(processed)
        result = OcrResult(easy_text, easy_conf, "easyocr", digit_count, confidence_threshold)
        if result.is_valid_length and result.is_confident:
            return result
    except Exception:
        result = OcrResult("", 0.0, "easyocr", digit_count, confidence_threshold)

    try:
        tess_text = recognize_with_tesseract(processed)
        tess_conf = 1.0 if len(tess_text) == digit_count else 0.0
        if len(tess_text) == digit_count:
            return OcrResult(tess_text, tess_conf, "tesseract", digit_count, confidence_threshold)
    except Exception:
        pass

    # 둘 다 자릿수를 못 맞추면 EasyOCR 결과(빈 값일 수 있음)를 그대로 반환.
    # 호출 측에서 이미지를 새로고침해 재시도하는 로직을 두는 것을 권장합니다.
    return result
