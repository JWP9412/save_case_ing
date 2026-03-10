# -*- coding: utf-8 -*-
"""
캡차(Captcha) UI 상호작용 유틸리티
===================================

캡차 이미지 표시, 입력 검증, 엔터키 처리, 다음 입력칸 포커스 이동, 입력 대기 등 캡차 위젯 전용 조작.
app_controller에서 해당 메서드 호출 시 이 모듈에 위임합니다.
"""
import time
import os


def get_captcha_input(app, case_index):
    """캡차 입력값 가져오기"""
    if case_index in app.case_inputs:
        return app.case_inputs[case_index].get()
    return None


def validate_captcha_entry(app, index):
    """캡차 입력 6자리 숫자만 허용 (CTkEntry용)."""
    if index not in app.case_inputs:
        return
    val = app.case_inputs[index].get()
    cleaned = "".join(c for c in val if c.isdigit())[:6]
    if cleaned != val:
        app.case_inputs[index].set(cleaned)


def on_captcha_enter(app, case_index):
    """캡차 입력 후 엔터키 처리 (다음 입력칸으로만 이동)."""
    captcha_input = get_captcha_input(app, case_index)
    if captcha_input and captcha_input.strip():
        if len(captcha_input) == 6 and captcha_input.isdigit():
            app.log_message(
                f"✅ 캡차 입력 저장: {captcha_input} (사건 인덱스: {case_index}) - 길이: {len(captcha_input)}"
            )
            app.update_case_status(case_index, "입력완료", "blue")
            move_to_next_input(app, case_index)
        else:
            app.log_message(
                f"⚠️ 캡차 입력 형식 오류: {captcha_input} (길이: {len(captcha_input)}, 숫자여부: {captcha_input.isdigit()})"
            )
    else:
        app.log_message(f"⚠️ 캡차 입력이 비어있습니다 (사건 인덱스: {case_index})")


def move_to_next_input(app, current_case_index):
    """다음 입력칸으로 포커스 이동 (선택된 사건 목록에서 현재보다 뒤, 없으면 맨 앞)."""
    try:
        selected_cases = app.get_selected_cases()  # [(case_index, case), ...]
        next_index = None

        for idx, _ in selected_cases:
            if idx > current_case_index and idx in app.case_inputs:
                next_index = idx
                break

        if next_index is None:
            for idx, _ in selected_cases:
                if idx in app.case_inputs:
                    next_index = idx
                    break

        if next_index is not None and next_index in app.case_inputs:
            if next_index in app.case_entries and app.case_entries[next_index].winfo_exists():
                app.case_entries[next_index].focus()
                app.log_message(f"🔄 다음 입력칸으로 이동: 사건 인덱스 {next_index}")
            else:
                app.log_message("⚠️ 입력칸을 찾을 수 없습니다")
        else:
            app.log_message("ℹ️ 다음 입력할 사건이 없습니다")

    except Exception as e:
        app.log_message(f"⚠️ 다음 입력칸 이동 실패: {e}")


def update_captcha_image(app, case_index, image_path):
    """
    캡차 이미지 업데이트 (Thread-Safe).
    스레드에서 호출될 수 있으므로 root.after()를 사용하여 메인 스레드에서 실행합니다.
    """
    if case_index not in app.case_images:
        app.log_message(f"❌ 캡차 이미지 업데이트 실패: 인덱스 {case_index} 없음")
        app.log_message(f"🔍 [DEBUG] 사용 가능한 인덱스: {sorted(app.case_images.keys())}")
        return False

    delay_ms = case_index * 100

    def _update():
        try:
            if case_index not in app.case_images:
                app.log_message(f"❌ [ERROR] _update() 실행 시 인덱스 {case_index} 없음")
                return

            image_label = app.case_images[case_index]

            if image_path == "__CLICK__":
                image_label.config(
                    image="",
                    text="최근검색 (자동클릭)",
                    fg="blue",
                    font=("맑은 고딕", 10, "bold"),
                )
                if case_index in app.case_image_photos:
                    del app.case_image_photos[case_index]
                app.log_message(f"⚡ [DEBUG] 캡차 스킵 모드 표시: 인덱스 {case_index}")
                return

            if image_path and os.path.exists(image_path):
                file_size = os.path.getsize(image_path)
                app.log_message(
                    f"🔍 [DEBUG] 이미지 파일 확인: 인덱스 {case_index}, 경로: {image_path} ({file_size} bytes)"
                )

                from PIL import Image, ImageTk

                img = Image.open(image_path)
                img = img.resize((200, 60), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)

                app.case_image_photos[case_index] = photo
                image_label.config(image=photo, text="", width=200, height=60)
                image_label.image = photo

                app.root.update_idletasks()

                app.log_message(
                    f"🖼️ [DEBUG] 캡차 이미지 업데이트 성공: 인덱스 {case_index}, 사건번호: {app.case_list[case_index].get('사건번호', '') if case_index < len(app.case_list) else 'N/A'}"
                )
                app.log_message(f"✅ GUI에 캡차 이미지 표시 완료: {image_path}")

            else:
                app.log_message(f"⚠️ 캡차 이미지 없음: {image_path}")
                image_label.config(image="", text="이미지없음", fg="red")
                if case_index in app.case_image_photos:
                    del app.case_image_photos[case_index]

        except Exception as e:
            import traceback

            app.log_message(f"❌ 이미지 업데이트 오류: {e}")
            app.log_message(f"❌ [DEBUG] 스택 트레이스: {traceback.format_exc()}")
            if case_index in app.case_images:
                try:
                    app.case_images[case_index].config(image="", text="오류", fg="red")
                except Exception:
                    pass

    app.root.after(delay_ms, _update)
    return True


def wait_for_captcha_input(app, case_index, timeout_seconds=300):
    """캡차 입력 대기 (최대 timeout_seconds초)"""
    if case_index not in app.case_inputs:
        return None

    captcha_var = app.case_inputs[case_index]
    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        if not app.processing:
            return None

        captcha_text = captcha_var.get().strip()
        if len(captcha_text) == 6:
            captcha_var.set("")
            return captcha_text

        time.sleep(0.5)

    app.log_message(f"⏰ 캡차 입력 시간 초과: {timeout_seconds}초")
    return None
