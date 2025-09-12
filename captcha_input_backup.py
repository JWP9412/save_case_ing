"""
실시간 캡차 처리 시스템 - 파이썬 GUI 입력창
===============================================

역할: 사용자가 캡차 이미지를 보고 직접 6글자를 입력할 수 있는 GUI 창을 제공
기능: 
- Tkinter로 GUI 창 생성
- 캡차 이미지 표시 및 새로고침
- 6글자 캡차 입력 받기
- 입력값을 Cypress로 전달
- 사용자 친화적인 인터페이스 제공

사용법: Cypress가 자동으로 호출하여 실행
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import os
import sys

def get_captcha_input(case_number, captcha_image_path):
    """
    캡차 입력을 위한 GUI 창을 생성합니다.
    
    Args:
        case_number (str): 처리할 사건 번호 (예: "2024가합51101")
        captcha_image_path (str): 캡차 이미지 파일 경로 (현재는 사용하지 않음)
    
    Returns:
        str: 사용자가 입력한 6글자 캡차 텍스트, 실패시 빈 문자열
    """
    # ========================================
    # 1. GUI 윈도우 기본 설정
    # ========================================
    # Tkinter의 메인 윈도우 객체 생성
    # 이 윈도우가 모든 GUI 요소들의 컨테이너 역할을 함
    root = tk.Tk()
    root.title("실시간 캡차 처리")  # 윈도우 제목 표시줄에 표시될 텍스트
    root.geometry("600x600")        # 윈도우 크기 설정 (가로x세로 픽셀)
    root.resizable(True, True)      # 사용자가 윈도우 크기 조절 가능하도록 설정
    
    # 윈도우를 화면 중앙에 배치
    # tk::PlaceWindow . center는 Tkinter의 내장 명령어
    root.eval('tk::PlaceWindow . center')
    
    # ========================================
    # 2. 메인 컨테이너 프레임 생성
    # ========================================
    # 모든 GUI 요소들을 담을 메인 프레임 생성
    # padx=20, pady=20: 프레임 내부 여백 설정 (좌우 20px, 상하 20px)
    main_frame = tk.Frame(root, padx=20, pady=20)
    # fill=tk.BOTH: 프레임이 부모 윈도우의 가로, 세로 공간을 모두 채움
    # expand=True: 윈도우 크기가 변경될 때 프레임도 함께 확장됨
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # ========================================
    # 3. GUI 요소들 생성 및 배치
    # ========================================
    
    # 3-1. 제목 라벨 생성
    # text: 표시할 텍스트 (이모지 포함)
    # font: 폰트 설정 (폰트명, 크기, 스타일)
    # fg: foreground color (글자색)
    title_label = tk.Label(main_frame, text="📋 실시간 캡차 처리 표", 
                          font=("Arial", 16, "bold"), fg="blue")
    # pady=(0, 20): 상단 여백 0px, 하단 여백 20px
    title_label.pack(pady=(0, 20))
    
    # 3-2. 구분선 생성 (시각적 구분을 위한 선)
    # height=2: 선의 두께 2픽셀
    # bg="gray": 배경색 회색
    separator1 = tk.Frame(main_frame, height=2, bg="gray")
    # fill=tk.X: 가로 방향으로 프레임을 가득 채움
    separator1.pack(fill=tk.X, pady=(0, 20))
    
    # 3-3. 사건 정보 표시 영역
    # 사건 번호와 값을 나란히 표시하기 위한 컨테이너 프레임
    case_frame = tk.Frame(main_frame)
    case_frame.pack(fill=tk.X, pady=(0, 10))
    
    # 사건 번호 라벨 (고정 텍스트)
    tk.Label(case_frame, text="사건 번호:", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
    # 실제 사건 번호 표시 (빨간색으로 강조)
    # padx=(10, 0): 왼쪽 여백 10px, 오른쪽 여백 0px
    tk.Label(case_frame, text=case_number, font=("Arial", 12), fg="red").pack(side=tk.LEFT, padx=(10, 0))
    
    # ========================================
    # 4. 캡차 이미지 표시 영역 설정
    # ========================================
    
    # 4-1. 캡차 이미지를 담을 프레임 생성
    # relief=tk.SUNKEN: 테두리가 안쪽으로 들어간 3D 효과
    # bd=2: border width (테두리 두께) 2픽셀
    # bg="white": 배경색 흰색
    image_frame = tk.Frame(main_frame, relief=tk.SUNKEN, bd=2, bg="white")
    image_frame.pack(fill=tk.X, pady=(0, 10))
    
    # 4-2. 이미지 영역 헤더 (제목과 새로고침 버튼을 담을 영역)
    image_header = tk.Frame(image_frame, bg="white")
    image_header.pack(fill=tk.X, padx=5, pady=5)
    
    # 캡차 이미지 라벨 (고정 텍스트)
    tk.Label(image_header, text="캡차 이미지:", font=("Arial", 12, "bold"), bg="white").pack(side=tk.LEFT)
    
    # ========================================
    # 5. 새로고침 기능 구현
    # ========================================
    
    # 5-1. 새로고침 버튼 클릭 시 실행될 함수
    def refresh_image():
        """
        캡차 이미지를 새로고침하는 함수
        - 최신 스크린샷 파일을 찾아서 다시 로드
        - 사용자가 이미지가 안 보일 때 새로고침 버튼을 클릭하여 사용
        """
        # nonlocal: 중첩 함수에서 외부 함수의 변수를 수정하기 위해 사용
        # 이 변수들은 나중에 정의되지만, 여기서 수정할 수 있도록 선언
        nonlocal img_label, photo, screenshot_path
        
        try:
            # ========================================
            # 5-2. 최신 이미지 파일 찾기 로직
            # ========================================
            
            # 현재 스크립트 파일의 디렉토리 경로를 절대 경로로 가져오기
            # __file__: 현재 실행 중인 파일의 경로
            # os.path.abspath(): 상대 경로를 절대 경로로 변환
            # os.path.dirname(): 파일 경로에서 디렉토리 부분만 추출
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 스크린샷이 저장될 수 있는 두 개의 가능한 디렉토리 경로
            # 1. 메인 스크린샷 디렉토리: cypress/screenshots/
            # 2. 하위 디렉토리: cypress/screenshots/realtime-captcha-automation.cy.js/
            screenshot_dirs = [
                os.path.join(current_dir, "cypress", "screenshots"),  # 메인 스크린샷 디렉토리
                os.path.join(current_dir, "cypress", "screenshots", "realtime-captcha-automation.cy.js")  # 하위 디렉토리
            ]
            
            # 디버깅을 위한 로그 출력 (개발 시에만 사용)
            print(f"새로고침: 스크린샷 디렉토리들 검색")
            for dir_path in screenshot_dirs:
                print(f"  - {dir_path} (존재: {os.path.exists(dir_path)})")
            
            # ========================================
            # 5-3. 각 디렉토리에서 사건번호로 시작하는 이미지 파일 검색
            # ========================================
            for screenshot_dir in screenshot_dirs:
                # 디렉토리가 실제로 존재하는지 확인
                if os.path.exists(screenshot_dir):
                    import glob  # 파일 패턴 매칭을 위한 모듈
                    
                    # 사건번호로 시작하는 PNG 파일들을 찾는 패턴 생성
                    # 예: "2024가합51101-*.png" 형태의 패턴
                    pattern = os.path.join(screenshot_dir, f"{case_number}-*.png")
                    files = glob.glob(pattern)  # 패턴에 맞는 모든 파일 경로를 리스트로 반환
                    print(f"새로고침: 디렉토리 {screenshot_dir}에서 찾은 파일들 - {files}")
                    
                    # 파일이 발견된 경우
                    if files:
                        # ========================================
                        # 5-4. 파일명에서 날짜+시간 추출하여 최신 파일 찾기
                        # ========================================
                        def extract_datetime(filename):
                            """
                            파일명에서 날짜+시간 정보를 추출하는 내부 함수
                            파일명 형식: "사건번호-YYYYMMDD-HHMMSS.png"
                            예: "2024가합51101-20241201-143022.png"
                            
                            Args:
                                filename (str): 파일 경로
                            
                            Returns:
                                int: 날짜+시간을 숫자로 변환한 값 (비교용)
                            """
                            try:
                                # 파일 경로에서 파일명만 추출
                                basename = os.path.basename(filename)
                                # 하이픈(-)으로 분리하여 배열로 만들기
                                parts = basename.split('-')
                                if len(parts) >= 3:
                                    # 날짜(parts[1]) + 시간(parts[2]에서 확장자 제거)
                                    date_time = parts[1] + parts[2].split('.')[0]  # YYYYMMDDHHMMSS
                                    return int(date_time)  # 숫자로 변환하여 비교 가능하게 함
                                return 0  # 형식이 맞지 않으면 0 반환
                            except:
                                return 0  # 오류 발생 시 0 반환
                        
                        # 파일 목록에서 날짜+시간이 가장 큰(최신) 파일 찾기
                        # max() 함수에 key 파라미터로 extract_datetime 함수를 전달
                        latest_file = max(files, key=extract_datetime)
                        screenshot_path = latest_file  # 최신 파일 경로 저장
                        print(f"새로고침: 최신 이미지 로드 - {latest_file}")
                        break  # 파일을 찾았으면 더 이상 검색하지 않고 루프 종료
            
            # ========================================
            # 5-5. 찾은 이미지 파일을 GUI에 다시 로드
            # ========================================
            if screenshot_path and os.path.exists(screenshot_path):
                # PIL( Pillow ) 라이브러리를 사용하여 이미지 파일 열기
                img = Image.open(screenshot_path)
                # 이미지 크기를 240x80 픽셀로 리사이즈 (캡차 이미지에 적합한 크기)
                # LANCZOS: 고품질 리샘플링 알고리즘 사용
                img = img.resize((240, 80), Image.Resampling.LANCZOS)
                # Tkinter에서 사용할 수 있는 PhotoImage 객체로 변환
                photo = ImageTk.PhotoImage(img)
                # 기존 이미지 라벨의 이미지를 새로운 이미지로 교체
                img_label.configure(image=photo)
                img_label.image = photo  # 참조 유지 (가비지 컬렉션 방지)
                # 상태 라벨에 성공 메시지 표시 (초록색)
                status_label.configure(text=f"파일: {screenshot_path} (새로고침됨)", fg="green")
            else:
                # 이미지 파일을 찾지 못한 경우 오류 메시지 표시 (빨간색)
                status_label.configure(text="이미지를 찾을 수 없습니다", fg="red")
        except Exception as e:
            # 예외 발생 시 오류 메시지 표시 (빨간색)
            status_label.configure(text=f"이미지 로드 오류: {str(e)}", fg="red")
    
    # ========================================
    # 5-6. 새로고침 버튼 생성
    # ========================================
    # 새로고침 버튼 생성 및 배치
    # command=refresh_image: 버튼 클릭 시 refresh_image 함수 실행
    # bg="lightblue": 배경색 연한 파란색
    # relief=tk.RAISED: 버튼이 튀어나온 3D 효과
    refresh_btn = tk.Button(image_header, text="새로고침", command=refresh_image, 
                           font=("Arial", 10), bg="lightblue", relief=tk.RAISED)
    # side=tk.RIGHT: 헤더 프레임의 오른쪽에 배치
    # padx=(10, 0): 왼쪽 여백 10px, 오른쪽 여백 0px
    refresh_btn.pack(side=tk.RIGHT, padx=(10, 0))
    
    # ========================================
    # 6. 실제 캡차 이미지 표시 로직
    # ========================================
    try:
        # 스크린샷 경로 찾기 (최신 이미지 우선)
        screenshot_path = None
        
        # 1. 사건번호+날짜+시간 형식의 최신 이미지 찾기
        # 절대 경로로 스크린샷 디렉토리 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 두 개의 가능한 디렉토리 검색
        screenshot_dirs = [
            os.path.join(current_dir, "cypress", "screenshots"),  # 메인 스크린샷 디렉토리
            os.path.join(current_dir, "cypress", "screenshots", "realtime-captcha-automation.cy.js")  # 하위 디렉토리
        ]
        
        print(f"스크린샷 디렉토리들 검색:")
        # 디버깅을 위한 로그 출력 (개발 시에만 사용)
        for dir_path in screenshot_dirs:
            print(f"  - {dir_path} (존재: {os.path.exists(dir_path)})")
        
        # ========================================
        # 6-2. 각 디렉토리에서 사건번호로 시작하는 이미지 파일 검색
        # ========================================
        for screenshot_dir in screenshot_dirs:
            # 디렉토리가 실제로 존재하는지 확인
            if os.path.exists(screenshot_dir):
                import glob  # 파일 패턴 매칭을 위한 모듈
                
                # 사건번호로 시작하는 PNG 파일들을 찾는 패턴 생성
                # 예: "2024가합51101-*.png" 형태의 패턴
                pattern = os.path.join(screenshot_dir, f"{case_number}-*.png")
                files = glob.glob(pattern)  # 패턴에 맞는 모든 파일 경로를 리스트로 반환
                print(f"디렉토리 {screenshot_dir}에서 찾은 파일들: {files}")
                
                # 파일이 발견된 경우
                if files:
                    # ========================================
                    # 6-3. 파일명에서 날짜+시간 추출하여 최신 파일 찾기
                    # ========================================
                    def extract_datetime(filename):
                        """
                        파일명에서 날짜+시간 정보를 추출하는 내부 함수
                        파일명 형식: "사건번호-YYYYMMDD-HHMMSS.png"
                        예: "2024가합51101-20241201-143022.png"
                        
                        Args:
                            filename (str): 파일 경로
                        
                        Returns:
                            int: 날짜+시간을 숫자로 변환한 값 (비교용)
                        """
                        try:
                            # 파일 경로에서 파일명만 추출
                            basename = os.path.basename(filename)
                            # 하이픈(-)으로 분리하여 배열로 만들기
                            parts = basename.split('-')
                            if len(parts) >= 3:
                                # 날짜(parts[1]) + 시간(parts[2]에서 확장자 제거)
                                date_time = parts[1] + parts[2].split('.')[0]  # YYYYMMDDHHMMSS
                                return int(date_time)  # 숫자로 변환하여 비교 가능하게 함
                            return 0  # 형식이 맞지 않으면 0 반환
                        except:
                            return 0  # 오류 발생 시 0 반환
                    
                    # 파일 목록에서 날짜+시간이 가장 큰(최신) 파일 찾기
                    # max() 함수에 key 파라미터로 extract_datetime 함수를 전달
                    latest_file = max(files, key=extract_datetime)
                    screenshot_path = latest_file  # 최신 파일 경로 저장
                    print(f"최신 캡차 이미지 발견: {latest_file}")
                    break  # 파일을 찾았으면 더 이상 검색하지 않고 루프 종료
        
        # ========================================
        # 6-4. 대체 경로들 확인 (패턴 매칭으로 찾지 못한 경우)
        # ========================================
        # 위의 패턴 매칭으로 파일을 찾지 못한 경우, 가능한 경로들을 직접 확인
        if not screenshot_path:
            # 가능한 모든 경로들을 리스트로 정의
            # captcha_image_path가 None일 수 있으므로 f-string 사용 시 주의
            possible_paths = [
                os.path.join(current_dir, "cypress", "screenshots", "realtime-captcha-automation.cy.js", f"{captcha_image_path}.png"),
                os.path.join(current_dir, "cypress", "screenshots", f"{captcha_image_path}.png"),
                os.path.join(current_dir, f"{captcha_image_path}.png"),
                f"cypress/screenshots/realtime-captcha-automation.cy.js/{captcha_image_path}.png",
                f"cypress/screenshots/{captcha_image_path}.png",
                f"{captcha_image_path}.png"
            ]
            
            print(f"대체 경로들 검색:")
            # 각 경로가 실제로 존재하는지 확인
            for path in possible_paths:
                print(f"  - {path} (존재: {os.path.exists(path)})")
                if os.path.exists(path):
                    screenshot_path = path  # 존재하는 첫 번째 경로를 사용
                    break  # 찾았으면 루프 종료
        
        # ========================================
        # 6-5. 이미지 파일을 찾은 경우 GUI에 표시
        # ========================================
        if screenshot_path and os.path.exists(screenshot_path):
            # ========================================
            # 6-5-1. 이미지 로드 및 리사이즈
            # ========================================
            # PIL( Pillow ) 라이브러리를 사용하여 이미지 파일 열기
            img = Image.open(screenshot_path)
            # 이미지 크기를 240x80 픽셀로 리사이즈 (캡차 이미지에 적합한 크기)
            # LANCZOS: 고품질 리샘플링 알고리즘 사용
            img = img.resize((240, 80), Image.Resampling.LANCZOS)
            # Tkinter에서 사용할 수 있는 PhotoImage 객체로 변환
            photo = ImageTk.PhotoImage(img)
            
            # ========================================
            # 6-5-2. 이미지 표시용 컨테이너 및 라벨 생성
            # ========================================
            # 이미지를 담을 컨테이너 프레임 생성
            img_container = tk.Frame(image_frame, bg="white")
            img_container.pack(fill=tk.X, padx=5, pady=5)
            
            # 실제 이미지를 표시할 라벨 생성
            # relief=tk.SUNKEN: 테두리가 안쪽으로 들어간 3D 효과
            # bd=2: 테두리 두께 2픽셀
            img_label = tk.Label(img_container, image=photo, relief=tk.SUNKEN, bd=2, bg="white")
            img_label.image = photo  # 참조 유지 (가비지 컬렉션 방지)
            img_label.pack()
            
            # ========================================
            # 6-5-3. 드래그 기능 구현 (이미지를 마우스로 드래그 가능)
            # ========================================
            def start_drag(event):
                """
                드래그 시작 시 호출되는 함수
                - 마우스 좌표를 저장하여 드래그 거리 계산에 사용
                """
                img_label.drag_data = {"x": event.x, "y": event.y}
            
            def on_drag(event):
                """
                드래그 중에 호출되는 함수
                - 마우스 이동 거리를 계산하여 이미지 위치 업데이트
                """
                if hasattr(img_label, 'drag_data'):
                    # 현재 마우스 위치와 시작 위치의 차이 계산
                    dx = event.x - img_label.drag_data["x"]
                    dy = event.y - img_label.drag_data["y"]
                    # 이미지 위치를 새로운 위치로 이동
                    img_label.place(x=img_label.winfo_x() + dx, y=img_label.winfo_y() + dy)
                    # 다음 드래그를 위해 현재 위치를 시작 위치로 업데이트
                    img_label.drag_data = {"x": event.x, "y": event.y}
            
            def stop_drag(event):
                """
                드래그 종료 시 호출되는 함수
                - 드래그 데이터를 정리하여 메모리 절약
                """
                if hasattr(img_label, 'drag_data'):
                    del img_label.drag_data
            
            # ========================================
            # 6-5-4. 마우스 이벤트 바인딩
            # ========================================
            # <Button-1>: 마우스 왼쪽 버튼 클릭
            img_label.bind("<Button-1>", start_drag)
            # <B1-Motion>: 마우스 왼쪽 버튼을 누른 상태로 이동
            img_label.bind("<B1-Motion>", on_drag)
            # <ButtonRelease-1>: 마우스 왼쪽 버튼을 놓음
            img_label.bind("<ButtonRelease-1>", stop_drag)
            
            # ========================================
            # 6-5-5. 상태 표시 라벨
            # ========================================
            # 현재 로드된 파일명을 표시하는 라벨
            status_label = tk.Label(image_frame, text=f"파일: {os.path.basename(screenshot_path)}", 
                    font=("Arial", 10), fg="green", bg="white")
            status_label.pack(anchor=tk.W, padx=5)
        # ========================================
        # 6-6. 이미지 파일을 찾지 못한 경우 오류 메시지 표시
        # ========================================
        else:
            # 오류 메시지를 표시할 컨테이너 생성
            img_container = tk.Frame(image_frame, bg="white")
            img_container.pack(fill=tk.X, padx=5, pady=5)
            
            # "이미지를 찾을 수 없습니다" 메시지 표시
            img_label = tk.Label(img_container, text="이미지를 찾을 수 없습니다", 
                    font=("Arial", 10), fg="red", bg="white")
            img_label.pack(pady=(5, 0))
            
            # 가능한 경로들을 표시하는 라벨
            status_label = tk.Label(img_container, text=f"가능한 경로들:", 
                    font=("Arial", 9), fg="gray", bg="white")
            status_label.pack(anchor=tk.W)
            
            # 각 가능한 경로를 작은 글씨로 표시 (디버깅용)
            for path in possible_paths:
                tk.Label(img_container, text=f"  - {path}", font=("Arial", 8), fg="gray", bg="white").pack(anchor=tk.W)
                
    except Exception as e:
        # 예외 발생 시 오류 메시지 표시
        tk.Label(image_frame, text=f"이미지 로드 오류: {str(e)}", 
                font=("Arial", 10), fg="red").pack(anchor=tk.W)
    
    # ========================================
    # 7. 사용자 인터페이스 완성
    # ========================================
    
    # 7-1. 구분선 생성 (이미지 영역과 입력 영역 사이)
    separator2 = tk.Frame(main_frame, height=2, bg="gray")
    separator2.pack(fill=tk.X, pady=(0, 20))
    
    # 7-2. 사용자 안내 메시지
    # 사용자가 어떻게 해야 하는지 단계별로 안내
    instruction_label = tk.Label(main_frame, 
                                text="👤 사용자 안내:\n" +
                                     "1. 위의 캡차 이미지에서 6글자를 확인하세요\n" +
                                     "2. 6글자 캡차를 입력하세요 (예: ABC123)\n" +
                                     "3. 입력이 완료되면 확인 버튼을 눌러주세요",
                                font=("Arial", 11), justify=tk.LEFT)
    instruction_label.pack(pady=(0, 20))
    
    # ========================================
    # 7-3. 캡차 입력 영역 생성
    # ========================================
    
    # 7-3-1. 입력 프레임 생성
    input_frame = tk.Frame(main_frame)
    input_frame.pack(fill=tk.X, pady=(0, 20))
    
    # 7-3-2. 입력 라벨 생성
    tk.Label(input_frame, text="6글자 캡차 입력:", font=("Arial", 12, "bold")).pack(anchor=tk.W)
    
    # 7-3-3. 입력 필드 생성
    # StringVar: Tkinter의 문자열 변수 (입력값과 바인딩)
    captcha_var = tk.StringVar()
    # Entry: 텍스트 입력 필드
    # textvariable: 입력값이 captcha_var에 자동으로 저장됨
    # justify=tk.CENTER: 입력 텍스트를 중앙 정렬
    captcha_entry = tk.Entry(input_frame, textvariable=captcha_var, 
                            font=("Arial", 14), width=10, justify=tk.CENTER)
    captcha_entry.pack(pady=(5, 0))
    captcha_entry.focus()  # 프로그램 시작 시 입력 필드에 포커스 설정
    
    # ========================================
    # 8. 사용자 입력 처리 로직
    # ========================================
    
    # 8-1. 결과를 저장할 딕셔너리 변수
    # 이 변수에 사용자가 입력한 캡차 텍스트가 저장됨
    result = {"captcha": ""}
    
    def on_submit():
        """
        확인 버튼 클릭 시 실행되는 함수
        - 사용자가 입력한 캡차 텍스트를 검증
        - 6글자가 맞으면 결과에 저장하고 창을 닫음
        - 6글자가 아니면 오류 메시지를 표시하고 다시 입력 요청
        """
        # 사용자가 입력한 텍스트를 가져와서 앞뒤 공백 제거
        captcha_text = captcha_var.get().strip()
        
        # 입력된 텍스트가 정확히 6글자인지 검증
        if len(captcha_text) == 6:
            # 6글자가 맞으면 결과 딕셔너리에 저장
            result["captcha"] = captcha_text
            # GUI 창을 닫음 (root.destroy()가 호출되면 mainloop()가 종료됨)
            root.destroy()
        else:
            # 6글자가 아니면 오류 메시지 표시
            messagebox.showerror("오류", "6글자 캡차를 정확히 입력해주세요!")
            # 입력 필드를 비우고 다시 포커스를 맞춤
            captcha_entry.delete(0, tk.END)
            captcha_entry.focus()
    
    def on_cancel():
        """
        취소 버튼 클릭 시 실행되는 함수
        - 빈 문자열을 결과에 저장하고 창을 닫음
        - 이 경우 Cypress에서는 입력 실패로 처리됨
        """
        result["captcha"] = ""  # 빈 문자열로 설정
        root.destroy()  # GUI 창 닫기
    
    # ========================================
    # 9. 버튼 생성 및 이벤트 바인딩
    # ========================================
    
    # 9-1. 버튼들을 담을 프레임 생성
    button_frame = tk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=(0, 10))
    
    # 9-2. 확인 버튼 생성
    # command=on_submit: 버튼 클릭 시 on_submit 함수 실행
    # bg="lightgreen": 배경색 연한 초록색 (성공을 의미)
    # width=10: 버튼 너비 10글자 크기
    submit_btn = tk.Button(button_frame, text="✅ 확인", command=on_submit,
                          font=("Arial", 12), bg="lightgreen", width=10)
    submit_btn.pack(side=tk.LEFT, padx=(0, 10))  # 왼쪽에 배치, 오른쪽 여백 10px
    
    # 9-3. 취소 버튼 생성
    # command=on_cancel: 버튼 클릭 시 on_cancel 함수 실행
    # bg="lightcoral": 배경색 연한 빨간색 (취소를 의미)
    cancel_btn = tk.Button(button_frame, text="❌ 취소", command=on_cancel,
                          font=("Arial", 12), bg="lightcoral", width=10)
    cancel_btn.pack(side=tk.LEFT)  # 확인 버튼 옆에 배치
    
    # ========================================
    # 10. 키보드 이벤트 바인딩
    # ========================================
    
    # 10-1. Enter 키 바인딩
    # 사용자가 입력 필드에서 Enter 키를 누르면 확인 버튼과 동일한 동작
    # lambda e: on_submit(): 이벤트 객체를 받지만 사용하지 않고 on_submit() 호출
    root.bind('<Return>', lambda e: on_submit())
    
    # ========================================
    # 11. GUI 실행 및 결과 반환
    # ========================================
    
    # 11-1. GUI 메인 루프 시작
    # 이 함수가 호출되면 GUI가 화면에 표시되고 사용자 입력을 기다림
    # 사용자가 확인 또는 취소 버튼을 클릭하면 mainloop()가 종료됨
    root.mainloop()
    
    # 11-2. 결과 반환
    # 사용자가 입력한 캡차 텍스트를 반환 (취소한 경우 빈 문자열)
    return result["captcha"]

# ========================================
# 12. 메인 실행 부분 (스크립트가 직접 실행될 때만)
# ========================================

if __name__ == "__main__":
    """
    이 스크립트가 직접 실행될 때만 실행되는 부분
    (다른 파일에서 import할 때는 실행되지 않음)
    
    사용법: python captcha_input.py <사건번호>
    예시: python captcha_input.py 2024가합51101
    """
    
    # ========================================
    # 12-1. 명령행 인수 검증
    # ========================================
    
    # sys.argv: 명령행에서 전달된 인수들의 리스트
    # sys.argv[0]: 스크립트 파일명 (captcha_input.py)
    # sys.argv[1]: 첫 번째 인수 (사건번호)
    if len(sys.argv) < 2:
        print("ERROR: 사건번호가 필요합니다. 사용법: python captcha_input.py <사건번호>")
        sys.exit(1)  # 오류 코드 1로 프로그램 종료
    
    # ========================================
    # 12-2. 사건번호 추출 및 GUI 실행
    # ========================================
    
    # 명령행에서 전달된 사건번호를 변수에 저장
    case_number = sys.argv[1]
    print(f"DEBUG: 사건번호 = '{case_number}'")
    
    # GUI 함수 호출하여 사용자로부터 캡차 입력 받기
    # captcha_image_path=None: 이미지 경로는 함수 내부에서 자동으로 찾음
    captcha_input = get_captcha_input(case_number, None)
    
    # ========================================
    # 12-3. 입력값 검증 및 결과 출력
    # ========================================
    
    # 디버깅을 위한 상세 정보 출력
    print(f"DEBUG: captcha_input = '{captcha_input}'")
    print(f"DEBUG: type = {type(captcha_input)}")
    print(f"DEBUG: length = {len(captcha_input) if captcha_input else 'None'}")
    
    # 입력값이 유효한지 검증 (6글자 문자열인지 확인)
    if captcha_input and len(captcha_input) == 6:
        # 유효한 입력인 경우 성공 메시지와 함께 결과 출력
        # 이 출력은 Cypress에서 subprocess로 읽어서 사용함
        print(f"SUCCESS: {captcha_input}")
    else:
        # 유효하지 않은 입력인 경우 오류 메시지 출력 후 프로그램 종료
        print("ERROR: Invalid captcha input")
        sys.exit(1)  # 오류 코드 1로 프로그램 종료
