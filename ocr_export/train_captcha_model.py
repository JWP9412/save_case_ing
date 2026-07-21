"""캡차 샘플 이미지 폴더로 커스텀 CNN 모델을 학습합니다 (독립 실행형).

사용법:
    python train_captcha_model.py --samples-dir captcha_samples --out models/captcha_model.pt --epochs 30

샘플 이미지 파일명 규칙: "{N자리숫자}_{임의문자열}.png" (예: "482913_20260710_083000.png")
정답 라벨은 파일명의 첫 "_" 앞부분에서 읽어옵니다.

샘플은 captcha_ocr.py로 인식에 성공한 이미지를 저장해 모아두면 됩니다
(정답 여부를 별도로 검증했다면 그 라벨로 파일명을 지어도 됩니다).
"""
import argparse
import glob
import os

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split

from captcha_model import CaptchaCNN, image_bytes_to_tensor, NUM_DIGITS


class CaptchaDataset(Dataset):
    def __init__(self, sample_dir: str):
        self.paths = glob.glob(os.path.join(sample_dir, "*.png"))
        if not self.paths:
            raise RuntimeError(f"{sample_dir}에 학습용 샘플 이미지가 없습니다.")

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, idx):
        path = self.paths[idx]
        label = os.path.basename(path).split("_")[0]
        with open(path, "rb") as f:
            tensor = image_bytes_to_tensor(f.read()).squeeze(0)  # (1, H, W)
        target = torch.tensor([int(c) for c in label], dtype=torch.long)
        return tensor, target


def train(samples_dir: str, out_path: str, epochs: int, batch_size: int, lr: float, num_digits: int):
    dataset = CaptchaDataset(samples_dir)
    val_len = max(1, int(len(dataset) * 0.1))
    train_len = len(dataset) - val_len
    train_ds, val_ds = random_split(dataset, [train_len, val_len])

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)

    model = CaptchaCNN(num_digits)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for images, targets in train_loader:
            optimizer.zero_grad()
            outputs = model(images)  # list of num_digits tensors (batch, 10)
            loss = sum(criterion(outputs[i], targets[:, i]) for i in range(num_digits))
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        model.eval()
        correct_digits = correct_full = total = 0
        with torch.no_grad():
            for images, targets in val_loader:
                outputs = model(images)
                preds = torch.stack([o.argmax(dim=1) for o in outputs], dim=1)
                correct_digits += (preds == targets).sum().item()
                correct_full += (preds == targets).all(dim=1).sum().item()
                total += targets.size(0)

        digit_acc = correct_digits / (total * num_digits) if total else 0.0
        full_acc = correct_full / total if total else 0.0
        print(f"epoch {epoch}/{epochs} loss={total_loss:.4f} "
              f"digit_acc={digit_acc:.3f} full_acc={full_acc:.3f}")

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    torch.save(model.state_dict(), out_path)
    print(f"모델 저장 완료: {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples-dir", default="captcha_samples")
    parser.add_argument("--out", default="models/captcha_model.pt")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--num-digits", type=int, default=NUM_DIGITS)
    args = parser.parse_args()
    train(args.samples_dir, args.out, args.epochs, args.batch_size, args.lr, args.num_digits)
