# 숫자 캡차 OCR 모듈 (이식용)

> 이 폴더를 통째로 대상 프로젝트에 복사해 넣고, `captcha_ocr.py`를 import해서 쓰면 됩니다.
> Cursor 등 AI 코딩 도구에게 이 파일을 붙여넣고 "이 모듈을 내 프로젝트의 OO 기능에 연동해줘"라고
> 요청하면 아래 내용을 근거로 통합해줄 수 있습니다.

## 이 모듈이 하는 일

숫자로만 이루어진 캡차(자동입력방지문자) 이미지를 받아서 문자열로 인식합니다.
전처리 후 **EasyOCR을 먼저 시도하고, 신뢰도가 낮거나 실패하면 Tesseract로 자동 폴백**합니다.

- 입력: 캡차 이미지의 raw bytes (`png`/`jpg` 등 `cv2.imdecode`가 읽을 수 있는 포맷)
- 출력: `OcrResult(text, confidence, engine, ...)` 데이터클래스

## 설치

```bash
pip install -r requirements.txt
```

Tesseract 폴백까지 쓰려면 Tesseract OCR 엔진 자체도 설치하고 PATH에 등록해야 합니다.
(안 해도 EasyOCR만으로 동작은 합니다. 다만 폴백이 빠집니다.)
https://github.com/UB-Mannheim/tesseract/wiki

## 파일 구성

- `captcha_ocr.py` — 기본 OCR 로직 (EasyOCR → Tesseract 폴백). 외부 프로젝트 설정(config.py) 의존성 없음.
- `captcha_model.py` — (선택) 캡차 전용 커스텀 CNN 모델 정의 + 추론 함수.
- `train_captcha_model.py` — (선택) 캡차 샘플 이미지로 위 CNN을 학습시키는 스크립트.
- `requirements.txt` — 필요한 패키지 목록. torch는 CNN을 쓸 때만 필요.

## API

```python
from captcha_ocr import recognize_captcha, OcrResult

result: OcrResult = recognize_captcha(
    image_bytes,              # 캡차 이미지 bytes
    digit_count=6,             # 캡차 자릿수 (기본 6)
    confidence_threshold=0.7,  # EasyOCR 결과를 신뢰할 최소 신뢰도 (기본 0.7)
)

result.text                # 인식된 숫자 문자열 (실패 시 "" 일 수 있음)
result.confidence          # 0~1 신뢰도 (Tesseract 결과는 1.0 또는 0.0으로 근사)
result.engine               # "easyocr" 또는 "tesseract"
result.is_valid_length      # len(text) == digit_count 인지
result.is_confident         # confidence >= confidence_threshold 인지
```

## 통합 시 권장 패턴: 재시도 루프

**이 모듈 자체는 재시도를 하지 않습니다.** 캡차는 한 번에 못 맞힐 수 있으므로,
호출하는 쪽(브라우저 자동화 등)에서 "인식 결과를 제출 → 서버가 불일치라고 응답하면
캡차 이미지를 새로고침하고 다시 인식"하는 루프를 직접 감싸야 합니다. 예시:

```python
from captcha_ocr import recognize_captcha

MAX_RETRIES = 10

def solve_captcha(get_image_bytes, reload_image, submit_and_check):
    """
    get_image_bytes: () -> bytes            현재 캡차 이미지를 가져오는 함수
    reload_image:    () -> None              캡차 이미지를 새로고침하는 함수
    submit_and_check:(text: str) -> bool     인식값을 제출하고 성공 여부를 반환하는 함수
    """
    for attempt in range(MAX_RETRIES):
        image_bytes = get_image_bytes()
        result = recognize_captcha(image_bytes, digit_count=6, confidence_threshold=0.7)

        if not result.is_valid_length:
            reload_image()
            continue

        if submit_and_check(result.text):
            return True

        reload_image()  # 제출했지만 서버가 불일치라고 응답한 경우

    return False
```

이렇게 "낮은 확률로도 여러 번 시도"하는 구조가, 캡차 자체 난이도가 낮은 것과 맞물려
실전에서 충분히 높은 성공률을 냅니다. 자릿수/임계값(`digit_count`, `confidence_threshold`)과
`MAX_RETRIES`는 대상 사이트의 캡차 난이도에 맞춰 조정하세요.

## 커스텀 CNN 모델 (선택)

`captcha_ocr.py`(EasyOCR/Tesseract)만으로 정확도가 부족하면, 같은 사이트 캡차에 특화된
전용 CNN을 직접 학습시켜 쓸 수 있습니다.

### 1. 학습 데이터 모으기

`captcha_ocr.recognize_captcha()`로 인식에 성공(자릿수 일치 + 신뢰도 통과)한 이미지를
`"{정답숫자}_{아무문자열}.png"` 형식 파일명으로 저장해 한 폴더(예: `captcha_samples/`)에
계속 쌓으세요. 최소 수백 장 이상 모이면 학습 효과가 납니다.

```python
def save_sample(image_bytes: bytes, recognized_text: str, digit_count: int, out_dir: str):
    import os, time
    if len(recognized_text) != digit_count:
        return
    os.makedirs(out_dir, exist_ok=True)
    filename = f"{recognized_text}_{time.strftime('%Y%m%d_%H%M%S')}.png"
    with open(os.path.join(out_dir, filename), "wb") as f:
        f.write(image_bytes)
```

### 2. 학습

```bash
pip install torch
python train_captcha_model.py --samples-dir captcha_samples --out models/captcha_model.pt --epochs 30
```

캡차 자릿수가 6자리가 아니면 `captcha_model.py`의 `NUM_DIGITS`와
`train_captcha_model.py --num-digits`를 대상 사이트에 맞게 바꾸세요. 이미지 가로세로 비율이
크게 다르면 `captcha_model.py`의 `IMG_WIDTH` / `IMG_HEIGHT`도 조정하세요.

### 3. 추론에서 사용

```python
from captcha_model import load_model, predict
from captcha_ocr import recognize_captcha

model = load_model("models/captcha_model.pt")

def recognize(image_bytes: bytes):
    # 커스텀 모델을 먼저 시도하고, 실패하면 기본 OCR로 폴백
    text, confidence = predict(image_bytes, model)
    if len(text) == 6 and confidence >= 0.9:
        return text
    return recognize_captcha(image_bytes).text
```
