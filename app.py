import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- CẤU HÌNH ---
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
        st.error(f"Lỗi kết nối Google Sheet: {str(e)}")
        return None

# --- XỬ LÝ ĐĂNG NHẬP ---
def kiem_tra_dang_nhap(bang_tinh, user, pwd):
    try:
        ws = bang_tinh.worksheet("HocVien")
        tat_ca_dong = ws.get_all_values()
        # Bỏ dòng tiêu đề, duyệt từ dòng 2
        for dong in tat_ca_dong[1:]:
            if len(dong) < 4: continue # Bỏ qua dòng lỗi/thiếu dữ liệu
            
            # Cột 1 (index 0): User | Cột 2 (index 1): Pass
            u_sheet = str(dong[0]).strip()
            p_sheet = str(dong[1]).strip()
            
            if u_sheet == str(user).strip() and p_sheet == str(pwd).strip():
                # Cột 5 (index 4): Trạng thái
                trang_thai = str(dong[4]).strip() if len(dong) > 4 else ""
                if trang_thai == 'DaThi': return "DA_KHOA", None
                
                # Cột 3 (index 2): Vai trò | Cột 4 (index 3): Họ tên
                return str(dong[2]).strip(), str(dong[3]).strip()
    except Exception as e:
        st.error(f"Lỗi truy xuất dữ liệu Học Viên: {str(e)}")
    return None, None

# --- LƯU KẾT QUẢ ---
def luu_ket_qua(bang_tinh, user, diem):
    try:
        ws = bang_tinh.worksheet("HocVien")
        cell = ws.find(user)
        ws.update_cell(cell.row, 5, "DaThi")
        ws.update_cell(cell.row, 6, str(diem))
        return True
    except:
        return False

# --- GIAO DIỆN CHÍNH ---
def main():
    st.set_page_config(page_title="Thi Trắc Nghiệm Online", page_icon="📝")
    
    # CSS
    st.markdown("""<style>.stButton button { width: 100%; margin-top: 10px; font-weight: bold; font-size: 16px;}</style>""", unsafe_allow_html=True)

    # Khởi tạo Session State
    if 'vai_tro' not in st.session_state: st.session_state['vai_tro'] = None
    if 'chi_so' not in st.session_state: st.session_state['chi_so'] = 0
    if 'diem_so' not in st.session_state: st.session_state['diem_so'] = 0
    if 'ds_cau_hoi' not in st.session_state: st.session_state['ds_cau_hoi'] = []
    if 'da_nop_cau' not in st.session_state: st.session_state['da_nop_cau'] = False
    if 'lua_chon' not in st.session_state: st.session_state['lua_chon'] = None
    if 'thoi_gian_het' not in st.session_state: st.session_state['thoi_gian_het'] = None

    db = ket_noi_csdl()
    if db is None: st.stop()

    # --- 1. MÀN HÌNH ĐĂNG NHẬP ---
    if st.session_state['vai_tro'] is None:
        st.title("🎓 Đăng Nhập Hệ Thống")
        with st.form("form_login"):
            u = st.text_input("Tên đăng nhập")
            p = st.text_input("Mật khẩu", type="password")
            if st.form_submit_button("Đăng Nhập"):
                vt, ten = kiem_tra_dang_nhap(db, u, p)
                if vt == "DA_KHOA": st.error("⛔ Tài khoản đã thi xong!")
                elif vt:
                    st.session_state['vai_tro'] = vt
                    st.session_state['user'] = u
                    st.session_state['ho_ten'] = ten
                    st.rerun()
                else: st.error("❌ Sai thông tin đăng nhập")

    # --- 2. ADMIN ---
    elif st.session_state['vai_tro'] == 'admin':
        st.sidebar.write(f"Xin chào: {st.session_state['ho_ten']}")
        if st.sidebar.button("Đăng xuất"):
            st.session_state['vai_tro'] = None
            st.rerun()
        st.header("⚙️ Thêm Câu Hỏi")
        with st.form("add"):
            q = st.text_input("Câu hỏi")
            c1, c2 = st.columns(2)
            a, b = c1.text_input("Đáp án A"), c1.text_input("Đáp án B")
            c, d = c2.text_input("Đáp án C"), c2.text_input("Đáp án D")
            dung = st.selectbox("Đáp án đúng", ["A", "B", "C", "D"])
            gt = st.text_area("Giải thích")
            if st.form_submit_button("Lưu"):
                try:
                    db.worksheet("CauHoi").append_row([q, a, b, c, d, dung, gt])
                    st.success("Đã lưu!")
                except Exception as e: st.error(f"Lỗi lưu: {e}")

    # --- 3. HỌC VIÊN (CÓ CHẾ ĐỘ DÒ LỖI) ---
    elif st.session_state['vai_tro'] == 'hocvien':
        try: # Bắt lỗi toàn cục để tránh trắng màn hình
            
            # Tải câu hỏi
            if not st.session_state['ds_cau_hoi']:
                try:
                    ws_q = db.worksheet("CauHoi")
                    # Lấy dữ liệu, bỏ dòng đầu tiên (tiêu đề)
                    data = ws_q.get_all_values()
                    if len(data) > 1:
                        st.session_state['ds_cau_hoi'] = data[1:]
                    else:
                        st.warning("⚠️ Sheet 'CauHoi' đang trống hoặc chỉ có tiêu đề!")
                        st.stop()
                except Exception as e:
                    st.error(f"❌ Lỗi tải dữ liệu từ Sheet 'CauHoi': {e}")
                    st.info("💡 Gợi ý: Kiểm tra xem tab 'CauHoi' có tồn tại và đúng tên không?")
                    st.stop()

            ds = st.session_state['ds_cau_hoi']
            idx = st.session_state['chi_so']

            if not ds:
                st.warning("⚠️ Hệ thống chưa có câu hỏi nào.")
                st.stop()

            # Kết thúc bài thi
            if idx >= len(ds):
                luu_ket_qua(db, st.session_state['user'], st.session_state['diem_so'])
                st.balloons()
                st.success(f"Hoàn thành! Điểm: {st.session_state['diem_so']}/{len(ds)}")
                time.sleep(3)
                st.session_state['vai_tro'] = None
                st.rerun()
                return

            # Hiển thị câu hỏi
            cau = ds[idx]
            # Tự động điền trống nếu thiếu cột (Tránh lỗi Index Error)
            while len(cau) < 7: cau.append("") 
            
            st.subheader(f"Câu hỏi {idx + 1}:")
            st.info(cau[0]) # Cột 1: Câu hỏi

            if not st.session_state['da_nop_cau']:
                if st.session_state['thoi_gian_het'] is None:
                    st.session_state['thoi_gian_het'] = time.time() + THOI_GIAN_MOI_CAU
                
                con_lai = int(st.session_state['thoi_gian_het'] - time.time())
                if con_lai <= 0:
                    st.session_state['da_nop_cau'] = True
                    st.rerun()
                
                st.progress(max(0.0, min(1.0, con_lai/THOI_GIAN_MOI_CAU)))
                st.caption(f"⏱️ Còn lại: {con_lai} giây")

                with st.form(f"f_{idx}"):
                    opts = [f"A. {cau[1]}", f"B. {cau[2]}", f"C. {cau[3]}"]
                    if cau[4].strip(): opts.append(f"D. {cau[4]}")
                    
                    chon = st.radio("Chọn đáp án:", opts, index=None)
                    if st.form_submit_button("Chốt đáp án"):
                        if chon:
                            st.session_state['lua_chon'] = chon.split(".")[0]
                            st.session_state['da_nop_cau'] = True
                            st.rerun()
                        else: st.warning("Vui lòng chọn!")
                time.sleep(1)
                st.rerun()
            else:
                nguoi_chon = st.session_state['lua_chon']
                dap_an_dung = str(cau[5]).strip().upper()
                dung = (nguoi_chon == dap_an_dung)

                if dung: st.success(f"✅ CHÍNH XÁC!\n\n💡 {cau[6]}")
                elif nguoi_chon is None: st.error(f"⌛ HẾT GIỜ!\n\n👉 Đáp án đúng: {dap_an_dung}\n\n💡 {cau[6]}")
                else: st.error(f"❌ SAI! Đáp án là {dap_an_dung}\n\n💡 {cau[6]}")
                
                if st.button("Câu tiếp theo"):
                    if dung: st.session_state['diem_so'] += 1
                    st.session_state['chi_so'] += 1
                    st.session_state['da_nop_cau'] = False
                    st.session_state['thoi_gian_het'] = None
                    st.rerun()

        except Exception as e:
            # Đây là dòng quan trọng nhất: Hiện lỗi ra màn hình thay vì trắng xóa
            st.error(f"🚨 ĐÃ CÓ LỖI XẢY RA: {e}")
            st.write("Vui lòng chụp màn hình này gửi cho Admin để sửa lỗi.")

if __name__ == "__main__":
    main()