import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- CẤU HÌNH ---
THOI_GIAN_MOI_CAU = 30

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
        st.error(f"LỖI KẾT NỐI: {str(e)}")
        return None

# --- XỬ LÝ ĐĂNG NHẬP ---
def kiem_tra_dang_nhap(db, user, pwd):
    try:
        ws = db.worksheet("HocVien")
        rows = ws.get_all_values()
        for row in rows[1:]:
            if len(row) < 4: continue
            u_sheet = str(row[0]).strip()
            p_sheet = str(row[1]).strip()
            if u_sheet == str(user).strip() and p_sheet == str(pwd).strip():
                status = str(row[4]).strip() if len(row) > 4 else ""
                if status == 'DaThi': return "DA_KHOA", None
                return str(row[2]).strip(), str(row[3]).strip()
    except Exception as e:
        st.error(f"LỖI DỮ LIỆU: {e}")
    return None, None

# --- LƯU KẾT QUẢ ---
def luu_ket_qua(db, user, diem):
    try:
        ws = db.worksheet("HocVien")
        cell = ws.find(user)
        ws.update_cell(cell.row, 5, "DaThi")
        ws.update_cell(cell.row, 6, str(diem))
        return True
    except: return False

# --- GIAO DIỆN CHÍNH ---
def main():
    st.set_page_config(page_title="GCPD System", page_icon="🚓", layout="centered")

    # CSS TINH CHỈNH (Đã kiểm tra kỹ cú pháp)
    st.markdown("""
        <style>
        /* Căn chỉnh lề */
        .block-container { 
            padding-top: 2rem; 
            padding-bottom: 2rem; 
            max-width: 800px; 
        }
        
        /* Ẩn Header/Footer mặc định */
        header, footer { visibility: hidden; }
        .stApp { background-color: #ffffff; }
        
        /* STYLE CHO HEADER (CHỮ) */
        .gcpd-title {
            font-family: 'Arial Black', sans-serif;
            color: #002147; 
            font-size: 32px;
            text-transform: uppercase;
            margin-top: 10px;
            line-height: 1.2;
            font-weight: 900;
        }
        
        /* KHUNG CHỨA FORM (Chỉ dùng cho Form, loại bỏ khung thừa ở header) */
        .form-box {
            border: 2px solid #002147;
            border-radius: 8px;
            background-color: #f8f9fa;
            padding: 30px;
            margin-top: 15px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }

        /* INPUT & BUTTON */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
            border: 2px solid #002