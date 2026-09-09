# [중간] 2026-09-09 CLI가 user_settings를 안 읽어 「수신 메일 없음」

- **발생 일시**: 2026-09-09 (`python main.py --auto` / `auto_runner`)
- **심각도**: 중간 (메일 미발송·설정이 “날아간” 것처럼 보임)
- **관련 파일**: `auto_runner.py`, `main.py`, `config.py`, `data/user_settings.json`

---

## 1. 증상

설정 창에 알림 수신 메일(`won@kyungsaneng.co.kr`)을 저장해 두었는데 CLI 종료 시:

```
⚠️ 설정된 수신 메일 주소가 없습니다. 이메일을 발송할 수 없습니다.
```

## 2. 영향 범위

- CLI 자동조회 후 알림메일 시트 기록·즉시 GAS 발송이 스킵됨
- 사용자는 “설정이 사라졌다”고 오해하기 쉬움

## 3. 근본 원인

| 진입점 | `config.load_user_settings()` |
| --- | --- |
| `main.py` (GUI) | 있음 |
| `auto_runner.py` (CLI) | **원래부터 없음** (삭제가 아니라 누락) |

`NOTIFICATION_EMAIL_ADDRESS` 기본값은 `config.py`의 `""`이다.
JSON에는 값이 있어도 CLI 메모리는 비어 있었다.

## 4. 왜 막지 못했나

- GUI/CLI 진입점 비대칭이 `AGENTS.md`에 없었음
- “설정 없음” 로그가 **로드 누락**과 **진짜 미설정**을 구분하지 않음
- 에이전트가 `auto_runner`를 넓게 고치면서도 설정 로드를 점검하지 않음

## 5. 복구 방법

`auto_runner.py` import 직후:

```python
config.load_user_settings()
```

수정 후 재실행 → 주소 경고 없음. (즉시 GAS는 별건으로 401 날 수 있음)

## 6. 재발 방지 — 지우지 말 것

| 위치 | 가드 |
| --- | --- |
| `auto_runner.py` 상단 | `load_user_settings()` 호출 + “없으면 메일/시트 설정 빈값” 주석 |
| `AGENTS.md` 「진입점·설정 로드」 | 사용자 지시 없이 로드 경로 삭제·우회 금지. “설정 없음”이면 먼저 로드 여부 확인 |

## 7. 교훈

1. **설정은 파일이 아니라 “로드된 메모리”다.** 진입점마다 로드가 필요하다.
2. **보호해야 할 경로는 AGENTS/주석에 명시**해 에이전트·사람이 함부로 빼지 않게 할 것.
3. 증상 로그에 `user_settings 로드 여부`를 남기면 원인 파악이 빠르다.
