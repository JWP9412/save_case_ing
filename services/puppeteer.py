"""
Puppeteer 서비스 모듈 (Interactive Mode)
=====================================

Node.js 레인 워커를 유지하며 캡차 입력과 검색을 수행합니다.
같은 프로필(레인)의 사건은 Chrome을 재사용해 기동 횟수를 줄입니다.
"""

import json
import os
import subprocess
import time

import config
from services.logger_service import get_logger

logger = get_logger("puppeteer")


def _resolve_node_executable():
    """
    Node 실행 파일 경로.

    주니어 개발자 참고:
    - 포터블 배포: CaseIng.exe 옆 runtime/node/node.exe 를 우선 사용
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
    Puppeteer 서비스 클래스 (Interactive + 레인 워커)
    """

    def __init__(self, log_callback=None, processing_flag=None):
        self.processing_flag = processing_flag
        # 사건번호 → Node 프로세스 (실행 중 사건 매핑)
        self.running_processes = {}
        # 프로필(레인) → 상주 워커 프로세스
        self.lane_workers = {}
        # 사건번호 → 프로필 인덱스 (cleanup 시 워커를 죽이지 않기 위함)
        self._case_to_profile = {}
        # Node JSON의 generalInfo를 사건번호별로 임시 보관
        self.last_general_info = {}
        # Chrome 기동 횟수 (검증/로그용)
        self.chrome_launch_count = 0

    def _log(self, message):
        logger.info(message)

    def _build_env(self, smart_skip_enabled=True):
        env = os.environ.copy()
        env["CASEING_GOTO_TIMEOUT_MS"] = str(
            getattr(config, "NODE_GOTO_TIMEOUT_MS", 45000)
        )
        env["CASEING_NAV_MAX_RETRY"] = str(getattr(config, "NODE_NAV_MAX_RETRY", 2))
        env["CASEING_NAV_RETRY_DELAY_MS"] = str(
            getattr(config, "NODE_NAV_RETRY_DELAY_MS", 3000)
        )
        env["CASEING_SMART_SKIP_ENABLED"] = "1" if smart_skip_enabled else "0"
        return env

    def _popen_kwargs(self, env):
        base_dir = config.get_base_dir()
        popen_kwargs = dict(
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore",
            bufsize=1,
            cwd=base_dir,
            env=env,
        )
        if os.name == "nt":
            popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        return popen_kwargs

    def _ensure_lane_worker(self, instance_index, smart_skip_enabled=True):
        """
        프로필(레인)용 워커가 없으면 기동하고, 있으면 재사용합니다.

        주니어: PROFILE_COUNT == 레인 수 이면 레인당 Chrome 1개만 뜹니다.
        """
        proc = self.lane_workers.get(instance_index)
        if proc is not None and proc.poll() is None:
            return proc

        node_exe = _resolve_node_executable()
        script = _node_script_path()
        if not os.path.isfile(script):
            self._log(f"❌ Node 스크립트 없음: {script}")
            return None

        cmd = [node_exe, script, "--worker", str(instance_index)]
        env = self._build_env(smart_skip_enabled=smart_skip_enabled)
        process = subprocess.Popen(cmd, **self._popen_kwargs(env))
        self.lane_workers[instance_index] = process
        self.chrome_launch_count += 1
        self._log(
            f"🚀 [Worker] 레인 워커 기동 instance_{instance_index} "
            f"(누적 Chrome 기동: {self.chrome_launch_count})"
        )

        # WORKER_READY 대기
        start = time.time()
        timeout = min(30, getattr(config, "PUPPETEER_CAPTCHA_TIMEOUT", 90))
        while time.time() - start < timeout:
            if process.poll() is not None:
                err = process.stderr.read() if process.stderr else ""
                self._log(f"❌ 워커 기동 실패: {err}")
                self.lane_workers.pop(instance_index, None)
                return None
            line = process.stdout.readline()
            if not line:
                time.sleep(0.05)
                continue
            line = line.strip()
            if line.startswith("WORKER_READY"):
                return process
            if line:
                self._log(f"[Node] {line}")
        self._log(f"⏰ 워커 READY 타임아웃: instance_{instance_index}")
        self._kill_process(process)
        self.lane_workers.pop(instance_index, None)
        return None

    def _kill_process(self, process):
        if not process:
            return
        try:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
        except Exception as e:
            logger.debug("Kill error: %s", e)

    def capture_captcha_image(
        self,
        case_number,
        defendant,
        court,
        instance_index=0,
        smart_skip_enabled=True,
    ):
        """
        1단계: 레인 워커에 CASE 명령을 보내고 캡차(또는 스마트 스킵)를 받습니다.
        """
        try:
            self._log(
                f"🚀 [Interactive] 프로세스 시작: {case_number} ({court}) "
                f"[instance_{instance_index}]"
            )

            # 이전 사건 매핑만 정리 (워커는 유지)
            self.running_processes.pop(case_number, None)

            process = self._ensure_lane_worker(
                instance_index, smart_skip_enabled=smart_skip_enabled
            )
            if process is None:
                return None, None, None

            # CASE 명령 전송
            payload = {
                "cmd": "CASE",
                "caseNumber": case_number,
                "defendant": defendant,
                "court": court,
                "instanceIndex": int(instance_index),
                "smartSkip": bool(smart_skip_enabled),
            }
            try:
                process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
                process.stdin.flush()
            except Exception as e:
                self._log(f"❌ 워커 CASE 전송 실패: {e}")
                self.lane_workers.pop(instance_index, None)
                return None, None, None

            self.running_processes[case_number] = process
            self._case_to_profile[case_number] = instance_index

            start_time = time.time()
            timeout = config.PUPPETEER_CAPTCHA_TIMEOUT

            while time.time() - start_time < timeout:
                if callable(self.processing_flag) and not self.processing_flag():
                    self._log(f"⏹️ 처리 중지로 캡차 로드 중단: {case_number}")
                    self.unbind_case(case_number)
                    return None, None, None
                line = process.stdout.readline()
                if not line:
                    if process.poll() is not None:
                        stderr = process.stderr.read() if process.stderr else ""
                        self._log(f"❌ 프로세스 비정상 종료: {stderr}")
                        self.lane_workers.pop(instance_index, None)
                        self.unbind_case(case_number)
                        break
                    time.sleep(0.1)
                    continue

                line = line.strip()
                if not line:
                    continue

                if any(
                    keyword in line
                    for keyword in ["🚀", "🔍", "✅", "🖼️", "ℹ️", "WORKER"]
                ):
                    self._log(f"[Node] {line}")

                if "GUI_IMAGE_PATH:" in line:
                    image_path = line.split("GUI_IMAGE_PATH:")[1].strip()
                    self._log(f"🖼️ 캡차 이미지 획득: {image_path}")
                    return image_path, None, process

                if "CAPTCHA_STATUS: SKIP_AND_CLICK" in line:
                    self._log(f"⚡ 스마트 스킵 활성화: {case_number}")
                    return "__CLICK__", None, process

            self._log(f"⏰ 초기화 타임아웃: {case_number}")
            self.unbind_case(case_number)
            return None, None, None

        except Exception as e:
            self._log(f"❌ 프로세스 실행 오류: {e}")
            self.unbind_case(case_number)
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

            if process.poll() is None:
                process.stdin.write(captcha_input + "\n")
                process.stdin.flush()
            else:
                self._log("❌ 프로세스가 이미 종료되어 있습니다.")
                return False

            json_lines = []
            capture_json = False
            result_found = False

            start_time = time.time()
            timeout = config.PUPPETEER_PROCESSING_TIMEOUT

            while time.time() - start_time < timeout:
                if callable(self.processing_flag) and not self.processing_flag():
                    self._log(f"⏹️ 처리 중지로 실행 중단: {case_number}")
                    self.unbind_case(case_number)
                    return False
                line = process.stdout.readline()
                if not line:
                    if process.poll() is not None:
                        break
                    time.sleep(0.05)
                    continue

                line = line.strip()
                if not line:
                    continue

                if any(
                    k in line
                    for k in [
                        "💬",
                        "⚠️",
                        "✅",
                        "❌",
                        "📊",
                        "📋",
                        "WRONG_CAPTCHA",
                        "Interactive",
                        "전략",
                        "그리드",
                        "일반내용",
                    ]
                ):
                    self._log(f"[Node] {line}")

                if "WRONG_CAPTCHA_IMAGE:" in line:
                    wrong_captcha_path = line.split("WRONG_CAPTCHA_IMAGE:")[1].strip()
                    self._log(f"⚠️ 캡차 불일치 - 재입력용 이미지: {wrong_captcha_path}")
                    skip_cleanup = True
                    return {"status": "WRONG_CAPTCHA", "image_path": wrong_captcha_path}

                if line == "JSON_RESULT_START":
                    capture_json = True
                    json_lines = []
                    continue
                if line == "JSON_RESULT_END":
                    capture_json = False
                    result_found = True
                    break

                if capture_json:
                    json_lines.append(line)

            if result_found and json_lines:
                json_str = "\n".join(json_lines)
                try:
                    result = json.loads(json_str)
                    if not result.get("success", False):
                        error_msg = result.get("error", "알 수 없는 오류")
                        self._log(f"❌ 처리 실패 (Node): {error_msg}")
                        if "WRONG_CAPTCHA" in str(error_msg):
                            return {"status": "WRONG_CAPTCHA", "image_path": None}
                        return False

                    progress_data = result.get("progressData")
                    general_info = result.get("generalInfo")
                    if general_info is not None:
                        self.last_general_info[case_number] = general_info
                    if progress_data is None:
                        progress_data = []
                    self._log(f"✅ 처리 완료: {len(progress_data)}건 데이터 추출")
                    return progress_data
                except json.JSONDecodeError:
                    self._log(f"❌ JSON 파싱 실패: {json_str[:100]}...")
                    return False

            self._log("❌ 결과 수신 실패 (타임아웃 또는 프로세스 종료)")
            return False

        except Exception as e:
            self._log(f"❌ 실행 오류: {e}")
            return False
        finally:
            # WRONG_CAPTCHA 시 매핑 유지(재입력 대기). 그 외에는 사건 매핑만 해제(워커 유지).
            if not skip_cleanup:
                self.unbind_case(case_number)

    def unbind_case(self, case_number):
        """사건↔프로세스 매핑만 제거하고 워커는 죽이지 않습니다."""
        self.running_processes.pop(case_number, None)
        self._case_to_profile.pop(case_number, None)

    def cleanup_process(self, case_number):
        """
        사건 매핑 해제. 워커 모드에서는 레인 워커를 종료하지 않습니다.
        (배치 종료 시 shutdown_all_workers 사용)
        """
        self.unbind_case(case_number)

    def shutdown_all_workers(self):
        """모든 레인 워커에 QUIT을 보내고 종료합니다."""
        for idx, process in list(self.lane_workers.items()):
            try:
                if process and process.poll() is None:
                    try:
                        process.stdin.write(json.dumps({"cmd": "QUIT"}) + "\n")
                        process.stdin.flush()
                        process.wait(timeout=5)
                    except Exception:
                        self._kill_process(process)
            finally:
                self.lane_workers.pop(idx, None)
        self.running_processes.clear()
        self._case_to_profile.clear()
        self._log(
            f"✅ 모든 레인 워커 종료 완료 (이번 배치 Chrome 기동 횟수: {self.chrome_launch_count})"
        )
        self.chrome_launch_count = 0
