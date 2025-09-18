"""
실시간 캡차 처리 시스템 - 메인 파일 (리팩토링된 버전)
===============================================

역할: 다른 모듈들을 조합하여 캡차 입력 GUI를 실행
기능: 
- 이미지 찾기 (image_finder.py)
- GUI 생성 (gui_maker.py)
- 버튼 처리 (button_handler.py)
- 모든 것을 조합하여 실행

사용법: python captcha_input_new.py <사건번호>
"""

import sys
from image_finder import find_latest_image, find_image_by_pattern
from gui_maker import CaptchaGUI
from button_handler import ButtonHandler

def get_captcha_input(case_number, captcha_image_path=None):
    """
    캡차 입력을 위한 GUI 창을 생성하고 실행합니다.
    
    Args:
        case_number (str): 처리할 사건 번호 (예: "2024가합51101")
        captcha_image_path (str): 캡차 이미지 파일 경로 (선택사항)
    
    Returns:
        str: 사용자가 입력한 6글자 캡차 텍스트, 실패시 빈 문자열
    """
    print(f"=== 캡차 입력 시작 ===")
    print(f"사건번호: {case_number}")
    
    # ========================================
    # 1. 이미지 찾기
    # ========================================
    print("1. 이미지 파일 검색 중...")
    image_path = find_latest_image(case_number)
    
    # 패턴 매칭으로 찾지 못한 경우 대체 경로 확인
    if not image_path and captcha_image_path:
        print("   패턴 매칭 실패, 대체 경로 확인 중...")
        image_path = find_image_by_pattern(case_number, captcha_image_path)
    
    if not image_path:
        print("ERROR: 이미지 파일을 찾을 수 없습니다!")
        return ""
    
    print(f"INFO: 이미지 파일 발견: {image_path}")
    
    # ========================================
    # 2. GUI 생성
    # ========================================
    print("2. GUI 생성 중...")
    gui = CaptchaGUI(case_number)
    
    # 화면 구성 요소들 생성
    main_frame = gui.create_window()
    gui.create_title(main_frame)
    gui.create_case_info(main_frame)
    image_frame, image_header = gui.create_image_area(main_frame)
    gui.create_input_area(main_frame)
    submit_btn, cancel_btn = gui.create_buttons(main_frame)
    
    # 이미지 표시
    if not gui.show_image(image_path, image_frame):
        gui.show_error("이미지를 로드할 수 없습니다")
    
    print("INFO: GUI 생성 완료")
    
    # ========================================
    # 3. 이벤트 처리 설정
    # ========================================
    print("3. 이벤트 처리 설정 중...")
    handler = ButtonHandler(gui)
    handler.bind_events(submit_btn, cancel_btn)
    print("INFO: 이벤트 처리 설정 완료")
    
    # ========================================
    # 4. GUI 실행 및 결과 반환
    # ========================================
    print("4. GUI 실행 중... (사용자 입력 대기)")
    gui.run()  # 사용자 입력을 기다림
    
    # 사용자 입력 결과 가져오기
    result = handler.get_result()
    print(f"5. 입력 완료: {result if result else '취소됨'}")
    
    return result

def main():
    """
    메인 실행 함수
    """
    # 명령행 인수 검증
    if len(sys.argv) < 2:
        print("ERROR: 사건번호가 필요합니다. 사용법: python captcha_input_new.py <사건번호>")
        sys.exit(1)
    
    # 사건번호 추출
    case_number = sys.argv[1]
    print(f"DEBUG: 사건번호 = '{case_number}'")
    
    # 캡차 입력 GUI 실행
    captcha_input = get_captcha_input(case_number, None)
    
    # 결과 검증 및 출력
    print(f"DEBUG: captcha_input = '{captcha_input}'")
    print(f"DEBUG: type = {type(captcha_input)}")
    print(f"DEBUG: length = {len(captcha_input) if captcha_input else 'None'}")
    
    if captcha_input and len(captcha_input) == 6:
        print(f"SUCCESS: {captcha_input}")
        print(f"DEBUG: 캡차 입력 성공 - '{captcha_input}'")
    else:
        print("ERROR: Invalid captcha input")
        print(f"DEBUG: 잘못된 캡차 입력 - '{captcha_input}' (길이: {len(captcha_input) if captcha_input else 0})")
        sys.exit(1)

# 테스트용 함수
def test_integration():
    """
    통합 테스트 함수
    """
    print("=== 통합 테스트 ===")
    
    # 테스트 사건번호
    test_case = "2024가합51101"
    
    # 각 모듈 개별 테스트
    print("1. 이미지 찾기 테스트...")
    from image_finder import test_image_finder
    test_image_finder()
    
    print("\n2. GUI 생성 테스트...")
    from gui_maker import test_gui_maker
    test_gui_maker()
    
    print("\n3. 버튼 핸들러 테스트...")
    from button_handler import test_button_handler
    test_button_handler()
    
    print("\nINFO: 모든 모듈 테스트 완료!")

if __name__ == "__main__":
    # 직접 실행할 때만 메인 함수 실행
    main()
