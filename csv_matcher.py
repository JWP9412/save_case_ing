import pandas as pd
from rapidfuzz import process, fuzz
import os
import sys
import io
import tkinter as tk
from tkinter import simpledialog, messagebox, scrolledtext

# --------------------------------------------------------------------------
# [건설 하자 전문가의 조언]
# 이 프로그램은 '현장 조사 리스트'의 항목을 '표준 하자 리스트'에서 찾아
# 자동으로 매칭해주는 도구입니다. (붙여넣기 버전)
# --------------------------------------------------------------------------

def get_text_from_gui(title, prompt):
    """
    사용자에게 텍스트 입력 창을 띄워 데이터를 입력받습니다.
    """
    input_text = ""
    
    def on_submit():
        nonlocal input_text
        input_text = txt_area.get("1.0", tk.END)
        root.quit()
        root.destroy()

    root = tk.Tk()
    root.title(title)
    root.geometry("600x500")

    lbl = tk.Label(root, text=prompt, font=("Pretendard", 12, "bold"), pady=10)
    lbl.pack()

    txt_area = scrolledtext.ScrolledText(root, width=70, height=20)
    txt_area.pack(padx=10, pady=5)

    btn = tk.Button(root, text="입력 완료 (다음 단계로)", command=on_submit, bg="lightblue", height=2)
    btn.pack(pady=10, fill='x', padx=10)

    root.mainloop()
    return input_text

def parse_text_to_df(text_data, name):
    """
    입력받은 텍스트를 데이터프레임으로 변환합니다.
    """
    if not text_data.strip():
        return None

    try:
        # 1. 먼저 탭(엑셀 붙여넣기)으로 시도
        df = pd.read_csv(io.StringIO(text_data), sep='\t')
        if len(df.columns) < 2:
            # 컬럼이 너무 적으면 CSV(쉼표)로 다시 시도
            df_csv = pd.read_csv(io.StringIO(text_data), sep=',')
            if len(df_csv.columns) > len(df.columns):
                df = df_csv
        
        # 데이터가 비어있는지 확인
        if df.empty:
            print(f"❌ {name} 데이터가 비어있습니다!")
            return None
            
        print(f"✅ {name} 로드 성공: 총 {len(df)}행, 컬럼: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"❌ {name} 데이터 변환 중 오류: {e}")
        return None

def apply_synonyms(text, synonym_dict):
    """
    동의어 사전을 이용해 텍스트 내의 단어를 표준 용어로 치환합니다.
    주의: '긴 단어'부터 먼저 치환해야 부분 일치 오류를 막을 수 있습니다.
    예: '에폭시 페인트'가 있을 때 '페인트'->'도장' 보다 '에폭시 페인트'->'에폭시 도장'이 우선되어야 함.
    """
    if not isinstance(text, str):
        return text
    
    # 동의어 키들을 길이 순서대로 정렬 (긴 것부터 먼저 치환)
    # 이렇게 안 하면 '수성 페인트'에서 '페인트'만 먼저 바뀌는 문제 발생 가능
    sorted_keys = sorted(synonym_dict.keys(), key=len, reverse=True)
    
    current_text = text
    for key in sorted_keys:
        if key in current_text:
            # 해당 단어(key)를 기준 용어(value)로 치환
            current_text = current_text.replace(key, synonym_dict[key])
            
    return current_text

def parse_synonym_text(text_data):
    """
    동의어 사전 텍스트를 파싱하여 딕셔너리로 변환합니다.
    모든 동의어(용어1, 2, 3...)가 '기준 용어'를 가리키도록 만듭니다.
    또한 '기준 용어' 자체도 자기 자신을 가리키게 하여 검색의 편의를 돕습니다.
    """
    synonyms = {}
    if not text_data.strip():
        return synonyms
        
    lines = text_data.strip().split('\n')
    
    start_idx = 0
    first_line_parts = lines[0].split('\t')
    if "용어" in first_line_parts[0] or "기준" in first_line_parts[0]:
        start_idx = 1
        
    for line in lines[start_idx:]:
        if not line.strip():
            continue

        parts = [p.strip() for p in line.split('\t') if p.strip()]
        
        if len(parts) >= 1:
            standard_term = parts[0]  # 기준 용어 (사과)
            
            # 기준 용어 자체도 사전에 등록 (사과 -> 사과)
            # (사실 치환해도 변화는 없지만, 로직상 통일성을 위해)
            synonyms[standard_term] = standard_term
            
            if len(parts) >= 2:
                # 나머지 동의어들 (애플, APPLE...) -> 기준 용어 (사과)
                for alias in parts[1:]:
                    synonyms[alias] = standard_term
                
    return synonyms

def parse_location_dict(text_data):
    """
    위치 키워드를 유연하게 파싱합니다.
    엑셀에서 가로(행)로 데이터를 붙여넣는 상황에 최적화했습니다.
    예:
    대분류 | 주차장 | 옥상
    중분류 | 바닥   | 천장
    
    각 줄의 첫 번째 단어를 '카테고리'로 인식하고, 나머지를 키워드로 등록합니다.
    단, 사용자가 [대분류:30] 처럼 명시적으로 태그를 쓴 경우도 지원합니다.
    """
    locations = {} 
    # 기본 감점 설정
    default_penalties = {'대분류': 30, '중분류': 15, '소분류': 5}
    penalties = {}
    
    if not text_data.strip():
        return locations, penalties

    lines = text_data.strip().split('\n')
    current_category = '기본'

    for line in lines:
        line = line.strip()
        if not line: continue
        
        # 탭(\t)이나 콤마(,)로 분리
        parts = line.replace('\t', ',').split(',')
        parts = [p.strip() for p in parts if p.strip()]
        
        if not parts: continue

        # 첫 번째 단어 분석
        first_token = parts[0]
        
        # Case 1: [태그] 형식인 경우 (예: [대분류])
        if first_token.startswith('[') and ']' in first_token:
            tag_content = first_token[1:first_token.find(']')]
            if ':' in tag_content:
                name, score = tag_content.split(':', 1)
                current_category = name.strip()
                try: penalties[current_category] = int(score.strip())
                except: penalties[current_category] = 10
            else:
                current_category = tag_content.strip()
                penalties[current_category] = default_penalties.get(current_category, 10)
            
            # 나머지 단어들은 키워드로 추가
            keywords = parts[1:]
            
        # Case 2: 엑셀에서 그냥 '대분류'라고 적고 옆에 쭉 나열한 경우 (이미지 예시)
        elif first_token in ['대분류', '중분류', '소분류'] or first_token.endswith('분류'):
            current_category = first_token
            penalties[current_category] = default_penalties.get(current_category, 10)
            keywords = parts[1:] # 첫 단어(대분류) 빼고 나머지
            
        # Case 3: 그냥 키워드 나열인 경우 (이전 카테고리에 이어서)
        else:
            keywords = parts

        # 키워드 저장
        if current_category not in locations:
            locations[current_category] = []
            if current_category not in penalties: # 점수 설정 안 된 경우
                 penalties[current_category] = 10

        locations[current_category].extend(keywords)
                
    return locations, penalties

def calculate_location_score(text1, text2, loc_dict, penalty_dict):
    """
    동적으로 생성된 위치 사전을 기반으로 점수를 계산합니다.
    """
    def extract_keywords(text, keywords):
        return {k for k in keywords if k in text}

    score_adjustment = 0
    log_msg = []
    
    has_conflict = False
    
    # 등록된 모든 카테고리에 대해 순회
    for category, keywords in loc_dict.items():
        if not keywords: continue
        
        penalty = penalty_dict.get(category, 10) # 해당 카테고리의 감점 점수 가져오기
        
        set1 = extract_keywords(text1, keywords)
        set2 = extract_keywords(text2, keywords)
        
        if not set1 and not set2:
            continue
            
        common = set1.intersection(set2)
        
        if common:
            score_adjustment += 5 # 보너스는 고정 (또는 이것도 설정 가능하게?)
            log_msg.append(f"{category}일치")
        elif set1 and set2:
            # 충돌 발생! 설정된 패널티만큼 감점
            score_adjustment -= penalty
            has_conflict = True
            log_msg.append(f"{category}불일치(-{penalty})")
        
    return score_adjustment, " ".join(log_msg)

def match_dataframes(df_standard, df_target, synonym_dict=None, location_dict=None, penalty_dict=None, output_file="하자매칭결과.xlsx"):
    print(f"\n✅  데이터 로드 완료! (기존: {len(df_standard)}개 / 후행: {len(df_target)}개)")

    # 2. 비교할 컬럼(열) 선택
    print("\n------------------------------------------------")
    print("1️⃣  [기존 사건 목록]의 컬럼 목록:")
    for i, col in enumerate(df_standard.columns):
        print(f"   [{i}] {col}")
    
    try:
        std_idx = int(input("👉 기존 사건의 비교 항목(예: 하자명) 번호를 입력하세요: "))
        std_col = df_standard.columns[std_idx]
    except (ValueError, IndexError):
        print("❌  잘못된 번호입니다.")
        return

    print("\n2️⃣  [후행 사건 목록]의 컬럼 목록:")
    for i, col in enumerate(df_target.columns):
        print(f"   [{i}] {col}")

    try:
        tgt_idx = int(input("👉 후행 사건의 비교 항목(예: 지적사항) 번호를 입력하세요: "))
        tgt_col = df_target.columns[tgt_idx]
    except (ValueError, IndexError):
        print("❌  잘못된 번호입니다.")
        return

    # 3. 매칭 알고리즘 가동
    print(f"\n🔍  '{tgt_col}' 내용을 기반으로 가장 유사한 항목을 찾습니다...")
    print("    (4가지 분석 모드: 원본/동의어 X 띄어쓰기 유/무)")
    
    # 기존 데이터 전처리
    df_standard_clean = df_standard.dropna(subset=[std_col]).reset_index(drop=True)
    
    # 검색용 텍스트 준비
    texts_original = df_standard_clean[std_col].astype(str).tolist()
    texts_nospace = [t.replace(" ", "").replace("\n", "") for t in texts_original]
    
    # [중요] 기준 목록 자체에도 동의어 치환을 미리 해둡니다.
    # 예: 기준 목록에 '옥상 우레탄 파손'이라고 되어 있으면 -> '옥상 도막방수 파손' 등으로 통일
    # 그래야 현장에서 '도막방수'라고 쓰든 '우레탄'이라고 쓰든 둘 다 만날 수 있음
    texts_synonym = [apply_synonyms(t, synonym_dict) if synonym_dict else t for t in texts_original]
    texts_synonym_nospace = [t.replace(" ", "").replace("\n", "") for t in texts_synonym]

    results = []
    
    for idx, row in df_target.iterrows():
        query_original = str(row[tgt_col])
        if query_original == "nan" or not query_original.strip():
            # 빈 행 처리 (생략)
            continue 

        # --- 4가지 버전의 검색어 준비 ---
        
        # 1. 원본 그대로 (띄어쓰기 O)
        q1 = query_original
        # 2. 원본에서 띄어쓰기 제거
        q2 = query_original.replace(" ", "").replace("\n", "")
        
        # 3. 동의어 적용 (띄어쓰기 O)
        # 전문가 요청: '애플', 'APPLE', '홍옥' 등 무엇이 있든 전부 '사과'로 바꿉니다.
        q3 = apply_synonyms(query_original, synonym_dict) if synonym_dict else query_original
        # 4. 동의어 적용 후 띄어쓰기 제거
        q4 = q3.replace(" ", "").replace("\n", "")
        
        # --- 4번의 매칭 수행 ---
        
        # 매칭 함수 (대상 리스트, 검색어, 스코어링 방식)
        def get_best_match(query, candidates, scorer):
            match = process.extractOne(query, candidates, scorer=scorer)
            if match:
                return match # (text, score, index)
            return (None, 0, -1)

        # 1. 원본 vs 원본 (유사도: ratio)
        m1_text, m1_score, m1_idx = get_best_match(q1, texts_original, fuzz.ratio)
        
        # 2. 띄어쓰기X vs 띄어쓰기X
        m2_text, m2_score, m2_idx = get_best_match(q2, texts_nospace, fuzz.ratio)
        
        # 3. 동의어 vs 동의어 (여기가 핵심!)
        m3_text, m3_score, m3_idx = get_best_match(q3, texts_synonym, fuzz.ratio)
        
        # 4. 동의어+띄어쓰기X vs 동의어+띄어쓰기X
        m4_text, m4_score, m4_idx = get_best_match(q4, texts_synonym_nospace, fuzz.ratio)

        # --- 위치 정보 기반 점수 보정 (Location Weighted) ---
        # 4가지 후보 중에서 가장 그럴듯한 놈을 고르기 전에, 위치 정보를 봅니다.
        # 동의어가 적용된 텍스트(q3)를 기준으로 위치 분석을 하는 게 가장 정확합니다.
        
        candidates = [
            (m1_score, m1_text, m1_idx, "1.원본"),
            (m2_score, m2_text, m2_idx, "2.띄어쓰기X"),
            (m3_score, m3_text, m3_idx, "3.동의어"),
            (m4_score, m4_text, m4_idx, "4.동의어+띄어쓰기X")
        ]
        
        best_final_score = -999
        best_candidate = None
        best_loc_log = ""
        
        # 각 후보들에 대해 위치 점수를 반영해 봅니다.
        for score, text, idx, method in candidates:
            if idx == -1: continue # 매칭 실패한 건 패스
            
            # 위치 보정 점수 계산 (후행 텍스트 vs 후보 텍스트)
            # 동의어가 적용된 텍스트끼리 비교해야 정확합니다.
            target_text_for_loc = q3 
            candidate_text_for_loc = texts_synonym[idx]
            
            loc_adj, loc_log = 0, ""
            if location_dict and penalty_dict:
                loc_adj, loc_log = calculate_location_score(target_text_for_loc, candidate_text_for_loc, location_dict, penalty_dict)
            
            final_score = score + loc_adj
            
            # 100점 넘으면 100점으로 제한, 0점 미만 0점
            final_score = max(0, min(100, final_score))
            
            if final_score > best_final_score:
                best_final_score = final_score
                best_candidate = (score, text, idx, method) # 원본 점수 유지
                best_loc_log = f"보정:{loc_adj} ({loc_log})"

        # --- 결과 기록 ---
        row_data = {}
        
        # [1] 기존 사건 데이터 (매칭된 내용) - 맨 왼쪽
        if best_candidate:
            raw_score, matched_text, best_idx, method = best_candidate
            matched_row = df_standard_clean.iloc[best_idx]
            for col in df_standard_clean.columns:
                row_data[f"[기존] {col}"] = matched_row[col]
        else:
            for col in df_standard_clean.columns:
                row_data[f"[기존] {col}"] = "매칭 실패"

        # [2] 후행 사건 데이터 (원본 내용) - 중간
        for col in df_target.columns:
            row_data[f"[후행] {col}"] = row[col]

        # [3] 분석 결과 및 점수 - 맨 오른쪽
        if best_candidate:
             row_data['[최종] 점수'] = best_final_score
             row_data['[최종] 매칭방식'] = method
             row_data['[최종] 위치분석'] = best_loc_log
             
             if best_final_score < 60:
                 row_data['[검토] 의견'] = "❓ 확인 필요"
             else:
                 row_data['[검토] 의견'] = "✅ 매칭 성공"
        else:
             row_data['[최종] 점수'] = 0
             row_data['[최종] 매칭방식'] = "실패"
             row_data['[최종] 위치분석'] = ""
             row_data['[검토] 의견'] = "❌ 실패"
             
        # 상세 점수들 (참고용)
        row_data['[점수] 1.원본'] = m1_score
        row_data['[점수] 2.띄어쓰기X'] = m2_score
        row_data['[점수] 3.동의어'] = m3_score
        row_data['[점수] 4.동의어+띄어쓰기X'] = m4_score

        if idx % 50 == 0:
            print(".", end="", flush=True)

    # 4. 결과 저장
    result_df = pd.DataFrame(results)
    result_df.to_excel(output_file, index=False)
    print(f"\n\n🎉  모든 작업이 완료되었습니다!")
    print(f"📂  결과 파일: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    print("🖥️  데이터 입력 창을 띄웁니다...")

    # 0. 동의어 사전 입력
    synonym_text = get_text_from_gui(
        "[0단계] 동의어 사전 입력 (선택사항)", 
        "동의어 엑셀 데이터를 복사해서 붙여넣으세요.\n"
        "(첫 번째 열: 기준 용어, 나머지 열: 동의어들)\n"
        "예:\n도장 | 페인트 | 칠\n조적 | 벽돌 | 블록"
    )
    
    synonym_dict = parse_synonym_text(synonym_text)
    if synonym_dict:
        print(f"📚 동의어 사전 등록 완료: {len(synonym_dict)}개 단어")
    
    # 0.5. 위치 키워드 사전 입력 (추가됨)
    location_text = get_text_from_gui(
        "[0.5단계] 위치 키워드 사전 입력 (선택사항)", 
        "엑셀에서 위치 키워드를 복사해서 붙여넣으세요.\n"
        "예시 (첫 열이 분류명):\n"
        "대분류 | 지하주차장 | 옥상\n"
        "중분류 | 천장 | 바닥"
    )
    
    location_dict, penalty_dict = parse_location_dict(location_text)
    if any(location_dict.values()):
        print(f"🏗️ 위치 사전 등록 완료: {len(location_dict)}개 카테고리")

    # 1. 기존 사건 목록 입력
    std_text = get_text_from_gui(
        "[1단계] 기존 사건 목록 입력", 
        "아래 빈칸에 [기존 사건 목록] 엑셀 내용을 복사해서 붙여넣으세요.\n(제목 행 포함해서 붙여넣기)"
    )
    
    if not std_text.strip():
        print("❌  입력된 내용이 없습니다. 종료합니다.")
        sys.exit()

    df_std = parse_text_to_df(std_text, "기존 목록")
    if df_std is None:
        sys.exit()

    # 2. 후행 사건 목록 입력
    field_text = get_text_from_gui(
        "[2단계] 후행 사건 목록 입력", 
        "아래 빈칸에 [후행 사건 목록] 엑셀 내용을 복사해서 붙여넣으세요.\n(제목 행 포함해서 붙여넣기)"
    )

    if not field_text.strip():
        print("❌  입력된 내용이 없습니다. 종료합니다.")
        sys.exit()

    df_field = parse_text_to_df(field_text, "후행 목록")
    if df_field is None:
        sys.exit()

    # 3. 매칭 실행 (동의어 사전 + 위치 사전 전달)
    match_dataframes(df_std, df_field, synonym_dict, location_dict, penalty_dict)