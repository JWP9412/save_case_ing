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
    
    # 캡차 이미지 표시
    image_frame = tk.Frame(main_frame)
    image_frame.pack(fill=tk.X, pady=(0, 10))
    
    tk.Label(image_frame, text="캡차 이미지:", font=("Arial", 12, "bold")).pack(anchor=tk.W)
    
    # 실제 캡차 이미지 표시
    try:
        # 스크린샷 경로 찾기
        screenshot_path = None
        possible_paths = [
            f"cypress/screenshots/realtime-captcha-automation.cy.js/{captcha_image_path}",
            f"cypress/screenshots/{captcha_image_path}",
            captcha_image_path
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                screenshot_path = path
                break
        
        if screenshot_path and os.path.exists(screenshot_path):
            # 이미지 로드 및 리사이즈
            img = Image.open(screenshot_path)
            img = img.resize((240, 80), Image.Resampling.LANCZOS)  # 2배 확대
            photo = ImageTk.PhotoImage(img)
            
            # 이미지 라벨
            img_label = tk.Label(image_frame, image=photo, relief=tk.SUNKEN, bd=2)
            img_label.image = photo  # 참조 유지
            img_label.pack(pady=(5, 0))
            
            tk.Label(image_frame, text=f"파일: {screenshot_path}", 
                    font=("Arial", 10), fg="green").pack(anchor=tk.W)
        else:
            tk.Label(image_frame, text=f"이미지를 찾을 수 없습니다: {captcha_image_path}", 
                    font=("Arial", 10), fg="red").pack(anchor=tk.W)
            tk.Label(image_frame, text="가능한 경로들:", font=("Arial", 9), fg="gray").pack(anchor=tk.W)
            for path in possible_paths:
                tk.Label(image_frame, text=f"  - {path}", font=("Arial", 8), fg="gray").pack(anchor=tk.W)
                
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
    # 테스트용
    case_number = "2024가합51101"
    captcha_image_path = "realtime-captcha-image.png"
    
    captcha_input = get_captcha_input(case_number, captcha_image_path)
    # 인코딩 문제 해결을 위해 캡차만 출력
    print(captcha_input)
