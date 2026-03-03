import streamlit as st
import time

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="FTO GCPD",
    page_icon="🚓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. KIỂM TRA THƯ VIỆN ---
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    import pandas as pd
    import random
except ImportError:
    st.error("Lỗi thư viện. Hãy kiểm tra requirements.txt")
    st.stop()

THOI_GIAN_THI = 25

# --- 3. CSS GIAO DIỆN CHUYÊN NGHIỆP ---
def inject_css():
    st.markdown("""
        <style>
        .stApp { background-color: #f4f7f6; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
        .block-container { padding-top: 3rem !important; padding-bottom: 4rem !important; max-width: 900px; }
        .gcpd-title { color: #0b2545; font-size: 26px; font-weight: 900; text-align: center; text-transform: uppercase; margin-bottom: 0px; letter-spacing: 1.5px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1); }
        .user-info { background: linear-gradient(135deg, #0b2545, #134074); color: white; padding: 6px 18px; border-radius: 30px; font-size: 13px; font-weight: 600; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: inline-block; margin-top: 10px; }
        div[data-baseweb="tab-list"] { position: sticky; top: 0; z-index: 999; background-color: #f4f7f6; padding-top: 15px; border-bottom: 2px solid #e0e0e0; gap: 8px; }
        .stTabs [data-baseweb="tab"] { height: 40px; padding: 0 20px; background-color: transparent; border-radius: 8px 8px 0 0; color: #7f8c8d; font-size: 14px; font-weight: 700; border: none; transition: all 0.3s ease; }
        .stTabs [aria-selected="true"] { background-color: white !important; color: #0b2545 !important; border-top: 3px solid #134074 !important; border-left: 1px solid #e0e0e0 !important; border-right: 1px solid #e0e0e0 !important; box-shadow: 0 -3px 6px rgba(0,0,0,0.03); }
        .question-box { background: #ffffff; padding: 20px; border-left: 5px solid #134074; border-radius: 8px; font-weight: 600; color: #2c3e50; margin-bottom: 15px; font-size: 16px; line-height: 1.6; box-shadow: 0 4px 10px rgba(0,0,0,0.06); }
        .explain-box { background: #e8f4f8; padding: 15px; border-radius: 8px; color: #0c5460; font-size: 14px; font-weight: 500; border: 1px solid #bee5eb; margin-top: 10px; }
        .timer-box { font-family: 'Courier New', monospace; font-size: 24px; font-weight: bold; color: white; background: linear-gradient(135deg, #e63946, #d62828); padding: 5px 20px; border-radius: 20px; width: fit-content; margin: 0 auto 15px auto; box-shadow: 0 4px 10px rgba(230, 57, 70, 0.3); }
        .stButton button { background: linear-gradient(135deg, #134074, #0b2545) !important; color: white !important; font-weight: 600 !important; font-size: 14px !important; padding: 0.5rem 1.2rem !important; border-radius: 6px !important; border: none !important; box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important; transition: all 0.2s ease-in-out !important; }
        .stButton button:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important; }
        div[data-testid="column"] button:has(div:contains("THOÁT")), button:has(div:contains("DỪNG LÀM BÀI")) { background: transparent !important; color: #e63946 !important; border: 2px solid #e63946 !important; box-shadow: none !important; }
        div[data-testid="column"] button:has(div:contains("THOÁT")):hover, button:has(div:contains("DỪNG LÀM BÀI")):hover { background: #e63946 !important; color: white !important; }
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

# --- 4. KẾT NỐI DATABASE ---
@st.cache_resource
def ket_noi_csdl():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        return gspread.authorize(creds).open("HeThongTracNghiem")
    except Exception as e:
        return None

# --- 5. HÀM XỬ LÝ DỮ LIỆU ---
def check_login(db, u, p):
    try:
        rows = db.worksheet("HocVien").get_all_values()
        for r in rows[1:]:
            if len(r) < 3: continue
            if str(r[0]).strip() == str(u).strip() and str(r[1]).strip() == str(p).strip():
                stt = str(r[4]).strip() if len(r)>4 else "ChuaDuocThi"
                return str(r[2]).strip(), str(r[3]).strip(), stt
    except: pass
    return None, None, None

def save_to_sheet(db, sheet_name, df_to_save):
    try:
        ws = db.worksheet(sheet_name)
        ws.clear()
        data = [df_to_save.columns.tolist()] + df_to_save.values.tolist()
        ws.update(data)
        st.cache_data.clear() 
        return True
    except Exception as e:
        st.error(f"Lỗi lưu: {e}")
        return False

@st.cache_data(ttl=300) 
def get_exams(_db):
    try: return _db.worksheet("CauHoi").get_all_values()
    except: return []

@st.cache_data(ttl=300)
def get_giao_trinh(_db):
    try: return _db.worksheet("GiaoTrinh").get_all_records()
    except: return []

def render_mixed_content(content):
    if not content: return
    lines = str(content).split('\n')
    for line in lines:
        line = line.strip()
        clean_line = line.strip(" -\"'")
        if clean_line.startswith(('http://', 'https://')):
            try: st.image(clean_line, use_container_width=True)
            except: pass 
            st.markdown(f"🔗 [*Nhấn vào đây để xem Ảnh/Tài liệu*]({clean_line})")
            st.write("") 
        elif line: 
            st.markdown(line, unsafe_allow_html=True)

# --- 6. MAIN ---
def main():
    inject_css()
    
    if 'vai_tro' not in st.session_state: st.session_state.vai_tro = None
    if 'bat_dau' not in st.session_state: st.session_state.bat_dau = False
    if 'diem_so' not in st.session_state: st.session_state.diem_so = 0
    if 'chi_so' not in st.session_state: st.session_state.chi_so = 0
    if 'ds_cau_hoi' not in st.session_state: st.session_state.ds_cau_hoi = []
    if 'da_nop' not in st.session_state: st.session_state.da_nop = False
    if 'time_end' not in st.session_state: st.session_state.time_end = None
    if 'choice' not in st.session_state: st.session_state.choice = None

    db = ket_noi_csdl()
    if not db: 
        st.error("Không thể kết nối Database. Vui lòng kiểm tra lại.")
        st.stop()

    # --- A. LOGIN ---
    if st.session_state.vai_tro is None:
        c1, c2 = st.columns([1, 2.5])
        with c1: st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", use_container_width=True)
        with c2: st.markdown('<div class="gcpd-title">FTO GACHA CITY <BR> POLICE DERPARTMENT</div>', unsafe_allow_html=True)
        
        with st.form("login"):
            u = st.text_input("SỐ HIỆU (Momo)")
            p = st.text_input("MÃ BẢO MẬT", type="password")
            if st.form_submit_button("ĐĂNG NHẬP"):
                role, name, stt = check_login(db, u, p)
                if role:
                    st.session_state.vai_tro = role
                    st.session_state.user = u
                    st.session_state.ho_ten = name
                    st.rerun()
                else: st.error("Sai thông tin!")

    # --- B. DASHBOARD ---
    else:
        c1, c2, c3 = st.columns([1, 4, 1], gap="small")
        with c1: 
            st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", width=40)
        with c2: 
            st.markdown(f"<div style='text-align:center; padding-top:2px;'><span class='user-info'>👮 {st.session_state.ho_ten} | {st.session_state.vai_tro}</span></div>", unsafe_allow_html=True)
        with c3:
            if st.button("THOÁT", key="logout"):
                st.session_state.clear()
                st.rerun()
        
        st.write("")
        role = st.session_state.vai_tro
        
        # --- TAB MENU ---
        if role == 'Admin':
            tabs = st.tabs(["👥 USER", "⚙️ CÂU HỎI", "📚 TÀI LIỆU"])
            active_tab = "Admin"
        elif role == 'GiangVien':
            tabs = st.tabs(["👥 CẤP QUYỀN", "⚙️ CÂU HỎI", "📚 TÀI LIỆU"])
            active_tab = "GV"
        else:
            tabs = st.tabs(["📚 TÀI LIỆU", "📝 THI TRẮC NGHIỆM"])
            active_tab = "HV"

        # --- LOGIC THI CỬ ---
        if st.session_state.bat_dau:
            if st.session_state.mode == 'thu':
                st.info("📝 THI THỬ")
                if st.button("❌ DỪNG LÀM BÀI", key="stop_exam"):
                    st.session_state.bat_dau = False
                    st.session_state.ds_cau_hoi = []
                    st.rerun()
            else:
                st.error("🚨 THI CHÍNH THỨC")

            qs = st.session_state.ds_cau_hoi
            idx = st.session_state.chi_so
            
            # --- KHI HOÀN THÀNH BÀI THI ---
            if idx >= len(qs):
                if st.session_state.get('mode') == 'that':
                    if st.session_state.diem_so >= 45:
                        st.balloons()
                        st.success(f"KẾT QUẢ: {st.session_state.diem_so}/{len(qs)}")
                        st.success("🎉 CHÚC MỪNG BẠN ĐÃ VƯỢT QUA KÌ THI CHÍNH THỨC!")
                    else:
                        st.error(f"KẾT QUẢ: {st.session_state.diem_so}/{len(qs)}")
                        st.warning("❌ Bạn cần cố gắng ôn luyện thêm. Liên hệ Giảng viên để được cấp quyền thi lại.")
                else:
                    st.balloons()
                    st.success(f"KẾT QUẢ THI THỬ: {st.session_state.diem_so}/{len(qs)}")

                if st.button("NỘP BÀI THI"):
