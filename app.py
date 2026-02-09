import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import time
import random

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="FTO System", page_icon="🚓", layout="centered")
THOI_GIAN_MOI_CAU = 30

# --- 2. CSS GIAO DIỆN ---
def inject_css():
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem; padding-bottom: 5rem; }
        header, footer { visibility: hidden; }
        .stApp { background-color: #ffffff; }
        .gcpd-title {
            font-family: 'Arial Black', sans-serif; color: #002147; 
            font-size: 24px; text-transform: uppercase;
            font-weight: 900; text-align: center;
        }
        [data-testid="stForm"] {
            border: 2px solid #002147; border-radius: 10px; padding: 15px;
            background-color: #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stButton button {
            background-color: #002147 !important; color: #FFD700 !important;
            font-weight: bold !important; width: 100%; padding: 12px !important;
        }
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

# --- 4. HÀM XỬ LÝ DỮ LIỆU ---
def kiem_tra_dang_nhap(db, user, pwd):
    try:
        ws = db.worksheet("HocVien")
        rows = ws.get_all_values()
        # Duyệt qua các dòng, bỏ qua dòng tiêu đề
        for row in rows[1:]:
            if len(row) < 3: continue
            # Cấu trúc: Col 0=User, 1=Pass, 2=Role, 3=Name, 4=Status
            u_db = str(row[0]).strip()
            p_db = str(row[1]).strip()
            
            if u_db == str(user).strip() and p_db == str(pwd).strip():
                role = str(row[2]).strip()
                name = str(row[3]).strip() if len(row) > 3 else u_db
                status = str(row[4]).strip() if len(row) > 4 else "ChuaDuocThi"
                return role, name, status
    except: pass
    return None, None, None

def cap_nhat_trang_thai(db, user, stt):
    try:
        ws = db.worksheet("HocVien")
        cell = ws.find(user)
        ws.update_cell(cell.row, 5, stt) # Cột 5 là Trạng Thái
    except: pass

def luu_ket_qua(db, user, diem):
    try:
        ws = db.worksheet("HocVien")
        cell = ws.find(user)
        ws.update_cell(cell.row, 5, "DaThi")
        ws.update_cell(cell.row, 6, str(diem))
    except: pass

def lay_giao_trinh(db):
    try:
        return db.worksheet("GiaoTrinh").get_all_records()
    except: return []

# --- 5. CHƯƠNG TRÌNH CHÍNH ---
def main():
    inject_css()
    
    # Khởi tạo Session State
    if 'vai_tro' not in st.session_state:
        st.session_state.update(
            vai_tro=None, ho_ten="", user="", 
            bat_dau=False, diem_so=0, chi_so=0, 
            ds_cau_hoi=[], da_nop_cau=False, 
            thoi_gian_het=None, lua_chon=None, loai_thi=None
        )

    db = ket_noi_csdl()
    if not db: st.stop()

    # --- A. MÀN HÌNH ĐĂNG NHẬP ---
    if st.session_state['vai_tro'] is None:
        with st.form("login_form"):
            c1, c2 = st.columns([1, 2.5])
            with c1: st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", use_column_width=True)
            with c2: st.markdown('<div class="gcpd-title">FTO ACADEMY<br>LOGIN</div>', unsafe_allow_html=True)
            st.divider()
            
            u = st.text_input("TÊN ĐĂNG NHẬP (Momo)")
            p = st.text_input("MẬT KHẨU", type="password")
            
            if st.form_submit_button("ĐĂNG NHẬP"):
                vt, ten, stt = kiem_tra_dang_nhap(db, u, p)
                if vt:
                    st.session_state.update(vai_tro=vt, user=u, ho_ten=ten)
                    st.rerun()
                else:
                    st.error("❌ Sai thông tin đăng nhập!")

    # --- B. ĐÃ ĐĂNG NHẬP ---
    else:
        # Sidebar thông tin
        with st.sidebar:
            st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", width=100)
            st.markdown(f"**Xin chào: {st.session_state['ho_ten']}**")
            st.code(f"Role: {st.session_state['vai_tro']}")
            
            if st.button("ĐĂNG XUẤT"):
                st.session_state.clear()
                st.rer
