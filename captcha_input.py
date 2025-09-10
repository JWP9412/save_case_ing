import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import os
import sys

def get_captcha_input(case_number, captcha_image_path):
    """
    캡차 입력을 위한 GUI 창을 생성합니다.
    """
    # 메인 윈도우 생성
    root = tk.Tk()
    root.title("실시간 캡차 처리")
    root.geometry("600x600")
    root.resizable(True, True)
    
    # 중앙에 배치
    root.eval('tk::PlaceWindow . center')
    
    # 메인 프레임
    main_frame = tk.Frame(root, padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 제목
    title_label = tk.Label(main_frame, text="📋 실시간 캡차 처리 표", 
                          font=("Arial", 16, "bold"), fg="blue")
    title_label.pack(pady=(0, 20))
    
    # 구분선
    separator1 = tk.Frame(main_frame, height=2, bg="gray")
    separator1.pack(fill=tk.X, pady=(0, 20))
    
    # 사건 정보
    case_frame = tk.Frame(main_frame)
    case_frame.pack(fill=tk.X, pady=(0, 10))
    
    tk.Label(case_frame, text="사건 번호:", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
    tk.Label(case_frame, text=case_number, font=("Arial", 12), fg="red").pack(side=tk.LEFT, padx=(10, 0))
    
    # 캡차 이미지 표시 (드래그 가능한 프레임)
    image_frame = tk.Frame(main_frame, relief=tk.SUNKEN, bd=2, bg="white")
    image_frame.pack(fill=tk.X, pady=(0, 10))
    
    # 캡차 이미지 헤더와 새로고침 버튼
    image_header = tk.Frame(image_frame, bg="white")
    image_header.pack(fill=tk.X, padx=5, pady=5)
    
    tk.Label(image_header, text="캡차 이미지:", font=("Arial", 12, "bold"), bg="white").pack(side=tk.LEFT)
    
    # 새로고침 버튼
    def refresh_image():
        nonlocal img_label, photo, screenshot_path
        try:
            # 최신 이미지 다시 찾기 (사건번호+날짜+시간 형식)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 두 개의 가능한 디렉토리 검색
            screenshot_dirs = [
                os.path.join(current_dir, "cypress", "screenshots"),  # 메인 스크린샷 디렉토리
                os.path.join(current_dir, "cypress", "screenshots", "realtime-captcha-automation.cy.js")  # 하위 디렉토리
            ]
            
            print(f"새로고침: 스크린샷 디렉토리들 검색")
            for dir_path in screenshot_dirs:
                print(f"  - {dir_path} (존재: {os.path.exists(dir_path)})")
            
            for screenshot_dir in screenshot_dirs:
                if os.path.exists(screenshot_dir):
                    import glob
                    # 사건번호로 시작하는 파일들 찾기
                    pattern = os.path.join(screenshot_dir, f"{case_number}-*.png")
                    files = glob.glob(pattern)
                    print(f"새로고침: 디렉토리 {screenshot_dir}에서 찾은 파일들 - {files}")
                    
                    if files:
                        # 파일명에서 날짜+시간 추출하여 최신 파일 찾기
                        def extract_datetime(filename):
                            try:
                                basename = os.path.basename(filename)
                                parts = basename.split('-')
                                if len(parts) >= 3:
                                    date_time = parts[1] + parts[2].split('.')[0]  # YYYYMMDDHHMMSS
                                    return int(date_time)
                                return 0
                            except:
                                return 0
                        
                        latest_file = max(files, key=extract_datetime)
                        screenshot_path = latest_file
                        print(f"새로고침: 최신 이미지 로드 - {latest_file}")
                        break  # 찾았으면 루프 종료
            
            # 이미지 다시 로드
            if screenshot_path and os.path.exists(screenshot_path):
                img = Image.open(screenshot_path)
                img = img.resize((240, 80), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                img_label.configure(image=photo)
                img_label.image = photo  # 참조 유지
                status_label.configure(text=f"파일: {screenshot_path} (새로고침됨)", fg="green")
            else:
                status_label.configure(text="이미지를 찾을 수 없습니다", fg="red")
        except Exception as e:
            status_label.configure(text=f"이미지 로드 오류: {str(e)}", fg="red")
    
    refresh_btn = tk.Button(image_header, text="새로고침", command=refresh_image, 
                           font=("Arial", 10), bg="lightblue", relief=tk.RAISED)
    refresh_btn.pack(side=tk.RIGHT, padx=(10, 0))
    
    # 실제 캡차 이미지 표시
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
        for dir_path in screenshot_dirs:
            print(f"  - {dir_path} (존재: {os.path.exists(dir_path)})")
        
        for screenshot_dir in screenshot_dirs:
            if os.path.exists(screenshot_dir):
                import glob
                # 사건번호로 시작하는 파일들 찾기
                pattern = os.path.join(screenshot_dir, f"{case_number}-*.png")
                files = glob.glob(pattern)
                print(f"디렉토리 {screenshot_dir}에서 찾은 파일들: {files}")
                
                if files:
                    # 파일명에서 날짜+시간 추출하여 최신 파일 찾기
                    def extract_datetime(filename):
                        try:
                            # 파일명에서 날짜+시간 부분 추출 (예: 2024가합51101-20241201-143022.png)
                            basename = os.path.basename(filename)
                            parts = basename.split('-')
                            if len(parts) >= 3:
                                date_time = parts[1] + parts[2].split('.')[0]  # YYYYMMDDHHMMSS
                                return int(date_time)
                            return 0
                        except:
                            return 0
                    
                    latest_file = max(files, key=extract_datetime)
                    screenshot_path = latest_file
                    print(f"최신 캡차 이미지 발견: {latest_file}")
                    break  # 찾았으면 루프 종료
        
        # 2. 기본 경로들도 확인
        if not screenshot_path:
            possible_paths = [
                os.path.join(current_dir, "cypress", "screenshots", "realtime-captcha-automation.cy.js", f"{captcha_image_path}.png"),
                os.path.join(current_dir, "cypress", "screenshots", f"{captcha_image_path}.png"),
                os.path.join(current_dir, f"{captcha_image_path}.png"),
                f"cypress/screenshots/realtime-captcha-automation.cy.js/{captcha_image_path}.png",
                f"cypress/screenshots/{captcha_image_path}.png",
                f"{captcha_image_path}.png"
            ]
            
            print(f"대체 경로들 검색:")
            for path in possible_paths:
                print(f"  - {path} (존재: {os.path.exists(path)})")
                if os.path.exists(path):
                    screenshot_path = path
                    break
        
        if screenshot_path and os.path.exists(screenshot_path):
            # 이미지 로드 및 리사이즈
            img = Image.open(screenshot_path)
            img = img.resize((240, 80), Image.Resampling.LANCZOS)  # 2배 확대
            photo = ImageTk.PhotoImage(img)
            
            # 이미지 라벨 (드래그 가능한 영역)
            img_container = tk.Frame(image_frame, bg="white")
            img_container.pack(fill=tk.X, padx=5, pady=5)
            
            img_label = tk.Label(img_container, image=photo, relief=tk.SUNKEN, bd=2, bg="white")
            img_label.image = photo  # 참조 유지
            img_label.pack()
            
            # 드래그 이벤트 바인딩
            def start_drag(event):
                img_label.drag_data = {"x": event.x, "y": event.y}
            
            def on_drag(event):
                if hasattr(img_label, 'drag_data'):
                    dx = event.x - img_label.drag_data["x"]
                    dy = event.y - img_label.drag_data["y"]
                    img_label.place(x=img_label.winfo_x() + dx, y=img_label.winfo_y() + dy)
                    img_label.drag_data = {"x": event.x, "y": event.y}
            
            def stop_drag(event):
                if hasattr(img_label, 'drag_data'):
                    del img_label.drag_data
            
            img_label.bind("<Button-1>", start_drag)
            img_label.bind("<B1-Motion>", on_drag)
            img_label.bind("<ButtonRelease-1>", stop_drag)
            
            status_label = tk.Label(image_frame, text=f"파일: {os.path.basename(screenshot_path)}", 
                    font=("Arial", 10), fg="green", bg="white")
            status_label.pack(anchor=tk.W, padx=5)
        else:
            img_container = tk.Frame(image_frame, bg="white")
            img_container.pack(fill=tk.X, padx=5, pady=5)
            
            img_label = tk.Label(img_container, text="이미지를 찾을 수 없습니다", 
                    font=("Arial", 10), fg="red", bg="white")
            img_label.pack(pady=(5, 0))
            status_label = tk.Label(img_container, text=f"가능한 경로들:", 
                    font=("Arial", 9), fg="gray", bg="white")
            status_label.pack(anchor=tk.W)
            for path in possible_paths:
                tk.Label(img_container, text=f"  - {path}", font=("Arial", 8), fg="gray", bg="white").pack(anchor=tk.W)
                
    except Exception as e:
        tk.Label(image_frame, text=f"이미지 로드 오류: {str(e)}", 
                font=("Arial", 10), fg="red").pack(anchor=tk.W)
    
    # 구분선
    separator2 = tk.Frame(main_frame, height=2, bg="gray")
    separator2.pack(fill=tk.X, pady=(0, 20))
    
    # 사용자 안내
    instruction_label = tk.Label(main_frame, 
                                text="👤 사용자 안내:\n" +
                                     "1. 위의 캡차 이미지에서 6글자를 확인하세요\n" +
                                     "2. 6글자 캡차를 입력하세요 (예: ABC123)\n" +
                                     "3. 입력이 완료되면 확인 버튼을 눌러주세요",
                                font=("Arial", 11), justify=tk.LEFT)
    instruction_label.pack(pady=(0, 20))
    
    # 입력 프레임
    input_frame = tk.Frame(main_frame)
    input_frame.pack(fill=tk.X, pady=(0, 20))
    
    tk.Label(input_frame, text="6글자 캡차 입력:", font=("Arial", 12, "bold")).pack(anchor=tk.W)
    
    # 입력 필드
    captcha_var = tk.StringVar()
    captcha_entry = tk.Entry(input_frame, textvariable=captcha_var, 
                            font=("Arial", 14), width=10, justify=tk.CENTER)
    captcha_entry.pack(pady=(5, 0))
    captcha_entry.focus()
    
    # 결과 변수
    result = {"captcha": ""}
    
    def on_submit():
        captcha_text = captcha_var.get().strip()
        if len(captcha_text) == 6:
            result["captcha"] = captcha_text
            root.destroy()
        else:
            messagebox.showerror("오류", "6글자 캡차를 정확히 입력해주세요!")
            captcha_entry.delete(0, tk.END)
            captcha_entry.focus()
    
    def on_cancel():
        result["captcha"] = ""
        root.destroy()
    
    # 버튼 프레임
    button_frame = tk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=(0, 10))
    
    # 확인 버튼
    submit_btn = tk.Button(button_frame, text="✅ 확인", command=on_submit,
                          font=("Arial", 12), bg="lightgreen", width=10)
    submit_btn.pack(side=tk.LEFT, padx=(0, 10))
    
    # 취소 버튼
    cancel_btn = tk.Button(button_frame, text="❌ 취소", command=on_cancel,
                          font=("Arial", 12), bg="lightcoral", width=10)
    cancel_btn.pack(side=tk.LEFT)
    
    # Enter 키 바인딩
    root.bind('<Return>', lambda e: on_submit())
    
    # 윈도우 실행
    root.mainloop()
    
    return result["captcha"]

if __name__ == "__main__":
    # 명령행 인수로 사건번호 받기 (필수)
    if len(sys.argv) < 2:
        print("ERROR: 사건번호가 필요합니다. 사용법: python captcha_input.py <사건번호>")
        sys.exit(1)
    
    case_number = sys.argv[1]
    print(f"DEBUG: 사건번호 = '{case_number}'")
    
    captcha_input = get_captcha_input(case_number, None)
    
    # 입력값 검증 및 출력
    print(f"DEBUG: captcha_input = '{captcha_input}'")
    print(f"DEBUG: type = {type(captcha_input)}")
    print(f"DEBUG: length = {len(captcha_input) if captcha_input else 'None'}")
    
    if captcha_input and len(captcha_input) == 6:
        print(f"SUCCESS: {captcha_input}")
    else:
        print("ERROR: Invalid captcha input")
        sys.exit(1)
