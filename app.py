import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import time
import random # <--- THƯ VIỆN MỚI ĐỂ TRỘN CÂU HỎI

# --- 1. CẤU HÌNH ---
THOI_GIAN_MOI_CAU = 30
SO_CAU_THI_THU = 10

# --- 2. HÀM GIAO DIỆN ---
def inject_css():
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem; padding-bottom: 3rem; padding-left: 0.5rem; padding-right: 0.5rem; }
        header, footer { visibility: hidden; }
        .stApp { background-color: #ffffff; }
        .gcpd-title {
            font-family: 'Arial Black', sans-serif; color: #002147; 
            font-size: 24px; text-transform: uppercase;
            margin-top: 5px; line-height: 1.2; font-weight: 900;
            text-align: center; text-shadow: 1px 1px 0px #ffffff;
        }
        [data-testid="stForm"] {
            background-color: #ffffff; border: 2px solid #002147; 
            border-radius: 10px; padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .lesson-card {
            background-color: #ffffff; border-left: 6px solid #002147; 
            padding: 15px; margin-bottom: 15px; border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); color: #333333;
        }
        .lesson-title { color: #002147; font-size: 18px; font-weight: bold; margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 5px; }
        .lesson-content { font-size: 15px; line-height: 1.6; color: #333; white-space: pre-wrap; }
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
            background-color: #ffffff !important; color: #002147 !important; 
            border: 1px solid #002147 !important; border-radius: 5px !important;
        }
        .stTextInput label, .stSelectbox label, .stRadio label { color: #002147 !important; font-weight: bold !important; }
        .stRadio div[role="radiogroup"] { color: #333333; }
        .stButton button {
            background-color: #002147 !important; color: #FFD700 !important; 
            font-weight: bold !important; width: 100%; padding: 12px !important;
            border-radius: 8px !important; border: none !important;
        }
        .stButton button:hover { background-color: #003366 !important; }
        .stProgress > div > div > div > div { background-color: #002147 !important; }
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

# --- 4. CÁC HÀM XỬ LÝ DỮ LIỆU ---
def kiem_tra_dang_nhap(db, user, pwd):
    try:
        ws = db.worksheet("HocVien")
        rows = ws.get_all_values()
        for row in rows[1:]:
            if len(row) < 4: continue
            if str(row[0]).strip() == str(user).strip() and str(row[1]).strip() == str(pwd).strip():
                status = str(row[4]).strip() if len(row) > 4 else ""
                role = str(row[2]).strip()
                name = str(row[3]).strip()
                return role, name, status # Trả về cả trạng thái để xử lý quyền thi
    except: pass
    return None, None, None

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

def reset_trang_thai_thi():
    # Hàm tiện ích để reset lại điểm và câu hỏi khi chuyển đổi giữa Thi thử và Thi thật
    st.session_state.update(chi_so=0, diem_so=0, ds_cau_hoi=[], da_nop_cau=False, bat_dau=False, thoi_gian_het=None, lua_chon=None, che_do_thi=None)

# --- 5. CHƯƠNG TRÌNH CHÍNH ---
def main():
    st.set_page_config(page_title="FTO System", page_icon="🚓", layout="centered")
    inject_css() 

    # Cập nhật Session State thêm biến che_do_thi và trang_thai
    if 'vai_tro' not in st.session_state: 
        st.session_state.update(vai_tro=None, user="", ho_ten="", trang_thai="", chi_so=0, diem_so=0, ds_cau_hoi=[], da_nop_cau=False, bat_dau=False, thoi_gian_het=None, lua_chon=None, che_do_thi=None)

    db = ket_noi_csdl()
    if not db: st.stop()

    # --- A. MÀN HÌNH ĐĂNG NHẬP ---
    if st.session_state['vai_tro'] is None:
        with st.form("login"):
            c1, c2 = st.columns([1, 2.5])
            with c1: st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", use_column_width=True)
            with c2: st.markdown('<div class="gcpd-title">GACHA CITY<BR>POLICE DEPT<BR>ACADEMY</div>', unsafe_allow_html=True)
            st.divider()
            
            st.markdown("<h4 style='text-align: center; color: #002147;'>▼ ĐĂNG NHẬP HỆ THỐNG</h4>", unsafe_allow_html=True)
            u = st.text_input("SỐ HIỆU (Momo)")
            p = st.text_input("MÃ BẢO MẬT", type="password")
            
            if st.form_submit_button("XÁC THỰC DANH TÍNH"):
                vt, ten, tt = kiem_tra_dang_nhap(db, u, p)
                if vt:
                    # Cho phép đăng nhập dù trạng thái là gì, chỉ giới hạn lúc vào phòng thi
                    st.session_state.update(vai_tro=vt, user=u, ho_ten=ten, trang_thai=tt)
                    st.rerun()
                else: st.error("❌ SAI THÔNG TIN ĐĂNG NHẬP")

    # --- B. ĐÃ ĐĂNG NHẬP ---
    else:
        with st.sidebar:
            st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", width=100)
            st.markdown(f"### 👮 {st.session_state['ho_ten']}")
            st.markdown(f"<span style='background-color:#002147; color:#FFD700; padding: 4px 8px; border-radius: 4px; font-weight:bold; font-size: 12px;'>{st.session_state['vai_tro']}</span>", unsafe_allow_html=True)
            
            if st.session_state['bat_dau']:
                st.divider()
                st.metric("🏆 ĐIỂM SỐ", f"{st.session_state['diem_so']}")
            st.divider()
            
            # PHÂN QUYỀN MENU CHÍNH
            if st.session_state['vai_tro'] == 'GiangVien':
                ds_chuc_nang = ["📖 GIÁO TRÌNH FTO", "⚙️ QUẢN LÝ CÂU HỎI", "👥 QUẢN LÝ HỌC VIÊN"]
            else:
                ds_chuc_nang = ["📖 GIÁO TRÌNH FTO", "🎯 THI THỬ (ÔN TẬP)", "📝 THI CHÍNH THỨC"]
            
            menu = st.radio("MENU CHỨC NĂNG", ds_chuc_nang, on_change=reset_trang_thai_thi) # Reset khi đổi menu
            
            st.write(""); st.write("")
            if st.button("ĐĂNG XUẤT"):
                for key in list(st.session_state.keys()): del st.session_state[key]
                st.rerun()

        # ==========================================
        # 1. GIÁO TRÌNH (Ai cũng xem được)
        # ==========================================
        if menu == "📖 GIÁO TRÌNH FTO":
            st.markdown("<h2 style='color:#002147;'>📚 TÀI LIỆU NỘI BỘ</h2>", unsafe_allow_html=True)
            ds_bai = lay_giao_trinh(db)
            if not ds_bai: st.warning("Chưa có bài giảng.")
            else:
                for bai in ds_bai:
                    with st.container():
                        st.markdown(f"""
                        <div class="lesson-card">
                            <div class="lesson-title">{bai['BaiHoc']}</div>
                            <div class="lesson-content">{bai['NoiDung']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        if str(bai['HinhAnh']).startswith("http"): st.image(bai['HinhAnh'], use_column_width=True)
                        st.divider()

        # ==========================================
        # 2A. QUẢN LÝ CÂU HỎI (CHỈ GV)
        # ==========================================
        elif menu == "⚙️ QUẢN LÝ CÂU HỎI":
            st.markdown("<h2 style='color:#002147;'>⚙️ NGÂN HÀNG CÂU HỎI</h2>", unsafe_allow_html=True)
            st.caption("💡 Sửa trực tiếp vào bảng. Bấm '+' để thêm. Chọn dòng và bấm Delete để xóa.")
            
            ws_cauhoi = db.worksheet("CauHoi")
            all_values = ws_cauhoi.get_all_values()
            headers = ["CauHoi", "A", "B", "C", "D", "DapAn_Dung", "GiaiThich"]
            
            df = pd.DataFrame(all_values[1:], columns=headers) if len(all_values) > 1 else pd.DataFrame(columns=headers)
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, height=500)

            if st.button("💾 LƯU CÂU HỎI", type="primary"):
                with st.spinner("Đang lưu..."):
                    try:
                        ws_cauhoi.clear()
                        ws_cauhoi.update([headers] + edited_df.values.tolist())
                        st.success("✅ Đã cập nhật ngân hàng câu hỏi!")
                        time.sleep(1); st.rerun()
                    except Exception as e: st.error(f"Lỗi khi lưu: {e}")

        # ==========================================
        # 2B. QUẢN LÝ HỌC VIÊN (CHỈ GV - CẤP QUYỀN THI TẠI ĐÂY)
        # ==========================================
        elif menu == "👥 QUẢN LÝ HỌC VIÊN":
            st.markdown("<h2 style='color:#002147;'>👥 DANH SÁCH SĨ QUAN (HỌC VIÊN)</h2>", unsafe_allow_html=True)
            st.info("💡 Để cấp quyền thi chính thức, hãy gõ chữ **DuocThi** vào cột TrangThai. Nếu muốn cho thi lại, hãy xóa trắng cột TrangThai.")
            
            ws_hv = db.worksheet("HocVien")
            all_hv = ws_hv.get_all_values()
            # Cấu trúc: 0:User, 1:Pass, 2:Role, 3:Name, 4:Status, 5:Score
            headers_hv = ["Username (Momo)", "Password", "Role", "HoTen", "TrangThai", "Diem"]
            
            # Đảm bảo dữ liệu đủ cột để cho vào bảng
            padded_data = []
            for row in all_hv[1:]:
                while len(row) < 6: row.append("")
                padded_data.append(row[:6])

            df_hv = pd.DataFrame(padded_data, columns=headers_hv)
            edited_hv = st.data_editor(df_hv, num_rows="dynamic", use_container_width=True, height=500)

            if st.button("💾 CẬP NHẬT HỒ SƠ", type="primary"):
                with st.spinner("Đang lưu..."):
                    try:
                        ws_hv.clear()
                        ws_hv.update([headers_hv] + edited_hv.values.tolist())
                        st.success("✅ Đã cập nhật quyền lợi và trạng thái học viên!")
                        time.sleep(1); st.rerun()
                    except Exception as e: st.error(f"Lỗi: {e}")

        # ==========================================
        # 3A. THI THỬ (CHỈ HỌC VIÊN)
        # ==========================================
        elif menu == "🎯 THI THỬ (ÔN TẬP)":
            st.session_state['che_do_thi'] = 'THU'
            
            if not st.session_state['bat_dau']:
                with st.form("start_mock"):
                    st.markdown("<h3 style='color:#002147; text-align:center;'>🎯 CHẾ ĐỘ THI THỬ</h3>", unsafe_allow_html=True)
                    st.info(f"Chế độ này sẽ chọn ngẫu nhiên **{SO_CAU_THI_THU} câu hỏi** từ ngân hàng. Điểm số KHÔNG bị ghi nhận vào hồ sơ.")
                    if st.form_submit_button("BẮT ĐẦU THI THỬ", type="primary"):
                        st.session_state['bat_dau'] = True
                        st.rerun()
            else:
                # Trộn ngẫu nhiên câu hỏi (Chỉ làm 1 lần khi bắt đầu)
                if not st.session_state['ds_cau_hoi']:
                    raw = db.worksheet("CauHoi").get_all_values()
                    all_questions = raw[1:] if len(raw) > 1 else []
                    if len(all_questions) < SO_CAU_THI_THU:
                        st.session_state['ds_cau_hoi'] = all_questions # Lấy hết nếu không đủ số lượng
                    else:
                        st.session_state['ds_cau_hoi'] = random.sample(all_questions, SO_CAU_THI_THU)

                ds = st.session_state['ds_cau_hoi']
                idx = st.session_state['chi_so']

                if idx >= len(ds):
                    st.balloons()
                    st.success(f"🎉 HOÀN THÀNH BÀI THI THỬ: {st.session_state['diem_so']}/{len(ds)}")
                    if st.button("VỀ LẠI TRANG CHỦ"):
                        reset_trang_thai_thi()
                        st.rerun()
                    st.stop()

                cau = ds[idx]
                while len(cau) < 7: cau.append("")

                if not st.session_state['da_nop_cau']:
                    if st.session_state['thoi_gian_het'] is None: st.session_state['thoi_gian_het'] = time.time() + THOI_GIAN_MOI_CAU
                    con_lai = int(st.session_state['thoi_gian_het'] - time.time())
                    if con_lai <= 0: st.session_state['da_nop_cau'] = True; st.session_state['lua_chon'] = None; st.rerun()

                    c_time, c_score = st.columns([2.5,1])
                    c_time.progress(max(0.0, min(1.0, con_lai/THOI_GIAN_MOI_CAU))); c_time.caption(f"⏳ {con_lai}s")
                    c_score.markdown(f"**Đ: {st.session_state['diem_so']}**")

                    with st.form(f"mock_q_{idx}"):
                        st.markdown(f"<h5 style='color:#002147'>Câu {idx+1}/{len(ds)}: {cau[0]}</h5>", unsafe_allow_html=True)
                        opts = [f"A. {cau[1]}", f"B. {cau[2]}", f"C. {cau[3]}"]
                        if str(cau[4]).strip(): opts.append(f"D. {cau[4]}")
                        chon = st.radio("Lựa chọn:", opts, index=None)
                        if st.form_submit_button("CHỐT ĐÁP ÁN"):
                            if chon: 
                                st.session_state['lua_chon'] = chon.split(".")[0]
                                st.session_state['da_nop_cau'] = True
                                st.rerun()
                            else: st.warning("Vui lòng chọn đáp án!")
                    time.sleep(1); st.rerun()
                else:
                    nguoi_chon = st.session_state['lua_chon']
                    dap_an_dung = str(cau[5]).strip().upper()
                    if nguoi_chon == dap_an_dung: st.success("✅ CHÍNH XÁC!")
                    else: st.error(f"❌ SAI RỒI! Đáp án đúng: {dap_an_dung}")
                    if str(cau[6]).strip(): st.info(f"💡 Giải thích: {cau[6]}")
                    
                    if st.button("CÂU TIẾP THEO"):
                        if nguoi_chon == dap_an_dung: st.session_state['diem_so'] += 1
                        st.session_state['chi_so'] += 1; st.session_state['da_nop_cau'] = False
                        st.session_state['thoi_gian_het'] = None
                        st.rerun()

        # ==========================================
        # 3B. THI CHÍNH THỨC (CHỈ HỌC VIÊN ĐƯỢC CẤP QUYỀN)
        # ==========================================
        elif menu == "📝 THI CHÍNH THỨC":
            # --- KIỂM TRA QUYỀN THI TRƯỚC TIÊN ---
            # Lấy trạng thái mới nhất từ database đề phòng giảng viên vừa cập nhật
            ws_check = db.worksheet("HocVien")
            cell_user = ws_check.find(st.session_state['user'])
            trang_thai_hien_tai = ws_check.cell(cell_user.row, 5).value if cell_user else ""
            
            if trang_thai_hien_tai == 'DaThi':
                st.error("⛔ Bạn đã hoàn thành bài thi chính thức. Hồ sơ đã được lưu.")
                st.stop()
            elif trang_thai_hien_tai == 'VI_PHAM':
                st.error("🚨 HỒ SƠ BỊ KHÓA!")
                st.warning("Hệ thống ghi nhận bạn đã thoát khỏi ứng dụng trong quá trình làm bài thi trước đó.")
                st.stop()
            elif trang_thai_hien_tai != 'DuocThi' and trang_thai_hien_tai != 'DangThi':
                # Nếu không phải 'DuocThi' hoặc đang thi dở ('DangThi') thì chặn
                st.warning("🔒 BẠN CHƯA ĐƯỢC CẤP QUYỀN THI")
                st.info("Vui lòng ôn tập ở phần 'Thi Thử' và liên hệ FTO Manager/Giảng Viên để được cấp quyền mở khóa bài thi chính thức.")
                st.stop()

            # --- VÀO THI CHÍNH THỨC ---
            st.session_state['che_do_thi'] = 'THAT'

            if not st.session_state['bat_dau']:
                with st.form("start_exam"):
                    c1, c2 = st.columns([1, 2.5])
                    with c1: st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", use_column_width=True)
                    with c2: st.markdown('<div class="gcpd-title">BÀI THI CHÍNH THỨC</div>', unsafe_allow_html=True)
                    st.divider()
                    st.warning("⚠️ LƯU Ý QUAN TRỌNG:\n\n1. Thời gian tính ngay khi bấm bắt đầu.\n2. Nếu thoát ra giữa chừng, bài thi sẽ bị HỦY và KHÓA HỒ SƠ.\n3. Điểm số sẽ được ghi vào học bạ.")
                    
                    if st.form_submit_button("BẮT ĐẦU LÀM BÀI", type="primary"):
                        danh_dau_dang_thi(db, st.session_state['user'])
                        st.session_state['bat_dau'] = True
                        st.rerun()
            else:
                if not st.session_state['ds_cau_hoi']:
                    raw = db.worksheet("CauHoi").get_all_values()
                    st.session_state['ds_cau_hoi'] = raw[1:] if len(raw) > 1 else []
                
                ds = st.session_state['ds_cau_hoi']
                idx = st.session_state['chi_so']

                if idx >= len(ds):
                    st.balloons(); st.success(f"KẾT QUẢ CUỐI CÙNG: {st.session_state['diem_so']}/{len(ds)}")
                    if st.button("NỘP HỒ SƠ"):
                        luu_ket_qua(db, st.session_state['user'], st.session_state['diem_so'])
                        reset_trang_thai_thi()
                        st.rerun()
                    st.stop()

                cau = ds[idx]
                while len(cau) < 7: cau.append("")

                if not st.session_state['da_nop_cau']:
                    if st.session_state['thoi_gian_het'] is None: st.session_state['thoi_gian_het'] = time.time() + THOI_GIAN_MOI_CAU
                    con_lai = int(st.session_state['thoi_gian_het'] - time.time())
                    if con_lai <= 0: st.session_state['da_nop_cau'] = True; st.session_state['lua_chon'] = None; st.rerun()

                    c_time, c_score = st.columns([2.5,1])
                    c_time.progress(max(0.0, min(1.0, con_lai/THOI_GIAN_MOI_CAU))); c_time.caption(f"⏳ {con_lai}s")
                    c_score.markdown(f"**Đ: {st.session_state['diem_so']}**")

                    with st.form(f"real_q_{idx}"):
                        st.markdown(f"<h5 style='color:#002147'>Câu {idx+1}: {cau[0]}</h5>", unsafe_allow_html=True)
                        opts = [f"A. {cau[1]}", f"B. {cau[2]}", f"C. {cau[3]}"]
                        if str(cau[4]).strip(): opts.append(f"D. {cau[4]}")
                        chon = st.radio("Lựa chọn:", opts, index=None)
                        if st.form_submit_button("CHỐT ĐÁP ÁN"):
                            if chon: 
                                st.session_state['lua_chon'] = chon.split(".")[0]
                                st.session_state['da_nop_cau'] = True
                                st.rerun()
                            else: st.warning("Vui lòng chọn đáp án!")
                    time.sleep(1); st.rerun()
                
                else:
                    nguoi_chon = st.session_state['lua_chon']
                    dap_an_dung = str(cau[5]).strip().upper()
                    if nguoi_chon == dap_an_dung: st.success("✅ CHÍNH XÁC!")
                    else: st.error(f"❌ SAI RỒI! Đáp án đúng: {dap_an_dung}")
                    if str(cau[6]).strip(): st.info(f"💡 Giải thích: {cau[6]}")
                    
                    if st.button("CÂU TIẾP THEO"):
                        if nguoi_chon == dap_an_dung: st.session_state['diem_so'] += 1
                        st.session_state['chi_so'] += 1; st.session_state['da_nop_cau'] = False
                        st.session_state['thoi_gian_het'] = None
                        st.rerun()

if __name__ == "__main__":
    main()
