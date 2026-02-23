# -*- coding: utf-8 -*-
"""
GUI 패널 모듈
============
메인 윈도우를 구성하는 각 영역(헤더, 제어, 설정, 사건 목록, 진행상황)을
별도 모듈로 분리하여 유지보수성을 높였습니다.
주니어 개발자: 새 패널을 추가할 때 이 폴더에 모듈을 만들고 아래에 import를 추가하세요.
"""
from gui.panels.header import HeaderPanel
from gui.panels.control_panel import ControlPanel
from gui.panels.settings_panel import SettingsPanel
from gui.panels.progress_panel import ProgressPanel
from gui.panels.case_list_panel import CaseListPanel

__all__ = [
    "HeaderPanel",
    "ControlPanel",
    "SettingsPanel",
    "ProgressPanel",
    "CaseListPanel",
]
