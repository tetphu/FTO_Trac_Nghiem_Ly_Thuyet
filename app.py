import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
from datetime import datetime

# --- CẤU HÌNH HỆ THỐNG ---
THOI_GIAN_MOI_CAU = 30  # Số giây cho mỗi câu hỏi

# --- HÀM KẾT NỐI GOOGLE SHEET ---
def ket_noi_csdl():
    pham_vi = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Kiểm tra xem đang chạy trên Cloud (Secrets) hay máy cá nhân
    if "gcp_service_account" in st.secrets:
        thong_tin_xac_thuc = st.secrets["gcp_service_account"]
        chung_chi = ServiceAccountCredentials.from_json_keyfile_dict(thong_tin_xac_thuc, pham_vi)
    else:
        chung_chi = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", pham_vi)
        
    khach_hang = gspread.authorize(chung_chi)
    # Mở bảng tính theo tên
    bang_tinh = khach_hang.open("HeThongTracNghiem") 
    return bang_tinh

# --- HÀM XỬ LÝ ĐĂNG NHẬP ---
def kiem_tra_dang_nhap(bang_tinh, ten_dang_nhap, mat_khau):
    try:
        # Truy cập vào Tab 'HocVien'
        trang_hoc_vien = bang_tinh.worksheet("HocVien")
        danh_sach_ban_ghi = trang_hoc_vien.get_all_records()
        
        for ban_ghi in danh_sach_ban_ghi:
            # So sánh Tên đăng nhập và Mật khẩu (Dùng cột tiếng Việt)
            if str(ban_ghi['TenDangNhap']).strip() == str(ten_dang_nhap).strip() and str(ban_ghi['MatKhau']).strip() == str(mat_khau).strip():
                
                # Kiểm tra xem đã thi chưa
                trang_thai = str(ban_ghi.get('TrangThai', '')).strip()
                if trang_thai == 'DaThi':
                    return "DA_KHOA", None 
                
                # Trả về Vai trò và Họ tên
                return ban_ghi['VaiTro'], ban_ghi['HoTen']
    except Exception as loi:
        st.error(f"Lỗi đăng nhập: {loi}")
        return None, None
    return None, None

# --- HÀM LƯU ĐIỂM SỐ VÀ KHÓA TÀI KHOẢN ---
def luu_ket_qua(bang_tinh, ten_dang_nhap, diem_so):
    try:
        trang_hoc_vien = bang_tinh.worksheet("HocVien")
        
        # Tìm dòng chứa Tên đăng nhập
        o_tim_thay = trang_hoc_vien.find(ten_dang_nhap)
        
        # Cập nhật cột E (TrangThai - Cột 5) thành 'DaThi'
        trang_hoc_vien.update_cell(o_tim_thay.row, 5, "DaThi")
        
        # Cập nhật cột F (DiemSo - Cột 6)
        trang_hoc_vien.update_cell(o_tim_thay.row, 6, str(diem_so))
        
        return True
    except Exception as loi:
        st.error(f"Lỗi khi lưu kết quả: {loi}")
        return False

# --- HÀM LẤY DANH SÁCH CÂU HỎI ---
def lay_du_lieu_cau_hoi(bang_tinh):
    # Truy cập vào Tab 'CauHoi'
    trang_cau_hoi = bang_tinh.worksheet("CauHoi")
    return trang_cau_hoi.get_all_records()

# --- GIAO DIỆN CHÍNH CỦA PHẦN MỀM ---
def main():
    st.set_page_config(page_title="Thi Trắc Nghiệm Online", page_icon="🇻🇳")
    
    # CSS làm đẹp giao diện tiếng Việt
    st.markdown("""
        <style>
        .stAlert { padding: 1rem; border-radius: 0.5rem; margin-top: 1rem;}
        .stButton button { width: 100%; margin-top: 10px; font-weight: bold; font-size: 16px;}
        h1, h2, h3 { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        </style>
    """, unsafe_allow_html=True)

    # Kết nối CSDL
    try:
        db = ket_noi_csdl()
    except Exception as loi:
        st.error(f"❌ Không thể kết nối Google Sheet! Vui lòng kiểm tra lại file cấu hình. Chi tiết: {loi}")
        st.stop()

    # --- KHỞI TẠO CÁC BIẾN TRẠNG THÁI (SESSION STATE) ---
    if 'vai_tro' not in st.session_state: st.session_state['vai_tro'] = None
    if 'chi_so_cau_hien_tai' not in st.session_state: st.session_state['chi_so_cau_hien_tai'] = 0
    if 'diem_so' not in st.session_state: st.session_state['diem_so'] = 0
    if 'danh_sach_cau_hoi' not in st.session_state: st.session_state['danh_sach_cau_hoi'] = []
    
    # Trạng thái trong 1 câu hỏi
    if 'da_nop_cau_nay' not in st.session_state: st.session_state['da_nop_cau_nay'] = False
    if 'lua_chon_cua_hoc_vien' not in st.session_state: st.session_state['lua_chon_cua_hoc_vien'] = None
    if 'thoi_gian_ket_thuc_cau' not in st.session_state: st.session_state['thoi_gian_ket_thuc_cau'] = None

    # ==========================================
    # 1. MÀN HÌNH ĐĂNG NHẬP
    # ==========================================
    if st.session_state['vai_tro'] is None:
        st.title("🎓 Hệ Thống Thi Trắc Nghiệm")
        st.write("Chào mừng bạn! Vui lòng đăng nhập để bắt đầu.")
        
        with st.form("form_dang_nhap"):
            nhap_ten = st.text_input("Tên đăng nhập")
            nhap_mat_khau = st.text_input("Mật khẩu", type="password")
            nut_dang_nhap = st.form_submit_button("Đăng Nhập")
            
            if nut_dang_nhap:
                vai_tro, ho_ten = kiem_tra_dang_nhap(db, nhap_ten, nhap_mat_khau)
                
                if vai_tro == "DA_KHOA":
                    st.error("⛔ TÀI KHOẢN ĐÃ BỊ KHÓA!\nBạn đã hoàn thành bài thi này rồi.")
                elif vai_tro:
                    # Lưu thông tin vào phiên làm việc
                    st.session_state['vai_tro'] = vai_tro
                    st.session_state['ten_dang_nhap'] = nhap_ten
                    st.session_state['ho_ten'] = ho_ten
                    
                    # Đặt lại các chỉ số về 0
                    st.session_state['chi_so_cau_hien_tai'] = 0
                    st.session_state['diem_so'] = 0
                    st.session_state['danh_sach_cau_hoi'] = []
                    st.session_state['da_nop_cau_nay'] = False
                    st.session_state['thoi_gian_ket_thuc_cau'] = None
                    st.rerun()
                else:
                    st.error("❌ Sai tên đăng nhập hoặc mật khẩu!")

    # ==========================================
    # 2. GIAO DIỆN QUẢN TRỊ (ADMIN)
    # ==========================================
    elif st.session_state['vai_tro'] == 'admin':
        st.sidebar.markdown(f"👤 Quản trị viên: **{st.session_state['ho_ten']}**")
        if st.sidebar.button("Đăng xuất"):
            st.session_state['vai_tro'] = None
            st.rerun()
        
        st.header("⚙️ Thêm Câu Hỏi Mới")
        with st.form("form_them_cau_hoi"):
            cau_hoi = st.text_input("Nội dung câu hỏi")
            cot1, cot2 = st.columns(2)
            with cot1:
                da_a = st.text_input("Đáp án A")
                da_b = st.text_input("Đáp án B")
            with cot2:
                da_c = st.text_input("Đáp án C")
                da_d = st.text_input("Đáp án D")
            
            dap_an_dung = st.selectbox("Đáp án ĐÚNG", ["A", "B", "C", "D"])
            giai_thich = st.text_area("Lời giải thích chi tiết")
            
            if st.form_submit_button("Lưu câu hỏi"):
                try:
                    trang_cau_hoi = db.worksheet("CauHoi")
                    # Lưu vào các cột theo đúng thứ tự
                    trang_cau_hoi.append_row([cau_hoi, da_a, da_b, da_c, da_d, dap_an_dung, giai_thich])
                    st.success("✅ Đã thêm câu hỏi thành công!")
                except Exception as loi:
                    st.error(f"Lỗi khi lưu: {loi}")

    # ==========================================
    # 3. GIAO DIỆN HỌC VIÊN
    # ==========================================
    elif st.session_state['vai_tro'] == 'hocvien':
        # Tải câu hỏi nếu chưa có
        if not st.session_state['danh_sach_cau_hoi']:
            try:
                st.session_state['danh_sach_cau_hoi'] = lay_du_lieu_cau_hoi(db)
            except Exception as loi:
                st.error(f"Lỗi tải dữ liệu câu hỏi: {loi}")
                st.stop()
        
        ds_cau_hoi = st.session_state['danh_sach_cau_hoi']
        chi_so = st.session_state['chi_so_cau_hien_tai']

        st.sidebar.markdown(f"👋 Xin chào: **{st.session_state['ho_ten']}**")
        st.sidebar.metric("Điểm số", st.session_state['diem_so'])
        
        # --- XỬ LÝ KHI HẾT CÂU HỎI (NỘP BÀI) ---
        if chi_so >= len(ds_cau_hoi):
            # Lưu kết quả
            ket_qua = luu_ket_qua(db, st.session_state['ten_dang_nhap'], st.session_state['diem_so'])
            
            st.balloons()
            st.success(f"🎉 CHÚC MỪNG BẠN ĐÃ HOÀN THÀNH BÀI THI!")
            st.markdown(f"### 🏆 Kết quả chung cuộc: {st.session_state['diem_so']} / {len(ds_cau_hoi)}")
            
            if ket_qua:
                st.info("💾 Kết quả đã được lưu và tài khoản đã được khóa.")
            else:
                st.error("⚠️ Có lỗi khi lưu điểm. Vui lòng chụp màn hình gửi giáo viên.")

            st.warning("Hệ thống sẽ tự động đăng xuất sau 5 giây...")
            time.sleep(5)
            st.session_state['vai_tro'] = None
            st.rerun()
            return

        # --- HIỂN THỊ CÂU HỎI HIỆN TẠI ---
        du_lieu_cau_hoi = ds_cau_hoi[chi_so]
        
        # Lấy lời giải thích
        loi_giai = ""
        if 'GiaiThich' in du_lieu_cau_hoi:
            loi_giai = str(du_lieu_cau_hoi['GiaiThich'])
        else:
            loi_giai = "Không có giải thích chi tiết."

        st.subheader(f"Câu hỏi số {chi_so + 1}:")
        st.info(f"{du_lieu_cau_hoi['CauHoi']}")

        # --- TRƯỜNG HỢP A: ĐANG LÀM BÀI ---
        if not st.session_state['da_nop_cau_nay']:
            # Xử lý đồng hồ đếm ngược
            if st.session_state['thoi_gian_ket_thuc_cau'] is None:
                st.session_state['thoi_gian_ket_thuc_cau'] = time.time() + THOI_GIAN_MOI_CAU
            
            thoi_gian_con = st.session_state['thoi_gian_ket_thuc_cau'] - time.time()
            
            # Hết giờ tự động nộp
            if thoi_gian_con <= 0:
                st.session_state['da_nop_cau_nay'] = True
                st.session_state['lua_chon_cua_hoc_vien'] = None 
                st.rerun()

            st.progress(max(0.0, min(1.0, thoi_gian_con / THOI_GIAN_MOI_CAU)))
            st.caption(f"⏱️ Thời gian còn lại: {int(thoi_gian_con)} giây")

            with st.form(key=f"form_cau_{chi_so}"):
                cac_lua_chon = [
                    f"A. {du_lieu_cau_hoi['DapAn_A']}", 
                    f"B. {du_lieu_cau_hoi['DapAn_B']}", 
                    f"C. {du_lieu_cau_hoi['DapAn_C']}"
                ]
                # Kiểm tra đáp án D có tồn tại không
                if 'DapAn_D' in du_lieu_cau_hoi and str(du_lieu_cau_hoi['DapAn_D']).strip():
                    cac_lua_chon.append(f"D. {du_lieu_cau_hoi['DapAn_D']}")

                chon = st.radio("Chọn đáp án của bạn:", cac_lua_chon, index=None)
                
                if st.form_submit_button("Chốt Đáp Án"):
                    if chon:
                        st.session_state['lua_chon_cua_hoc_vien'] = chon.split(".")[0] # Lấy A,B,C,D
                        st.session_state['da_nop_cau_nay'] = True
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng chọn một đáp án!")

            time.sleep(1)
            st.rerun()

        # --- TRƯỜNG HỢP B: ĐÃ TRẢ LỜI (HIỆN KẾT QUẢ) ---
        else:
            lua_chon = st.session_state['lua_chon_cua_hoc_vien']
            dap_an_dung = str(du_lieu_cau_hoi['DapAn_Dung']).strip().upper()
            dung_hay_sai = (lua_chon == dap_an_dung)

            if dung_hay_sai:
                st.success(f"✅ CHÍNH XÁC!\n\n💡 **Giải thích:** {loi_giai}")
            elif lua_chon is None:
                st.error(f"⌛ HẾT GIỜ!\n\n👉 Đáp án đúng là: **{dap_an_dung}**\n\n💡 **Giải thích:** {loi_giai}")
            else:
                st.error(f"❌ SAI RỒI (Bạn chọn {lua_chon})\n\n👉 Đáp án đúng là: **{dap_an_dung}**\n\n💡 **Giải thích:** {loi_giai}")

            if st.button("Câu tiếp theo ➡️"):
                if dung_hay_sai:
                    st.session_state['diem_so'] += 1
                
                # Reset trạng thái cho câu mới
                st.session_state['chi_so_cau_hien_tai'] += 1
                st.session_state['da_nop_cau_nay'] = False
                st.session_state['lua_chon_cua_hoc_vien'] = None
                st.session_state['thoi_gian_ket_thuc_cau'] = None
                st.rerun()

if __name__ == "__main__":
    main()