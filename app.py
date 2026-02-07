import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
from datetime import datetime

# --- CẤU HÌNH ---
THOI_GIAN_MOI_CAU = 30 

# --- HÀM KẾT NỐI ---
def ket_noi_csdl():
    pham_vi = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        chung_chi = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, pham_vi)
    else:
        chung_chi = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", pham_vi)
    khach_hang = gspread.authorize(chung_chi)
    return khach_hang.open("HeThongTracNghiem")

# --- XỬ LÝ ĐĂNG NHẬP (Sửa key sang Tiếng Việt) ---
def kiem_tra_dang_nhap(bang_tinh, ten_dang_nhap, mat_khau):
    try:
        trang_hoc_vien = bang_tinh.worksheet("HocVien")
        danh_sach = trang_hoc_vien.get_all_records()
        
        for ban_ghi in danh_sach:
            # Code mới: Dùng key 'Tên Đăng Nhập' và 'Mật Khẩu'
            u_sheet = str(ban_ghi.get('Tên Đăng Nhập', '')).strip()
            p_sheet = str(ban_ghi.get('Mật Khẩu', '')).strip()
            
            if u_sheet == str(ten_dang_nhap).strip() and p_sheet == str(mat_khau).strip():
                trang_thai = str(ban_ghi.get('Trạng Thái', '')).strip()
                if trang_thai == 'DaThi':
                    return "DA_KHOA", None 
                
                # Code mới: Dùng key 'Vai Trò' và 'Họ Tên'
                return ban_ghi.get('Vai Trò'), ban_ghi.get('Họ Tên')
    except Exception as e:
        st.error(f"Lỗi đăng nhập: {e}")
    return None, None

# --- LƯU KẾT QUẢ (Sửa cột lưu) ---
def luu_ket_qua(bang_tinh, ten_dang_nhap, diem_so):
    try:
        trang_hoc_vien = bang_tinh.worksheet("HocVien")
        # Tìm dòng chứa tên đăng nhập
        o_tim_thay = trang_hoc_vien.find(ten_dang_nhap)
        # Cập nhật cột E (5) và F (6) - Lưu ý: Nếu bạn thêm cột thì số này phải sửa
        # Cột 'Trạng Thái' là cột thứ 5
        trang_hoc_vien.update_cell(o_tim_thay.row, 5, "DaThi")
        # Cột 'Điểm Số' là cột thứ 6
        trang_hoc_vien.update_cell(o_tim_thay.row, 6, str(diem_so))
        return True
    except Exception as e:
        st.error(f"Lỗi lưu: {e}")
        return False

def lay_du_lieu_cau_hoi(bang_tinh):
    return bang_tinh.worksheet("CauHoi").get_all_records()

# --- GIAO DIỆN CHÍNH ---
def main():
    st.set_page_config(page_title="Thi Trắc Nghiệm", page_icon="🇻🇳")
    st.markdown("""
        <style>
        .stAlert { padding: 1rem; border-radius: 0.5rem; margin-top: 1rem;}
        .stButton button { width: 100%; margin-top: 10px; font-weight: bold; font-size: 16px;}
        </style>
    """, unsafe_allow_html=True)

    try:
        db = ket_noi_csdl()
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        st.stop()

    if 'vai_tro' not in st.session_state: st.session_state['vai_tro'] = None
    if 'chi_so' not in st.session_state: st.session_state['chi_so'] = 0
    if 'diem_so' not in st.session_state: st.session_state['diem_so'] = 0
    if 'ds_cau_hoi' not in st.session_state: st.session_state['ds_cau_hoi'] = []
    if 'da_nop' not in st.session_state: st.session_state['da_nop'] = False
    if 'lua_chon' not in st.session_state: st.session_state['lua_chon'] = None
    if 'thoi_gian_het' not in st.session_state: st.session_state['thoi_gian_het'] = None

    # --- 1. MÀN HÌNH ĐĂNG NHẬP ---
    if st.session_state['vai_tro'] is None:
        st.title("🎓 Đăng Nhập Hệ Thống")
        with st.form("dang_nhap"):
            u = st.text_input("Tên đăng nhập")
            p = st.text_input("Mật khẩu", type="password")
            if st.form_submit_button("Đăng Nhập"):
                vt, ten = kiem_tra_dang_nhap(db, u, p)
                if vt == "DA_KHOA":
                    st.error("⛔ Bạn đã thi rồi, tài khoản đang bị khóa!")
                elif vt:
                    st.session_state['vai_tro'] = vt
                    st.session_state['user'] = u
                    st.session_state['name'] = ten
                    st.session_state['chi_so'] = 0
                    st.session_state['diem_so'] = 0
                    st.session_state['ds_cau_hoi'] = []
                    st.session_state['da_nop'] = False
                    st.session_state['thoi_gian_het'] = None
                    st.rerun()
                else:
                    st.error("❌ Sai thông tin đăng nhập")

    # --- 2. GIAO DIỆN ADMIN ---
    elif st.session_state['vai_tro'] == 'admin':
        st.sidebar.write(f"Xin chào: **{st.session_state['name']}**")
        if st.sidebar.button("Đăng xuất"):
            st.session_state['vai_tro'] = None
            st.rerun()
        
        st.header("⚙️ Thêm Câu Hỏi Mới")
        with st.form("them_cau"):
            q = st.text_input("Câu Hỏi")
            c1, c2 = st.columns(2)
            a = c1.text_input("Đáp Án A")
            b = c1.text_input("Đáp Án B")
            c = c2.text_input("Đáp Án C")
            d = c2.text_input("Đáp Án D")
            dung = st.selectbox("Đáp Án Đúng", ["A", "B", "C", "D"])
            giai_thich = st.text_area("Giải Thích")
            
            if st.form_submit_button("Lưu"):
                try:
                    ws = db.worksheet("CauHoi")
                    ws.append_row([q, a, b, c, d, dung, giai_thich])
                    st.success("Đã lưu thành công!")
                except Exception as e:
                    st.error(f"Lỗi: {e}")

    # --- 3. GIAO DIỆN HỌC VIÊN ---
    elif st.session_state['vai_tro'] == 'hocvien':
        if not st.session_state['ds_cau_hoi']:
            st.session_state['ds_cau_hoi'] = lay_du_lieu_cau_hoi(db)
        
        ds = st.session_state['ds_cau_hoi']
        idx = st.session_state['chi_so']

        st.sidebar.write(f"Thí sinh: **{st.session_state['name']}**")
        st.sidebar.write(f"Điểm: **{st.session_state['diem_so']}**")

        # KẾT THÚC
        if idx >= len(ds):
            luu_ket_qua(db, st.session_state['user'], st.session_state['diem_so'])
            st.balloons()
            st.success(f"Hoàn thành! Điểm: {st.session_state['diem_so']}/{len(ds)}")
            st.info("Đang đăng xuất...")
            time.sleep(3)
            st.session_state['vai_tro'] = None
            st.rerun()
            return

        # HIỂN THỊ CÂU HỎI
        cau = ds[idx]
        # Code mới: Gọi đúng tên cột Tiếng Việt
        noi_dung = cau.get('Câu Hỏi', '')
        da_a = cau.get('Đáp Án A', '')
        da_b = cau.get('Đáp Án B', '')
        da_c = cau.get('Đáp Án C', '')
        da_d = cau.get('Đáp Án D', '')
        # Lưu ý: Nếu cột giải thích bạn đặt tên khác thì sửa ở đây
        loi_giai = cau.get('Giải Thích', 'Không có giải thích')

        st.subheader(f"Câu {idx+1}:")
        st.info(noi_dung)

        # LOGIC THI
        if not st.session_state['da_nop']:
            if st.session_state['thoi_gian_het'] is None:
                st.session_state['thoi_gian_het'] = time.time() + THOI_GIAN_MOI_CAU
            
            con_lai = st.session_state['thoi_gian_het'] - time.time()
            if con_lai <= 0:
                st.session_state['da_nop'] = True
                st.session_state['lua_chon'] = None
                st.rerun()
            
            st.progress(max(0.0, min(1.0, con_lai/THOI_GIAN_MOI_CAU)))
            
            with st.form(f"f_{idx}"):
                opts = [f"A. {da_a}", f"B. {da_b}", f"C. {da_c}"]
                if str(da_d).strip(): opts.append(f"D. {da_d}")
                
                chon = st.radio("Chọn đáp án:", opts, index=None)
                if st.form_submit_button("Trả Lời"):
                    if chon:
                        st.session_state['lua_chon'] = chon.split(".")[0]
                        st.session_state['da_nop'] = True
                        st.rerun()
                    else:
                        st.warning("Vui lòng chọn đáp án!")
            time.sleep(1)
            st.rerun()
        
        else:
            # XEM KẾT QUẢ
            nguoi_chon = st.session_state['lua_chon']
            # Code mới: Gọi đúng tên cột Tiếng Việt 'Đáp Án Đúng'
            dap_an_dung = str(cau.get('Đáp Án Đúng', '')).strip().upper()
            
            if nguoi_chon == dap_an_dung:
                st.success(f"CHÍNH XÁC! \n\n{loi_giai}")
                dung = True
            else:
                st.error(f"SAI RỒI! Đáp án đúng là {dap_an_dung} \n\n{loi_giai}")
                dung = False
            
            if st.button("Câu Tiếp Theo"):
                if dung: st.session_state['diem_so'] += 1
                st.session_state['chi_so'] += 1
                st.session_state['da_nop'] = False
                st.session_state['thoi_gian_het'] = None
                st.rerun()

if __name__ == "__main__":
    main()