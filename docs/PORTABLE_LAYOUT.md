# 포터블 배포 폴더 레이아웃 (조립 규칙)

빌드 스크립트(`scripts/build_portable.ps1`)가 만드는 **최종 배포 폴더** 구조입니다.
사용자에게는 이 폴더를 zip으로 압축해 전달합니다.

```
case-ing-portable/
  CaseIng.exe              # 더블클릭 실행 (PyInstaller onedir)
  _internal/               # PyInstaller가 넣는 Python 런타임·의존성 (자동 생성)
  runtime/
    node/                  # Node.js Windows x64 포터블 (node.exe 포함)
      node.exe
      ...
    puppeteer/             # Chrome 브라우저 (puppeteer 캐시 — .puppeteerrc.cjs가 지정)
      chrome/
  src/                     # Puppeteer 스크립트 (interactive_runner.js 등)
  node_modules/            # npm install 결과 (puppeteer 라이브러리)
  package.json
  .puppeteerrc.cjs         # puppeteer가 Chrome을 runtime/puppeteer에서 찾도록 지정
  ocr_export/              # EasyOCR 래퍼 (captcha_ocr.py)
  api/
    certification/
      README.md            # client_secret.json 넣는 방법
      # client_secret.json  ← 배포자가 직접 넣거나, 사용자가 추가
  assets/                  # 배너 이미지 등
  data/                    # 빈 폴더(또는 .gitkeep). 실행 후 토큰·캐시 생성
  docs/
    DEPLOY_WINDOWS.md      # 사용자 안내
```

## 포함하지 않는 것

| 항목 | 이유 |
|------|------|
| `.venv/`, `build/`, 소스 전체 gui/services | exe·_internal에 이미 포함 |
| `cookie_data_for_save/` | PC마다 새로 생성 |
| `data/google_user_token.json` | 개인 계정 토큰 — 새 PC에서 로그인 |
| `screenshots/`, `results/`, `logs/` | 런타임 생성 |
| `service-account.json` / `client_secret.json` (git) | 비밀 — 수동 배치 |

## 경로 규칙

- 앱은 `config.BASE_DIR` = **CaseIng.exe가 있는 폴더** 를 루트로 사용합니다.
- Node는 `runtime/node/node.exe` 를 먼저 찾고, 없으면 PATH의 `node`를 씁니다.
- `cwd`는 항상 `BASE_DIR` 이라 `src/`, `cookie_data_for_save/` 상대경로가 맞습니다.
- Chrome은 `.puppeteerrc.cjs` 덕분에 `runtime/puppeteer/` 에서 찾습니다.
  (기본값인 사용자 홈 `~/.cache/puppeteer` 를 쓰면 다른 PC에서 Chrome이 없어 실패)
