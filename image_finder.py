"""
이미지 파일을 찾는 기능만 담당하는 파일
"""

import os
import glob

def find_latest_image(case_number):
    """
    사건번호로 최신 이미지 파일을 찾는 함수
    
    Args:
        case_number (str): 사건번호 (예: "2024가합51101")
    
    Returns:
        str: 찾은 이미지 파일 경로, 없으면 None
    """
    # 현재 스크립트 파일의 디렉토리 경로
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 스크린샷이 저장될 수 있는 디렉토리들
    screenshot_dirs = [
        os.path.join(current_dir, "screenshots"),  # Puppeteer 저장 경로
        os.path.join(current_dir, "cypress", "screenshots"),
        os.path.join(current_dir, "cypress", "screenshots", "realtime-captcha-automation.cy.js")
    ]
    
    print(f"이미지 검색 중... 사건번호: {case_number}")
    
    # 각 디렉토리에서 사건번호로 시작하는 파일 찾기
    for screenshot_dir in screenshot_dirs:
        print(f"  - 디렉토리 확인: {screenshot_dir}")
        
        if os.path.exists(screenshot_dir):
            pattern = os.path.join(screenshot_dir, f"{case_number}-*.png")
            files = glob.glob(pattern)
            print(f"    찾은 파일들: {files}")
            
            if files:
                # 가장 최신 파일 찾기 (파일 수정 시간 기준)
                latest_file = max(files, key=os.path.getmtime)
                print(f"    [OK] 최신 파일: {latest_file}")
                return latest_file
        else:
            print(f"    [ERROR] 디렉토리 없음")
    
    print("[ERROR] 이미지를 찾을 수 없음")
    return None  # 파일을 찾지 못한 경우

def find_image_by_pattern(case_number, captcha_image_path):
    """
    패턴 매칭으로 찾지 못한 경우 대체 경로들 확인
    
    Args:
        case_number (str): 사건번호
        captcha_image_path (str): 이미지 파일명 (확장자 제외)
    
    Returns:
        str: 찾은 이미지 파일 경로, 없으면 None
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 가능한 모든 경로들
    possible_paths = [
        os.path.join(current_dir, "screenshots", f"{captcha_image_path}.png"),  # Puppeteer 저장 경로
        os.path.join(current_dir, "cypress", "screenshots", "realtime-captcha-automation.cy.js", f"{captcha_image_path}.png"),
        os.path.join(current_dir, "cypress", "screenshots", f"{captcha_image_path}.png"),
        os.path.join(current_dir, f"{captcha_image_path}.png"),
        f"screenshots/{captcha_image_path}.png",  # Puppeteer 저장 경로
        f"cypress/screenshots/realtime-captcha-automation.cy.js/{captcha_image_path}.png",
        f"cypress/screenshots/{captcha_image_path}.png",
        f"{captcha_image_path}.png"
    ]
    
    print(f"대체 경로들 검색...")
    for path in possible_paths:
        print(f"  - {path} (존재: {os.path.exists(path)})")
        if os.path.exists(path):
            print(f"    ✅ 파일 발견: {path}")
            return path
    
    print("❌ 대체 경로에서도 파일을 찾을 수 없음")
    return None

# 테스트용 함수
def test_image_finder():
    """
    이미지 찾기 기능 테스트
    """
    print("=== 이미지 찾기 테스트 ===")
    
    # 테스트 사건번호들
    test_cases = ["2024가합51101", "2023가합10019", "2025나10816"]
    
    for case_number in test_cases:
        print(f"\n사건번호: {case_number}")
        image_path = find_latest_image(case_number)
        
        if image_path:
            print(f"✅ 성공: {image_path}")
        else:
            print("❌ 실패: 이미지를 찾을 수 없음")

if __name__ == "__main__":
    # 직접 실행할 때만 테스트 실행
    test_image_finder()