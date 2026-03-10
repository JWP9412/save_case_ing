# case-ing

대법원 나의 사건 조회 자동화 시스템 (Puppeteer + Python GUI) - v4.3.99

## 원본 출처

이 프로젝트는 [iicdii/case-ing](https://github.com/iicdii/case-ing)를 기반으로 하여 **Puppeteer 기반 병렬 처리** 및 **Python GUI 일괄 처리 시스템**으로 전환한 포크 버전입니다.

**원본 저장소**: https://github.com/iicdii/case-ing  
**포크 저장소**: https://github.com/JWP9412/save_case_ing

<a href="https://github.com/iicdii/case-ing/blob/master/LICENSE" alt="License">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" />
</a>

case-ing는 case + ~ing의 합성어로 여러 개의 사건 진행현황을 쉽게 조회하도록 도와주는 자동화 도구입니다.

---

## 현재 버전 특징 (v4.3.99)

### 주요 개선 사항

1. **아키텍처 정리** *(v4.3.99)*
   - 메인 GUI를 `gui/app_controller.py`의 `AppController`로 통합. `batch_gui_maker.py` 제거.
   - `utils/` 폴더 제거. `email_manager.py`를 `services/`로 이동.
   - ProcessController에서 Tkinter 의존성 제거, UI는 app 위임 및 ui_queue로만 처리.

2. **CLI 자동 실행(Auto-run) 안정화** *(v4.3.0)*
   - `--auto` 옵션으로 백그라운드 자동 조회. GUI와 동일한 2단계(브라우저 기동 -> 클릭 명령) 프로세스.
   - 다중 접속 시 프로필 락 지원.

3. **이메일 요약 리포트 디자인 개편** *(v4.3.0)*
   - **[사건번호 | 피고/사건명]** 구조의 HTML 표. 결과 상태별 그룹화.

4. **안정성 및 오류 처리 강화** *(v4.2.2)*
   - 사건 조회 실패 시 알림 및 실패 건 자동 재실행.

5. **알림메일 고도화** *(v4.2.0)*
   - 메일 본문 HTML 표·시트별 그룹화. GAS 웹 앱 연동 즉시 발송.

---

## 프로젝트 구조

```
case-ing/
├── auto_runner.py               CLI 실행기 (MockApp 인터페이스 통일)
├── config.py                    설정 상수 (APP_VERSION = "4.3.99" 등)
├── main.py                      진입점 (run_app 또는 run_auto_batch)
├── data/                        설정 및 이력용 JSON 통합 폴더
├── src/                         Puppeteer 자동화 코드
├── services/                    비즈니스 로직 (process_controller, email_manager, google_sheets 등)
├── gui/                         UI (app_controller, main_window, panels, dialogs, utils)
├── gas/                         GAS 스크립트 (즉시 발송 지원)
└── 00.CHANGELOG, 00.README      버전별 문서
```

---

## 사용법

### 1. GUI 모드 실행
```bash
python main.py
```

### 2. CLI 자동 실행 모드 (v4.3.0 안정화)
작업 스케줄러 등을 통해 백그라운드에서 주기적으로 조회를 실행할 때 사용합니다.
```bash
python main.py --auto
```

---

## 개발 히스토리

- **v4.3.99**: 아키텍처 정리(AppController 통합, utils 제거, services 리팩터링), GitHub 푸시 전 정리
- **v4.3.0**: CLI 자동 실행 안정화, 이메일 요약 표 디자인 개편
- **v4.2.2**: batch_gui_maker 리팩터링, 프로세스 컨트롤러 분리
- **v4.2.0**: 알림메일 고도화(HTML·그룹화·즉시 발송)
- **v4.1.2**: 사건 목록 UI 분리

상세 변경 이력: [00.CHANGELOG/CHANGELOG_v4.3.99.md](00.CHANGELOG/CHANGELOG_v4.3.99.md)  
버전별 README: [00.README/](00.README/)

---

## 라이선스

MIT License
