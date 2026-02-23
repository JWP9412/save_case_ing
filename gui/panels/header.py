# -*- coding: utf-8 -*-
"""
헤더 패널 (Header Panel)
=======================
상단 배너 영역을 담당합니다.
- config.HEADER_IMAGE_PATH에 이미지가 있으면 중앙에 배너 이미지를 표시하고,
- 없거나 로드 실패 시 앱 제목·부제목 텍스트로 대체합니다.
Why: 사용자에게 앱 식별감을 주고, 배너로 브랜딩을 할 수 있게 합니다.
"""
import os
import tkinter as tk
import customtkinter as ctk
import config


class HeaderPanel:
    """
    헤더(배너) 영역만 생성하는 클래스.
    메인 윈도우에서 호출하여 상단 프레임을 받습니다.
    """

    @staticmethod
    def create(parent, app):
        """
        헤더 프레임을 생성하여 반환합니다.

        Parameters
        ----------
        parent : tk.Widget
            부모 위젯 (메인 콘텐츠 영역 등).
        app : object
            메인 윈도우 객체. log_message(메시지) 호출 가능해야 함.

        Returns
        -------
        ctk.CTkFrame
            배너 또는 텍스트 헤더가 들어 있는 프레임. pack()으로 배치된 상태.
        """
        # 헤더 배경색: config에서 읽고, 없으면 기본 진한 파랑
        header_bg = getattr(config, "HEADER_BG_COLOR", "#001A33")
        header_frame = ctk.CTkFrame(
            parent, fg_color=(header_bg, header_bg), height=120
        )
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        # pack_propagate(False): 자식 크기에 맞춰 프레임이 줄어들지 않도록 높이 120 유지
        header_frame.pack_propagate(False)

        # 배너 이미지 경로: 상대 경로면 프로젝트 루트 기준으로 절대 경로로 변환
        banner_path = getattr(config, "HEADER_IMAGE_PATH", "./assets/title_banner.png")
        if not os.path.isabs(banner_path):
            # __file__은 이 파일(header.py) 경로이므로, 프로젝트 루트는 상위 두 단계
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)
            )))
            banner_path = os.path.normpath(os.path.join(base_dir, banner_path))

        if os.path.isfile(banner_path):
            try:
                if hasattr(app, "log_message"):
                    app.log_message(f"배너 경로: {banner_path}")
                from PIL import Image
                with Image.open(banner_path) as im:
                    bw, bh = im.size
                if bw <= 0 or bh <= 0:
                    if hasattr(app, "log_message"):
                        app.log_message("배너 이미지 로드 실패: 이미지 크기가 유효하지 않음")
                else:
                    # 배너 프레임 높이(120px)에 맞춰 세로를 채우고, 가로는 비율 유지·최대 900px
                    banner_h = 120
                    max_banner_w = 900
                    scale = min(banner_h / bh, max_banner_w / bw)
                    w, h = int(bw * scale), int(bh * scale)
                    pil_img = Image.open(banner_path)
                    ctk_image = ctk.CTkImage(
                        light_image=pil_img,
                        dark_image=pil_img,
                        size=(w, h),
                    )
                    banner_label = ctk.CTkLabel(
                        header_frame,
                        text="",
                        image=ctk_image,
                    )
                    banner_label.pack(anchor=tk.CENTER, expand=False)
                    return header_frame
            except Exception as e:
                if hasattr(app, "log_message"):
                    app.log_message(f"배너 이미지 로드 실패: {banner_path} — {e}")
                else:
                    print(f"배너 이미지 로드 실패: {banner_path} — {e}")

        # 이미지 없거나 실패 시: 텍스트 헤더 표시
        title_label = ctk.CTkLabel(
            header_frame,
            text=f"⚖️ {config.APP_TITLE}",
            font=ctk.CTkFont(family="맑은 고딕", size=26, weight="bold"),
            text_color="#ECF0F1",
        )
        title_label.pack(pady=(20, 5))
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text=f"{config.APP_SUBTITLE} v{config.APP_VERSION}",
            font=ctk.CTkFont(family="맑은 고딕", size=13),
            text_color="#BDC3C7",
        )
        subtitle_label.pack(pady=(0, 15))
        return header_frame
