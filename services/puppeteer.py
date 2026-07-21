"""
Puppeteer 서비스 모듈 (Interactive Mode)
=====================================

Node.js 단일 프로세스를 유지하며 캡차 입력과 검색을 수행합니다.
브라우저 재연결 방식을 폐기하고, stdin/stdout 통신을 사용합니다.
"""

import subprocess
import json
import os
import time
import config
from services.logger_service import get_logger

logger = get_logger("puppeteer")


def _resolve_node_executable():
    """
    Node 실행 파일 경로.

    주니어 개발자 참고:
    - 포터블 배포: CaseIng.exe 옆 runtime/node/node.exe 를 우선 사용
      (다른 PC에 Node를 따로 설치하지 않아도 됨)
    - 개발 환경: PATH의 `node` 명령 사용
    """
    bundled = config.path_from_base("runtime", "node", "node.exe")
    if os.path.isfile(bundled):
        return bundled
    return "node"


def _node_script_path():
    """interactive_runner.js 절대경로 (BASE_DIR/src/...)."""
    return config.path_from_base("src", "interactive_runner.js")


class PuppeteerService:
    """
    Puppeteer 서비스 클래스 (Interactive)
    """

    def __init__(self, log_callback=None, processing_flag=None):
        self.processing_flag = processing_flag
        self.running_processes = {}  # {case_number: process}

    def _log(self, message):
        """로그 메시지 출력 (표준 로거 사용)"""
        logger.info(message)

    def capture_captcha_image(self, case_number, defendant, court, instance_index=0):
        """
        1단계: 프로세스 시작 및 캡차 캡처 (또는 스마트 스킵 확인).
        instance_index: 전용 차로제용. cookie_data_for_save/instance_N 사용.
        """
        try:
            self._log(f"🚀 [Interactive] 프로세스 시작: {case_number} ({court}) [instance_{instance_index}]")

            # 기존 프로세스 정리
            self.cleanup_process(case_number)

            node_exe = _resolve_node_executable()
            script = _node_script_path()
            if not os.path.isfile(script):
                self._log(f"❌ Node 스크립트 없음: {script}")
                return None, None, None

            # cwd=BASE_DIR: cookie_data_for_save, screenshots 등 상대경로가 exe 옆에서 동작
            cmd = [
                node_exe,
                script,
                case_number,
                defendant,
                court,
                str(instance_index),
            ]
            base_dir = config.get_base_dir()

            # 프로세스 실행 (stdin 파이프 연결 필수)
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="ignore",
                bufsize=1,  # 라인 버퍼링
                cwd=base_dir,
            )

            # 프로세스 관리 목록에 등록
            self.running_processes[case_number] = process

            start_time = time.time()
            timeout = config.PUPPETEER_CAPTCHA_TIMEOUT

            image_path = None

            # 출력 모니터링 루프 (처리 중지 시 즉시 중단)
            while time.time() - start_time < timeout:
                if callable(self.processing_flag) and not self.processing_flag():
                    self._log(f"⏹️ 처리 중지로 캡차 로드 중단: {case_number}")
                    self.cleanup_process(case_number)
                    return None, None, None
                line = process.stdout.readline()
                if not line:
                    if process.poll() is not None:
                        # 프로세스가 종료됨
                        stderr = process.stderr.read()
                        self._log(f"❌ 프로세스 비정상 종료: {stderr}")
                        break
                    time.sleep(0.1)
                    continue

                line = line.strip()
                if not line:
                    continue

                # 중요 로그 표시
                if any(
                    keyword in line
                    for keyword in [
                        "GUI_IMAGE_PATH",
                        "CAPTCHA_STATUS",
                        "Smart Skip",
                        "오류",
                        "Error",
                    ]
                ):
                    pass  # 아래 로직에서 처리하거나 별도 로그
                elif any(keyword in line for keyword in ["🚀", "🔍", "✅", "🖼️", "ℹ️"]):
                    self._log(f"[Node] {line}")

                # 1. 캡차 이미지 경로 수신
                if "GUI_IMAGE_PATH:" in line:
                    image_path = line.split("GUI_IMAGE_PATH: ")[1].strip()
                    self._log(f"🖼️ 캡차 이미지 획득: {image_path}")
                    # 프로세스는 계속 살아있음 (입력 대기 상태)
                    return image_path, None, process  # 호환성을 위해 튜플 반환

                # 2. 스마트 스킵 신호 수신
                elif "CAPTCHA_STATUS: SKIP_AND_CLICK" in line:
                    self._log(f"⚡ 스마트 스킵 활성화: {case_number}")
                    return "__CLICK__", None, process

                # 3. 입력 대기 신호 (혹시 이미지 경로보다 늦게 뜨더라도 무시)
                elif "입력 대기 중" in line:
                    pass

            self._log(f"⏰ 초기화 타임아웃: {case_number}")
            self.cleanup_process(case_number)
            return None, None, None

        except Exception as e:
            self._log(f"❌ 프로세스 실행 오류: {e}")
            self.cleanup_process(case_number)
            return None, None, None

    def execute_case_processing(self, case, captcha_input, browser_ws_url=None):
        """
        2단계: 입력값(캡차 또는 CLICK) 전송 및 결과 수신
        """
        case_number = case.get("사건번호", "")
        process = self.running_processes.get(case_number)

        if not process:
            self._log(f"❌ 실행 중인 프로세스 없음: {case_number} (재시작 필요)")
            return False

        skip_cleanup = False
        try:
            self._log(f"📤 Node.js로 입력 전송: {captcha_input}")

            # 입력값 전송 (줄바꿈 필수)
            if process.poll() is None:
                process.stdin.write(captcha_input + "\n")
                process.stdin.flush()
            else:
                self._log("❌ 프로세스가 이미 종료되어 있습니다.")
                return False

            # 결과 JSON 수신 대기 (WRONG_CAPTCHA_IMAGE 선처리)
            json_lines = []
            capture_json = False
            result_found = False

            start_time = time.time()
            timeout = config.PUPPETEER_PROCESSING_TIMEOUT

            while time.time() - start_time < timeout:
                if callable(self.processing_flag) and not self.processing_flag():
                    self._log(f"⏹️ 처리 중지로 실행 중단: {case_number}")
                    self.cleanup_process(case_number)
                    return False
                line = process.stdout.readline()
                if not line:
                    if process.poll() is not None:
                        break
                    time.sleep(0.1)
                    continue

                line = line.strip()

                # 캡차 불일치 재시도: 새 이미지 경로 수신 시 즉시 반환 (프로세스 유지)
                if "WRONG_CAPTCHA_IMAGE:" in line:
                    wrong_captcha_path = line.split("WRONG_CAPTCHA_IMAGE:")[1].strip()
                    self._log(f"⚠️ 캡차 불일치 - 재입력용 이미지: {wrong_captcha_path}")
                    skip_cleanup = True
                    return {"status": "WRONG_CAPTCHA", "image_path": wrong_captcha_path}

                # 결과 JSON 블록 캡처
                if line == "JSON_RESULT_START":
                    capture_json = True
                    continue
                elif line == "JSON_RESULT_END":
                    capture_json = False
                    result_found = True
                    break

                if capture_json:
                    json_lines.append(line)
                else:
                    # 진행 상황 로그 출력
                    if any(k in line for k in ["✅", "❌", "📊", "⚠️", "Interactive"]):
                        self._log(f"[Node] {line}")

            # 결과 처리
            if result_found and json_lines:
                json_str = "".join(json_lines)
                try:
                    result = json.loads(json_str)
                    if result.get("success"):
                        progress_data = result.get("progressData", [])
                        self._log(f"✅ 처리 완료: {len(progress_data)}건 데이터 추출")
                        # 빈 리스트일 경우 그대로 빈 리스트 반환 (True로 변환하지 않음)
                        return progress_data
                    else:
                        error_msg = result.get("error", "Unknown error")
                        self._log(f"❌ 처리 실패 (Node): {error_msg}")
                        return False
                except json.JSONDecodeError:
                    self._log(f"❌ JSON 파싱 실패: {json_str[:100]}...")
                    return False
            else:
                self._log(f"❌ 결과 수신 실패 (타임아웃 또는 프로세스 종료)")
                return False

        except Exception as e:
            self._log(f"❌ 실행 오류: {e}")
            return False
        finally:
            # WRONG_CAPTCHA 시 프로세스 유지(재입력 대기), 그 외에는 정리
            if not skip_cleanup:
                self.cleanup_process(case_number)

    def cleanup_process(self, case_number):
        """프로세스 안전하게 종료"""
        process = self.running_processes.pop(case_number, None)
        if process:
            try:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
            except Exception as e:
                logger.debug("Cleanup error: %s", e)
