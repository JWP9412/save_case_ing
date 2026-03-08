# case-ing

대법원 나의 사건 조회 자동화 시스템 (Puppeteer + Python GUI) - v4.3.0

## 원본 출처

이 프로젝트는 [iicdii/case-ing](https://github.com/iicdii/case-ing)를 기반으로 하여 **Puppeteer 기반 병렬 처리** 및 **Python GUI 일괄 처리 시스템**으로 전환한 포크 버전입니다.

**원본 저장소**: https://github.com/iicdii/case-ing  
**포크 저장소**: https://github.com/JWP9412/save_case_ing

<a href="https://github.com/iicdii/case-ing/blob/master/LICENSE" alt="License">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" />
</a>

case-ing는 case + ~ing의 합성어로 여러 개의 사건 진행현황을 쉽게 조회하도록 도와주는 자동화 도구입니다.

---

## 현재 버전 특징 (v4.3.0)

### 주요 개선 사항

1. **CLI 자동 실행(Auto-run) 안정화** *(v4.3.0 신규)*
   - `--auto` 옵션을 통한 백그라운드 자동 조회 시 발생하던 즉시 실패 오류 완벽 해결.
   - GUI 모드와 동일한 2단계(브라우저 기동 -> 클릭 명령) 조회 프로세스 정립.
   - 다중 접속 시의 프로필 락(Profile Lock) 지원으로 안정적인 대량 처리 지원.

2. **이메일 요약 리포트 디자인 개편** *(v4.3.0)*
   - 단순 나열되던 사건번호를 **[사건번호 | 피고/사건명]** 구조의 명확한 HTML 표로 변경.
   - 결과 상태(성공, 실패, 캡차 재시도 등)에 따른 그룹화로 시각적 분석 편의성 증대.

3. **구조적 리팩터링 (batch_gui_maker.py 다이어트)** *(v4.2.2)*
   - 메인 GUI 파일인 `batch_gui_maker.py`의 비대해진 코드를 서비스 모듈로 분리.
   - 사건 처리 핵심 로직을 `services/process_controller.py`로 이전.

4. **안정성 및 오류 처리 강화** *(v4.2.2)*
   - 사건 조회 실패 시 사용자 알림 및 실패 건 대상 자동 재실행 기능 도입.

5. **알림메일 고도화** *(v4.2.0)*
   - 메일 본문 HTML 표 생성 및 시트별 그룹화. GAS 웹 앱 연동 즉시 발송.

---

## 프로젝트 구조

```
case-ing/
├── auto_runner.py               CLI 실행기 (v4.3.0 강화)
├── batch_gui_maker.py           메인 GUI (UI 구성 및 이벤트 위임)
├── config.py                    설정 상수 (APP_VERSION = "4.3.0" 등)
├── main.py                      진입점 (run_app 또는 run_auto_batch)
├── data/                        설정 및 이력용 JSON 통합 폴더
├── src/                         Puppeteer 자동화 코드
├── services/                    비즈니스 로직 (process_controller, history_manager 등)
├── gui/                         UI 컴포넌트 (panels, dialogs)
├── utils/                       공통 유틸 (email_manager 등)
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

- **v4.3.0**: CLI 자동 실행 안정화, 이메일 요약 표 디자인 개편, 결과 리스트 상세화
- **v4.2.2**: batch_gui_maker.py 리팩터링, 프로세스 컨트롤러 분리, UI 일관성 강화
- **v4.2.0**: 알림메일 고도화(HTML·그룹화·즉시 발송), 제어 패널 UI·로깅 강화
- **v4.1.2**: 리팩토링(사건 목록 UI 분리), utils 폴더 추가

상세 변경 이력: [00.CHANGELOG/CHANGELOG_v4.3.0.md](00.CHANGELOG/CHANGELOG_v4.3.0.md)  
버전별 README: [00.README/](00.README/)

---

## 라이선스

MIT License
