import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# --- CẤU HÌNH ---
THOI_GIAN_MOI_CAU = 30  # Số giây đếm ngược mỗi câu

# --- KẾT NỐI GOOGLE SHEET ---
def connect_db():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Kiểm tra chạy trên Cloud hay Local
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        
    client = gspread.authorize(creds)
    sheet = client.open("HeThongTracNghiem")
    return sheet

# --- CÁC HÀM XỬ LÝ DỮ LIỆU ---
def login(sheet, user, pwd):
    try:
        users_ws = sheet.worksheet("Users")
        records = users_ws.get_all_records()
        for record in records:
            if str(record['Username']) == user and str(record['Password']) == pwd:
                return record['Role'], record['HoTen']
    except:
        return None, None
    return None, None

def luu_diem(sheet, user, diem, hoten):
    try:
        scores_ws = sheet.worksheet("Scores")
        scores_ws.append_row([user, hoten, diem, str(datetime.now())])
    except:
        pass

def get_questions(sheet):
    ws = sheet.worksheet("Questions")
    return ws.get_all_records()

# --- GIAO DIỆN CHÍNH ---
def main():
    st.set_page_config(page_title="Thi Trắc Nghiệm", page_icon="📝")
    
    # CSS tùy chỉnh giao diện thông báo
    st.markdown("""
        <style>
        .stAlert { padding: 1rem; border-radius: 0.5rem; margin-top: 1rem;}
        div.stButton > button:first-child { width: 100%; margin-top: 10px; }
        </style>
    """, unsafe_allow_html=True)

    try:
        db = connect_db()
    except:
        st.error("Lỗi kết nối! Kiểm tra lại file credentials.json hoặc Secrets.")
        st.stop()

    # --- KHỞI TẠO TRẠNG THÁI (SESSION STATE) ---
    if 'role' not in st.session_state: st.session_state['role'] = None
    if 'current_index' not in st.session_state: st.session_state['current_index'] = 0