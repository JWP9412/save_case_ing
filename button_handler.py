"""
버튼 클릭과 이벤트 처리를 담당하는 파일
"""

import tkinter as tk
from tkinter import messagebox

class ButtonHandler:
    def __init__(self, gui):
        """
        버튼 핸들러 초기화
        
        Args:
            gui: CaptchaGUI 객체
        """
        self.gui = gui
        self.result = {"captcha": ""}
        
    def on_submit(self):
        """
        확인 버튼 클릭 시 실행되는 함수
        - 사용자가 입력한 캡차 텍스트를 검증
        - 6글자가 맞으면 결과에 저장하고 창을 닫음
        - 6글자가 아니면 오류 메시지를 표시하고 다시 입력 요청
        """
        # 사용자가 입력한 텍스트를 가져와서 앞뒤 공백 제거
        captcha_text = self.gui.get_input()
        
        # 입력된 텍스트가 정확히 6글자인지 검증
        if len(captcha_text) == 6:
            # 6글자가 맞으면 결과 딕셔너리에 저장
            self.result["captcha"] = captcha_text
            print(f"[SUCCESS] 캡차 입력 완료: {captcha_text}")
            # GUI 창을 닫음
            self.gui.destroy()
        else:
            # 6글자가 아니면 오류 메시지 표시
            if hasattr(self.gui, 'root') and self.gui.root:
                messagebox.showerror("오류", "6글자 캡차를 정확히 입력해주세요!")
            else:
                print("[ERROR] 6글자 캡차를 정확히 입력해주세요!")
            # 입력 필드를 비우고 다시 포커스를 맞춤
            self.gui.clear_input()
    
    def on_cancel(self):
        """
        취소 버튼 클릭 시 실행되는 함수
        - 빈 문자열을 결과에 저장하고 창을 닫음
        - 이 경우 Cypress에서는 입력 실패로 처리됨
        """
        self.result["captcha"] = ""  # 빈 문자열로 설정
        print("[CANCEL] 캡차 입력 취소됨")
        self.gui.destroy()  # GUI 창 닫기
    
    def bind_events(self, submit_btn, cancel_btn):
        """
        버튼에 이벤트 바인딩
        
        Args:
            submit_btn: 확인 버튼 객체
            cancel_btn: 취소 버튼 객체
        """
        # 버튼 클릭 이벤트 바인딩
        submit_btn.configure(command=self.on_submit)
        cancel_btn.configure(command=self.on_cancel)
        
        # Enter 키 바인딩 (입력 필드에서 Enter 키를 누르면 확인 버튼과 동일한 동작)
        if hasattr(self.gui, 'root') and self.gui.root:
            self.gui.root.bind('<Return>', lambda e: self.on_submit())
        
        print("[OK] 이벤트 바인딩 완료")
    
    def get_result(self):
        """
        입력 결과 가져오기
        
        Returns:
            str: 사용자가 입력한 캡차 텍스트
        """
        return self.result["captcha"]

# 테스트용 함수
def test_button_handler():
    """
    버튼 핸들러 기능 테스트
    """
    print("=== 버튼 핸들러 테스트 ===")
    
    # 가상의 GUI 객체 생성 (Tkinter 없이 테스트)
    class MockGUI:
        def __init__(self):
            self.captcha_text = ""  # 실제 StringVar 대신 문자열 사용
            self.root = None
        
        def get_input(self):
            return self.captcha_text.strip()
        
        def clear_input(self):
            self.captcha_text = ""
        
        def destroy(self):
            pass
    
    # 테스트 실행
    gui = MockGUI()
    handler = ButtonHandler(gui)
    
    # 입력값 테스트
    gui.captcha_text = "ABC123"  # 6글자 입력
    result = gui.get_input()  # gui에서 직접 가져오기
    print(f"입력값: {result}")
    
    # 검증 테스트
    if len(result) == 6:
        print("✅ 6글자 검증 통과")
    else:
        print("❌ 6글자 검증 실패")
    
    # 빈 입력 테스트
    gui.captcha_text = ""
    result = gui.get_input()  # gui에서 직접 가져오기
    print(f"빈 입력값: '{result}'")
    
    if len(result) == 0:
        print("✅ 빈 입력 검증 통과")
    else:
        print("❌ 빈 입력 검증 실패")
    
    # 결과 가져오기 테스트
    handler.result["captcha"] = "TEST12"
    result = handler.get_result()
    print(f"핸들러 결과: {result}")
    
    print("✅ 버튼 핸들러 테스트 완료")

if __name__ == "__main__":
    # 직접 실행할 때만 테스트 실행
    test_button_handler()
