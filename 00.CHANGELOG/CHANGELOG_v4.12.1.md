# CHANGELOG v4.12.1

## v4.12.1 주요 변경 (2026-08-10)

### Bug Fixes

- **Windows node.exe 콘솔 창 숨김**
  - 사건 조회 시 병렬로 뜨던 `node.exe` 검은 콘솔 창을 더 이상 표시하지 않음.
  - `services/puppeteer.py`에서 Windows일 때 `CREATE_NO_WINDOW`로 Node 프로세스를 백그라운드 실행.
  - 캡차·진행내용·일반내용 통신(stdin/stdout)은 기존과 동일.

### 이전 버전 요약 (v4.12.0)

- 일반내용 돋보기 뷰어 (기본내용·기일·제출서류·당사자·대리인 로컬 저장·표시).

## Technical

- `config.py`: `APP_VERSION = "4.12.1"`.
- `services/puppeteer.py`: `os.name == "nt"` 시 `subprocess.CREATE_NO_WINDOW`.
