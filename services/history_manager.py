# -*- coding: utf-8 -*-
"""
히스토리/로그 파일 I/O 서비스
============================

검색 로그(search_log.json), 상태 히스토리(status_history.json) 등
JSON 파일 읽기·쓰기를 담당합니다. app_controller에서 사용하는 Lock과
로그 콜백은 app을 통해 전달받습니다.
"""

import json
import os
import threading

import config


class HistoryManager:
    """검색 로그·상태 히스토리 파일을 읽고 쓰는 매니저. app._file_lock, app.log_message 사용."""

    def __init__(self, app):
        self.app = app
        self._fallback_lock = threading.Lock()

    def _lock(self):
        return getattr(self.app, "_file_lock", None) or self._fallback_lock

    def _log(self, msg):
        if hasattr(self.app, "log_message") and callable(self.app.log_message):
            self.app.log_message(msg)

    def load_search_log(self):
        """검색 성공 이력 로드. 반환: 사건번호 리스트. 파일 없으면 []."""
        path = getattr(config, "SEARCH_LOG_FILE", "search_log.json")
        try:
            lock = self._lock()
            if lock is not None:
                with lock:
                    return self._load_search_log_impl(path)
            return self._load_search_log_impl(path)
        except Exception as e:
            self._log(f"⚠️ 검색 이력 로드 실패: {e}")
            return []

    def _load_search_log_impl(self, path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    return list(data.keys())
        return []

    def add_to_search_log(self, case_number):
        """캡차 입력 성공 시 사건번호를 search_log에 추가."""
        if not case_number:
            return
        path = getattr(config, "SEARCH_LOG_FILE", "search_log.json")
        try:
            lock = self._lock()
            if lock is not None:
                with lock:
                    self._add_to_search_log_impl(path, case_number)
            else:
                self._add_to_search_log_impl(path, case_number)
        except Exception as e:
            self._log(f"⚠️ 검색 이력 저장 실패: {e}")

    def _add_to_search_log_impl(self, path, case_number):
        log = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    log = data if isinstance(data, list) else list(data.keys()) if isinstance(data, dict) else []
            except Exception:
                pass
        if case_number not in log:
            log.append(case_number)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)

    def load_status_history(self):
        """상태 열 영구 보존용 JSON 로드. 반환: { 사건번호: {"status", "color", "emoji"}, ... }."""
        path = getattr(config, "STATUS_HISTORY_FILE", "status_history.json")
        try:
            lock = self._lock()
            if lock is not None:
                with lock:
                    return self._load_status_history_impl(path)
            return self._load_status_history_impl(path)
        except Exception:
            pass
        return {}

    def _load_status_history_impl(self, path):
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_status_history(self, case_number, status, color, emoji=""):
        """상태 변경 시 JSON에 기록."""
        path = getattr(config, "STATUS_HISTORY_FILE", "status_history.json")
        try:
            lock = self._lock()
            if lock is not None:
                with lock:
                    self._save_status_history_impl(path, case_number, status, color, emoji)
            else:
                self._save_status_history_impl(path, case_number, status, color, emoji)
        except Exception as e:
            self._log(f"⚠️ 상태 기록 저장 실패: {e}")

    def _save_status_history_impl(self, path, case_number, status, color, emoji):
        history = {}
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                pass
        history[case_number] = {"status": status, "color": color, "emoji": emoji}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
