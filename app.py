import streamlit as st
import time

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="FTO System", page_icon="🚓", layout="centered")

# --- 2. KIỂM TRA THƯ VIỆN ---
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    import pandas as pd
    import random
except ImportError as e:
    st.error(f"❌ LỖI: Thiếu thư viện. Hãy kiểm tra file requirements.txt.\nChi tiết: {e}")
    st.stop()

THOI_GIAN_MOI_CAU = 30

# --- 3. CSS GIAO DIỆN ---
def inject_css():
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem; padding-bottom: 5rem; }
        header, footer { visibility: hidden; }
        
        .gcpd-title {
            font-family: sans-serif; color: #002147; 
            font-size: 24px; font-weight: 900; text-align: center;
            text-transform: uppercase; margin-bottom: 20px;
        }
        
        .timer-digital {
            font-size: 45px; font-weight: 900; color: #d32f2f;
            text-align: center; background-color: #ffebee;
            border: 2px solid #d32f2f; border-radius: 12px;
            width: 120px; margin: 0 auto 20px auto;
            padding: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .question-box {
            background-color: #ffffff; padding: 20px; border-radius: 10px;
            border: 2px solid #002147;
            font-size: 18px; font-weight: bold; color: #002147;
            margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }

        .explanation-box {
            background-color: #e8f5e9; padding: 15px;
            border-radius: 8px; border-left: 5px solid #4caf50;
            margin-top: 15px; color: #1b5e20; font-size: 16px;
        }

        .stButton button {
            background-color: #002147 !important; color: #FFD700 !important;
            font-weight: bold !important; width: 100%; padding: 12px !important;
            border-radius: 8px !important; font-size: 16px !important;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 4. KẾT NỐI DATABASE ---
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
        st.error(f"❌ LỖI KẾT NỐI: {e}")
        return None

# --- 5. HÀM XỬ LÝ ---
def kiem_tra_dang_nhap(db, user, pwd):
    try:
        ws = db.worksheet("HocVien")
        rows = ws.get_all_values()
        for row in rows[1:]:
            if len(row) < 3: continue
            if str(row[0]).strip() == str(user).strip() and str(row[1]).strip() == str(pwd).strip():
                status = str(row[4]).strip() if len(row) > 4 else "ChuaDuocThi"
                return str(row[2]).strip(), str(row[3]).strip(), status
    except: pass
    return None, None, None

def luu_ket_qua(db, user, diem):
    try:
        ws = db.worksheet("HocVien")
        cell = ws.find(user)
        ws.update_cell(cell.row, 5, "DaThi")
        ws.update_cell(cell.row, 6, str(diem))
    except: pass

def cap_nhat_trang_thai(db, user, stt):
    try:
        ws = db.worksheet("HocVien")
        cell = ws.find(user)
        ws.update_cell(cell.row, 5, stt)
    except: pass

def lay_giao_trinh(db):
    try: return db.worksheet("GiaoTrinh").get_all_records()
    except: return []

# --- 6. CHƯƠNG TRÌNH CHÍNH ---
def main():
    inject_css()
    if 'vai_tro' not in st.session_state:
        st.session_state.update(vai_tro=None, diem_so=0, chi_so=0, bat_dau=False, da_nop_cau=False, ds_cau_hoi=[], thoi_gian_het=None, lua_chon=None, loai_thi=None)

    db = ket_noi_csdl()
    if not db: st.stop()

    # --- A. ĐĂNG NHẬP ---
    if st.session_state['vai_tro'] is None:
        c1, c2 = st.columns([1, 2.5])
        with c1: st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", use_column_width=True)
        with c2: st.markdown('<div class="gcpd-title">ACADEMY LOGIN</div>', unsafe_allow_html=True)
        
        with st.form("login"):
            u = st.text_input("SỐ HIỆU (Momo)")
            p = st.text_input("MÃ BẢO MẬT", type="password")
            if st.form_submit_button("ĐĂNG NHẬP"):
                vt, ten, stt = kiem_tra_dang_nhap(db, u, p)
                if vt:
                    st.session_state.update(vai_tro=vt, user=u, ho_ten=ten, trang_thai_hien_tai=stt)
                    st.rerun()
                else: st.error("Sai thông tin!")

    # --- B. DASHBOARD ---
    else:
        with st.sidebar:
            st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", width=80)
            st.markdown(f"**{st.session_state['ho_ten']}**")
            if st.button("ĐĂNG XUẤT"):
                st.session_state.clear()
                st.rerun()

        role = st.session_state['vai_tro']
        if role == 'Admin': menu_opts = ["QUẢN TRỊ USER", "QUẢN LÝ CÂU HỎI", "GIÁO TRÌNH"]
        elif role == 'GiangVien': menu_opts = ["CẤP QUYỀN THI", "QUẢN LÝ CÂU HỎI", "GIÁO TRÌNH"]
        else: menu_opts = ["THI THỬ", "THI SÁT HẠCH"]
        
        if st.session_state['bat_dau']: menu = "ĐANG THI"
        else: menu = st.radio("MENU", menu_opts)

        # 1. QUẢN LÝ CÂU HỎI
        if menu == "QUẢN LÝ CÂU HỎI":
            st.info("⚙️ NGÂN HÀNG CÂU HỎI")
            ws = db.worksheet("CauHoi")
            vals = ws.get_all_values()
            headers = ["CauHoi","A","B","C","D","DapAn_Dung","GiaiThich"]
            clean = [r[:7]+[""]*(7-len(r)) for r in vals[1:]] if len(vals)>1 else []
            df = pd.DataFrame(clean, columns=headers)
            edited = st.
