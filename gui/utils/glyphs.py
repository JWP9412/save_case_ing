# -*- coding: utf-8 -*-
"""
UI 안전 문자(글리프) 유틸
========================

주니어 개발자 참고:
- 버튼/상태 라벨 폰트가 '맑은 고딕'이면 이모지(🔄 📧 등)가 빈 네모로 깨집니다.
- Tk/CTk는 이모지 전용 폰트로 자동 폴백하지 않습니다.
- 그래서 맑은 고딕에 있는 도형 문자(▶ ■ ● 등)만 쓰거나, 아이콘을 빼는 방식으로 통일합니다.
- config.UI_USE_EMOJI=True 이면 치환하지 않고 원문을 그대로 둡니다(디버그용).
"""
import re

import config

# 깨지는 이모지 → 안전 문자(또는 빈 문자열) 치환 맵
# 키가 길수록 먼저 치환되도록 길이 내림차순으로 정렬해 사용합니다.
_EMOJI_MAP = {
    "🎛️": "",
    "🔄": "",
    "🖼️": "▶",
    "✔️": "",
    "✅": "",
    "❌": "X",
    "⚠️": "!",
    "⛔": "■",
    "🧹": "",
    "📧": "",
    "✉": "",
    "⚙": "",
    "📅": "",
    "📭": "",
    "⚡": "▶",
    "🎉": "",
    "🚀": "",
    "📋": "",
    "📝": "",
    "📊": "",
    "🔐": "",
    "📸": "",
    "⏳": "",
    "ℹ️": "i",
    "❓": "?",
    "🛑": "■",
    "▶️": "▶",
}

# 이모지/보충 기호 범위(대략). 맵에 없는 것도 제거합니다.
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"  # 이모지 대부분
    "\U00002700-\U000027BF"  # 딩뱃
    "\U00002600-\U000026FF"  # 기타 기호
    "\U0000FE0F"              # variation selector
    "\U0000200D"              # ZWJ
    "]+",
    flags=re.UNICODE,
)


def sanitize(text):
    """
    UI에 표시할 문자열에서 깨지는 이모지를 안전 문자로 바꿉니다.

    - UI_USE_EMOJI=True 이면 원문 그대로 반환
    - 맵에 있는 이모지는 지정 문자로 치환
    - 그 외 이모지 범위 문자는 제거
    - 앞뒤 공백 정리, 연속 공백은 하나로
    """
    if text is None:
        return ""
    s = str(text)
    if getattr(config, "UI_USE_EMOJI", False):
        return s

    # 긴 키부터 치환(조합 이모지 우선)
    for key in sorted(_EMOJI_MAP.keys(), key=len, reverse=True):
        if key in s:
            s = s.replace(key, _EMOJI_MAP[key])

    s = _EMOJI_RE.sub("", s)
    # 치환 후 남은 이중 공백 정리
    s = re.sub(r"[ \t]{2,}", " ", s)
    # 줄바꿈 앞뒤 공백만 정리 (버튼의 \n 은 유지)
    lines = [ln.strip() for ln in s.split("\n")]
    return "\n".join(lines).strip()
