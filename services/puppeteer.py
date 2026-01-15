"""
Puppeteer 서비스 모듈
====================

Puppeteer를 통한 웹 크롤링 실행을 담당하는 모듈입니다.

주요 기능:
- 캡차 이미지 캡처
- 사건 처리 실행 (크롤링)
- 결과 파일에서 진행내용 데이터 추출

사용법:
    from services.puppeteer import PuppeteerService
    
    service = PuppeteerService(log_callback=log_func)
    image_path = service.capture_captcha_image(case_number, defendant, court)
    result = service.execute_case_processing(case, captcha_input, browser_ws_url)
"""

import subprocess
import json
import glob
import os
import time
import config


class PuppeteerService:
    """
    Puppeteer 서비스 클래스
    
    Puppeteer를 통한 웹 크롤링 실행을 담당합니다.
    """
    
    def __init__(self, log_callback=None, processing_flag=None):
        """
        초기화
        
        매개변수:
            log_callback: 로그 메시지를 출력할 함수 (선택사항)
                예: lambda msg: print(msg)
            processing_flag: 처리 중지 플래그 (선택사항)
                이 플래그가 False가 되면 처리 중지
        """
        self.log_callback = log_callback
        self.processing_flag = processing_flag
    
    def _log(self, message):
        """로그 메시지 출력 (콜백 함수 사용)"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)
    
    def capture_captcha_image(self, case_number, defendant, court):
        """
        캡차 이미지 캡처 함수
        
        Puppeteer를 실행하여 캡차 이미지를 캡처하고 WebSocket URL을 받아옵니다.
        
        매개변수:
            case_number: 사건번호
            defendant: 피고 이름
            court: 법원 이름
        
        반환값:
            (image_path, ws_url, process): 튜플
                - image_path: 캡차 이미지 파일 경로 (없으면 None)
                - ws_url: 브라우저 WebSocket URL (없으면 None)
                - process: Node.js 프로세스 객체
        
        주의:
            - 프로세스는 백그라운드에서 계속 실행됩니다 (브라우저 유지)
            - 나중에 browser.close()를 호출하여 종료해야 합니다
        """
        try:
            self._log(f"🔐 캡차 이미지 캡처 시작: {case_number} (법원: {court})")
            
            # ============================================================
            # 1단계: Puppeteer 실행 명령어 준비
            # ============================================================
            # Puppeteer 실행을 위한 명령어 (캡차 이미지 캡처 전용) - 법원 정보 포함!
            cmd = ["node", "src/single-case-captcha.js", case_number, defendant, court]
            self._log(f"🚀 명령어: node src/single-case-captcha.js {case_number} {defendant} {court}")
            
            # ============================================================
            # 2단계: Puppeteer 실행 (비동기로 실행하여 캡차 이미지만 캡처)
            # ============================================================
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                     text=True, encoding='utf-8', errors='ignore')
            
            # ============================================================
            # 3단계: stdout을 실시간으로 읽기
            # ============================================================
            image_path = None
            ws_url = None
            ws_url_found = False
            
            self._log(f"🔍 Puppeteer 출력 실시간 모니터링 시작: {case_number}")
            
            # 타임아웃 설정 (최대 90초 대기 - 네트워크 지연 고려)
            start_time = time.time()
            timeout = config.PUPPETEER_CAPTCHA_TIMEOUT
            
            while time.time() - start_time < timeout:
                line = process.stdout.readline()
                if not line:
                    # EOF이지만 WS URL을 이미 받았으면 OK
                    if ws_url_found:
                        break
                    # 아직 못 받았으면 조금 더 대기
                    time.sleep(0.1)
                    continue
                
                # GUI_IMAGE_PATH 찾기
                if 'GUI_IMAGE_PATH:' in line:
                    image_path = line.split('GUI_IMAGE_PATH: ')[1].strip()
                    self._log(f"🖼️ 이미지 경로 발견: {image_path}")
                
                # BROWSER_WS_URL 찾기 (브라우저 재연결용)
                elif 'BROWSER_WS_URL:' in line:
                    ws_url = line.split('BROWSER_WS_URL: ')[1].strip()
                    self._log(f"🔗 브라우저 WebSocket URL 저장: {case_number}")
                    ws_url_found = True
                    # 프로세스는 백그라운드에서 계속 실행됨
                    break
                
                # 에러 메시지만 표시
                elif 'ERROR' in line.upper() or '❌' in line or 'FAIL' in line.upper():
                    self._log(f"⚠️ Puppeteer 오류: {line.strip()}")
            
            # 브라우저를 종료하지 않고 유지 (사용자 입력 대기)
            self._log(f"🔒 브라우저 유지: {case_number} (사용자 입력 대기)")
            
            if image_path and os.path.exists(image_path):
                self._log(f"✅ 새로운 캡차 이미지 캡처 성공: {image_path}")
                file_size = os.path.getsize(image_path)
                self._log(f"🔍 이미지 파일 확인: {image_path} ({file_size} bytes)")
                self._log(f"🖼️ GUI에 이미지 표시 준비 완료: {case_number}")
                return image_path, ws_url, process
            else:
                self._log(f"❌ 캡차 이미지 캡처 실패: {case_number}")
                return None, ws_url, process
                
        except subprocess.TimeoutExpired:
            self._log(f"⏰ Puppeteer 실행 시간 초과: {case_number}")
            return None, None, None
        except Exception as e:
            self._log(f"❌ 캡차 이미지 캡처 오류: {e}")
            return None, None, None
    
    def execute_case_processing(self, case, captcha_input, browser_ws_url=None):
        """
        실제 Puppeteer로 사건 처리 실행 함수
        
        이 함수는 Node.js의 Puppeteer 스크립트를 실행하여 웹 크롤링을 수행합니다.
        
        매개변수:
            case: 사건 정보 딕셔너리 (사건번호, 피고, 법원 등)
            captcha_input: 사용자가 입력한 캡차 텍스트 (6자리 숫자)
            browser_ws_url: 브라우저 WebSocket URL (선택사항, 있으면 재연결)
        
        반환값:
            progress_data: 크롤링한 진행내용 데이터 리스트 또는 False (실패 시)
        
        처리 순서:
            1. 사건 정보 추출 (사건번호, 피고, 법원)
            2. 기존 브라우저가 있으면 재연결, 없으면 새로 시작
            3. Node.js 스크립트 실행 (src/index.js)
            4. 실시간으로 출력 로그 수집
            5. 결과 JSON 파일에서 진행내용 데이터 추출
        
        주의:
            - WebSocket URL이 있으면 기존 브라우저를 재사용합니다 (빠름)
            - 없으면 새 브라우저를 시작합니다 (느림)
            - 최대 3분(180초) 타임아웃이 설정되어 있습니다
        """
        try:
            # ============================================================
            # 1단계: 사건 정보 추출
            # ============================================================
            case_number = case.get('사건번호', '')
            defendant = case.get('피고', '')
            court = case.get('법원', '')
            
            self._log(f"🔄 Puppeteer로 사건 처리 중: {case_number}")
            self._log(f"📋 사건 정보 - 피고: {defendant}, 법원: {court}")
            self._log(f"🔐 캡차 입력: {captcha_input}")
            
            # ============================================================
            # 2단계: Puppeteer 실행 명령어 준비
            # ============================================================
            # Node.js 스크립트를 실행하기 위한 명령어 리스트
            # 예: ["node", "src/index.js", "--single-case", "2023가합10019", ...]
            cmd = ["node", "src/index.js", "--single-case", case_number, 
                   "--defendant", defendant, "--court", court, "--captcha", captcha_input]
            
            # ============================================================
            # 3단계: WebSocket URL 추가 (기존 브라우저 재연결)
            # ============================================================
            # WebSocket URL이 있으면 명령어에 추가
            # 이렇게 하면 Puppeteer가 기존 브라우저에 연결합니다
            if browser_ws_url:
                cmd.extend(["--browser-ws-url", browser_ws_url])
                self._log(f"🔗 기존 브라우저 재연결: {case_number}")
            else:
                self._log(f"⚠️ WebSocket URL 없음 - 새 브라우저 시작")
            
            self._log(f"🚀 명령어 실행: {' '.join(cmd)}")
            self._log(f"⏳ Puppeteer 실행 중... (최대 {config.PUPPETEER_PROCESSING_TIMEOUT}초 대기)")
            
            # ============================================================
            # 4단계: Puppeteer 실행 (중지 가능한 Popen 사용)
            # ============================================================
            self._log(f"🔄 [DEBUG] subprocess.Popen 실행 시작")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                     text=True, encoding='utf-8', errors='ignore', bufsize=1)
            
            # ============================================================
            # 5단계: 출력을 실시간으로 수집
            # ============================================================
            start_time = time.time()
            timeout = config.PUPPETEER_PROCESSING_TIMEOUT
            
            stdout_lines = []
            stderr_lines = []
            
            # 실시간으로 출력 읽기
            while time.time() - start_time < timeout:
                # 중지 플래그 확인
                if self.processing_flag is not None and not self.processing_flag:
                    self._log(f"⏹️ [DEBUG] 중지 감지 - 프로세스 종료 중")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except:
                        process.kill()
                    self._log(f"⏹️ 프로세스 강제 종료됨")
                    return False
                
                # stdout 실시간 읽기
                line = process.stdout.readline()
                if line:
                    line = line.strip()
                    stdout_lines.append(line)
                    # 중요한 로그만 표시
                    if line and any(keyword in line for keyword in ['✅', '❌', '⚠️', '🔐', '📄', '📊', '검색', '진행내용', 'DEBUG', 'ERROR', 'STEP']):
                        self._log(f"[Puppeteer] {line}")
                
                # 프로세스 종료 확인
                if process.poll() is not None:
                    # 나머지 출력 모두 읽기
                    for line in process.stdout:
                        line = line.strip()
                        if line:
                            stdout_lines.append(line)
                            if any(keyword in line for keyword in ['✅', '❌', '⚠️', '🔐', '📄', '📊', '검색', '진행내용', 'DEBUG', 'ERROR', 'STEP']):
                                self._log(f"[Puppeteer] {line}")
                    # stderr도 읽기
                    stderr_output = process.stderr.read()
                    if stderr_output:
                        stderr_lines = stderr_output.split('\n')
                    break
                
                time.sleep(0.01)  # 10ms 대기 (CPU 사용률 낮추기)
            
            # ============================================================
            # 6단계: 타임아웃 체크
            # ============================================================
            if process.poll() is None:
                self._log(f"⏰ 타임아웃 - 프로세스 강제 종료")
                process.kill()
                return False
            
            returncode = process.returncode
            self._log(f"🔄 [DEBUG] subprocess.Popen 완료 (코드: {returncode})")
            
            # ============================================================
            # 7단계: 결과 확인 및 진행내용 데이터 추출
            # ============================================================
            if returncode == 0:
                self._log(f"✅ Puppeteer 처리 성공: {case_number}")
                
                # 결과 JSON 파일에서 진행내용 데이터 추출
                self._log(f"🔍 결과 파일에서 진행내용 추출 중...")
                progress_data = self.extract_progress_from_result(case_number)
                if progress_data:
                    self._log(f"📊 진행내용 데이터 추출: {len(progress_data)}개 행")
                    return progress_data
                else:
                    self._log(f"⚠️ 진행내용 데이터 없음: {case_number}")
                    return True  # 처리는 성공했지만 데이터는 없음
            else:
                self._log(f"❌ Puppeteer 처리 실패: {case_number} (종료 코드: {returncode})")
                if stderr_lines:
                    self._log(f"❌ 오류 메시지:")
                    for line in stderr_lines[:10]:  # 최대 10줄만
                        if line.strip():
                            self._log(f"  {line.strip()}")
                return False
                
        except Exception as e:
            self._log(f"❌ Puppeteer 실행 오류: {case_number} - {e}")
            return False
    
    def extract_progress_from_result(self, case_number):
        """
        결과 JSON 파일에서 진행내용 데이터 추출
        
        매개변수:
            case_number: 사건번호
        
        반환값:
            progress_data: 진행내용 데이터 리스트 또는 None (실패 시)
        """
        try:
            # results 디렉토리에서 해당 사건의 결과 파일 찾기
            results_dir = config.RESULTS_DIR
            pattern = os.path.join(results_dir, f"case_result_*{case_number}*.json")
            result_files = glob.glob(pattern)
            
            if not result_files:
                self._log(f"⚠️ 결과 파일 없음: {case_number}")
                return None
            
            # 가장 최근 파일 선택
            latest_file = max(result_files, key=os.path.getctime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            
            # 진행내용 데이터 추출
            progress_data = result_data.get('progressData', [])
            return progress_data
            
        except Exception as e:
            self._log(f"❌ 진행내용 데이터 추출 오류: {e}")
            return None

