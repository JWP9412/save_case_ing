# CHANGELOG v4.0.0 (2026-01-28)

## Features & Improvements

- **배너 이미지 표시 수정 및 크기 최적화**
  - `CTkImage` 타입 오류 수정: `light_image`/`dark_image`에 파일 경로(문자열) 대신 PIL `Image` 객체를 전달하도록 변경. CustomTkinter 요구사항에 맞춰 배너가 정상 표시되도록 함.
  - 배너 이미지 크기 조정: 헤더 프레임 높이(120px)에 맞춰 세로를 채우고, 가로는 비율 유지·최대 900px로 제한. 기존 400×100 제한을 제거하여 배너 영역을 활용하도록 개선.

## Technical

- **batch_gui_maker.py** `create_header`:
  - 배너 로드 시 `Image.open(banner_path)`로 PIL 이미지를 열어 `CTkImage(light_image=pil_img, dark_image=pil_img, size=(w, h))`로 전달.
  - 스케일 계산: `scale = min(banner_h / bh, max_banner_w / bw)` (banner_h=120, max_banner_w=900).
