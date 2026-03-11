import os
import sys
import time
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from services.logger_service import setup_logger, get_logger
from services.google_sheets import GoogleSheetsService
from services.puppeteer import PuppeteerService
from services.history_manager import HistoryManager as LogHistoryManager
from services.update_history import HistoryManager as UpdateHistoryManager
from services import update_history as update_history_service
from services.process_controller import ProcessController
from services import email_manager as email_manager_module


class MockApp:
    """
    CLI(명령줄) 모드에서 GUI(Tkinter) 객체를 흉내내는 가짜 앱 객체입니다.
    ProcessController가 GUI 메서드를 호출할 때 에러가 나지 않도록 인터페이스만 제공합니다.
    """
    def __init__(self):
        setup_logger()
        self._logger = get_logger("auto_runner")
        self._file_lock = threading.Lock()
        
        # ProcessController가 기대하는 상태 변수들
        self.case_list = []
        self.browser_ws_urls = {}
        self.browser_processes = {}
        self.case_start_times = {}
        self.processed_cases = set()
        self.processing = True
        self.ui_queue = queue.Queue()
        self.lane_events = {}
        self.case_images = {}
        self.case_status = {}
        self.case_checkboxes = {}
        
        max_profiles = getattr(config, "MAX_PARALLEL_LIMIT", 20)
        self.profile_locks = [threading.Lock() for _ in range(max_profiles)]
        
        # 서비스 인스턴스 초기화
        self.google_sheets_service = GoogleSheetsService()
        self.puppeteer_service = PuppeteerService()
        self.log_history_manager = LogHistoryManager(self)
        self.history_manager = UpdateHistoryManager()
        
        # Mock Tkinter Root
        class MockRoot:
            def after(self, ms, func, *args):
                try:
                    func(*args)
                except Exception:
                    pass
        self.root = MockRoot()
        
        # Mock GUI Elements
        class MockBtn:
            def configure(self, **kwargs): pass
            def cget(self, attr): return ""
        self.start_btn = MockBtn()
        self.stop_btn = MockBtn()
        self.complete_btn = MockBtn()
        self.email_btn = MockBtn()
        
        class MockVar:
            def set(self, val): pass
            def get(self): return 3
        self.header_select_all_var = MockVar()
        self.max_parallel = MockVar()
        
    def log_message(self, msg):
        self._logger.info(msg)
        try:
            print(msg)
        except UnicodeEncodeError:
            enc = getattr(sys.stdout, "encoding", None) or "utf-8"
            safe = msg.encode(enc, errors="replace").decode(enc)
            print(safe)
        
    def update_case_status(self, case_number, status_text, color, icon=""):
        """CLI 처리 중 상태 변경 시 로그 출력 및 파일(status_history.json) 저장"""
        self.log_message(f"[상태] {case_number}: {icon} {status_text}")
        try:
            self.log_history_manager.save_status_history(case_number, status_text, color, icon)
        except Exception as e:
            self.log_message(f"⚠️ 상태 기록 저장 실패: {e}")
        
    def update_progress(self, percent, msg):
        self.log_message(f"[진행률 {percent:.1f}%] {msg}")
        
    def add_to_search_log(self, case_number):
        self.log_history_manager.add_to_search_log(case_number)
        
    def _set_control_btn_state(self, btn, state):
        pass
        
    def find_case_index(self, case_number):
        return case_number
        
    def load_update_history(self):
        return self.history_manager.load_history()
        
    def update_case_timestamp(self, case, original_index, row_count, is_auto=True, hearing_info=None):
        """CLI 조회 성공 시 업데이트 기록 저장 (자동 조회 플래그·기일 캐시 포함). history_ui.py 시그니처와 동일."""
        try:
            case_number = case.get("사건번호", "")
            with self._file_lock:
                history = update_history_service.load_update_history(config.UPDATE_HISTORY_FILE)
                new_history = update_history_service.update_case_record(
                    case_number, row_count, history, is_auto=is_auto, hearing_info=hearing_info
                )
                update_history_service.save_update_history(
                    new_history, config.UPDATE_HISTORY_FILE
                )
            self.log_message(f"📝 자동 조회 기록 완료: {case_number}")
        except Exception as e:
            self.log_message(f"⚠️ 자동 조회 기록 실패: {e}")
        
    def update_email_btn_text(self):
        pass
        
    def update_captcha_image(self, case_index, image_path):
        pass
        
    def deselect_all_cases(self):
        pass
        
    def start_batch_processing(self):
        pass

    def reset_internal_data(self):
        """인터페이스 일관성용. CLI에서는 사용하지 않음."""
        pass

    def cleanup_case_process(self, case_number):
        """인터페이스 일관성용. 실제 정리는 ProcessController.cleanup_case_process에서 수행."""
        pass

    def show_warning(self, message):
        """CLI: 경고 메시지 로그만 출력."""
        self.log_message(f"⚠️ [경고] {message}")

    def show_info(self, message):
        """CLI: 안내 메시지 로그만 출력."""
        self.log_message(f"ℹ️ [알림] {message}")

    def ask_yesno(self, title, message):
        """CLI: 대화상자 불가. 항상 False 반환."""
        self.log_message(f"❓ [{title}] {message} (CLI에서는 자동으로 아니오)")
        return False

    def get_case_status_text(self, case_index):
        """CLI: 상태 라벨 없음. 빈 문자열 반환."""
        return getattr(self, "case_status", {}).get(case_index, "")

    def update_auto_search_label(self, case_number):
        """CLI: UI 없음. no-op."""
        pass


def run_auto_batch():
    """
    작업 스케줄러 등을 통해 자동 실행될 때 호출되는 메인 함수.
    GUI 없이 스마트 스킵(CLICK)을 이용해 백그라운드에서 전체 사건을 조회하고 알림 메일을 발송합니다.
    """
    print("=== 일괄 처리 자동 실행 모드(CLI) 시작 ===")
    app = MockApp()
    app.log_message("🚀 백그라운드 자동 실행 초기화 완료")
    
    # 1. 사건 목록 가져오기
    try:
        cases = app.google_sheets_service.load_case_list()
        if not cases:
            app.log_message("📭 구글 시트에 처리할 사건이 없습니다.")
            return
    except Exception as e:
        app.log_message(f"❌ 사건 목록 로드 실패: {e}")
        return
        
    app.log_message(f"📋 총 {len(cases)}개의 사건을 로드했습니다. 스마트 스킵 조회를 시작합니다.")
    
    # 2. ProcessController를 이용한 병렬 처리 (CLICK 방식 강제)
    controller = ProcessController(app)
    max_workers = getattr(config, "MAX_PARALLEL_INSTANCES", 3)
    
    # 처리 완료 여부: 건수 + 메일 하단용 사건번호 리스트 (스레드 안전)
    results = {"success": 0, "captcha": 0, "fail": 0}
    success_list = []
    captcha_list = []
    fail_list = []
    results_lock = threading.Lock()
    
    def process_worker(case):
        case_number = case.get("사건번호", "")
        if not case_number:
            return
            
        case_info = {
            "사건번호": case_number,
            "피고": case.get("피고", ""),
            "사건명": case.get("사건명", "")
        }
        
        max_attempts = 3  # 1차 + 재시도 2회
        for attempt in range(1, max_attempts + 1):
            app.case_start_times[case_number] = time.time()
            try:
                result = controller.process_cli_auto_case(case, case_number)
                if result is True:
                    with results_lock:
                        results["success"] += 1
                        success_list.append(case_info)
                    return
                if result == "captcha":
                    with results_lock:
                        results["captcha"] += 1
                        captcha_list.append(case_info)
                    return
                # result == "fail" (재시도 가능)
                if attempt < max_attempts:
                    app.log_message(f"🔄 {case_number} 재시도 ({attempt}/{max_attempts - 1})")
                else:
                    with results_lock:
                        results["fail"] += 1
                        fail_list.append(case_info)
            except Exception as e:
                app.log_message(f"❌ 사건 {case_number} 처리 중 예외 발생: {e}")
                if attempt < max_attempts:
                    app.log_message(f"🔄 {case_number} 재시도 ({attempt}/{max_attempts - 1})")
                else:
                    with results_lock:
                        results["fail"] += 1
                        fail_list.append(case_info)
                    return
            finally:
                # 다음 재시도를 위해 또는 완전히 실패 시 프로세스 정리
                if result != True and result != "captcha" and attempt < max_attempts:
                    controller.cleanup_case_process(case_number)
                elif result == "fail" or attempt == max_attempts:
                    controller.cleanup_case_process(case_number)
            
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_worker, case) for case in cases]
        for future in as_completed(futures):
            future.result()  # 예외 확인
            
    app.log_message(
        f"🏁 조회 완료: 성공 {results['success']}건, 캡차(재시도 안 함) {results['captcha']}건, "
        f"3회 시도 후 실패 {results['fail']}건"
    )
    
    # 3. 브라우저 프로세스 정리
    try:
        for case_num in list(app.browser_processes.keys()):
            app.puppeteer_service.cleanup_process(case_num)
        app.puppeteer_service.terminate_node_server()
    except Exception as e:
        app.log_message(f"⚠️ 프로세스 정리 중 오류: {e}")
    
    # 4. 결과 메일 발송 (성공/캡차/실패 목록을 메일 하단에 포함, 업데이트 없어도 발송)
    app.log_message("📧 이메일 발송을 준비합니다.")
    summary_html, _ = email_manager_module.get_summary_html(
        success_cases=success_list,
        failed_cases=fail_list,
        captcha_cases=captcha_list,
    )
    
    recipient = (getattr(config, "NOTIFICATION_EMAIL_ADDRESS", "") or "").strip()
    if not recipient:
        app.log_message("⚠️ 설정된 수신 메일 주소가 없습니다. 이메일을 발송할 수 없습니다.")
    elif not summary_html or not summary_html.strip():
        app.log_message("📭 조회 결과가 없어 이메일을 발송하지 않습니다.")
    else:
        try:
            ok = app.google_sheets_service.append_notification_mail(summary_html, recipient)
            if ok:
                email_manager_module.clear_unsent_emails_and_update_last_sent()
                webapp_url = (getattr(config, "NOTIFICATION_GAS_WEBAPP_URL", "") or "").strip()
                if webapp_url:
                    try:
                        import urllib.request
                        req = urllib.request.Request(webapp_url, method="POST", data=b"")
                        with urllib.request.urlopen(req, timeout=15) as _:
                            app.log_message("✅ GAS 웹 앱을 통해 이메일 즉시 발송을 요청했습니다.")
                    except Exception as e:
                        app.log_message(f"⚠️ GAS 웹 앱 호출 실패 (트리거로 발송될 예정): {e}")
                else:
                    app.log_message("✅ 알림메일 시트에 기록되었습니다. (즉시 발송 URL 없음, 트리거 대기)")
            else:
                app.log_message("❌ 구글 시트 알림메일 기록에 실패했습니다.")
        except Exception as e:
            app.log_message(f"❌ 이메일 발송 처리 중 예외 발생: {e}")

    print("=== 일괄 처리 자동 실행 모드(CLI) 종료 ===")

if __name__ == "__main__":
    run_auto_batch()
