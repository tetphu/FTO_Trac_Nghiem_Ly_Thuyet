import streamlit as st
import time

# --- 1. CẤU HÌNH (PHẢI Ở DÒNG ĐẦU TIÊN) ---
st.set_page_config(page_title="FTO System", page_icon="🚓", layout="centered")

# --- 2. MÀN HÌNH CHỜ (ĐỂ BIẾT APP CÒN SỐNG) ---
status_placeholder = st.empty()
status_placeholder.info("🔄 ĐANG TẢI HỆ THỐNG... VUI LÒNG CHỜ")

# --- 3. KHỐI AN TOÀN (BẮT LỖI TRẮNG MÀN HÌNH) ---
try:
    # --- IMPORT THƯ VIỆN ---
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    import pandas as pd
    import random

    # --- CẤU HÌNH BIẾN ---
    THOI_GIAN_MOI_CAU = 30

    # --- CSS GIAO DIỆN ---
    def inject_css():
        st.markdown("""
            <style>
            .block-container { padding-top: 1rem; padding-bottom: 5rem; }
            header, footer { visibility: hidden; }
            
            .gcpd-title {
                font-family: sans-serif; color: #002147; 
                font-size: 24px; font-weight: 900; text-align: center;
                text-transform: uppercase; margin-bottom: 10px;
            }
            .user-info {
                background-color: #e3f2fd; padding: 10px; border-radius: 8px;
                color: #0d47a1; font-weight: bold; text-align: center;
                margin-bottom: 10px; border: 1px solid #bbdefb;
            }
            .timer-digital {
                font-size: 45px; font-weight: 900; color: #d32f2f;
                text-align: center; background-color: #ffebee;
                border: 2px solid #d32f2f; border-radius: 12px;
                width: 120px; margin: 0 auto 20px auto; padding: 5px;
            }
            .question-box {
                background-color: #ffffff; padding: 20px; border-radius: 10px;
                border: 2px solid #002147;
                font-size: 18px; font-weight: bold; color: #002147; margin-bottom: 15px;
            }
            .explanation-box {
                background-color: #e8f5e9; padding: 15px;
                border-radius: 8px; border-left: 5px solid #4caf50;
                margin-top: 15px; color: #1b5e20;
            }
            .stButton button {
                background-color: #002147 !important; color: #FFD700 !important;
                font-weight: bold !important; width: 100%; padding: 12px !important;
            }
            div.row-widget.stRadio > div { flex-direction: row; justify-content: center; }
            </style>
        """, unsafe_allow_html=True)

    # --- KẾT NỐI DATABASE ---
    def ket_noi_csdl():
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        return client.open("HeThongTracNghiem")

    # --- CÁC HÀM XỬ LÝ ---
    def kiem_tra_dang_nhap(db, user, pwd):
        ws = db.worksheet("HocVien")
        rows = ws.get_all_values()
        for row in rows[1:]:
            if len(row) < 3: continue
            if str(row[0]).strip() == str(user).strip() and str(row[1]).strip() == str(pwd).strip():
                status = str(row[4]).strip() if len(row) > 4 else "ChuaDuocThi"
                return str(row[2]).strip(), str(row[3]).strip(), status
        return None, None, None

    def luu_ket_qua(db, user, diem):
        try:
            ws = db.worksheet("HocVien")
            cell = ws.find(user)
            ws.update_cell(cell.row, 5, "DaThi")
            ws.update_cell(cell.row, 6, str(diem))
        except: pass

    def cap_nhat_trang_thai(db, user, stt):
        try:
            ws = db.worksheet("HocVien")
            cell = ws.find(user)
            ws.update_cell(cell.row, 5, stt)
        except: pass

    def lay_giao_trinh(db):
        try: return db.worksheet("GiaoTrinh").get_all_records()
        except: return []

    # --- CHƯƠNG TRÌNH CHÍNH (MAIN) ---
    def main():
        inject_css()
        if 'vai_tro' not in st.session_state:
            st.session_state.update(vai_tro=None, diem_so=0, chi_so=0, bat_dau=False, da_nop_cau=False, ds_cau_hoi=[], thoi_
