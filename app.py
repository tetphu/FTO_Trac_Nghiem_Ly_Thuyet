import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import time

# --- 1. CẤU HÌNH ---
THOI_GIAN_MOI_CAU = 30

# --- 2. HÀM GIAO DIỆN ---
def inject_css():
    st.markdown("""
        <style>
        .block-container { padding-top: 2rem; padding-bottom: 5rem; }
        header, footer { visibility: hidden; }
        .stApp { background-color: #ffffff; }
        .gcpd-title {
            font-family: 'Arial Black', sans-serif; color: #002147; 
            font-size: 35px; text-transform: uppercase;
            margin-top: 10px; line-height: 1.2; font-weight: 900;
        }
        [data-testid="stForm"] {
            border: 3px solid #002147; border-radius: 12px; padding: 20px;
            background-image: url("https://raw.githubusercontent.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/refs/heads/main/nen.png");
            background-size: cover; background-position: center;
            background-color: rgba(255, 255, 255, 0.9); background-blend-mode: overlay;
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
            border: 2px solid #002147 !important; border-radius: 4px !important;
            font-weight: bold; color: #000 !important;
        }
        .stButton button {
            background-color: #002147 !important; color: #FFD700 !important;
            font-weight: bold !important; width: 100%; padding: 10px;
        }
        .lesson-card {
            background-color: #f8f9fa; border-left: 5px solid #002147;
            padding: 20px; margin-bottom: 20px; border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .lesson-title { color: #002147; font-size: 24px; font-weight: bold; margin-bottom: 10px; }
        .lesson-content { font-size: 16px; line-height: 1.6; color: #333; white-space: pre-wrap; }
        </style>
    """, unsafe_allow_html=True)

# --- 3. KẾT NỐI GOOGLE SHEET ---
def ket_noi_csdl():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        return client.open("HeThongTracNghiem")
    except Exception as e:
        st.error(f"Lỗi kết nối: {str(e)}")
        return None

# --- 4. CÁC HÀM XỬ LÝ DỮ LIỆU ---
def kiem_tra_dang_nhap(db, user, pwd):
    try:
        ws = db.worksheet("HocVien")
        rows = ws.get_all_values()
        for row in rows[1:]:
            if len(row) < 4: continue
            if str(row[0]).strip() == str(user).strip() and str(row[1]).strip() == str(pwd).strip():
                status = str(row[4]).strip() if len(row) > 4 else ""
                if status == 'DaThi': return "DA_KHOA", None
                if status == 'DangThi': return "VI_PHAM", None
                return str(row[2]).strip(), str(row[3]).strip()
    except: pass
    return None, None

def danh_dau_dang_thi(db, user):
    try:
        ws = db.worksheet("HocVien")
        cell = ws.find(user)
        ws.update_cell(cell.row, 5, "DangThi")
        return True
    except: return False

def luu_ket_qua(db, user, diem):
    try:
        ws = db.worksheet("HocVien")
        cell = ws.find(user)
        ws.update_cell(cell.row, 5, "DaThi")
        ws.update_cell(cell.row, 6, str(diem))
        return True
    except: return False

def lay_giao_trinh(db):
    try:
        ws = db.worksheet("GiaoTrinh")
        return ws.get_all_records()
    except: return []

# --- 5. CHƯƠNG TRÌNH CHÍNH ---
def main():
    st.set_page_config(page_title="FTO System", page_icon="🚓", layout="wide")
    inject_css() 

    if 'vai_tro' not in st.session_state: 
        st.session_state.update(vai_tro=None, chi_so=0, diem_so=0, ds_cau_hoi=[], da_nop_cau=False, bat_dau=False, thoi_gian_het=None, lua_chon=None)

    db = ket_noi_csdl()
    if not db: st.stop()

    # --- A. MÀN HÌNH ĐĂNG NHẬP ---
    if st.session_state['vai_tro'] is None:
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            with st.form("login"):
                wc1, wc2 = st.columns([1, 2.5])
                with wc1: st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", width=150)
                with wc2: st.markdown('<div class="gcpd-title">GACHA CITY<BR>POLICE DEPT<BR>ACADEMY</div>', unsafe_allow_html=True)
                st.divider()
                st.markdown("### ▼ ĐĂNG NHẬP HỆ THỐNG")
                u = st.text_input("SỐ HIỆU (Momo)")
                p = st.text_input("MÃ BẢO MẬT", type="password")
                
                if st.form_submit_button("XÁC THỰC DANH TÍNH"):
                    vt, ten = kiem_tra_dang_nhap(db, u, p)
                    if vt == "DA_KHOA": st.error
