import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
from datetime import datetime

# --- CẤU HÌNH ---
THOI_GIAN_MOI_CAU = 30  # Số giây đếm ngược

# --- KẾT NỐI GOOGLE SHEET ---
def ket_noi_csdl():
    pham_vi = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Kiểm tra xem chạy trên Cloud hay Máy cá nhân
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        chung_chi = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, pham_vi)
    else:
        chung_chi = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", pham_vi)
        
    khach_hang = gspread.authorize(chung_chi)
    return khach_hang.open("HeThongTracNghiem")

# --- XỬ LÝ ĐĂNG NHẬP (DỰA VÀO VỊ TRÍ CỘT) ---
def kiem_tra_dang_nhap(bang_tinh, user, pwd):
    try:
        ws = bang_tinh.worksheet("HocVien")
        # Lấy tất cả dữ liệu (bao gồm cả dòng tiêu đề)
        tat_ca_dong = ws.get_all_values()
        
        # Bỏ qua dòng tiêu đề (dòng 1), bắt đầu duyệt từ dòng 2
        for dong in tat_ca_dong[1:]:
            # Kiểm tra dòng có đủ dữ liệu không (tránh lỗi index out of range)
            if len(dong) < 4: continue

            # Cột 1 (Index 0): Tên đăng nhập
            # Cột 2 (Index 1): Mật khẩu
            u_sheet = str(dong[0]).strip()
            p_sheet = str(dong[1]).strip()
            
            if u_sheet == str(user).strip() and p_sheet == str(pwd).strip():
                # Cột 5 (Index 4): Trạng thái (DaThi)
                trang_thai = ""
                if len(dong) > 4: 
                    trang_thai = str(dong[4]).strip()
                
                if trang_thai == 'DaThi':
                    return "DA_KHOA", None
                
                # Cột 3 (Index 2): Vai trò | Cột 4 (Index 3): Họ tên
                return dong[2], dong[3]
                
    except Exception as e:
        st.error(f"Lỗi đăng nhập: {e}")
    return None, None

# --- LƯU KẾT QUẢ ---
def luu_ket_qua(bang_tinh, user, diem):
    try:
        ws = bang_tinh.worksheet("HocVien")
        cell = ws.find(user) # Tìm dòng chứa user
        
        # Cập nhật Cột 5 (Trạng thái) và Cột 6 (Điểm số)
        ws.update_cell(cell.row, 5, "DaThi")
        ws.update_cell(cell.row, 6, str(diem))
        return True
    except Exception as e:
        st.error(f"Lỗi lưu kết quả: {e}")
        return False

# --- LẤY CÂU HỎI (DỰA VÀO VỊ TRÍ CỘT) ---
def lay_ds_cau_hoi(bang_tinh):
    ws = bang_tinh.worksheet("CauHoi")
    tat_ca = ws.get_all_values()
    # Bỏ dòng tiêu đề (dòng 1), chỉ lấy dữ liệu
    return tat_ca[1:]

# --- GIAO DIỆN CHÍNH ---
def main():
    st.set_page_config(page_title="Thi Trắc Nghiệm Online", page_icon="📝")
    st.markdown("""
        <style>
        .stAlert { padding: 1rem; border-radius: 0.5rem; margin-top: 1rem;}
        .stButton button { width: 100%; margin