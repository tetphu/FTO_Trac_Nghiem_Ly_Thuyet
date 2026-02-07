import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- CẤU HÌNH ---
THOI_GIAN_MOI_CAU = 30  # Số giây đếm ngược

# --- KẾT NỐI GOOGLE SHEET ---
def ket_noi_csdl():
    # Khai báo phạm vi quyền truy cập
    pham_vi = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Kiểm tra chạy trên Cloud hay Local
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        chung_chi = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, pham_vi)
    else:
        chung_chi = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", pham_vi)
        
    khach_hang = gspread.authorize(chung_chi)
    return khach_hang.open("HeThongTracNghiem")

# --- XỬ LÝ ĐĂNG NHẬP ---
def kiem_tra_dang_nhap(bang_tinh, user, pwd):
    try:
        ws = bang_tinh.worksheet("HocVien")
        tat_ca_dong = ws.get_all_values()
        
        # Duyệt từ dòng 2 (bỏ dòng tiêu đề)
        for dong in tat_ca_dong[1:]:
            if len(dong) < 4: continue

            # Cột 1: Tên đăng nhập | Cột 2: Mật khẩu
            u_sheet = str(dong[0]).strip()
            p_sheet = str(dong[1]).strip()
            
            if u_sheet == str(user).strip() and p_sheet == str(pwd).strip():
                # Cột 5: Trạng thái (DaThi)
                trang_thai = ""
                if len(dong) > 4: 
                    trang_thai = str(dong[4]).strip()
                
                if trang_thai == 'DaThi':
                    return "DA_KHOA", None
                
                # Cột 3: Vai trò | Cột 4: Họ tên
                return str(dong[2]).strip(), str(dong[3]).strip()
                
    except Exception as e:
        st.error(f"Lỗi đăng nhập: {e}")
    return None, None

# --- LƯU KẾT QUẢ ---
def luu_ket_qua(bang_tinh, user, diem):
    try:
        ws = bang_tinh.worksheet("HocVien")
        cell = ws.find(user)
        ws.update_cell(cell.row, 5, "DaThi")
        ws.update_cell(cell.row, 6, str(diem))
        return True
    except Exception as e:
        st.error(f"Lỗi lưu kết quả: {e}")
        return False

# --- LẤY CÂU HỎI ---
def lay_ds_cau_hoi(bang_tinh):
    ws = bang_tinh.worksheet("CauHoi")
    tat_ca = ws.get_all_values()
    return tat_ca[1:]

# --- GIAO DIỆN CHÍNH ---
def main():
    st.set_page_config(page_title="Thi Trắc Nghiệm Online", page_icon="📝")
    
    st.markdown(
        """
        <style>
        .stAlert { padding: 1rem; border-radius: 0.5rem; margin-top: 1rem;}
        .stButton button { width: 100%; margin-top: 10px; font-weight: bold; font-size: 16px;}
        </style>
        """,
        unsafe_allow_html=True
    )

    try:
        db = ket_noi_csdl()
    except Exception as e:
        st.error(f"❌ Lỗi kết nối Google Sheet: {e}")
        st.stop()

    if 'vai_tro' not in st.session_state: st.session_state['vai_tro'] = None
    if 'chi_so' not in st.session_state: st.session_state['chi_so'] = 0
    if 'diem_so' not in st.session_state: st.session_state['diem_so'] = 0
    if 'ds_cau_hoi' not in st.session_state: st.session_state['ds_cau_hoi'] = []
    if 'da_nop_cau' not in st.session_state: st.session_state['da_nop_cau'] = False
    if 'lua_chon' not in st.session_state: st.session_state['lua_chon'] = None
    if 'thoi_gian_het' not in st.session_state: st.session_state['thoi_gian_het'] = None

    # ==========================================
    # 1. MÀN HÌNH ĐĂNG NHẬP
    # ==========================================
    if st.session_state['vai_tro'] is None:
        st.title("🎓 Đăng Nhập Hệ Thống")
        with st.form("form_login"):
            u = st.text_input("Tên đăng nhập")
            p = st.text_input("Mật khẩu", type="password")
            btn = st.form_submit_button("Đăng Nhập")
            
            if btn:
                vai_tro, ho_ten = kiem_tra_dang_nhap(db, u, p)
                if vai_tro == "DA_KHOA":
                    st.error("⛔ Tài khoản này đã thi xong và bị khóa!")
                elif vai_tro:
                    st.session_state['vai_tro'] = vai_tro
                    st.session_state['user'] = u
                    st.session_state['ho_ten'] = ho_ten
                    
                    st.session_state['chi_so'] = 0
                    st.session_state['diem_so'] = 0
                    st.session_state['ds_cau_hoi'] = []
                    st.session_state['da_nop_cau'] = False
                    st.session_state['lua_chon'] = None
                    st.session_state['thoi_gian_het'] = None
                    st.rerun()
                else:
                    st.error("❌ Sai tên đăng nhập hoặc mật khẩu")

    # ==========================================
    # 2. GIAO DIỆN GIẢNG VIÊN (Thay cho Admin)
    # ==========================================
    elif st.session_state['vai_tro'] == 'GiangVien': # <--- ĐÃ ĐỔI TÊN
        st.sidebar.markdown(f"👤 Giảng Viên: **{st.session_state['ho_ten']}**")
        if st.sidebar.button("Đăng xuất"):
            st.session_state['vai_tro'] = None
            st.rerun()
        
        st.header("⚙️ Thêm Câu Hỏi Mới")
        with st.form("form_them_cau"):
            q = st.text_input("Nội dung câu hỏi (Cột 1)")
            c1, c2 = st.columns(2)
            a = c1.text_input("Đáp án A (Cột 2)")
            b = c1.text_input("Đáp án B (Cột 3)")
            c = c2.text_input("Đáp án C (Cột 4)")
            d = c2.text_input("Đáp án D (Cột 5)")
            dung = st.selectbox("Đáp án đúng (Cột 6)", ["A", "B", "C", "D"])
            giai_thich = st.text_area("Giải thích (Cột 7)")
            
            if st.form_submit_button("Lưu câu hỏi"):
                try:
                    ws = db.worksheet("CauHoi")
                    ws.append_row([q, a, b, c, d, dung, giai_thich])
                    st.success("✅ Đã lưu thành công!")
                except Exception as e:
                    st.error(f"Lỗi khi lưu: {e}")

    # ==========================================
    # 3. GIAO DIỆN HỌC VIÊN (Thay cho Student)
    # ==========================================
    elif st.session_state['vai_tro'] == 'hocvien': # <--- ĐÃ ĐỔI TÊN
        if not st.session_state['ds_cau_hoi']:
            try:
                st.session_state['ds_cau_hoi'] = lay_ds_cau_hoi(db)
            except Exception as e:
                st.error(f"Lỗi tải câu hỏi: {e}")
                st.stop()
        
        ds = st.session_state['ds_cau_hoi']
        idx = st.session_state['chi_so']

        if not ds:
            st.warning("⚠️ Chưa có câu hỏi nào trong hệ thống.")
            st.stop()

        st.sidebar.markdown(f"👋 Xin chào: **{st.session_state['ho_ten']}**")
        st.sidebar.metric("Điểm số", st.session_state['diem_so'])

        # --- KẾT THÚC BÀI THI ---
        if idx >= len(ds):
            luu_ket_qua(db, st.session_state['user'], st.session_state['diem_so'])
            st.balloons()
            st.success(f"🎉 HOÀN THÀNH! Điểm số: {st.session_state['diem_so']}/{len(ds)}")
            st.info("Hệ thống sẽ đăng xuất sau vài giây...")
            time.sleep(3)
            st.session_state['vai_tro'] = None
            st.rerun()
            return

        # --- HIỂN THỊ CÂU HỎI ---
        cau = ds[idx]
        while len(cau) < 7: cau.append("")
            
        noi_dung = cau[0]
        da_a = cau[1]
        da_b = cau[2]
        da_c = cau[3]
        da_d = cau[4]
        dap_an_dung = str(cau[5]).strip().upper()
        loi_giai = cau[6]

        st.subheader(f"Câu hỏi {idx + 1}:")
        st.info(noi_dung)

        # --- LOGIC LÀM BÀI ---
        if not st.session_state['da_nop_cau']:
            if st.session_state['thoi_gian_het'] is None:
                st.session_state['thoi_gian_het'] = time.time() + THOI_GIAN_MOI_CAU
            
            con_lai = int(st.session_state['thoi_gian_het'] - time.time())
            if con_lai <= 0:
                st.session_state['da_nop_cau'] = True
                st.session_state['lua_chon'] = None
                st.rerun()

            st.progress(max(0.0, min(1.0, con_lai / THOI_GIAN_MOI_CAU)))
            st.caption(f"⏱️ Còn lại: {con_lai} giây")

            with st.form(f"form_thi_{idx}"):
                opts = [f"A. {da_a}", f"B. {da_b}", f"C. {da_c}"]
                if str(da_d).strip(): 
                    opts.append(f"D. {da_d}")
                
                chon = st.radio("Chọn đáp án:", opts, index=None)
                if st.form_submit_button("Chốt đáp án"):
                    if chon:
                        st.session_state['lua_chon'] = chon.split(".")[0]
                        st.session_state['da_nop_cau'] = True
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng chọn một đáp án!")
            time.sleep(1) 
            st.rerun()

        # --- XEM KẾT QUẢ ---
        else:
            nguoi_chon = st.session_state['lua_chon']
            dap_an_dung = str(dap_an_dung).strip().upper()
            dung = (nguoi_chon == dap_an_dung)

            if dung:
                st.success(f"✅ CHÍNH XÁC!\n\n💡 {loi_giai}")
            elif nguoi_chon is None:
                st.error(f"⌛ HẾT GIỜ!\n\n👉 Đáp án đúng: {dap_an_dung}\n\n💡 {loi_giai}")
            else:
                st.error(f"❌ SAI RỒI! (Bạn chọn {nguoi_chon})\n\n👉 Đáp án đúng: {dap_an_dung}\n\n💡 {loi_giai}")

            if st.button("Câu tiếp theo ➡️"):
                if dung: st.session_state['diem_so'] += 1
                st.session_state['chi_so'] += 1
                st.session_state['da_nop_cau'] = False
                st.session_state['lua_chon'] = None
                st.session_state['thoi_gian_het'] = None
                st.rerun()

    # --- BÁO LỖI NẾU KHÔNG ĐÚNG VAI TRÒ ---
    else:
        st.error(f"⚠️ LỖI VAI TRÒ KHÔNG HỢP LỆ: '{st.session_state['vai_tro']}'")
        st.info("👉 Vui lòng vào Google Sheet, cột 'Vai Trò' và sửa thành 'GiangVien' hoặc 'hocvien'.")
        if st.button("Quay lại đăng nhập"):
            st.session_state['vai_tro'] = None
            st.rerun()

if __name__ == "__main__":
    main()