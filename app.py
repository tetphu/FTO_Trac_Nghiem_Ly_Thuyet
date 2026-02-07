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
        st.error(f"LỖI KẾT NỐI HỆ THỐNG: {str(e)}")
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
        st.error(f"LỖI DỮ LIỆU: {str(e)}")
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
# --- GIAO DIỆN: GCPD COMPACT MODE (SIÊU GỌN) ---
# =============================================
def main():
    st.set_page_config(page_title="GCPD System", page_icon="🚓", layout="centered")
    
    # --- CSS: TỐI ƯU HÓA KHÔNG GIAN ---
    st.markdown("""
        <style>
        /* 1. ĐẨY GIAO DIỆN LÊN SÁT MÉP TRÊN */
        .block-container {
            padding-top: 1rem !important; /* Xóa khoảng trắng mặc định ở đầu */
            padding-bottom: 0rem !important;
            max-width: 800px; /* Giới hạn chiều rộng để nhìn tập trung hơn */
        }
        
        /* 2. ẨN MENU STREAMLIT ĐỂ RỘNG CHỖ HƠN */
        header {visibility: hidden;}
        footer {visibility: hidden;}

        /* 3. NỀN TRANG WEB */
        .stApp { background-color: #ffffff; }

        /* 4. KHUNG BAO BỌC (WRAPPER) - Gọn gàng hơn */
        .gcpd-wrapper {
            border: 3px solid #002147;
            border-radius: 4px;
            box-shadow: 0px 5px 15px rgba(0,0,0,0.1);
            background-color: #f8f9fa;
            overflow: hidden;
            margin-bottom: 10px;
        }

        /* 5. HEADER TÍCH HỢP (Logo + Tên nằm cùng 1 dòng) */
        .gcpd-header {
            background-color: #002147;
            color: #FFD700;
            padding: 10px 20px; /* Giảm padding */
            display: flex;
            align_items: center;
            justify_content: space-between;
            border-bottom: 3px solid #FFD700;
        }
        .gcpd-title {
            font-family: 'Arial Black', sans-serif;
            font-size: 20px; /* Giảm cỡ chữ */
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 0;
        }
        .gcpd-sub {
            font-size: 10px;
            color: #fff;
            margin: 0;
        }

        /* 6. BODY GỌN GÀNG */
        .gcpd-body {
            padding: 15px 25px; /* Giảm khoảng cách lề */
        }

        /* 7. INPUT FIELDS (Nhỏ gọn hơn) */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
            border: 2px solid #002147 !important;
            border-radius: 2px !important;
            background-color: #ffffff !important;
            color: #000 !important;
            font-family: 'Courier New', monospace;
            font-weight: bold;
            min-height: 0px !important;
            padding: 8px !important; /* Ô nhập thấp hơn */
        }
        .stTextInput label { font-size: 12px !important; margin-bottom: 0px !important; }

        /* 8. BUTTON (NÚT BẤM) */
        .stButton button {
            background-color: #002147 !important;
            color: #FFD700 !important;
            border: none !important;
            border-radius: 2px !important;
            font-weight: bold !important;
            padding: 8px 0px !important; /* Nút mỏng hơn */
            margin-top: 5px !important;
            width: 100%;
        }
        
        /* 9. RADIO BUTTON (ĐÁP ÁN) - Khoảng cách sít lại */
        .stRadio div[role="radiogroup"] > label {
            background-color: #ffffff;
            padding: 8px 10px; /* Giảm padding */
            border: 1px solid #ccc;
            border-left: 4px solid #002147;
            margin-bottom: 4px; /* Các đáp án gần nhau hơn */
            color: #000 !important;
            font-size: 14px !important;
        }
        .stRadio div[role="radiogroup"] { gap: 0px !important; }

        /* 10. SIDEBAR */
        [data-testid="stSidebar"] {
            background-color: #f0f2f6;
            border-right: 2px solid #002147;
            padding-top: 0px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Biến Session
    if 'vai_tro' not in st.session_state: st.session_state['vai_tro'] = None
    if 'chi_so' not in st.session_state: st.session_state['chi_so'] = 0
    if 'diem_so' not in st.session_state: st.session_state['diem_so'] = 0
    if 'ds_cau_hoi' not in st.session_state: st.session_state['ds_cau_hoi'] = []
    if 'da_nop_cau' not in st.session_state: st.session_state['da_nop_cau'] = False
    if 'lua_chon' not in st.session_state: st.session_state['lua_chon'] = None
    if 'thoi_gian_het' not in st.session_state: st.session_state['thoi_gian_het'] = None

    db = ket_noi_csdl()
    if db is None: st.stop()

    # --- HEADER CHUNG (TÍCH HỢP VÀO CODE HTML ĐỂ TIẾT KIỆM CHỖ) ---
    header_html = """
        <div class="gcpd-wrapper">
            <div class="gcpd-header">
                <div>
                    <div class="gcpd-title">GACHA CITY POLICE DEPT.</div>
                    <p class="gcpd-sub">HỆ THỐNG SÁT HẠCH TRỰC TUYẾN</p>
                </div>
                <img src="https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true" height="40">
            </div>
            <div class="gcpd-body">
    """

    # ==========================================
    # 1. ĐĂNG NHẬP (COMPACT)
    # ==========================================
    if st.session_state['vai_tro'] is None:
        st.markdown(header_html, unsafe_allow_html=True) # Mở khung
        
        st.write("▼ ĐỊNH DANH SĨ QUAN")
        with st.form("form_login"):
            u = st.text_input("SỐ HIỆU (USER)", placeholder="Mã số...")
            p = st.text_input("MÃ BẢO MẬT (PASS)", type="password", placeholder="Mật khẩu...")
            btn = st.form_submit_button("TRUY CẬP")
            
            if btn:
                vt, ten = kiem_tra_dang_nhap(db, u, p)
                if vt == "DA_KHOA": st.error("⛔ HỒ SƠ ĐÃ KHÓA")
                elif vt:
                    st.session_state['vai_tro'] = vt
                    st.session_state['user'] = u
                    st.session_state['ho_ten'] = ten
                    st.session_state['chi_so'] = 0; st.session_state['diem_so'] = 0; st.session_state['ds_cau_hoi'] = []; st.session_state['da_nop_cau'] = False; st.session_state['lua_chon'] = None; st.session_state['thoi_gian_het'] = None
                    st.rerun()
                else: st.error("❌ SAI THÔNG TIN")
        
        st.markdown('</div></div>', unsafe_allow_html=True) # Đóng khung

    # ==========================================
    # 2. GIẢNG VIÊN
    # ==========================================
    elif st.session_state['vai_tro'] == 'GiangVien':
        st.sidebar.markdown(f"**CHỈ HUY:** {st.session_state['ho_ten']}")
        if st.sidebar.button("ĐĂNG XUẤT"): st.session_state['vai_tro'] = None; st.rerun()
        
        st.markdown(header_html, unsafe_allow_html=True)
        st.caption("BẢNG CẬP NHẬT DỮ LIỆU")
        
        with st.form("add"):
            q = st.text_input("NỘI DUNG CÂU HỎI")
            c1, c2 = st.columns(2)
            with c1: a, b = st.text_input("ĐÁP ÁN A"), st.text_input("ĐÁP ÁN B")
            with c2: c, d = st.text_input("ĐÁP ÁN C"), st.text_input("ĐÁP ÁN D")
            dung = st.selectbox("ĐÁP ÁN ĐÚNG", ["A", "B", "C", "D"])
            gt = st.text_area("GIẢI THÍCH", height=68)
            
            if st.form_submit_button("LƯU DỮ LIỆU"):
                try:
                    db.worksheet("CauHoi").append_row([q, a, b, c, d, dung, gt])
                    st.success("ĐÃ LƯU")
                except Exception as e: st.error(f"LỖI: {e}")
        st.markdown('</div></div>', unsafe_allow_html=True)

    # ==========================================
    # 3. HỌC VIÊN
    # ==========================================
    elif st.session_state['vai_tro'] == 'hocvien':
        # Sidebar gọn hơn
        st.sidebar.markdown(f"**SĨ QUAN:** {st.session_state['ho_ten']}")
        st.sidebar.metric("ĐIỂM", f"{st.session_state['diem_so']}")
        
        if not st.session_state['ds_cau_hoi']:
            try:
                raw = db.worksheet("CauHoi").get_all_values()
                if len(raw) > 1: st.session_state['ds_cau_hoi'] = raw[1:]
                else: st.error("KHÔNG CÓ DỮ LIỆU"); st.stop()
            except: st.error("LỖI MẠNG"); st.stop()
        
        ds = st.session_state['ds_cau_hoi']
        idx = st.session_state['chi_so']

        # Kết thúc
        if idx >= len(ds):
            st.markdown(header_html, unsafe_allow_html=True)
            st.balloons()
            st.markdown(f"<h2 style='text-align:center; color:#002147;'>KẾT QUẢ: {st.session_state['diem_so']} / {len(ds)}</h2>", unsafe_allow_html=True)
            st.info("ĐANG LƯU & ĐĂNG XUẤT...")
            luu_ket_qua(db, st.session_state['user'], st.session_state['diem_so'])
            time.sleep(3)
            st.session_state['vai_tro'] = None
            st.rerun()
            st.markdown('</div></div>', unsafe_allow_html=True)
            return

        cau = ds[idx]
        while len(cau) < 7: cau.append("")
        
        # Mở khung câu hỏi
        st.markdown(header_html, unsafe_allow_html=True)
        
        # Nội dung câu hỏi (Giảm padding)
        st.markdown(f"<div style='background:#f0f2f6; padding:10px; border-left:4px solid #FFD700; margin-bottom:10px; font-weight:bold; font-size:16px; color:#000;'>CÂU {idx + 1}: {cau[0]}</div>", unsafe_allow_html=True)

        if not st.session_state['da_nop_cau']:
            if st.session_state['thoi_gian_het'] is None: st.session_state['thoi_gian_het'] = time.time() + THOI_GIAN_MOI_CAU
            con_lai = int(st.session_state['thoi_gian_het'] - time.time())
            if con_lai <= 0: st.session_state['da_nop_cau'] = True; st.rerun()
            
            st.progress(max(0.0, min(1.0, con_lai/THOI_GI