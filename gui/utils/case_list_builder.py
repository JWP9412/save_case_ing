# -*- coding: utf-8 -*-
"""
사건 목록 UI 빌더 (배치 렌더링)
===============================

구글 시트 데이터를 받아 사건 목록(체크박스, 라벨, 입력창)을 비동기 배치로 그리는 로직.
app_controller에서 update_case_list_ui, _on_ui_update_complete, reset_internal_data 호출 시 이 모듈에 위임합니다.
"""
from config import COL_WIDTHS, COL_NAMES, DEFAULT_COL_ORDER


def reset_internal_data(app):
    """
    새로고침 시 이전 작업의 잔재(이미지, 입력값 등)를 비우는 메서드.
    status_text(로그)는 건드리지 않아 로그는 유지된다.
    """
    for key in (
        "case_checkboxes",
        "case_inputs",
        "case_entries",
        "case_status",
        "case_images",
        "case_image_photos",
        "case_frames",
        "case_update_labels",
        "case_update_date_labels",
        "case_record_labels",
        "case_start_times",
        "case_info_text_widgets",
        "case_cell_frames",
        "case_separators",
        "browser_ws_urls",
        "browser_processes",
    ):
        setattr(app, key, {})


def update_case_list_ui(app):
    """사건 목록 UI 업데이트 (비동기 배치 처리로 UI 프리징 방지)"""
    if getattr(app, "_ui_updating", False):
        app.log_message("⚠️ UI 업데이트가 이미 진행 중입니다. 대기합니다.")
        return

    try:
        app._ui_updating = True
        n = len(app.case_list) if app.case_list else 0
        if hasattr(app, "case_list_title_label") and app.case_list_title_label.winfo_exists():
            app.case_list_title_label.configure(text=f"📋 사건 목록({n}) (로딩 중...)")
        app.log_message(f"🔄 [DEBUG] UI 업데이트 시작: {n}건 (배치 처리)")

        for widget in app.case_list_frame.winfo_children():
            widget.destroy()

        app.case_checkboxes = {}
        app.case_inputs = {}
        app.case_entries = {}
        app.case_status = {}
        app.case_images = {}
        app.case_image_photos = {}
        app.case_frames = {}
        app.case_cell_frames = {}
        app.case_separators = {}
        app.case_update_labels = {}
        app.case_update_date_labels = {}
        app.case_record_labels = {}
        app.case_start_times = {}
        app.case_info_text_widgets = {}

        loaded_widths = app.load_column_widths()
        if loaded_widths is not None and len(loaded_widths) == len(COL_WIDTHS):
            app.col_widths = list(loaded_widths)
        elif not hasattr(app, "col_widths") or len(app.col_widths) != len(COL_WIDTHS):
            app.col_widths = list(COL_WIDTHS)

        order_loaded = app.load_column_order()
        if order_loaded is not None and len(order_loaded) == len(COL_NAMES):
            app.col_order = list(order_loaded)
        elif not hasattr(app, "col_order") or len(app.col_order) != len(COL_NAMES):
            app.col_order = list(DEFAULT_COL_ORDER)

        effective_total, extra_last = app._get_effective_widths()
        app._extra_width_last_col = extra_last

        if hasattr(app, "header_container") and app.header_container.winfo_exists():
            app.header_container.configure(width=effective_total)
        if hasattr(app, "header_canvas") and app.header_canvas.winfo_exists():
            app.header_canvas.configure(scrollregion=(0, 0, effective_total, 40))
        if hasattr(app, "case_list_frame") and app.case_list_frame.winfo_exists():
            app.case_list_frame.configure(width=effective_total)

        app.create_list_header()

        status_history = app.log_history_manager.load_status_history()
        batch_size = 5

        def process_batch(start_idx):
            if not app.root.winfo_exists():
                app._ui_updating = False
                return

            end_idx = min(start_idx + batch_size, len(app.case_list))
            for i in range(start_idx, end_idx):
                case = app.case_list[i]
                case_number = case.get("사건번호", "")
                initial_status = status_history.get(case_number)

                row, comps, cell_frames = app.create_case_row(
                    app.case_list_frame,
                    case,
                    i,
                    effective_total,
                    initial_status=initial_status,
                )

                app.case_cell_frames[i] = cell_frames
                app.case_info_text_widgets[i] = [
                    comps["label_info_1"],
                    comps["label_info_2"],
                    comps["label_info_4"],
                ]
                app.case_checkboxes[i] = comps["checkbox_var"]
                app.case_images[i] = comps["image_label"]
                app.case_inputs[i] = comps["captcha_var"]
                app.case_entries[i] = comps["captcha_entry"]
                app.case_status[i] = comps["status_label"]
                app.case_update_date_labels[i] = comps["update_date_label"]
                app.case_update_labels[i] = comps["update_d_label"]
                app.case_record_labels[i] = comps["record_label"]

            app.case_list_frame.update_idletasks()
            app.case_canvas.configure(scrollregion=app.case_canvas.bbox("all"))

            if end_idx < len(app.case_list):
                app.root.after(1, lambda: process_batch(end_idx))
            else:
                _on_ui_update_complete(app)

        if app.case_list:
            process_batch(0)
        else:
            _on_ui_update_complete(app)

    except Exception as e:
        app.log_message(f"❌ UI 업데이트 중 오류 발생: {e}")
        app._ui_updating = False


def _on_ui_update_complete(app):
    """UI 업데이트 완료 후 마무리 작업"""
    try:
        n = len(app.case_list) if app.case_list else 0
        if hasattr(app, "case_list_title_label") and app.case_list_title_label.winfo_exists():
            app.case_list_title_label.configure(text=f"📋 사건 목록({n})")

        if app.case_checkboxes:
            selected_count = sum(1 for v in app.case_checkboxes.values() if v.get())
            app.header_select_all_var.set(selected_count == len(app.case_checkboxes))

        app.log_message(f"✅ UI 업데이트 완료: {n}건")

        app.case_canvas.yview_moveto(0)
        app.case_canvas.xview_moveto(0)
        if hasattr(app, "header_canvas") and app.header_canvas.winfo_exists():
            app.header_canvas.xview_moveto(0)

        app._bind_mousewheel_to_case_list()

        app.log_message("✅ UI 구성 완료 (Modern Style)")

    except Exception as e:
        app.log_message(f"❌ [ERROR] UI 업데이트 오류: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        app._ui_updating = False
