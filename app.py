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
                if status == 'DaThi': return "DA_KHOA", None
                
                # Trả về vai trò gốc (GiangVien hoặc hocvien)
                role = str(row[2]).strip()
                name = str(row[3]).strip()
                return role, name
    except: pass
    return None, None

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

    # CSS GIỮ NGUYÊN
    st.markdown("""
        <style>
        .block-container { padding-top: 2rem; padding-bottom: 5rem; }
        header, footer { visibility: hidden; }
        .stApp { background-color: #ffffff; }
        
        /* HEADER STYLE */
        .gcpd-title {
            font-family: 'Arial Black', sans-serif; color: #002147; 
            font-size: 35px; text-transform: uppercase;
            margin-top: 10px; line-height: 1.2; font-weight: 900;
        }
        
        /* FORM LOGIN STYLE */
        [data-testid="stForm"] {
            border: 3px solid #002147; border-radius: 12px; padding: 20px;
            background-image: url("https://raw.githubusercontent.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/refs/heads/main/nen.png");
            background-size: cover; background-position: center;
            background-color: rgba(255, 255, 255, 0.9); background-blend-mode: overlay;
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }

        /* INPUT & BUTTON */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
            border: 2px solid #002147 !important; border-radius: 4px !important;
            font-weight: bold; color: #000 !important;
        }
        .stButton button {
            background-color: #002147 !important; color: #FFD700 !important;
            font-weight: bold !important; width: 100%; padding: 10px;
        }
        
        /* BÀI GIẢNG STYLE */
        .lesson-card {
            background-color: #f8f9fa; border-left: 5px solid #002147;
            padding: 20px; margin-bottom: 20px; border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .lesson-title { color: #002147; font-size: 24px; font-weight: bold; margin-bottom: 10px; }
        .lesson-content { font-size: 16px; line-height: 1.6; color: #333; white-space: pre-wrap; }
        </style>
    """, unsafe_allow_html=True)

    # KHỞI TẠO STATE
    if 'vai_tro' not in st.session_state: st.session_state.update(vai_tro=None, chi_so=0, diem_so=0, ds_cau_hoi=[], da_nop_cau=False, bat_dau=False, thoi_gian_het=None, lua_chon=None)

    db = ket_noi_csdl()
    if not db: st.stop()

    # ==========================================
    # 1. MÀN HÌNH ĐĂNG NHẬP
    # ==========================================
    if st.session_state['vai_tro'] is None:
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            with st.form("login"):
                wc1, wc2 = st.columns([1, 2.5])
                with wc1: st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", width=150)
                with wc2: st.markdown('<div class="gcpd-title">GACHA CITY<BR>POLICE DEPT<BR>ACADEMY</div>', unsafe_allow_html=True)
                st.divider()
                
                st.markdown("### ▼ ĐĂNG NHẬP HỆ THỐNG")
                u = st.text_input("SỐ HIỆU (Momo)")
                p = st.text_input("MÃ BẢO MẬT", type="password")
                
                if st.form_submit_button("XÁC THỰC DANH TÍNH"):
                    vt, ten = kiem_tra_dang_nhap(db, u, p)
                    if vt == "DA_KHOA": st.error("⛔ HỒ SƠ ĐÃ KHÓA")
                    elif vt:
                        st.session_state.update(vai_tro=vt, user=u, ho_ten=ten)
                        st.rerun()
                    else: st.error("❌ SAI THÔNG TIN")

    # ==========================================
    # 2. ĐÃ ĐĂNG NHẬP -> XỬ LÝ PHÂN QUYỀN MENU
    # ==========================================
    else:
        # --- SIDEBAR ---
        with st.sidebar:
            st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", width=100)
            st.markdown(f"### 👮 Sĩ quan: {st.session_state['ho_ten']}")
            st.code(f"Vai trò: {st.session_state['vai_tro']}") # Hiện vai trò để check
            st.divider()
            
            # --- LOGIC PHÂN QUYỀN MENU ---
            # Mặc định ai cũng thấy phần thi
            ds_chuc_nang = ["📝 SÁT HẠCH LÝ THUYẾT"]
            
            # Chỉ Giảng Viên mới thấy Giáo trình và Quản lý câu hỏi
            if st.session_state['vai_tro'] == 'GiangVien':
                ds_chuc_nang.insert(0, "📖 GIÁO TRÌNH FTO (GV)")
                ds_chuc_nang.append("⚙️ QUẢN LÝ CÂU HỎI (GV)")
            
            menu = st.radio("MENU CHỨC NĂNG", ds_chuc_nang)
            
            st.write("")
            st.write("")
            if st.button("ĐĂNG XUẤT"):
                for key in list(st.session_state.keys()): del st.session_state[key]
                st.rerun()

        # ==========================================
        # CHỨC NĂNG: ĐỌC GIÁO TRÌNH (CHỈ GV)
        # ==========================================
        if "GIÁO TRÌNH FTO" in menu:
            st.title("📚 TÀI LIỆU NỘI BỘ GIẢNG VIÊN")
            st.info("Khu vực chỉ dành cho Giảng viên FTO.")
            
            ds_bai = lay_giao_trinh(db)
            if not ds_bai:
                st.warning("Chưa có dữ liệu bài giảng trong Google Sheet.")
            else:
                for bai in ds_bai:
                    with st.container():
                        st.markdown(f"""
                        <div class="lesson-card">
                            <div class="lesson-title">{bai['BaiHoc']}</div>
                            <div class="lesson-content">{bai['NoiDung']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        if str(bai['HinhAnh']).strip().startswith("http"):
                            st.image(bai['HinhAnh'], caption="Minh họa", use_column_width=True)
                        st.divider()

        # ==========================================
        # CHỨC NĂNG: QUẢN LÝ CÂU HỎI (CHỈ GV)
        # ==========================================
        elif "QUẢN LÝ CÂU HỎI" in menu:
            st.title("⚙️ CẬP NHẬT NGÂN HÀNG CÂU HỎI")
            with st.form("add_question"):
                q = st.text_input("NỘI DUNG CÂU HỎI")
                c1, c2 = st.columns(2)
                a, b = c1.text_input("ĐÁP ÁN A"), c1.text_input("ĐÁP ÁN B")
                c, d = c2.text_input("ĐÁP ÁN C"), c2.text_input("ĐÁP ÁN D")
                dung = st.selectbox("ĐÁP ÁN ĐÚNG", ["A", "B", "C", "D"])
                gt = st.text_area("GIẢI THÍCH (Hiện khi chọn sai)")
                if st.form_submit_button("LƯU VÀO DATABASE"):
                    try:
                        db.worksheet("CauHoi").append_row([q, a, b, c, d, dung, gt])
                        st.success("ĐÃ THÊM THÀNH CÔNG!")
                    except Exception as e: st.error(str(e))

        # ==========================================
        # CHỨC NĂNG: THI SÁT HẠCH (AI CŨNG THẤY)
        # ==========================================
        elif "SÁT HẠCH LÝ THUYẾT" in menu:
            # LOGIC THI (Giữ nguyên)
            if not st.session_state['bat_dau']:
                c1, c2, c3 = st.columns([1,2,1])
                with c2:
                    st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", width=100)
                    st.markdown("### BÀI THI SÁT HẠCH LÝ THUYẾT")
                    st.warning("⚠️ LƯU Ý: Thời gian sẽ tính ngay khi bấm nút.")
                    if st.button("BẮT ĐẦU LÀM BÀI", type="primary"):
                        st.session_state['bat_dau'] = True
                        st.rerun()
            
            else:
                if not st.session_state['ds_cau_hoi']:
                    raw = db.worksheet("CauHoi").get_all_values()
                    if len(raw) > 1: st.session_state['ds_cau_hoi'] = raw[1:]
                    else: st.error("Lỗi dữ liệu"); st.stop()

                ds = st.session_state['ds_cau_hoi']
                idx = st.session_state['chi_so']

                if idx >= len(ds):
                    st.balloons()
                    st.success(f"🎉 HOÀN THÀNH! KẾT QUẢ: {st.session_state['diem_so']} / {len(ds)}")
                    if st.button("NỘP HỒ SƠ"):
                        luu_ket_qua(db, st.session_state['user'], st.session_state['diem_so'])
                        for key in list(st.session_state.keys()): del st.session_state[key]
                        st.rerun()
                    return

                cau = ds[idx]
                while len(cau) < 7: cau.append("")

                if not st.session_state['da_nop_cau']:
                    if st.session_state['thoi_gian_het'] is None: 
                        st.session_state['thoi_gian_het'] = time.time() + THOI_GIAN_MOI_CAU
                    
                    con_lai = int(st.session_state['thoi_gian_het'] - time.time())
                    if con_lai <= 0: 
                        st.session_state['da_nop_cau'] = True; st.session_state['lua_chon'] = None; st.rerun()

                    st.progress(max(0.0, min(1.0, con_lai / THOI_GIAN_MOI_CAU)))
                    st.caption(f"⏳ CÒN LẠI: {con_lai} GIÂY")

                    with st.form(f"q_{idx}"):
                        st.markdown(f"**Câu {idx+1}: {cau[0]}**")
                        opts = [f"A. {cau[1]}", f"B. {cau[2]}", f"C. {cau[3]}"]
                        if str(cau[4]).strip(): opts.append(f"D. {cau[4]}")
                        chon = st.radio("", opts, index=None)
                        if st.form_submit_button("CHỐT ĐÁP ÁN"):
                            if chon:
                                st.session_state['lua_chon'] = chon.split(".")[0]
                                st.session_state['da_nop_cau'] = True
                                st.rerun()
                            else: st.warning("Chọn đáp án đi Sĩ quan!")
                    time.sleep(1); st.rerun()
                
                else:
                    nguoi_chon = st.session_state['lua_chon']
                    dap_an_dung = str(cau[5]).strip().upper()
                    
                    if nguoi_chon == dap_an_dung:
                        st.success(f"✅ CHÍNH XÁC!")
                    else:
                        st.error(f"❌ SAI RỒI! (Đáp án đúng: {dap_an_dung})")
                    st.info(f"💡 {cau[6]}")
                    
                    if st.button("CÂU TIẾP THEO"):
                        if nguoi_chon == dap_an_dung: st.session_state['diem_so'] += 1
                        st.session_state['chi_so'] += 1
                        st.session_state['da_nop_cau'] = False
                        st.session_state['thoi_gian_het'] = None
                        st.rerun()

if __name__ == "__main__":
    main()
