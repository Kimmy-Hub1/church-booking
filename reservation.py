import streamlit as st
import pandas as pd
from datetime import datetime, time
import os

# --- 설정 및 데이터 로드 ---
st.set_page_config(page_title="교회 소모임실 예약", layout="wide")

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
    same_day_room = existing_df[(existing_df["날짜"] == str(date)) & (existing_df["방 이름"] == room)]
    for _, row in same_day_room.iterrows():
        ex_start = datetime.strptime(row["시작시간"], "%H:%M").time()
        ex_end = datetime.strptime(row["종료시간"], "%H:%M").time()
        if not (end <= ex_start or start >= ex_end):
            return True
    return False

# --- 사이드바: 모드 전환 보안 ---
st.sidebar.title("⛪ 메뉴")
access_mode = st.sidebar.radio("접속 모드", ["신청 모드", "관리자 모드"])

rooms = ["소모임실 1", "소모임실 2", "소모임실 3", "소모임실 4", "소모임실 5", "소모임실 6"]

# --- 1. 신청 모드 (일반 교인용) ---
if access_mode == "신청 모드":
    st.header("📝 소모임실 예약 신청")
    st.write("원하시는 방과 시간을 선택해 주세요.")
    
    with st.form("reservation_form"):
        col1, col2 = st.columns(2)
        with col1:
            room_choice = st.selectbox("사용할 방", rooms)
            user_name = st.text_input("신청자 성함")
            user_phone = st.text_input("연락처 (숫자만)")
        
        with col2:
            res_date = st.date_input("사용 날짜", datetime.now())
            start_time = st.time_input("시작 시간", time(10, 0))
            end_time = st.time_input("종료 시간", time(11, 0))
        
        submit = st.form_submit_button("예약 확정하기")
        
        if submit:
            if not user_name or not user_phone:
                st.warning("⚠️ 성함과 연락처를 입력해 주세요.")
            elif start_time >= end_time:
                st.error("❌ 종료 시간은 시작 시간보다 늦어야 합니다.")
            elif is_overlapping(room_choice, res_date, start_time, end_time, df):
                st.error(f"🚫 이미 예약된 시간입니다. 다른 시간을 선택해 주세요.")
            else:
                new_res = {
                    "방 이름": room_choice, "신청자": user_name, "연락처": user_phone,
                    "날짜": str(res_date), "시작시간": start_time.strftime("%H:%M"), "종료시간": end_time.strftime("%H:%M")
                }
                df = pd.concat([df, pd.DataFrame([new_res])], ignore_index=True)
                save_data(df)
                st.success(f"🎉 예약 완료!")

# --- 2. 관리자 모드 (사무실/교역자용) ---
else:
    st.header("🔐 관리자 전용 페이지")
    
    # 비밀번호 확인 (교회 상황에 맞게 수정하세요)
    password = st.text_input("관리자 비밀번호를 입력하세요", type="password")
    
    if password == "1234": # 실제 사용 시 이 부분을 비밀번호로 변경하세요
        st.subheader("📊 전체 예약 현황 확인 및 관리")
        
        view_date = st.date_input("조회 날짜 선택", datetime.now())
        filtered_df = df[df["날짜"] == str(view_date)].sort_values("시작시간")
        
        if filtered_df.empty:
            st.info("해당 날짜에 예약이 없습니다.")
        else:
            display_df = filtered_df.reset_index(drop=True)
            st.dataframe(display_df, use_container_width=True)
            
            with st.expander("🗑️ 예약 취소(삭제)"):
                idx_to_del = st.selectbox("삭제할 예약 번호", display_df.index)
                if st.button("예약 삭제 실행"):
                    target_row = display_df.iloc[idx_to_del]
                    df = df[~((df["방 이름"] == target_row["방 이름"]) & 
                              (df["날짜"] == target_row["날짜"]) & 
                              (df["시작시간"] == target_row["시작시간"]))]
                    save_data(df)
                    st.success("해당 예약이 삭제되었습니다.")
                    st.rerun()
    elif password:
        st.error("비밀번호가 올바르지 않습니다.")