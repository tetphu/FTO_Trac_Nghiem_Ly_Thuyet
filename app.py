import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
from datetime import datetime

# --- CẤU HÌNH ---
THOI_GIAN_MOI_CAU = 30 

# --- KẾT NỐI GOOGLE SHEET ---
def ket_noi_csdl():
    pham_vi = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        chung_chi = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, pham_vi)
    else:
        chung_chi = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", pham_vi)
        
    khach_hang = gspread.authorize(chung_chi)
    return khach_hang.open("HeThongTracNghiem")

# --- XỬ LÝ ĐĂNG NHẬP (DỰA VÀO SỐ THỨ TỰ CỘT) ---
def kiem_tra_dang_nhap(bang_tinh, user, pwd):
    try:
        ws = bang_tinh.worksheet("HocVien")
        # Lấy toàn bộ dữ liệu dạng danh sách (List of Lists)
        # Ví dụ: [['User', 'Pass'..], ['admin', '123'..]]
        tat_ca_dong = ws.get_all_values()
        
        # Bỏ qua dòng đầu tiên (Tiêu đề) -> Bắt đầu từ dòng 2
        for dong in tat_ca_dong[1:]:
            # Kiểm tra độ dài dòng để tránh lỗi nếu dòng bị trống
            if len(dong) < 4: continue 

            # Cột 0 (A): User | Cột 1 (B): Pass
            u_sheet = str(dong[0]).strip()
            p_sheet = str(dong[1]).strip()
            
            if u_sheet == str(user).strip() and p_sheet == str(pwd).strip():
                # Cột 4 (E): Trạng thái
                trang_thai = ""
                if len(dong) > 4: # Kiểm tra xem có cột E không
                    trang_thai = str(dong[4]).strip()
                
                if trang_thai == 'DaThi':
                    return "DA_KHOA", None
                
                # Cột 2 (C): Vai trò | Cột 3 (D): Họ tên
                return dong[2], dong[3]
                
    except Exception as e:
        st.error(f"Lỗi đăng nhập: {e}")
    return None, None

# --- LƯU KẾT QUẢ ---
def luu_ket_qua(bang_tinh, user, diem):
    try:
        ws = bang_tinh.worksheet("HocVien")
        cell = ws.find(user) # Vẫn dùng find để tìm dòng nhanh nhất
        
        # Cập nhật cột 5 (E) và cột 6 (F)
        ws.update_cell(cell.row, 5, "DaThi")
        ws.update_cell(cell.row, 6, str(diem))
        return True
    except Exception as e:
        st.error(f"Lỗi lưu kết quả: {e}")
        return False

# --- LẤY CÂU HỎI (DỰA VÀO SỐ THỨ TỰ CỘT) ---
def lay_ds_cau_hoi(bang_tinh):
    ws = bang_tinh.worksheet("CauHoi")
    tat_ca = ws.get_all_values()
    # Bỏ dòng tiêu đề, chỉ lấy dữ liệu
    return tat_ca[1:]

# --- GIAO DIỆN CHÍNH ---
def main():
    st.set_page_config(page_title="Thi Trắc Nghiệm Online", page_icon="📝")
    st.markdown("""
        <style>
        .stAlert { padding: 1rem; border-radius: 0.5rem; margin-top: 1rem;}
        .stButton button { width: 100%; margin-top: 10px; font-weight: bold; font-size: 16px;}
        </style>
    """, unsafe_allow_html=True)

    try:
        db = ket_noi_csdl()
    except Exception as e:
        st.error(f"❌ Lỗi kết nối: {e}")
        st.stop()

    # Session State
    if 'vai_tro' not in st.session_state: st.session_state['vai_tro'] = None
    if 'chi_so' not in st.session_state: st.session_state['chi_so'] = 0
    if 'diem_so' not in st.session_state: st.session_state['diem_so'] = 0
    if 'ds_cau_hoi' not in st.session_state: st.session_state['ds_cau_hoi'] = []
    if 'da_nop_cau' not in st.session_state: st.session_state['da_nop_cau'] = False
    if 'lua_chon' not in st.session_state: st.session_state['lua_chon'] = None
    if 'thoi_gian_het' not in st.session_state: st.session_state['thoi_gian_het'] = None

    # --- 1. ĐĂNG NHẬP ---
    if st.session_state['vai_tro'] is None:
        st.title("🎓 Đăng Nhập Hệ Thống")
        with st.form("login_form"):
            u = st.text_input("Tên đăng nhập")
            p = st.text_input("Mật khẩu", type="password")
            btn = st.form_submit_button("Đăng Nhập")
            
            if btn:
                vai_tro, ho_ten = kiem_tra_dang_nhap(db, u, p)
                if vai_tro == "DA_KHOA":
                    st.error("⛔ Tài khoản này đã thi rồi!")
                elif vai_tro:
                    st.session_state['vai_tro'] = vai_tro.strip() # Xóa khoảng trắng thừa
                    st.session_state['user'] = u
                    st.session_state['ho_ten'] = ho_ten
                    # Reset
                    st.session_state['chi_so'] = 0
                    st.session_state['diem_so'] = 0
                    st.session_state['ds_cau_hoi'] = []
                    st.session_state['da_nop_cau'] = False
                    st.session_state['lua_chon'] = None
                    st.session_state['thoi_gian_het'] = None
                    st.rerun()
                else:
                    st.error("❌ Sai thông tin đăng nhập")

    # --- 2. ADMIN ---
    elif st.session_state['vai_tro'] == 'admin':
        st.sidebar.markdown(f"👤 Admin: **{st.session_state['ho_ten']}**")
        if st.sidebar.button("Đăng xuất"):
            st.session_state['vai_tro'] = None
            st.rerun()
        
        st.header("⚙️ Thêm Câu Hỏi Mới")
        with st.form("add_q"):
            # Nhập liệu vẫn như cũ
            q = st.text_input("Câu hỏi (Cột A)")
            c1, c2 = st.columns(2)
            a = c1.text_input("Đáp án A (Cột B)")
            b = c1.text_input("Đáp án B (Cột C)")
            c = c2.text_input("Đáp án C (Cột D)")
            d = c2.text_input("Đáp án D (Cột E)")
            dung = st.selectbox("Đáp án đúng (Cột F)", ["A", "B", "C", "D"])
            giai_thich = st.text_area("Giải thích (Cột G)")
            
            if st.form_submit_button("Lưu"):
                try:
                    ws = db.worksheet("CauHoi")
                    ws.append_row([q, a, b, c, d, dung, giai_thich])
                    st.success("✅ Đã lưu!")
                except Exception as e:
                    st.error(f"Lỗi: {e}")

    # --- 3. HỌC VIÊN ---
    elif st.session_state['vai_tro'] == 'hocvien':
        if not st.session_state['ds_cau_hoi']:
            try:
                st.session_state['ds_cau_hoi'] = lay_ds_cau_hoi(db)
            except Exception as e:
                st.error(f"Lỗi tải câu hỏi: {e}")
                st.stop()
        
        ds = st.session_state['ds_cau_hoi']
        idx = st.session_state['chi_so']

        # Nếu không có câu hỏi
        if not ds:
            st.warning("Chưa có câu hỏi nào.")
            st.stop()

        st.sidebar.markdown(f"👋 Xin chào: **{st.session_state['ho_ten']}**")
        st.sidebar.metric("Điểm số", st.session_state['diem_so'])

        # KẾT THÚC
        if idx >= len(ds):
            luu_ket_qua(db, st.session_state['user'], st.session_state['diem_so'])
            st.balloons()
            st.success(f"🎉 HOÀN THÀNH! Điểm số: {st.session_state['diem_so']}/{len(ds)}")
            st.info("Đang đăng xuất...")
            time.sleep(3)
            st.session_state['vai_tro'] = None
            st.rerun()
            return

        # HIỂN THỊ CÂU HỎI (TRUY CẬP BẰNG INDEX)
        cau = ds[idx]
        
        # Đảm bảo dòng dữ liệu có đủ cột, nếu thiếu thì điền chuỗi rỗng
        while len(cau) < 7:
            cau.append("")
            
        noi_dung = cau[0] # Cột A
        da_a = cau[1]     # Cột B
        da_b = cau[2]     # Cột C
        da_c = cau[3]     # Cột D
        da_d = cau[4]     # Cột E
        dap_an_dung = str(cau[5]).strip().upper() # Cột F
        loi_giai = cau[6] # Cột G

        st.subheader(f"Câu {idx + 1}:")
        st.info(noi_dung)

        # LOGIC LÀM BÀI
        if not st.session_state['da_nop_cau']:
            if st.session_state['thoi_gian_het'] is None:
                st.session_state['thoi_gian_het'] = time.time() + THOI_GIAN_MOI_CAU
            
            con_lai = st.session_state['thoi_gian_het'] - time.time()
            if con_lai <= 0:
                st.session_state['da_nop_cau'] = True
                st.session_state['lua_chon'] = None
                st.rerun()

            st.progress(max(0.0, min(1.0, con_lai/THOI_GIAN_MOI_CAU)))
            st.caption(f