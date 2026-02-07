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
        st.error(f"SYSTEM ERROR: Connection failed. {str(e)}")
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
    except Exception as e:
        st.error(f"DATA RETRIEVAL ERROR: {str(e)}")
    return None, None

# --- LƯU KẾT QUẢ ---
def luu_ket_qua(bang_tinh, user, diem):
    try:
        ws = bang_tinh.worksheet("HocVien")
        cell = ws.find(user)
        ws.update_cell(cell.row, 5, "DaThi")
        ws.update_cell(cell.row, 6, str(diem))
        return True
    except: return False

# --- LẤY CÂU HỎI ---
def lay_ds_cau_hoi(bang_tinh):
    return bang_tinh.worksheet("CauHoi").get_all_values()[1:]

# =============================================
# --- GIAO DIỆN: AMERICAN PD STYLE ---
# =============================================
def main():
    st.set_page_config(page_title="GCPD POLICE DEPT", page_icon="🚓", layout="centered")
    
    # --- CSS: TẠO KHUNG BAO BỌC VÀ PHONG CÁCH MỸ ---
    st.markdown("""
        <style>
        /* 1. NỀN TỔNG THỂ: Màu xám xi măng tối (Đường phố/Sở cảnh sát) */
        .stApp {
            background-color: #2c3e50;
            background-image: radial-gradient(#34495e 15%, transparent 16%), radial-gradient(#34495e 15%, transparent 16%);
            background-size: 20px 20px;
        }

        /* 2. KHUNG BAO BỌC CHÍNH (THE FRAME) */
        .pd-frame {
            background-color: #ffffff;
            border: 8px solid #002147; /* Xanh Navy Cảnh sát Mỹ */
            border-top: 20px solid #002147; /* Thanh tiêu đề dày phía trên */
            border-bottom: 8px solid #FFD700; /* Viền vàng phía dưới (Huy hiệu) */
            border-radius: 4px;
            padding: 30px;
            box-shadow: 0 0 50px rgba(0,0,0,0.8); /* Đổ bóng sâu */
            margin-top: 20px;
            position: relative;
        }

        /* Trang trí: Dòng chữ POLICE DEPT chìm */
        .pd-frame::before {
            content: "OFFICIAL USE ONLY";
            position: absolute;
            top: -18px;
            left: 50%;
            transform: translateX(-50%);
            color: #FFD700;
            font-weight: bold;
            font-size: 10px;
            letter-spacing: 2px;
        }

        /* 3. TYPOGRAPHY (FONT CHỮ) */
        h1, h2, h3 {
            font-family: 'Impact', 'Arial Black', sans-serif !important;
            text-transform: uppercase;
            color: #002147 !important; /* Xanh Navy */
            letter-spacing: 1px;
        }
        
        h4, h5, p, label {
            font-family: 'Courier New', monospace; /* Font kiểu máy đánh chữ hồ sơ */
            font-weight: bold;
            color: #333;
        }

        /* 4. INPUT FIELD (O NHAP LIEU) */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
            border: 2px solid #002147 !important;
            border-radius: 0px !important; /* Vuông vức */
            background-color: #f4f4f4 !important;
            color: #000 !important;
            font-family: 'Courier New', monospace;
        }

        /* 5. BUTTON (NÚT BẤM) */
        .stButton button {
            background-color: #002147 !important; /* Xanh Navy */
            color: #FFD700 !important; /* Chữ Vàng */
            border: 2px solid #FFD700 !important;
            border-radius: 2px !important;
            font-weight: 900 !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 12px 24px;
            transition: 0.2s;
        }
        .stButton button:hover {
            background-color: #003366 !important;
            box-shadow: 0 0 10px #FFD700;
        }

        /* 6. SIDEBAR (THANH BÊN) */
        [data-testid="stSidebar"] {
            background-color: #001529; /* Rất tối */
            border-right: 4px solid #FFD700;
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            color: #FFD700 !important; /* Chữ vàng trên nền tối */
        }
        [data-testid="stSidebar"] .stMarkdown {
            color: #fff !important;
        }

        /* 7. RADIO BUTTON */
        .stRadio div[role="radiogroup"] > label {
            background-color: #ecf0f1;
            padding: 10px;
            border-left: 5px solid #002147;
            margin-bottom: 5px;
            color: #000 !important;
        }

        /* 8. ALERT/THÔNG BÁO */
        .stAlert {
            background-color: #ffeb3b;
            color: black;
            border: 3px solid black;
            font-weight: bold;
            text-transform: uppercase;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- Header Logo & Tiêu đề ---
    # Đặt bên ngoài khung để tạo header trang web
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", width=120)
    with col2:
        st.markdown("<h1 style='color:#FFD700 !important; text-shadow: 2px 2px #000;'>GCPD DEPARTMENT</h1>", unsafe_allow_html=True)
        st.markdown("<h5 style='color:#FFF !important;'>LAW ENFORCEMENT TRAINING DIVISION</h5>", unsafe_allow_html=True)

    # Khởi tạo
    db = ket_noi_csdl()
    if db is None: st.stop()
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
        
        # --- BẮT ĐẦU KHUNG PD ---
        st.markdown('<div class="pd-frame">', unsafe_allow_html=True)
        
        col_c1, col_c2 = st.columns([2,1])
        with col_c1:
            st.markdown("### AUTHORIZED LOGIN")
            st.write("SECURE TERMINAL ACCESS // RESTRICTED AREA")
        with col_c2:
            st.image("https://cdn-icons-png.flaticon.com/512/2402/2402453.png", width=60) # Icon huy hiệu
            
        st.divider()

        with st.form("form_login"):
            u = st.text_input("BADGE NUMBER (USER)", placeholder="ENTER ID...")
            p = st.text_input("ACCESS CODE (PASSWORD)", type="password", placeholder="ENTER CODE...")
            st.write("")
            btn = st.form_submit_button("AUTHENTICATE")
            
            if btn:
                vt, ten = kiem_tra_dang_nhap(db, u, p)
                if vt == "DA_KHOA":
                    st.error("ACCESS DENIED: PROFILE LOCKED (EXAM COMPLETED)")
                elif vt:
                    st.session_state['vai_tro'] = vt
                    st.session_state['user'] = u
                    st.session_state['ho_ten'] = ten
                    # Reset
                    st.session_state['chi_so'] = 0; st.session_state['diem_so'] = 0; st.session_state['ds_cau_hoi'] = []; st.session_state['da_nop_cau'] = False; st.session_state['lua_chon'] = None; st.session_state['thoi_gian_het'] = None
                    st.success("ACCESS GRANTED.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("ACCESS DENIED: INVALID CREDENTIALS")
        
        st.markdown('</div>', unsafe_allow_html=True) # --- KẾT THÚC KHUNG PD ---

    # ==========================================
    # 2. GIAO DIỆN GIẢNG VIÊN (COMMANDER)
    # ==========================================
    elif st.session_state['vai_tro'] == 'GiangVien':
        st.sidebar.markdown(f"### COMMANDER: {st.session_state['ho_ten']}")
        st.sidebar.info("CLEARANCE LEVEL: 5 (ADMIN)")
        if st.sidebar.button("LOGOUT"):
            st.session_state['vai_tro'] = None
            st.rerun()
        
        st.markdown('<div class="pd-frame">', unsafe_allow_html=True)
        st.markdown("### DATABASE UPDATE // NEW SCENARIO")
        st.divider()
        
        with st.form("add"):
            q = st.text_input("INCIDENT DESCRIPTION (QUESTION)")
            c1, c2 = st.columns(2)
            a, b = c1.text_input("OPTION A"), c1.text_input("OPTION B")
            c, d = c2.text_input("OPTION C"), c2.text_input("OPTION D")
            dung = st.selectbox("CORRECT PROTOCOL", ["A", "B", "C", "D"])
            gt = st.text_area("DEBRIEFING NOTES (EXPLANATION)")
            
            if st.form_submit_button("UPLOAD TO SERVER"):
                try:
                    db.worksheet("CauHoi").append_row([q, a, b, c, d, dung, gt])
                    st.success("DATABASE UPDATED SUCCESSFULLY.")
                except Exception as e: st.error(f"UPLOAD FAILED: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    # ==========================================
    # 3. GIAO DIỆN HỌC VIÊN (OFFICER)
    # ==========================================
    elif st.session_state['vai_tro'] == 'hocvien':
        # Sidebar
        st.sidebar.markdown(f"### OFFICER: {st.session_state['ho_ten']}")
        st.sidebar.markdown("---")
        st.sidebar.metric("CURRENT SCORE", f"{st.session_state['diem_so']}")
        st.sidebar.markdown("---")
        st.sidebar.write("STATUS: ACTIVE DUTY")
        
        # Tải dữ liệu
        if not st.session_state['ds_cau_hoi']:
            try: st.session_state['ds_cau_hoi'] = db.worksheet("CauHoi").get_all_values()[1:]
            except: st.error("DATABASE ERROR."); st.stop()
        
        ds = st.session_state['ds_cau_hoi']
        idx = st.session_state['chi_so']
        if not ds: st.warning("NO SCENARIOS AVAILABLE."); st.stop()

        # Kết thúc
        if idx >= len(ds):
            st.markdown('<div class="pd-frame" style="text-align:center;">', unsafe_allow_html=True)
            st.balloons()
            st.markdown("## MISSION DEBRIEF")
            st.markdown(f"<h1>FINAL SCORE: {st.session_state['diem_so']} / {len(ds)}</h1>", unsafe_allow_html=True)
            st.info("SAVING RECORDS TO CENTRAL SERVER...")
            luu_ket_qua(db, st.session_state['user'], st.session_state['diem_so'])
            time.sleep(3)
            st.session_state['vai_tro'] = None
            st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            return

        # Hiển thị câu hỏi
        cau = ds[idx]; 
        while len(cau) < 7: cau.append("")
        
        # --- KHUNG PD CHO CÂU HỎI ---
        st.markdown(f'<div class="pd-frame">', unsafe_allow_html=True)
        st.markdown(f"#### CASE FILE #{idx + 1}")
        st.markdown(f"<div style='background:#eee; padding:15px; border-left:5px solid #FFD700; margin-bottom:15px; font-weight:bold; font-size:18px;'>{cau[0]}</div>", unsafe_allow_html=True)

        if not st.session_state['da_nop_cau']:
            if st.session_state['thoi_gian_het'] is None: st.session_state['thoi_gian_het'] = time.time() + THOI_GIAN_MOI_CAU
            con_lai = int(st.session_state['thoi_gian_het'] - time.time())
            if con_lai <= 0: st.session_state['da_nop_cau'] = True; st.rerun()
            
            st.progress(max(0.0, min(1.0, con_lai/THOI_GIAN_MOI_CAU)))
            st.caption(f"RESPONSE TIME: {con_lai}s")

            with st.form(f"f_{idx}"):
                opts = [f"A. {cau[1]}", f"B. {cau[2]}", f"C. {cau[3]}"]
                if cau[4].strip(): opts.append(f"D. {cau[4]}")
                chon = st.radio("SELECT PROTOCOL:", opts, index=None)
                st.write("")
                if st.form_submit_button("EXECUTE"):
                    if chon: st.session_state['lua_chon'] = chon.split(".")[0]; st.session_state['da_nop_cau'] = True; st.rerun()
                    else: st.warning("SELECTION REQUIRED.")
            time.sleep(1); st.rerun()
        else:
            nguoi_chon = st.session_state['lua_chon']; dung_an = str(cau[5]).strip().upper()
            if nguoi_chon == dung_an:
                st.success(f"✅ PROTOCOL FOLLOWED.\n\nNOTE: {cau[6]}")
                dung = True
            else:
                msg = f"❌ VIOLATION (You selected {nguoi_chon})" if nguoi_chon else "⌛ TIME EXPIRED"
                st.error(f"{msg}\n\nCORRECT PROTOCOL: {dung_an}\n\nNOTE: {cau[6]}")
                dung = False
            
            if st.button("NEXT CASE ➡️"):
                if dung: st.session_state['diem_so'] += 1
                st.session_state['chi_so'] += 1; st.session_state['da_nop_cau'] = False; st.session_state['thoi_gian_het'] = None; st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True) # End Frame

    # --- LỖI ---
    else:
        st.error(f"UNAUTHORIZED ROLE: {st.session_state['vai_tro']}")
        if st.button("RETURN"): st.session_state['vai_tro'] = None; st.rerun()

if __name__ == "__main__":
    main()