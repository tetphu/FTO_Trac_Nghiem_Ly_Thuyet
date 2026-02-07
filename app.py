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

    # CSS TINH GỌN - KHÔNG CÒN KHUNG THỪA
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem; padding-bottom: 0rem; max-width: 900px; }
        header, footer { visibility: hidden; }
        .stApp { background-color: #ffffff; }
        
        /* 1. HEADER TEXT STYLE */
        .gcpd-title {
            font-family: 'Arial Black', sans-serif;
            color: #002147; /* Xanh Navy Đậm */
            font-size: 36px; /* Chữ to hơn */
            text-transform: uppercase;
            margin-top: 15px;
            line-height: 1.2;
            font-weight: 900;
        }
        
        /* 2. KHUNG FORM (CHỈ BAO QUANH FORM, KHÔNG BAO HEADER) */
        .form-box {
            border: 2px solid #002147;
            border-radius: 8px;
            background-color: #f8f9fa;
            padding: 25px;
            margin-top: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        /* 3. INPUT & BUTTON */
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
        }
        .stButton button:hover {
            background-color: #003366 !important;
        }
        
        /* 4. THANH PROGRESS */
        .stProgress > div > div > div > div {
            background-color: #002147;
        }

        /* 5. SIDEBAR */
        [data-testid="stSidebar"] { background-color: #f0f2f6; border-right: 3px solid #002147; }
        
        /* 6. TEXT CHÀO MỪNG */
        .welcome-text {
            font-size: 24px;
            font-weight: bold;
            color: #002147;
            text-align: center;
            margin-bottom: 20px;
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

    # --- HEADER: KHÔNG CÓ KHUNG BAO BỌC ---
    # Logo và Chữ nằm tự do trên nền trắng
    col_logo, col_text = st.columns([1, 2.5])
    with col_logo:
        # Logo to (width=220)
        st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", width=220)
    with col_text:
        # Chữ màu xanh, to, căn giữa
        st.markdown('<div class="gcpd-title">GACHA CITY<br>POLICE DEPARTMENT</div>', unsafe_allow_html=True)
    
    # Khoảng cách nhẹ thay vì dòng kẻ ngang gây hiểu lầm
    st.write("") 

    # --- 1. MÀN HÌNH ĐĂNG NHẬP ---
    if st.session_state['vai_tro'] is None:
        # Chỉ đóng khung phần form đăng nhập
        st.markdown('<div class="form-box">', unsafe_allow_html=True)
        st.subheader("▼ XÁC THỰC DANH TÍNH")
        with st.form("login"):
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
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 2. GIẢNG VIÊN ---
    elif st.session_state['vai_tro'] == 'GiangVien':
        st.sidebar.markdown(f"**CHỈ HUY:** {st.session_state['ho_ten']}")
        if st.sidebar.button("ĐĂNG XUẤT"): st.session_state['vai_tro'] = None; st.rerun()
        
        st.markdown('<div class="form-box">', unsafe_allow_html=True)
        st.subheader("CẬP NHẬT DỮ LIỆU")
        with st.form("add"):
            q = st.text_input("NỘI DUNG CÂU HỎI")
            c1, c2 = st.columns(2)
            a, b = c1.text_input("ĐÁP ÁN A"), c1.text_input("ĐÁP ÁN B")
            c, d = c2.text_input("ĐÁP ÁN C"), c2.text_input("ĐÁP ÁN D")
            dung = st.selectbox("ĐÁP ÁN ĐÚNG", ["A", "B", "C", "D"])