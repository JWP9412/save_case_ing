"""숫자 캡차 전용 커스텀 CNN 모델 (독립 실행형).

captcha_ocr.py(EasyOCR/Tesseract)만으로 정확도가 부족할 때 쓰는 선택 사항입니다.
같은 사이트의 캡차 이미지를 다수(수백 장 이상) 모아 train_captcha_model.py로 학습시키면,
그 사이트 캡차 폰트/스타일에 특화된 인식기를 만들 수 있습니다.

입력 이미지 크기는 IMG_WIDTH x IMG_HEIGHT로 리사이즈되므로, 원본 캡차 이미지의
가로세로 비율이 크게 다르면 이 값들을 대상 캡차 크기에 맞게 조정하세요.

사용 예:
    from captcha_model import load_model, predict

    model = load_model("models/captcha_model.pt")
    text, confidence = predict(image_bytes, model)
"""
import io

import numpy as np
import torch
import torch.nn as nn
from PIL import Image

IMG_WIDTH = 121
IMG_HEIGHT = 46
NUM_DIGITS = 6          # 캡차 자릿수. 대상 사이트에 맞게 조정하세요.
NUM_CLASSES = 10        # 0~9


class CaptchaCNN(nn.Module):
    def __init__(self, num_digits: int = NUM_DIGITS):
        super().__init__()
        self.num_digits = num_digits
        self.features = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
        )
        with torch.no_grad():
            dummy = torch.zeros(1, 1, IMG_HEIGHT, IMG_WIDTH)
            self.flat_dim = self.features(dummy).numel()
        self.fc = nn.Sequential(nn.Linear(self.flat_dim, 256), nn.ReLU(), nn.Dropout(0.3))
        self.heads = nn.ModuleList([nn.Linear(256, NUM_CLASSES) for _ in range(num_digits)])

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return [head(x) for head in self.heads]


def image_bytes_to_tensor(image_bytes: bytes) -> torch.Tensor:
    img = Image.open(io.BytesIO(image_bytes)).convert("L").resize((IMG_WIDTH, IMG_HEIGHT))
    arr = np.asarray(img, dtype=np.float32) / 255.0
    tensor = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0)  # (1, 1, H, W)
    return tensor


_model_cache = None


def load_model(path: str, num_digits: int = NUM_DIGITS) -> CaptchaCNN:
    """모델 가중치 파일(.pt)을 로드합니다. 최초 호출 후 캐시해 재사용합니다."""
    global _model_cache
    if _model_cache is None:
        model = CaptchaCNN(num_digits)
        model.load_state_dict(torch.load(path, map_location="cpu"))
        model.eval()
        _model_cache = model
    return _model_cache


def predict(image_bytes: bytes, model: CaptchaCNN):
    """반환: (예측된 N자리 숫자 문자열, 평균 신뢰도 0~1)"""
    tensor = image_bytes_to_tensor(image_bytes)
    with torch.no_grad():
        logits_per_digit = model(tensor)
        digits = []
        confidences = []
        for logits in logits_per_digit:
            probs = torch.softmax(logits, dim=1)[0]
            digit = int(torch.argmax(probs).item())
            digits.append(str(digit))
            confidences.append(float(probs[digit].item()))
    text = "".join(digits)
    avg_confidence = sum(confidences) / len(confidences)
    return text, avg_confidence
