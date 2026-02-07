import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- CẤU HÌNH HỆ THỐNG ---
THOI_GIAN_MOI_CAU = 30

# --- KẾT NỐI GOOGLE SHEET ---
def ket_noi_csdl():
    try:
        pham_vi = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" in st.secrets:
            creds_dict = st.secrets["gcp_service_account"]
            chung_chi = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, pham_vi)
        else:
            chung_chi = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", pham_vi)
        khach_hang = gspread.authorize(chung_chi)
        return khach_hang.open("HeThongTracNghiem")
    except Exception as e:
        st.error(f"LỖI HỆ THỐNG: Không thể kết nối cơ sở dữ liệu. {str(e)}")
        return None

# --- XỬ LÝ ĐĂNG NHẬP ---
def kiem_tra_dang_nhap(bang_tinh, user, pwd):
    try:
        ws = bang_tinh.worksheet("HocVien")
        tat_ca_dong = ws.get_all_values()
        for dong in tat_ca_dong[1:]:
            if len(dong) < 4: continue
            u_sheet = str(dong[0]).strip()
            p_sheet = str(dong[1]).strip()
            if u_sheet == str(user).strip() and p_sheet == str(pwd).strip():
                trang_thai = str(dong[4]).strip() if len(dong) > 4 else ""
                if trang_thai == 'DaThi': return "DA_KHOA", None
                return str(dong[2]).strip(), str(dong[3]).strip()
    except Exception as e