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


class PuppeteerService:
    """
    Puppeteer 서비스 클래스 (Interactive)
    """

    def __init__(self, log_callback=None, processing_flag=None):
        self.log_callback = log_callback
        self.processing_flag = processing_flag
        self.running_processes = {}  # {case_number: process}

    def _log(self, message):
        """로그 메시지 출력"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def capture_captcha_image(self, case_number, defendant, court):
        """
        1단계: 프로세스 시작 및 캡차 캡처 (또는 스마트 스킵 확인)
        """
        try:
            self._log(f"🚀 [Interactive] 프로세스 시작: {case_number} ({court})")

            # 기존 프로세스 정리
            self.cleanup_process(case_number)

            cmd = ["node", "src/interactive_runner.js", case_number, defendant, court]

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
            )

            # 프로세스 관리 목록에 등록
            self.running_processes[case_number] = process

            start_time = time.time()
            timeout = config.PUPPETEER_CAPTCHA_TIMEOUT

            image_path = None

            # 출력 모니터링 루프
            while time.time() - start_time < timeout:
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

        try:
            self._log(f"📤 Node.js로 입력 전송: {captcha_input}")

            # 입력값 전송 (줄바꿈 필수)
            if process.poll() is None:
                process.stdin.write(captcha_input + "\n")
                process.stdin.flush()
            else:
                self._log("❌ 프로세스가 이미 종료되어 있습니다.")
                return False

            # 결과 JSON 수신 대기
            json_lines = []
            capture_json = False
            result_found = False

            start_time = time.time()
            timeout = config.PUPPETEER_PROCESSING_TIMEOUT

            while time.time() - start_time < timeout:
                line = process.stdout.readline()
                if not line:
                    if process.poll() is not None:
                        break
                    time.sleep(0.1)
                    continue

                line = line.strip()

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
                        # 빈 리스트라도 성공이면 True (또는 빈 리스트) 반환
                        return progress_data if progress_data else True
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
            # 작업 완료 후 프로세스 정리
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
                print(f"Cleanup error: {e}")
