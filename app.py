import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- CẤU HÌNH ---
THOI_GIAN_MOI_CAU = 30  # Thời gian (giây) cho mỗi câu

# --- KẾT NỐI GOOGLE SHEET ---
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

# --- CÁC HÀM XỬ LÝ DỮ LIỆU ---
def kiem_tra_dang_nhap(db, user, pwd):
    try:
        ws = db.worksheet("HocVien")
        rows = ws.get_all_values()
        for row in rows[1:]:
            if len(row) < 4: continue
            if str(row[0]).strip() == str(user).strip() and str(row[1]).strip() == str(pwd).strip():
                status = str(row[4]).strip() if len(row) > 4 else ""
                
                # --- KIỂM TRA TRẠNG THÁI ---
                if status == 'DaThi': return "DA_KHOA", None
                if status == 'DangThi': return "VI_PHAM", None
                
                role = str(row[2]).strip()
                name = str(row[3]).strip()
                return role, name
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

# --- GIAO DIỆN CHÍNH ---
def main():
    st.set_page_config(page_title="FTO System", page_icon="🚓", layout="wide")

    # CSS STYLE
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
            background-image: url("
