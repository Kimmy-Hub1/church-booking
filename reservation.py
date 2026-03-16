import streamlit as st
import pandas as pd
from datetime import datetime, time
import os

# --- 설정 및 데이터 로드 ---
st.set_page_config(page_title="교회 소모임실 스마트 예약", layout="wide")

DB_FILE = "room_reservations_v2.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["방 이름", "신청자", "연락처", "날짜", "시작시간", "종료시간"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

df = load_data()

# --- 중복 체크 함수 ---
def is_overlapping(room, date, start, end, existing_df):
    # 같은 날짜, 같은 방의 예약만 필터링
    same_day_room = existing_df[(existing_df["날짜"] == str(date)) & (existing_df["방 이름"] == room)]
    
    for _, row in same_day_room.iterrows():
        # 시간 문자열을 datetime 객체로 변환하여 비교
        ex_start = datetime.strptime(row["시작시간"], "%H:%M").time()
        ex_end = datetime.strptime(row["종료시간"], "%H:%M").time()
        
        # 겹침 조건 확인 (시작시간이 종료시간보다 빨라야 함은 기본 전제)
        if not (end <= ex_start or start >= ex_end):
            return True # 겹침 발생
    return False

# --- UI 레이아웃 ---
st.sidebar.title("⛪ 교회 예약 시스템")
menu = st.sidebar.radio("메뉴", ["신청 모드", "관리자 모드 (시간표)"])

rooms = ["소모임실 1", "소모임실 2", "소모임실 3", "소모임실 4", "소모임실 5", "소모임실 6"]

# --- 1. 신청 모드 ---
if menu == "신청 모드":
    st.header("📝 소모임실 예약 신청")
    
    with st.form("reservation_form"):
        col1, col2 = st.columns(2)
        with col1:
            room_choice = st.selectbox("사용할 방", rooms)
            user_name = st.text_input("신청자 성함")
            user_phone = st.text_input("연락처 (숫자만 입력)")
        
        with col2:
            res_date = st.date_input("사용 날짜", datetime.now())
            start_time = st.time_input("시작 시간", time(10, 0))
            end_time = st.time_input("종료 시간", time(11, 0))
        
        submit = st.form_submit_button("예약 신청하기")
        
        if submit:
            if not user_name or not user_phone:
                st.warning("⚠️ 모든 정보를 입력해주세요.")
            elif start_time >= end_time:
                st.error("❌ 종료 시간은 시작 시간보다 늦어야 합니다.")
            else:
                # 중복 체크 로직 가동
                if is_overlapping(room_choice, res_date, start_time, end_time, df):
                    st.error(f"🚫 {room_choice}의 해당 시간대는 이미 예약되어 있습니다. 다른 시간을 선택해주세요.")
                else:
                    new_res = {
                        "방 이름": room_choice,
                        "신청자": user_name,
                        "연락처": user_phone,
                        "날짜": str(res_date),
                        "시작시간": start_time.strftime("%H:%M"),
                        "종료시간": end_time.strftime("%H:%M")
                    }
                    df = pd.concat([df, pd.DataFrame([new_res])], ignore_index=True)
                    save_data(df)
                    st.success(f"🎉 예약 완료! {res_date} {start_time.strftime('%H:%M')}에 뵙겠습니다.")

# --- 2. 관리자 모드 ---
else:
    st.header("📋 전체 예약 시간표")
    
    view_date = st.date_input("조회 날짜 선택", datetime.now())
    filtered_df = df[df["날짜"] == str(view_date)].sort_values("시작시간")
    
    if filtered_df.empty:
        st.info(f"💡 {view_date}에는 아직 예약이 없습니다.")
    else:
        # 보기 좋게 출력하기 위해 인덱스 재설정
        display_df = filtered_df.reset_index(drop=True)
        st.dataframe(display_df, use_container_width=True)
        
        # 삭제 기능
        with st.expander("🗑️ 예약 취소/관리"):
            idx_to_del = st.selectbox("취소할 예약 번호 선택", display_df.index)
            if st.button("선택한 예약 삭제"):
                # 실제 원본 데이터프레임에서 해당 조건 데이터 삭제
                target_row = display_df.iloc[idx_to_del]
                df = df[~((df["방 이름"] == target_row["방 이름"]) & 
                          (df["날짜"] == target_row["날짜"]) & 
                          (df["시작시간"] == target_row["시작시간"]))]
                save_data(df)
                st.success("삭제되었습니다.")
                st.rerun()
