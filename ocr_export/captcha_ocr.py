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

주니어 참고:
- Chrome 브라우저는 병렬로 띄워도 됩니다.
- EasyOCR/PyTorch 모델 로드·인식은 스레드 세이프하지 않습니다.
  동시에 Reader를 만들면 Windows에서 access violation으로 프로세스가 죽을 수 있습니다.
  → `_easyocr_lock`으로 생성·readtext를 한 줄로 직렬화합니다.
"""
import re
import threading
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image

_DIGIT_RE = re.compile(r"\d")
_easyocr_reader = None
# Chrome은 병렬, OCR 모델 로드/인식은 한 줄로 (동시 init → access violation 방지)
_easyocr_lock = threading.Lock()


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


def is_easyocr_loaded() -> bool:
    """EasyOCR Reader가 이미 생성됐는지 (워밍업 로그용)."""
    return _easyocr_reader is not None


def ensure_easyocr_loaded() -> None:
    """
    EasyOCR Reader를 미리(또는 지금) 1회 생성합니다.
    앱에서 '모델 로딩 중' 로그를 찍은 뒤 호출하면 됩니다.
    """
    _get_easyocr_reader()


def _get_easyocr_reader():
    """
    EasyOCR Reader는 초기화가 느리므로 최초 1회만 생성해 재사용합니다.

    double-checked locking: 락 없이 None 체크만 하면 병렬 레인이
    Reader를 두 번 만들어 PyTorch VGG init에서 크래시 납니다.
    """
    global _easyocr_reader
    if _easyocr_reader is not None:
        return _easyocr_reader
    with _easyocr_lock:
        if _easyocr_reader is None:
            import easyocr  # 지연 임포트

            _easyocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        return _easyocr_reader


def preprocess(image_bytes: bytes) -> np.ndarray:
    """흑백 변환 -> 2배 확대 -> 가벼운 노이즈 제거 -> 대비 강화.

    주니어 참고:
    - 예전: 3배 확대 + fastNlMeansDenoising(느림, 픽셀 9배에서 연산).
    - 지금: 2배 확대 + medianBlur(3) — 체감 정확도 유지하면서 CPU 비용 대폭 감소.
    """
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("이미지를 디코딩할 수 없습니다. 유효한 이미지 바이트인지 확인하세요.")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    resized = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    denoised = cv2.medianBlur(resized, 3)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrasted = clahe.apply(denoised)
    return contrasted


def unload_easyocr() -> None:
    """
    EasyOCR Reader를 메모리에서 해제합니다.

    배치가 끝난 뒤 오래 OCR을 안 쓸 때 호출합니다.
    다음 인식 시 _get_easyocr_reader()가 다시 로드합니다.
    """
    global _easyocr_reader
    import gc

    with _easyocr_lock:
        if _easyocr_reader is not None:
            _easyocr_reader = None
            gc.collect()


def _extract_digits(text: str) -> str:
    return "".join(_DIGIT_RE.findall(text))


def recognize_with_easyocr(processed_img: np.ndarray) -> tuple[str, float]:
    """반환: (인식된 숫자 문자열, 평균 신뢰도 0~1). readtext도 락으로 직렬화."""
    reader = _get_easyocr_reader()
    with _easyocr_lock:
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


def recognize_with_tesseract(processed_img: np.ndarray) -> tuple[str, float]:
    """
    반환: (인식된 숫자 문자열, 신뢰도 0~1).

    주니어 참고:
    - 예전에는 자릿수만 맞으면 confidence=1.0 을 가짜로 넣었습니다.
      → 오독(예: 359207→359267)도 자동 제출됐습니다.
    - 지금은 image_to_data 의 문자별 conf(0~100) 평균을 씁니다.
    """
    import pytesseract
    from pytesseract import Output

    pil_img = Image.fromarray(processed_img)
    config_str = "--psm 7 -c tessedit_char_whitelist=0123456789"
    data = pytesseract.image_to_data(pil_img, config=config_str, output_type=Output.DICT)

    texts = []
    confs = []
    for text, conf in zip(data.get("text", []), data.get("conf", [])):
        try:
            conf_i = int(float(conf))
        except (TypeError, ValueError):
            continue
        # conf == -1 은 빈 블록/구분선
        if conf_i < 0:
            continue
        digits = _extract_digits(text or "")
        if not digits:
            continue
        texts.append(digits)
        confs.append(conf_i / 100.0)

    joined = _extract_digits("".join(texts))
    if not joined or not confs:
        # image_to_data 가 비면 string 폴백 (신뢰도는 낮게)
        text = pytesseract.image_to_string(pil_img, config=config_str)
        joined = _extract_digits(text)
        return joined, 0.0 if not joined else 0.5

    avg_conf = sum(confs) / len(confs)
    # 문자 중 가장 낮은 conf 도 반영 (한 글자만 틀려도 낮춤)
    min_conf = min(confs)
    confidence = (avg_conf * 0.7) + (min_conf * 0.3)
    return joined, float(confidence)


def recognize_captcha(
    image_bytes: bytes,
    digit_count: int = 6,
    confidence_threshold: float = 0.7,
) -> OcrResult:
    """숫자 캡차 이미지를 인식합니다.

    Args:
        image_bytes: 캡차 이미지 원본 바이트 (png/jpg 등, cv2.imdecode가 지원하는 포맷)
        digit_count: 캡차 자릿수 (기본 6자리)
        confidence_threshold: 이 값 이상이면 결과를 신뢰(0~1, 기본 0.7)

    Returns:
        OcrResult(text, confidence, engine, ...). text가 빈 문자열이면 두 엔진 모두 실패한 것.
        호출 측에서 result.is_valid_length / result.is_confident로 재시도 여부를 판단하면 됩니다.

    주니어 참고:
    - EasyOCR 우선, 미달 시 Tesseract.
    - 두 엔진 결과가 일치하면 신뢰도를 가산해 자동 제출 우선순위를 높입니다.
    """
    processed = preprocess(image_bytes)

    easy_text, easy_conf = "", 0.0
    easy_result = OcrResult("", 0.0, "easyocr", digit_count, confidence_threshold)
    try:
        easy_text, easy_conf = recognize_with_easyocr(processed)
        easy_result = OcrResult(easy_text, easy_conf, "easyocr", digit_count, confidence_threshold)
        if easy_result.is_valid_length and easy_result.is_confident:
            return easy_result
    except Exception:
        easy_result = OcrResult("", 0.0, "easyocr", digit_count, confidence_threshold)

    tess_text, tess_conf = "", 0.0
    try:
        tess_text, tess_conf = recognize_with_tesseract(processed)
        tess_result = OcrResult(
            tess_text, tess_conf, "tesseract", digit_count, confidence_threshold
        )
        # 두 엔진이 같은 숫자를 냈으면 신뢰도 가산 (교차 검증)
        if (
            easy_result.is_valid_length
            and tess_result.is_valid_length
            and easy_text == tess_text
            and easy_text
        ):
            boosted = min(1.0, max(easy_conf, tess_conf) + 0.15)
            return OcrResult(
                easy_text, boosted, "both", digit_count, confidence_threshold
            )
        if tess_result.is_valid_length and tess_result.is_confident:
            return tess_result
        # 자릿수는 맞지만 신뢰도 미달 → 더 나은 쪽 반환 (호출측이 is_confident로 거름)
        if tess_result.is_valid_length and tess_conf >= easy_conf:
            return tess_result
    except Exception:
        pass

    # EasyOCR 결과(빈 값일 수 있음)를 그대로 반환
    return easy_result