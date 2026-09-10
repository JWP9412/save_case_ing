"""
Puppeteer 서비스 모듈 (Interactive Mode)
=====================================

Node.js 레인 워커를 유지하며 캡차 입력과 검색을 수행합니다.
같은 프로필(레인)의 사건은 Chrome을 재사용해 기동 횟수를 줄입니다.
"""

import json
import os
import queue
import subprocess
import threading
import time

import config
from services.logger_service import get_logger

logger = get_logger("puppeteer")


def _hidden_run(args, **kwargs):
    """
    콘솔 유틸(taskkill 등)을 창 없이 실행합니다.

    주니어 개발자 참고:
    - Windows 는 taskkill.exe 가 붙을 때 CMD 창이 잠깐 뜹니다.
    - 조회 시작 때 창이 번쩍이는 원인은 Chrome 이 아니라 이 호출입니다.
    - CREATE_NO_WINDOW 는 콘솔 창만 숨깁니다. Chrome headless 와는 무관합니다.
    - 다른 OS 에서는 creationflags 를 넣지 않습니다.
    """
    if os.name == "nt":
        kwargs.setdefault("creationflags", subprocess.CREATE_NO_WINDOW)
    return subprocess.run(args, **kwargs)


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


def kill_orphan_interactive_runners(log_fn=None):
    """
    cmdline 에 interactive_runner.js 가 포함된 node.exe 를 찾아 강제 종료합니다.

    주니어 개발자 참고:
    - lane_workers 딕셔너리에서 빠진 고아 프로세스도 정리합니다.
    - Cursor 등 다른 Node 는 스크립트명으로 걸러 건드리지 않습니다.
    - 반환: 종료에 성공한 프로세스 수
    """
    def _log(msg):
        logger.info(msg)
        if callable(log_fn):
            try:
                log_fn(msg)
            except Exception:
                pass

    try:
        import psutil
    except Exception as e:
        _log(f"⚠️ psutil 없음 — Node 고아 스윕 생략: {e}")
        return 0

    killed = 0
    marker = "interactive_runner.js"
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = (proc.info.get("name") or "").lower()
            if name not in ("node.exe", "node"):
                continue
            cmdline = proc.info.get("cmdline") or []
            joined = " ".join(str(x) for x in cmdline).replace("\\", "/").lower()
            if marker not in joined:
                continue
            pid = proc.info.get("pid")
            _log(f"🔄 고아 Node 워커 종료: PID {pid} ({marker})")
            try:
                if os.name == "nt" and pid:
                    _hidden_run(
                        ["taskkill", "/F", "/T", "/PID", str(pid)],
                        capture_output=True,
                        timeout=5,
                    )
                else:
                    proc.kill()
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception:
            continue

    if killed > 0:
        _log(f"✅ 고아 Node 워커 {killed}개 종료 완료")
    else:
        _log("ℹ️ 종료할 고아 Node 워커 없음")
    return killed


class PuppeteerService:
    """
    Puppeteer 서비스 클래스 (Interactive + 레인 워커)
    """

    def __init__(self, log_callback=None, processing_flag=None):
        # CLI/GUI 콘솔에 진행 로그를 넘길 콜백 (없으면 파일 로그만)
        self.log_callback = log_callback
        self.processing_flag = processing_flag
        # 사건번호 → Node 프로세스 (실행 중 사건 매핑)
        self.running_processes = {}
        # 프로필(레인) → 상주 워커 프로세스
        self.lane_workers = {}
        # 레인 → stderr 파일 핸들 (PIPE 데드락 방지 + 원인 추적)
        self._lane_stderr_files = {}
        # 레인 → stdout 줄 큐 (읽기 스레드 1개만 사용, 줄 훔침 방지)
        self._lane_stdout_queues = {}
        # 레인 → 읽기 스레드 종료 신호
        self._lane_reader_stop = {}
        # 레인 → 읽기 스레드 핸들
        self._lane_reader_threads = {}
        # 사건번호 → 프로필 인덱스 (cleanup 시 워커를 죽이지 않기 위함)
        self._case_to_profile = {}
        # Node JSON의 generalInfo를 사건번호별로 임시 보관
        self.last_general_info = {}
        # Chrome 기동 횟수 (검증/로그용)
        self.chrome_launch_count = 0

    def _log(self, message):
        """
        진행 로그 1회만 남깁니다.

        주니어: GUI 에서는 log_callback(=app.log_message)이 이미
        logger.info → GuiLogHandler → 진행창 으로 이어집니다.
        여기서 logger.info 와 callback 을 둘 다 부르면 같은 줄이
        진행창에 두 번 찍히고 Tk 메인 스레드가 응답없음이 됩니다.
        콜백이 있으면 콜백만, 없으면(테스트 등) 파일 로거만 씁니다.
        """
        if callable(self.log_callback):
            try:
                self.log_callback(message)
                return
            except Exception:
                pass
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

        # GUI·CLI 동일 프로필: cwd 상대경로가 아니라 프로젝트 루트 절대경로를 넘깁니다.
        # 주니어: Node 가 process.cwd()만 쓰면 작업스케줄러/다른 cwd 에서 빈 프로필이 생깁니다.
        cookie_rel = getattr(config, "COOKIE_DATA_DIR", "cookie_data_for_save")
        cookie_abs = config.path_from_base(cookie_rel)
        env["CASEING_COOKIE_DIR"] = cookie_abs

        # Cursor 에이전트 셸이 PUPPETEER_CACHE_DIR 을 샌드박스 경로로 덮어쓰면
        # 번들 Chrome 이 없어 'Could not find Chrome' 로 즉시 실패합니다.
        # 사용자 기본 캐시(~/.cache/puppeteer)가 있으면 그쪽으로 되돌립니다.
        cache = (env.get("PUPPETEER_CACHE_DIR") or "").strip()
        default_cache = os.path.join(os.path.expanduser("~"), ".cache", "puppeteer")
        cache_norm = cache.replace("\\", "/").lower()
        needs_fix = (not cache) or ("cursor-sandbox-cache" in cache_norm) or (
            cache and not os.path.isdir(cache)
        )
        if needs_fix:
            if os.path.isdir(default_cache):
                env["PUPPETEER_CACHE_DIR"] = default_cache
                if cache and cache != default_cache:
                    self._log(
                        f"ℹ️ PUPPETEER_CACHE_DIR 보정: 샌드박스/없음 → {default_cache}"
                    )
            else:
                env.pop("PUPPETEER_CACHE_DIR", None)
        return env

    def _close_lane_stderr(self, instance_index):
        """레인 stderr 파일 핸들을 닫습니다."""
        fh = self._lane_stderr_files.pop(instance_index, None)
        if fh is None:
            return
        try:
            fh.close()
        except Exception:
            pass

    def _open_lane_stderr(self, instance_index):
        """
        레인별 Node stderr 로그 파일을 엽니다.

        주니어: stderr=PIPE + 미읽기 = 데드락. DEVNULL = 원인 소실.
        파일로 리다이렉트하면 둘 다 피합니다. 경로: data/node_stderr_instance_N.log
        """
        self._close_lane_stderr(instance_index)
        rel = getattr(config, "NODE_STDERR_LOG_DIR", "data")
        log_dir = rel if os.path.isabs(rel) else config.path_from_base(rel)
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception:
            log_dir = config.get_base_dir()
        path = os.path.join(log_dir, f"node_stderr_instance_{instance_index}.log")
        try:
            # 덮어쓰기: 이번 워커 기동분만 (너무 커지지 않게)
            fh = open(path, "w", encoding="utf-8", errors="replace")
            self._lane_stderr_files[instance_index] = fh
            self._log(f"📝 Node stderr 로그: {path}")
            return fh
        except Exception as e:
            self._log(f"⚠️ Node stderr 파일 열기 실패 → DEVNULL: {e}")
            return subprocess.DEVNULL

    def _popen_kwargs(self, env, stderr_target=None):
        """
        Node 워커 Popen 옵션.

        주니어: stderr=PIPE 인데 읽는 스레드가 없으면 Chrome 로그가 파이프를
        채워 Node가 write 에서 멈추고, Python 은 stdout.readline 에서 멈추는
        데드락이 납니다. stderr 는 파일(또는 DEVNULL)로 보냅니다.
        """
        base_dir = config.get_base_dir()
        popen_kwargs = dict(
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr_target if stderr_target is not None else subprocess.DEVNULL,
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
            self._log(
                f"❌ 브라우저 준비 실패: 스크립트 없음 "
                f"(레인 {instance_index}, path={script})"
            )
            return None

        self._log(
            f"▶ 브라우저 담당 프로그램 시작 시도 "
            f"(레인 {instance_index}, node={node_exe})"
        )
        cmd = [node_exe, script, "--worker", str(instance_index)]
        env = self._build_env(smart_skip_enabled=smart_skip_enabled)
        stderr_fh = self._open_lane_stderr(instance_index)
        process = subprocess.Popen(cmd, **self._popen_kwargs(env, stderr_target=stderr_fh))
        self.lane_workers[instance_index] = process
        self.chrome_launch_count += 1
        # 주니어: Popen 직후 레인당 읽기 스레드 1개만 띄웁니다.
        # 타임아웃마다 새 readline 스레드를 만들면 WORKER_READY 를 훔칩니다.
        self._start_lane_stdout_reader(instance_index, process)
        self._log(
            f"🚀 브라우저 담당 프로그램 시작 (레인 {instance_index}) "
            f"(누적 Chrome 기동: {self.chrome_launch_count})"
        )

        # Node가 stdout에 WORKER_READY 를 보낼 때까지 대기 (프로토콜 신호명은 유지)
        # 주니어: 콜드 스타트(첫 Chrome/Node)는 puppeteer 로드·프로필 잠금 해제로
        # 30초를 넘길 수 있습니다. 재기동은 짧게, 첫 기동만 여유를 둡니다.
        start = time.time()
        if self.chrome_launch_count <= 1:
            # 방금 chrome_launch_count 를 +1 했으므로 첫 워커는 여기로 옵니다.
            timeout = float(
                getattr(config, "PUPPETEER_WORKER_READY_TIMEOUT_FIRST", 60) or 60
            )
        else:
            timeout = float(
                getattr(config, "PUPPETEER_WORKER_READY_TIMEOUT", 30) or 30
            )
        timeout = max(5.0, timeout)
        last_progress_log = 0.0
        while time.time() - start < timeout:
            elapsed = time.time() - start
            if process.poll() is not None:
                code = process.returncode
                self._log(
                    f"❌ 브라우저 준비 실패: 프로그램이 바로 종료됨 "
                    f"(레인 {instance_index}, exit={code}, 경과 {int(elapsed)}s)"
                )
                # 이미 죽은 프로세스 — kill 불필요, 핸들·맵만 정리
                self._pop_lane_worker(instance_index, kill_if_alive=False)
                return None

            # 약 5초마다 진행 로그 (무음 대기 방지)
            if elapsed - last_progress_log >= 5.0:
                self._log(
                    f"⏳ 브라우저가 켜질 때까지 기다리는 중 (레인 {instance_index}) "
                    f"(경과 {int(elapsed)}s / 한도 {int(timeout)}s)"
                )
                last_progress_log = elapsed

            remaining = timeout - elapsed
            line, timed_out = self._readline_with_timeout(
                process, min(1.0, max(0.05, remaining)), instance_index=instance_index
            )
            if timed_out:
                continue
            if not line:
                continue
            line = line.strip()
            if not line:
                continue
            # 프로토콜 토큰(WORKER_READY) + CASE/QUIT 대기 로그도 준비 완료로 칩니다.
            # 주니어: READY 줄을 놓쳐도 "CASE/QUIT 대기 중"이면 이미 명령을 받을 수 있습니다.
            if self._is_worker_ready_line(line):
                self._log(
                    f"✅ 브라우저 준비 완료 (레인 {instance_index}) "
                    f"(기동 소요 {int(time.time() - start)}s)"
                )
                return process
            self._log(f"[Node] {line}")

        self._log(
            f"❌ 브라우저가 제시간에 안 켜짐 "
            f"(레인 {instance_index}, 경과 {int(time.time() - start)}s / "
            f"한도 {int(timeout)}s)"
        )
        self._pop_lane_worker(instance_index, kill_if_alive=True)
        return None

    def _kill_process_tree(self, process):
        """
        Node 워커와 자식(Chrome)까지 강제 종료.

        주니어: Windows 에서 process.kill() 만 하면 Chrome 자식이 남을 수 있습니다.
        taskkill /T 로 트리를 통째로 끊습니다.
        """
        if not process:
            return
        pid = getattr(process, "pid", None)
        if pid and process.poll() is None:
            try:
                if os.name == "nt":
                    _hidden_run(
                        ["taskkill", "/F", "/T", "/PID", str(pid)],
                        capture_output=True,
                        timeout=5,
                    )
                else:
                    process.kill()
                    process.wait(timeout=2)
            except Exception as e:
                logger.debug("Kill tree error: %s", e)
                try:
                    process.kill()
                except Exception:
                    pass

    def _kill_process(self, process):
        """먼저 terminate, 안 되면 프로세스 트리 강제 종료."""
        if not process:
            return
        try:
            if process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self._kill_process_tree(process)
                except Exception:
                    self._kill_process_tree(process)
        except Exception as e:
            logger.debug("Kill error: %s", e)

    def _is_worker_ready_line(self, line):
        """
        Node 워커가 '명령을 받을 준비'가 됐는지 판별합니다.

        주니어: WORKER_READY 가 줄 훔침으로 사라져도
        'CASE/QUIT 대기 중' 로그가 보이면 이미 stdin 대기 중입니다.
        """
        s = (line or "").strip()
        if not s:
            return False
        if s.startswith("WORKER_READY"):
            return True
        if "CASE/QUIT 대기" in s:
            return True
        return False

    def _start_lane_stdout_reader(self, instance_index, process):
        """
        레인당 stdout 읽기 스레드 1개 + Queue.

        주니어 개발자 참고 (줄 훔침 버그):
        - 예전 `_readline_with_timeout` 은 타임아웃마다 새 스레드로
          process.stdout.readline() 을 호출했습니다.
        - join 타임아웃이 나도 그 스레드는 죽지 않고, 나중에 온
          WORKER_READY 줄을 가로챕니다 → Python 본문은 30~60초를 허비합니다.
        - 레인마다 스레드 1개만 두고 큐에 넣으면 줄이 사라지지 않습니다.
        """
        self._stop_lane_stdout_reader(instance_index)
        if not process or not process.stdout:
            return
        q = queue.Queue()
        stop_ev = threading.Event()
        self._lane_stdout_queues[instance_index] = q
        self._lane_reader_stop[instance_index] = stop_ev

        def _reader():
            # 주니어: 프로세스가 죽으면 readline 이 '' 를 반환하며 루프가 끝납니다.
            try:
                while not stop_ev.is_set():
                    try:
                        line = process.stdout.readline()
                    except Exception:
                        break
                    if line == "" or line is None:
                        # EOF — 큐에 None 센티널을 넣어 대기자가 깨게 합니다.
                        try:
                            q.put(None)
                        except Exception:
                            pass
                        break
                    try:
                        q.put(line)
                    except Exception:
                        break
            except Exception:
                try:
                    q.put(None)
                except Exception:
                    pass

        t = threading.Thread(
            target=_reader,
            daemon=True,
            name=f"lane-stdout-{instance_index}",
        )
        self._lane_reader_threads[instance_index] = t
        t.start()

    def _stop_lane_stdout_reader(self, instance_index):
        """레인 stdout 읽기 스레드·큐를 정리합니다 (프로세스 kill 전/후)."""
        stop_ev = self._lane_reader_stop.pop(instance_index, None)
        if stop_ev is not None:
            try:
                stop_ev.set()
            except Exception:
                pass
        self._lane_stdout_queues.pop(instance_index, None)
        self._lane_reader_threads.pop(instance_index, None)

    def _readline_with_timeout(self, process, timeout_sec, instance_index=None):
        """
        stdout 한 줄을 timeout_sec 초만 기다립니다.

        타임아웃이면 (None, True), 읽으면 (line, False).

        주니어: instance_index 가 있으면 레인 큐에서만 꺼냅니다.
        큐가 없을 때만(레거시·예외) 일회성 스레드를 쓰되, 그 경우도
        가능하면 쓰지 않는 것이 안전합니다.
        """
        q = None
        if instance_index is not None:
            q = self._lane_stdout_queues.get(instance_index)
        if q is not None:
            try:
                line = q.get(timeout=max(0.05, float(timeout_sec)))
            except queue.Empty:
                return None, True
            # None 센티널 = EOF
            if line is None:
                return "", False
            return line, False

        # 폴백: 큐가 없는 경우(거의 없어야 함). 줄 훔침 위험이 있어 짧게만.
        result = {"line": None}

        def _reader():
            try:
                result["line"] = process.stdout.readline()
            except Exception:
                result["line"] = None

        t = threading.Thread(target=_reader, daemon=True)
        t.start()
        t.join(timeout=max(0.05, float(timeout_sec)))
        if t.is_alive():
            return None, True
        return result["line"], False

    def _drain_worker_stdout(self, process, instance_index):
        """
        다음 CASE 를 보내기 전에, 이전 사건이 남긴 stdout 을 비웁니다.

        주니어 개발자 참고:
        - 워커는 사건 끝에 WORKER_IDLE 을 stdout 에 찍습니다.
        - Python 이 JSON_RESULT 만 읽고 끝나면 IDLE 이 파이프(큐)에 남습니다.
        - 다음 사건 캡차 대기가 그 줄을 읽으면
          '캡차/스킵 없이 IDLE = 실패' 로 오판하고 레인을 죽입니다.
        - 이미 도착한 줄만 읽습니다 (짧은 타임아웃).
        """
        if not process or process.poll() is not None:
            return
        if instance_index is None and process.stdout is None:
            return
        drained_idle = 0
        while True:
            line, timed_out = self._readline_with_timeout(
                process, 0.12, instance_index=instance_index
            )
            if timed_out or not line:
                break
            line = line.strip()
            if not line:
                continue
            if line == "WORKER_IDLE":
                drained_idle += 1
                continue
            self._log(f"[Node leftover] {line}")
        if drained_idle:
            self._log(
                f"🧹 이전 사건 WORKER_IDLE {drained_idle}줄 폐기 "
                f"[instance_{instance_index}]"
            )

    def _pop_lane_worker(self, instance_index, *, kill_if_alive=True):
        """
        lane_workers 에서 제거하고, 아직 살아 있으면 프로세스 트리를 죽입니다.

        주니어: pop 만 하고 kill 을 빼먹으면 고아 node.exe 가 남습니다.
        """
        process = self.lane_workers.pop(instance_index, None)
        if process is not None and kill_if_alive:
            try:
                if process.poll() is None:
                    self._kill_process_tree(process)
            except Exception:
                pass
        self._stop_lane_stdout_reader(instance_index)
        self._close_lane_stderr(instance_index)
        return process

    def _kill_orphan_interactive_runners(self):
        """인스턴스 메서드 래퍼 — 로그 콜백을 붙인 고아 Node 스윕."""
        return kill_orphan_interactive_runners(log_fn=self._log)

    def _kill_lane_worker(self, instance_index):
        """특정 레인 워커만 종료 (타임아웃·좀비 방지)."""
        process = self._pop_lane_worker(instance_index, kill_if_alive=True)
        if process is not None:
            self._log(f"🔄 레인 워커 강제 종료: instance_{instance_index}")

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

        워커가 비정상 종료되면 같은 사건을 1회만 즉시 재시도합니다.
        (Request is already handled 등으로 프로세스가 죽은 경우 대응)
        """
        # 워커 사망 재시도는 최대 1회 (무한 루프 방지)
        for attempt in range(2):
            result, fail_reason = self._capture_captcha_image_once(
                case_number,
                defendant,
                court,
                instance_index=instance_index,
                smart_skip_enabled=smart_skip_enabled,
                attempt=attempt,
            )
            if result[0] is not None or fail_reason != "worker_died":
                return result
            if attempt == 0:
                self._log(
                    f"🔄 워커 사망 후 같은 사건 1회 재시도: {case_number} "
                    f"[instance_{instance_index}]"
                )
        return None, None, None

    def _capture_captcha_image_once(
        self,
        case_number,
        defendant,
        court,
        instance_index=0,
        smart_skip_enabled=True,
        attempt=0,
    ):
        """
        캡차 로드 1회 시도.

        Returns:
            (result_tuple, fail_reason)
            - result_tuple: (image_path|__CLICK__|None, None, process|None)
            - fail_reason: None | "worker_died" | "timeout" | "stopped" | "error"
        """
        try:
            attempt_tag = f" (재시도 {attempt})" if attempt else ""
            self._log(
                f"🚀 [Interactive] 프로세스 시작: {case_number} ({court}) "
                f"[instance_{instance_index}]{attempt_tag}"
            )

            # 이전 사건 매핑만 정리 (워커는 유지)
            self.running_processes.pop(case_number, None)

            process = self._ensure_lane_worker(
                instance_index, smart_skip_enabled=smart_skip_enabled
            )
            if process is None:
                return (None, None, None), "worker_died"

            # 이전 건 WORKER_IDLE 등이 파이프에 남아 있으면 먼저 버립니다.
            self._drain_worker_stdout(process, instance_index)

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
                self._log(f"▶ CASE 전송: {case_number} [instance_{instance_index}]")
                process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
                process.stdin.flush()
            except Exception as e:
                self._log(f"❌ 워커 CASE 전송 실패: {e}")
                self._pop_lane_worker(instance_index, kill_if_alive=True)
                return (None, None, None), "worker_died"

            self.running_processes[case_number] = process
            self._case_to_profile[case_number] = instance_index

            start_time = time.time()
            timeout = float(getattr(config, "PUPPETEER_CAPTCHA_TIMEOUT", 30) or 30)
            worker_died = False
            early_fail_reason = None  # WORKER_IDLE / JSON 실패 등
            early_fail_detail = ""
            capturing_json = False
            json_lines = []
            last_progress_log = 0.0
            # 이 사건 처리가 Node 에서 시작되기 전의 IDLE 은 잔여분입니다.
            this_case_started = False
            self._log(
                f"▶ 캡차·스킵 응답 대기 중: {case_number} (한도 {int(timeout)}s)"
            )

            while True:
                elapsed = time.time() - start_time
                remaining = timeout - elapsed
                if remaining <= 0:
                    break
                if callable(self.processing_flag) and not self.processing_flag():
                    self._log(f"⏹️ 처리 중지로 캡차 로드 중단: {case_number}")
                    self.unbind_case(case_number)
                    return (None, None, None), "stopped"

                # 약 5초마다 진행 로그 (무음 대기처럼 보이지 않게)
                if elapsed - last_progress_log >= 5.0:
                    self._log(
                        f"⏳ 캡차 응답 대기 중: {case_number} "
                        f"(경과 {int(elapsed)}s / 한도 {int(timeout)}s)"
                    )
                    last_progress_log = elapsed

                # 남은 시간만 기다리며 읽기 (블로킹으로 타임아웃이 밀리지 않게)
                line, timed_out = self._readline_with_timeout(
                    process, min(1.0, remaining), instance_index=instance_index
                )
                if timed_out:
                    continue
                if not line:
                    if process.poll() is not None:
                        code = process.returncode
                        self._log(
                            f"❌ 프로세스 비정상 종료: {case_number} "
                            f"(exit={code}, stderr→data/node_stderr_instance_*.log)"
                        )
                        # poll() 이 not None 이면 이미 종료됨
                        self._pop_lane_worker(instance_index, kill_if_alive=False)
                        self.unbind_case(case_number)
                        worker_died = True
                        break
                    continue

                line = line.strip()
                if not line:
                    continue

                # 접속/오류/스킵 관련 로그는 가능한 한 전부 보이게
                if any(
                    keyword in line
                    for keyword in [
                        "🚀",
                        "🔍",
                        "✅",
                        "🖼️",
                        "ℹ️",
                        "WORKER",
                        "⚠️",
                        "❌",
                        "🌐",
                        "🔁",
                        "📂",
                        "🍪",
                        "프로필",
                        "사이트",
                        "오류",
                        "실패",
                    ]
                ):
                    self._log(f"[Node] {line}")

                if "GUI_IMAGE_PATH:" in line:
                    image_path = line.split("GUI_IMAGE_PATH:")[1].strip()
                    self._log(f"🖼️ 캡차 이미지 획득: {image_path}")
                    return (image_path, None, process), None

                # 이 사건 로그가 찍히기 전의 IDLE 은 이전 건 잔여입니다.
                if (
                    "사건 처리 시작" in line
                    and case_number
                    and case_number in line
                ):
                    this_case_started = True

                if "CAPTCHA_STATUS: SKIP_AND_CLICK" in line:
                    self._log(f"⚡ 스마트 스킵 활성화: {case_number}")
                    return ("__CLICK__", None, process), None

                # 캡차/스킵 없이 사건이 끝난 경우 → 30초 기다리지 말고 즉시 실패
                if line == "JSON_RESULT_START":
                    capturing_json = True
                    json_lines = []
                    continue
                if capturing_json:
                    if line == "JSON_RESULT_END":
                        capturing_json = False
                        try:
                            payload = json.loads("\n".join(json_lines))
                        except Exception:
                            payload = None
                        if isinstance(payload, dict) and payload.get("success") is False:
                            early_fail_detail = str(payload.get("error") or "unknown")
                            early_fail_reason = "node_error"
                            self._log(
                                f"❌ Node 사건 실패(캡차 전): {case_number} — {early_fail_detail}"
                            )
                            break
                        json_lines = []
                        continue
                    json_lines.append(line)
                    continue

                if line.strip() == "WORKER_IDLE":
                    # 주니어: CASE 전송 직후 첫 IDLE 은 거의 항상 이전 건 잔여입니다.
                    # 이 사건 시작 로그 이전이면 무시하고 계속 기다립니다.
                    if not this_case_started:
                        self._log(
                            f"ℹ️ 이전 건 잔여 WORKER_IDLE 무시: {case_number} "
                            f"[instance_{instance_index}]"
                        )
                        continue
                    # 이 사건이 캡차/스킵 없이 끝났을 때만 실패
                    early_fail_reason = early_fail_reason or "worker_idle"
                    early_fail_detail = early_fail_detail or (
                        "캡차/스킵 응답 없이 WORKER_IDLE"
                    )
                    self._log(
                        f"❌ 캡차 응답 없이 WORKER_IDLE: {case_number} "
                        f"({early_fail_detail})"
                    )
                    break

            # 루프 종료: 워커 사망 vs Node 조기실패 vs 실제 타임아웃
            if worker_died:
                self._log(
                    f"❌ 워커 크래시로 캡차 로드 실패: {case_number} "
                    f"(초기화 타임아웃이 아님)"
                )
                return (None, None, None), "worker_died"

            if early_fail_reason:
                self.unbind_case(case_number)
                # 잔여 IDLE 오판으로 레인을 죽이면 Chrome 재기동이 폭주합니다.
                # 워커가 살아 있으면 같은 프로세스에 다음 CASE 를 재사용합니다.
                if (
                    early_fail_reason == "worker_idle"
                    and process is not None
                    and process.poll() is None
                ):
                    self._log(
                        f"ℹ️ WORKER_IDLE 이지만 워커 생존 → 레인 유지 "
                        f"[instance_{instance_index}]"
                    )
                    return (None, None, None), early_fail_reason
                # node_error 등: 워커가 브라우저를 닫았을 수 있어 레인 재기동
                self._kill_lane_worker(instance_index)
                return (None, None, None), early_fail_reason

            elapsed = int(time.time() - start_time)
            self._log(
                f"⏰ 초기화 타임아웃: {case_number} "
                f"(실제 {elapsed}초 대기, 한도 {int(timeout)}초)"
            )
            # 멈춘 워커는 다음 건이 못 쓰므로 강제 종료 → 다음 CASE 때 재기동
            self.unbind_case(case_number)
            self._kill_lane_worker(instance_index)
            return (None, None, None), "timeout"

        except Exception as e:
            self._log(f"❌ 프로세스 실행 오류: {e}")
            self.unbind_case(case_number)
            return (None, None, None), "error"

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
            # 주니어: stdout 은 레인 전용 읽기 스레드가 큐에 넣습니다.
            # 여기서 process.stdout.readline() 을 직접 쓰면 큐와 경쟁하거나
            # 줄이 안 와서 영원히 기다릴 수 있습니다.
            profile_index = self._case_to_profile.get(case_number)

            while time.time() - start_time < timeout:
                if callable(self.processing_flag) and not self.processing_flag():
                    self._log(f"⏹️ 처리 중지로 실행 중단: {case_number}")
                    self.unbind_case(case_number)
                    return False
                remaining = timeout - (time.time() - start_time)
                line, timed_out = self._readline_with_timeout(
                    process,
                    min(1.0, max(0.05, remaining)),
                    instance_index=profile_index,
                )
                if timed_out:
                    continue
                if not line:
                    if process.poll() is not None:
                        break
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
                            # 재입력 대기를 위해 사건↔워커 매핑 유지
                            skip_cleanup = True
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
        """
        모든 레인 워커에 QUIT을 보내고, 안 죽으면 프로세스 트리 강제 종료.
        이어서 cmdline 기준 고아 interactive_runner Node 도 스윕합니다.

        조회 중지/배치 완료/창 닫기 직후에 호출합니다.
        """
        for idx, process in list(self.lane_workers.items()):
            try:
                if process and process.poll() is None:
                    quit_sent = False
                    try:
                        process.stdin.write(json.dumps({"cmd": "QUIT"}) + "\n")
                        process.stdin.flush()
                        quit_sent = True
                    except Exception:
                        quit_sent = False
                    if quit_sent:
                        try:
                            process.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            self._kill_process_tree(process)
                    else:
                        self._kill_process_tree(process)
            finally:
                self.lane_workers.pop(idx, None)
                self._stop_lane_stdout_reader(idx)
                self._close_lane_stderr(idx)
        self.running_processes.clear()
        self._case_to_profile.clear()
        self._log(
            f"✅ 레인 워커 맵 정리 완료 (이번 배치 Chrome 기동 횟수: {self.chrome_launch_count})"
        )
        self.chrome_launch_count = 0
        # 딕셔너리에서 빠진 고아 Node 까지 정리 (창 종료·강제 중지 대비)
        self._kill_orphan_interactive_runners()
