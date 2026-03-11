# case-ing

대법원 나의 사건 조회 자동화 시스템 (Puppeteer + Python GUI) - v4.5.0

## 원본 출처

이 프로젝트는 [iicdii/case-ing](https://github.com/iicdii/case-ing)를 기반으로 하여 **Puppeteer 기반 병렬 처리** 및 **Python GUI 일괄 처리 시스템**으로 전환한 포크 버전입니다.

**원본 저장소**: https://github.com/iicdii/case-ing  
**포크 저장소**: https://github.com/JWP9412/save_case_ing

<a href="https://github.com/iicdii/case-ing/blob/master/LICENSE" alt="License">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" />
</a>

case-ing는 case + ~ing의 합성어로 여러 개의 사건 진행현황을 쉽게 조회하도록 도와주는 자동화 도구입니다.

---

## 현재 버전 특징 (v4.5.0)

### 주요 개선 사항

1. **사건목록 관리** *(v4.5.0)*
   - 사건 추가/수정/삭제/숨기기/숨김 해제 다이얼로그. 법원 필드 드롭다운·자동완성(오버레이 목록). 사건목록 관리·열 순서 버튼 하늘색·최우측 배치. 구글 시트 행 삭제/숨김 필터·사건번호 int 처리 버그 수정.

2. **사건 목록 UI 개선** *(v4.4.6)*
   - **기일 열**: 디데이(D+/D-) 표시, 변론/판결선고기일 민트색, 날짜 YY.MM.DD 형식, CTkTextbox로 드래그 복사·수직 가운데.
   - **최근 업데이트 열**: 날짜 `26.03.11.` 형식 + 시간 줄바꿈, grid 수직 가운데 정렬.
   - **사건 목록**: 법원/사건번호·피고/사건명 줄바꿈·수직·수평 가운데, 비고 좌측 정렬, 행 높이 90px, grid+스페이서 수직 가운데.
   - **시트 버튼**: "시트" 텍스트 제거, 아이콘만 표시.

3. **기일 정보 캐싱 및 자동 조회 표기** *(v4.4.1)*
   - 기일 데이터를 개별 사건 시트가 아닌 크롤링 완료 시점에 추출해 `update_history.json`에 저장하고, 사건 목록에서는 캐시만 읽어 표시. 없으면 "기일 미정".
   - 최초 조회 성공 후 "변경없음"인 경우에도 '자동 조회' 열이 "자동 가능"으로 갱신되도록 수정.

4. **사건 목록 '기일' 열** *(v4.4.0)*
   - 구글 시트 개별 시트(일자·내용)에서 변론기일/판결선고기일과 날짜·시간을 파싱해 '기일' 열에 "00기일 YY.MM.DD.(HH:MM)" 형식으로 표시 (캐시 기반).

5. **아키텍처 정리** *(v4.3.99)*
   - 메인 GUI를 `gui/app_controller.py`의 `AppController`로 통합. `batch_gui_maker.py` 제거.
   - `utils/` 폴더 제거. `email_manager.py`를 `services/`로 이동.
   - ProcessController에서 Tkinter 의존성 제거, UI는 app 위임 및 ui_queue로만 처리.

6. **CLI 자동 실행(Auto-run) 안정화** *(v4.3.0)*
   - `--auto` 옵션으로 백그라운드 자동 조회. GUI와 동일한 2단계(브라우저 기동 -> 클릭 명령) 프로세스.
   - 다중 접속 시 프로필 락 지원.

7. **이메일 요약 리포트 디자인 개편** *(v4.3.0)*
   - **[사건번호 | 피고/사건명]** 구조의 HTML 표. 결과 상태별 그룹화.

8. **안정성 및 오류 처리 강화** *(v4.2.2)*
   - 사건 조회 실패 시 알림 및 실패 건 자동 재실행.

9. **알림메일 고도화** *(v4.2.0)*
   - 메일 본문 HTML 표·시트별 그룹화. GAS 웹 앱 연동 즉시 발송.

---

## 프로젝트 구조

```
case-ing/
├── auto_runner.py               CLI 실행기 (MockApp 인터페이스 통일)
├── config.py                    설정 상수 (APP_VERSION = "4.5.0" 등)
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

- **v4.5.0**: 사건목록 관리(추가/수정/삭제/숨기기/숨김해제), 법원 드롭다운·자동완성, 버튼 하늘색·배치, 삭제/숨김·사건번호 int 버그 수정
- **v4.4.6**: 사건 목록 UI 개선(기일 디데이·민트색·날짜 형식, 최근 업데이트 수직 정렬, 행 수직 가운데·비고 좌측·시트 아이콘만·행 높이 90)
- **v4.3.99**: 아키텍처 정리(AppController 통합, utils 제거, services 리팩터링), GitHub 푸시 전 정리
- **v4.3.0**: CLI 자동 실행 안정화, 이메일 요약 표 디자인 개편
- **v4.2.2**: batch_gui_maker 리팩터링, 프로세스 컨트롤러 분리
- **v4.2.0**: 알림메일 고도화(HTML·그룹화·즉시 발송)
- **v4.1.2**: 사건 목록 UI 분리

상세 변경 이력: [00.CHANGELOG/CHANGELOG_v4.5.0.md](00.CHANGELOG/CHANGELOG_v4.5.0.md)  
버전별 README: [00.README/](00.README/)

---

## 라이선스

MIT License
