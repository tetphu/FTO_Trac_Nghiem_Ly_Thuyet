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
        st.error(f"LỖI KẾT NỐI: {str(e)}")
        return None

# --- XỬ LÝ ĐĂNG NHẬP ---
def kiem_tra_dang_nhap(db, user, pwd):
    try:
        ws = db.worksheet("HocVien")
        rows = ws.get_all_values()
        for row in rows[1:]:
            if len(row) < 4: continue
            u_sheet = str(row[0]).strip()
            p_sheet = str(row[1]).strip()
            if u_sheet == str(user).strip() and p_sheet == str(pwd).strip():
                status = str(row[4]).strip() if len(row) > 4 else ""
                if status == 'DaThi': return "DA_KHOA", None
                return str(row[2]).strip(), str(row[3]).strip()
    except Exception as e:
        st.error(f"LỖI DỮ LIỆU: {e}")
    return None, None

# --- LƯU KẾT QUẢ ---
def luu_ket_qua(db, user, diem):
    try:
        ws = db.worksheet("HocVien")
        cell = ws.find(user)
        ws.update_cell(cell.row, 5, "DaThi")
        ws.update_cell(cell.row, 6, str(diem))
        return True
    except: return False

# --- GIAO DIỆN CHÍNH ---
def main():
    st.set_page_config(page_title="GCPD System", page_icon="🚓", layout="centered")

    # CSS TINH CHỈNH (KHÔNG CÒN KHUNG RỖNG)
    st.markdown("""
        <style>
        /* Căn chỉnh lề */
        .block-container { 
            padding-top: 2rem; 
            padding-bottom: 2rem; 
            max-width: 800px; 
        }
        
        /* Ẩn Header/Footer mặc định */
        header, footer { visibility: hidden; }
        .stApp { background-color: #ffffff; }
        
        /* HEADER STYLE */
        .gcpd-title {
            font-family: 'Arial Black', sans-serif;
            color: #002147; 
            font-size: 32px;
            text-transform: uppercase;
            margin-top: 10px;
            line-height: 1.2;
            font-weight: 900;
        }
        
        /* QUAN TRỌNG: ĐÓNG KHUNG TRỰC TIẾP VÀO FORM */
        [data-testid="stForm"] {
            border: 3px solid #002147;
            border-radius: 10px;
            padding: 30px;
            background-color: #f8f9fa;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }

        /* INPUT & BUTTON */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
            border: 2px solid #002147 !important;
            border-radius: 4px !important;
            background-color: #fff !important;
            color: #000 !important;
            font-weight: bold;
        }
        .stButton button {
            background-color: #002147 !important;
            color: #FFD700 !important;
            border: none !important;
            font-weight: bold !important;
            width: 100%;
            padding: 12px;
            text-transform: uppercase;
            font-size: 16px;
            margin-top: 10px;
        }
        .stButton button:hover {
            background-color: #003366 !important;
        }
        
        /* THANH PROGRESS */
        .stProgress > div > div > div > div {
            background-color: #002147;
        }

        /* SIDEBAR */
        [data-testid="stSidebar"] { background-color: #f0f2f6; border-right: 3px solid #002147; }
        
        /* TEXT CÂU HỎI TRONG KHUNG */
        .question-box {
            background: #e9ecef; 
            padding: 15px; 
            border-left: 5px solid #002147; 
            margin-bottom: 15px; 
            color: #002147; 
            font-weight: bold; 
            font-size: 18px;
        }
        </style>
    """, unsafe_allow_html=True)

    # KHỞI TẠO SESSION
    if 'vai_tro' not in st.session_state: st.session_state['vai_tro'] = None
    if 'chi_so' not in st.session_state: st.session_state['chi_so'] = 0
    if 'diem_so' not in st.session_state: st.session_state['diem_so'] = 0
    if 'ds_cau_hoi' not in st.session_state: st.session_state['ds_cau_hoi'] = []
    if 'da_nop_cau' not in st.session_state: st.session_state['da_nop_cau'] = False
    if 'lua_chon' not in st.session_state: st.session_state['lua_chon'] = None
    if 'thoi_gian_het' not in st.session_state: st.session_state['thoi_gian_het'] = None
    if 'bat_dau' not in st.session_state: st.session_state['bat_dau'] = False

    db = ket_noi_csdl()
    if not db: st.stop()

    # --- HEADER ---
    col1, col2 = st.columns([1, 2.5])
    with col1:
        st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", width=220)
    with col2:
        st.markdown('<div class="gcpd-title">GACHA CITY<br>POLICE DEPARTMENT</div>', unsafe_allow_html=True)
    
    st.write("") 

    # ==========================================
    # 1. MÀN HÌNH ĐĂNG NHẬP
    # ==========================================
    if st.session_state['vai_tro'] is None:
        # Form tự động có viền nhờ CSS [data-testid="stForm"]
        with st.form("login_form"):
            st.markdown("### ▼ XÁC THỰC DANH TÍNH") # Đưa tiêu đề vào trong form
            u = st.text_input("SỐ HIỆU (USER)")
            p = st.text_input("MÃ BẢO MẬT (PASS)", type="password")
            st.write("")
            if st.form_submit_button("TRUY CẬP HỆ THỐNG"):
                vt, ten = kiem_tra_dang_nhap(db, u, p)
                if vt == "DA_KHOA": st.error("⛔ HỒ SƠ ĐÃ KHÓA")
                elif vt:
                    st.session_state.update(vai_tro=vt, user=u, ho_ten=ten, chi_so=0, diem_so=0, ds_cau_hoi=[], da_nop_cau=False, bat_dau=False)
                    st.rerun()
                else: st.error("❌ SAI THÔNG TIN")

    # ==========================================
    # 2. GIẢNG VIÊN (GiangVien)
    # ==========================================
    elif st.session_state['vai_tro'] == 'GiangVien':
        st.sidebar.markdown(f"**CHỈ HUY:** {st.session_state['ho_ten']}")
        if st.sidebar.button("ĐĂNG XUẤT"): st.session_state['vai_tro'] = None; st.rerun()
        
        with st.form("add_q"):
            st.subheader("CẬP NHẬT DỮ LIỆU")
            q = st.text_input("NỘI DUNG CÂU HỎI")
            c1, c2 = st.columns(2)
            a, b = c1.text_input("ĐÁP ÁN A"), c1.text_input("ĐÁP ÁN B")
            c, d = c2.text_input("ĐÁP ÁN C"), c2.text_input("ĐÁP ÁN D")
            dung = st.selectbox("ĐÁP ÁN ĐÚNG", ["A", "B", "C", "D"])
            gt = st.text_area("GIẢI THÍCH")
            if st.form_submit_button("LƯU DỮ LIỆU"):
                try:
                    db.worksheet("CauHoi").append_row([q, a, b, c, d, dung, gt])
                    st.success("ĐÃ LƯU")
                except Exception as e: st.error(str(e))

    # ==========================================
    # 3. HỌC VIÊN (hocvien)
    # ==========================================
    elif st.session_state['vai_tro'] == 'hocvien':
        st.sidebar.markdown(f"**SĨ QUAN:** {st.session_state['ho_ten']}")
        st.sidebar.metric("ĐIỂM", st.session_state['diem_so'])
        
        # --- MÀN HÌNH CHỜ (SẴN SÀNG) ---
        if not st.session_state['bat_dau']:
            # Dùng st.container để bọc nội dung, không tạo khung rỗng
            with st.container():
                st.markdown("""
                    <div style="text-align:center; padding: 40px;">
                        <h3 style="color:#002147;">Đã sẵn sàng chưa nào!</h3>
                        <p style="font-size:18px; font-weight:bold;