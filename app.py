import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import time

# --- 1. CẤU HÌNH ---
THOI_GIAN_MOI_CAU = 30

# --- 2. HÀM GIAO DIỆN (ĐÃ TỐI ƯU LIGHT/DARK THEME) ---
def inject_css():
    st.markdown("""
        <style>
        /* Tinh chỉnh lề cho mobile */
        .block-container { 
            padding-top: 1rem; 
            padding-bottom: 3rem; 
            padding-left: 0.5rem; 
            padding-right: 0.5rem;
        }
        
        /* Ẩn Header/Footer mặc định */
        header, footer { visibility: hidden; }
        
        /* TIÊU ĐỀ: Tự động đổi màu theo theme hoặc giữ màu thương hiệu nếu nền sáng */
        .gcpd-title {
            font-family: 'Arial Black', sans-serif; 
            color: #002147; /* Màu xanh cảnh sát */
            font-size: 24px; 
            text-transform: uppercase;
            margin-top: 5px; 
            line-height: 1.2; 
            font-weight: 900;
            text-align: center;
            text-shadow: 1px 1px 0px #ffffff; /* Viền trắng nhẹ để dễ đọc nếu nền tối */
        }
        
        /* KHUNG FORM (LOGIN, CÂU HỎI): Luôn nền trắng để chữ Xanh dễ đọc */
        [data-testid="stForm"] {
            background-color: #ffffff; /* Luôn là nền trắng */
            border: 2px solid #002147; 
            border-radius: 10px; 
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); /* Đổ bóng nhẹ */
        }
        
        /* KHUNG BÀI HỌC (Lesson Card) */
        .lesson-card {
            background-color: #ffffff; /* Luôn nền trắng */
            border-left: 6px solid #002147; /* Viền trái xanh đậm */
            padding: 15px; 
            margin-bottom: 15px; 
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            color: #333333; /* Chữ đen để dễ đọc */
        }
        .lesson-title { 
            color: #002147; 
            font-size: 18px; 
            font-weight: bold; 
            margin-bottom: 8px; 
            border-bottom: 1px solid #eee;
            padding-bottom: 5px;
        }
        .lesson-content { 
            font-size: 15px; 
            line-height: 1.6; 
            color: #333; 
            white-space: pre-wrap; 
        }

        /* TÙY CHỈNH INPUT & SELECT BOX (Ép nền trắng, chữ đen) */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
            background-color: #ffffff !important;
            color: #002147 !important; /* Chữ xanh khi gõ */
            border: 1px solid #002147 !important;
            border-radius: 5px !important;
        }
        
        /* LABEL (Nhãn của ô nhập liệu) */
        .stTextInput label, .stSelectbox label, .stRadio label {
            color: #002147 !important;
            font-weight: bold !important;
        }
        
        /* RADIO BUTTON (Đáp án) */
        .stRadio div[role="radiogroup"] {
            color: #333333; /* Màu chữ đáp án */
        }

        /* NÚT BẤM (BUTTON) */
        .stButton button {
            background-color: #002147 !important; 
            color: #FFD700 !important; /* Chữ vàng trên nền xanh */
            font-weight: bold !important; 
            width: 100%; 
            padding: 12px !important;
            border-radius: 8px !important;
            border: none !important;
        }
        .stButton button:hover {
            background-color: #003366 !important; /* Sáng hơn khi di chuột */
        }
        
        /* THANH TIẾN TRÌNH */
        .stProgress > div > div > div > div {
            background-color: #002147 !important;
        }
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
                if status == 'DaThi': return "DA_KHOA", None
                if status == 'DangThi': return "VI_PHAM", None
                return str(row[2]).strip(), str(row[3]).strip()
    except: pass
    return None, None

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

# --- 5. CHƯƠNG TRÌNH CHÍNH ---
def main():
    st.set_page_config(page_title="FTO System", page_icon="🚓", layout="centered")
    inject_css() 

    if 'vai_tro' not in st.session_state: 
        st.session_state.update(vai_tro=None, chi_so=0, diem_so=0, ds_cau_hoi=[], da_nop_cau=False, bat_dau=False, thoi_gian_het=None, lua_chon=None)

    db = ket_noi_csdl()
    if not db: st.stop()

    # --- A. MÀN HÌNH ĐĂNG NHẬP ---
    if st.session_state['vai_tro'] is None:
        with st.form("login"):
            c1, c2 = st.columns([1, 2.5])
            with c1: st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", use_column_width=True)
            with c2: st.markdown('<div class="gcpd-title">GACHA CITY<BR>POLICE DEPT<BR>ACADEMY</div>', unsafe_allow_html=True)
            st.divider()
            
            # Dùng markdown thay vì header để kiểm soát màu sắc
            st.markdown("<h4 style='text-align: center; color: #002147;'>▼ ĐĂNG NHẬP HỆ THỐNG</h4>", unsafe_allow_html=True)
            
            u = st.text_input("SỐ HIỆU (Momo)")
            p = st.text_input("MÃ BẢO MẬT", type="password")
            
            if st.form_submit_button("XÁC THỰC DANH TÍNH"):
                vt, ten = kiem_tra_dang_nhap(db, u, p)
                if vt == "DA_KHOA": st.error("⛔ ĐÃ HOÀN THÀNH BÀI THI.")
                elif vt == "VI_PHAM": 
                    st.error("🚨 CẢNH BÁO VI PHẠM!")
                    st.warning("Hồ sơ bị khóa do thoát khi đang thi.")
                elif vt:
                    st.session_state.update(vai_tro=vt, user=u, ho_ten=ten)
                    st.rerun()
                else: st.error("❌ SAI THÔNG TIN")

    # --- B. ĐÃ ĐĂNG NHẬP ---
    else:
        with st.sidebar:
            st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", width=100)
            st.markdown(f"### 👮 {st.session_state['ho_ten']}")
            # Badge vai trò
            st.markdown(f"<span style='background-color:#002147; color:#FFD700; padding: 4px 8px; border-radius: 4px; font-weight:bold; font-size: 12px;'>{st.session_state['vai_tro']}</span>", unsafe_allow_html=True)
            
            if st.session_state['bat_dau']:
                st.divider()
                st.metric("🏆 ĐIỂM", f"{st.session_state['diem_so']}")
            st.divider()
            
            if st.session_state['vai_tro'] == 'GiangVien':
                ds_chuc_nang = ["📖 GIÁO TRÌNH FTO (GV)", "⚙️ QUẢN LÝ CÂU HỎI (GV)"]
            else:
                ds_chuc_nang = ["📝 SÁT HẠCH LÝ THUYẾT"]
            
            menu = st.radio("MENU CHỨC NĂNG", ds_chuc_nang)
            st.write(""); st.write("")
            if st.button("ĐĂNG XUẤT"):
                for key in list(st.session_state.keys()): del st.session_state[key]
                st.rerun()

        # 1. GIÁO TRÌNH
        if "GIÁO TRÌNH FTO" in menu:
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

        # 2. QUẢN LÝ CÂU HỎI
        elif "QUẢN LÝ CÂU HỎI" in menu:
            st.markdown("<h2 style='color:#002147;'>⚙️ NGÂN HÀNG CÂU HỎI</h2>", unsafe_allow_html=True)
            st.caption("💡 Hướng dẫn: Sửa trực tiếp vào bảng. Bấm dấu '+' để thêm dòng mới. Chọn dòng và bấm Delete để xóa.")
            
            ws_cauhoi = db.worksheet("CauHoi")
            all_values = ws_cauhoi.get_all_values()
            headers = ["CauHoi", "A", "B", "C", "D", "DapAn_Dung", "GiaiThich"]
            
            if len(all_values) > 1:
                df = pd.DataFrame(all_values[1:], columns=headers)
            else:
                df = pd.DataFrame(columns=headers)

            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, height=500)

            if st.button("💾 LƯU THAY ĐỔI", type="primary"):
                with st.spinner("Đang lưu..."):
                    try:
                        ws_cauhoi.clear()
                        rows_to_update = [headers] + edited_df.values.tolist()
                        ws_cauhoi.update(rows_to_update)
                        st.success("✅ Đã cập nhật!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi khi lưu: {e}")

        # 3. THI SÁT HẠCH
        elif "SÁT HẠCH LÝ THUYẾT" in menu:
            # A. CHƯA BẮT ĐẦU
            if not st.session_state['bat_dau']:
                with st.form("start_exam"):
                    c1, c2 = st.columns([1, 2.5])
                    with c1: st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", use_column_width=True)
                    with c2: st.markdown('<div class="gcpd-title">BÀI THI SÁT HẠCH<br>LÝ THUYẾT</div>', unsafe_allow_html=True)
                    st.divider()
                    st.warning("⚠️ LƯU Ý QUAN TRỌNG:\n\n1. Thời gian tính ngay khi bấm bắt đầu.\n2. Nếu thoát ra giữa chừng, bài thi sẽ bị HỦY và KHÓA HỒ SƠ.")
                    
                    if st.form_submit_button("BẮT ĐẦU LÀM BÀI", type="primary"):
                        danh_dau_dang_thi(db, st.session_state['user'])
                        st.session_state['bat_dau'] = True
                        st.rerun()
            
            # B. ĐANG LÀM BÀI
            else:
                if not st.session_state['ds_cau_hoi']:
                    raw = db.worksheet("CauHoi").get_all_values()
                    st.session_state['ds_cau_hoi'] = raw[1:] if len(raw) > 1 else []
                
                ds = st.session_state['ds_cau_hoi']
                idx = st.session_state['chi_so']

                if idx >= len(ds):
                    st.balloons(); st.success(f"KẾT QUẢ: {st.session_state['diem_so']}/{len(ds)}")
                    if st.button("NỘP HỒ SƠ"):
                        luu_ket_qua(db, st.session_state['user'], st.session_state['diem_so'])
                        for key in list(st.session_state.keys()): del st.session_state[key]
                        st.rerun()
                    st.stop()

                cau = ds[idx]
                while len(cau) < 7: cau.append("")

                if not st.session_state['da_nop_cau']:
                    if st.session_state['thoi_gian_het'] is None: 
                        st.session_state['thoi_gian_het'] = time.time() + THOI_GIAN_MOI_CAU
                    con_lai = int(st.session_state['thoi_gian_het'] - time.time())
                    if con_lai <= 0: st.session_state['da_nop_cau'] = True; st.session_state['lua_chon'] = None; st.rerun()

                    c_time, c_score = st.columns([2.5,1])
                    c_time.progress(max(0.0, min(1.0, con_lai/THOI_GIAN_MOI_CAU))); c_time.caption(f"⏳ {con_lai}s")
                    c_score.markdown(f"**Đ: {st.session_state['diem_so']}**")

                    with st.form(f"q_{idx}"):
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
                    
                    if nguoi_chon == dap_an_dung: 
                        st.success("✅ CHÍNH XÁC!")
                    else: 
                        st.error(f"❌ SAI RỒI! Đáp án đúng là: {dap_an_dung}")
                    
                    if str(cau[6]).strip(): 
                        st.info(f"💡 Giải thích: {cau[6]}")
                    
                    if st.button("CÂU TIẾP THEO"):
                        if nguoi_chon == dap_an_dung: st.session_state['diem_so'] += 1
                        st.session_state['chi_so'] += 1; st.session_state['da_nop_cau'] = False
                        st.session_state['thoi_gian_het'] = None
                        st.rerun()

if __name__ == "__main__":
    main()
