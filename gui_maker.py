"""
GUI 화면을 만드는 기능만 담당하는 파일
"""

import tkinter as tk
from PIL import Image, ImageTk

class CaptchaGUI:
    def __init__(self, case_number):
        """
        캡차 입력 GUI 초기화
        
        Args:
            case_number (str): 사건번호
        """
        self.case_number = case_number
        self.root = None
        self.captcha_var = None
        self.captcha_entry = None
        self.img_label = None
        self.status_label = None
        self.main_frame = None
        
    def create_window(self):
        """
        메인 윈도우 생성
        """
        # 메인 윈도우 생성
        self.root = tk.Tk()
        self.root.title("실시간 캡차 처리")
        self.root.geometry("600x600")
        self.root.resizable(True, True)
        
        # 중앙에 배치
        self.root.eval('tk::PlaceWindow . center')
        
        # 메인 프레임
        self.main_frame = tk.Frame(self.root, padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        return self.main_frame
    
    def create_title(self, parent):
        """
        제목과 구분선 생성
        """
        # 제목
        title_label = tk.Label(parent, text="실시간 캡차 처리 표", 
                              font=("Arial", 16, "bold"), fg="blue")
        title_label.pack(pady=(0, 20))
        
        # 구분선
        separator1 = tk.Frame(parent, height=2, bg="gray")
        separator1.pack(fill=tk.X, pady=(0, 20))
        
        return title_label, separator1
    
    def create_case_info(self, parent):
        """
        사건 정보 표시 영역 생성
        """
        case_frame = tk.Frame(parent)
        case_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(case_frame, text="사건 번호:", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        tk.Label(case_frame, text=self.case_number, font=("Arial", 12), fg="red").pack(side=tk.LEFT, padx=(10, 0))
        
        return case_frame
    
    def create_image_area(self, parent):
        """
        캡차 이미지 표시 영역 생성
        """
        # 이미지 프레임
        image_frame = tk.Frame(parent, relief=tk.SUNKEN, bd=2, bg="white")
        image_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 이미지 헤더
        image_header = tk.Frame(image_frame, bg="white")
        image_header.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(image_header, text="캡차 이미지:", font=("Arial", 12, "bold"), bg="white").pack(side=tk.LEFT)
        
        return image_frame, image_header
    
    def create_input_area(self, parent):
        """
        입력 영역 생성
        """
        # 구분선
        separator2 = tk.Frame(parent, height=2, bg="gray")
        separator2.pack(fill=tk.X, pady=(0, 20))
        
        # 사용자 안내
        instruction_label = tk.Label(parent, 
                                    text="사용자 안내:\n" +
                                         "1. 위의 캡차 이미지에서 6글자를 확인하세요\n" +
                                         "2. 6글자 캡차를 입력하세요 (예: ABC123)\n" +
                                         "3. 입력이 완료되면 확인 버튼을 눌러주세요",
                                    font=("Arial", 11), justify=tk.LEFT)
        instruction_label.pack(pady=(0, 20))
        
        # 입력 프레임
        input_frame = tk.Frame(parent)
        input_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(input_frame, text="6글자 캡차 입력:", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        
        # 입력 필드
        self.captcha_var = tk.StringVar()
        self.captcha_entry = tk.Entry(input_frame, textvariable=self.captcha_var, 
                                    font=("Arial", 14), width=10, justify=tk.CENTER)
        self.captcha_entry.pack(pady=(5, 0))
        self.captcha_entry.focus()
        
        return input_frame
    
    def create_buttons(self, parent):
        """
        버튼 영역 생성
        """
        button_frame = tk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 확인 버튼
        submit_btn = tk.Button(button_frame, text="확인",
                              font=("Arial", 12), bg="lightgreen", width=10)
        submit_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 취소 버튼
        cancel_btn = tk.Button(button_frame, text="취소",
                              font=("Arial", 12), bg="lightcoral", width=10)
        cancel_btn.pack(side=tk.LEFT)
        
        return submit_btn, cancel_btn
    
    def show_image(self, image_path):
        """
        이미지를 GUI에 표시
        
        Args:
            image_path (str): 이미지 파일 경로
            
        Returns:
            bool: 성공 여부
        """
        if image_path:
            try:
                # 이미지 로드 및 리사이즈
                img = Image.open(image_path)
                img = img.resize((240, 80), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                # 이미지 라벨 생성 (이미지 프레임 내부에 배치)
                self.img_label = tk.Label(self.main_frame, image=photo, relief=tk.SUNKEN, bd=2, bg="white")
                self.img_label.image = photo  # 참조 유지
                self.img_label.pack(pady=10)
                
                return True
            except Exception as e:
                print(f"이미지 로드 오류: {e}")
                return False
        return False
    
    def show_error(self, message):
        """
        오류 메시지 표시
        
        Args:
            message (str): 오류 메시지
        """
        error_label = tk.Label(text=message, font=("Arial", 10), fg="red", bg="white")
        error_label.pack()
        
    def get_input(self):
        """
        사용자 입력값 가져오기
        
        Returns:
            str: 입력된 텍스트
        """
        return self.captcha_var.get().strip()
    
    def clear_input(self):
        """
        입력 필드 비우기
        """
        self.captcha_entry.delete(0, tk.END)
        self.captcha_entry.focus()
    
    def run(self):
        """
        GUI 실행
        """
        self.root.mainloop()
    
    def destroy(self):
        """
        GUI 종료
        """
        self.root.destroy()

# 테스트용 함수
def test_gui_maker():
    """
    GUI 생성 기능 테스트
    """
    print("=== GUI 생성 테스트 ===")
    
    case_number = "2024가합51101"
    gui = CaptchaGUI(case_number)
    
    # 화면 생성
    main_frame = gui.create_window()
    gui.create_title(main_frame)
    gui.create_case_info(main_frame)
    gui.create_image_area(main_frame)
    gui.create_input_area(main_frame)
    gui.create_buttons(main_frame)
    
    print("✅ GUI 생성 완료!")
    print("실제로는 gui.run()을 호출하여 GUI를 표시합니다.")

if __name__ == "__main__":
    # 직접 실행할 때만 테스트 실행
    test_gui_maker()
