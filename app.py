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

THOI_GIAN_THI = 40
# LINK BANNER (BẠN THAY LINK ẢNH CỦA BẠN VÀO ĐÂY)
BANNER_URL = "https://raw.githubusercontent.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/refs/heads/main/Anh/banner.png"

# --- 3. CSS GIAO DIỆN ĐĂNG NHẬP ---
def inject_login_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');

        .stApp { 
            background-color: #e9ecef !important; 
            font-family: 'Montserrat', sans-serif !important; 
        }
        
        .block-container { 
            max-width: 420px !important; 
            padding-top: 8vh !important; 
            background: transparent !important; 
            border: none !important; 
            box-shadow: none !important; 
        }
        
        [data-testid="stForm"] { 
            background-color: white !important; 
            border-radius: 12px !important; 
            border: none !important; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.15) !important; 
            padding: 0 !important; 
            overflow: hidden !important;
        }
        
        .login-header { 
            background-color: #031c36; 
            padding: 40px 20px 30px 20px; 
            text-align: center; 
            margin-bottom: 25px; 
        }
        
        .gcpd-logo { 
            background-color: #fccc04; 
            color: #031c36; 
            width: 80px; 
            height: 80px; 
            border-radius: 50%; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            font-weight: 900; 
            font-size: 22px; 
            margin: 0 auto 15px auto; 
            font-family: Arial, sans-serif;
        }
        
        .gcpd-title { 
            color: white; 
            font-size: 20px; 
            font-weight: 800; 
            text-transform: uppercase; 
            margin-bottom: 8px; 
            line-height: 1.3; 
        }
        
        .gcpd-subtitle { 
            color: #94a3b8; 
            font-size: 12px; 
            font-weight: 600; 
            letter-spacing: 1.5px; 
        }
        
        .stTextInput { padding: 0 30px !important; margin-bottom: 15px !important; }
        .stTextInput label p { 
            color: #64748b !important; 
            font-size: 12px !important; 
            font-weight: 700 !important; 
            text-transform: uppercase; 
        }
        .stTextInput input { 
            border-radius: 8px !important; 
            border: 1px solid #e2e8f0 !important; 
            padding: 12px 15px !important; 
            font-size: 14px !important;
            color: #333 !important;
        }
        .stTextInput input:focus { border-color: #031c36 !important; box-shadow: 0 0 0 1px #031c36 !important; }
        
        [data-testid="stFormSubmitButton"] {
            padding: 10px 30px 35px 30px !important;
            display: flex !important;
            justify-content: center !important;
        }
        [data-testid="stFormSubmitButton"] button { 
            width: 100% !important; 
            background-color: #031c36 !important; 
            border-radius: 8px !important; 
            padding: 12px !important; 
            border: none !important; 
            transition: background-color 0.2s !important;
        }
        [data-testid="stFormSubmitButton"] button p { 
            color: #fccc04 !important; 
            font-weight: 800 !important; 
            font-size: 15px !important; 
            margin: 0 !important; 
            text-transform: uppercase; 
            text-align: center !important;
            width: 100% !important;
        }
        [data-testid="stFormSubmitButton"] button:hover { background-color: #052648 !important; }
        
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

# --- 3.1 CSS GIAO DIỆN QUẢN LÝ / THI CỬ (DASHBOARD) ---
def inject_dashboard_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');
        
        .stApp { background-color: #dbe2ef !important; font-family: 'Montserrat', sans-serif !important; }
        .block-container { background-color: #ffffff !important; border: 3px solid #112d4e !important; border-radius: 15px !important; box-shadow: 0 10px 30px rgba(0,0,0,0.15) !important; padding: 2.5rem 2rem !important; margin-top: 2rem !important; margin-bottom: 2rem !important; max-width: 900px; }
        @media (max-width: 768px) { .block-container { padding: 1.5rem 1rem !important; margin-top: 0.5rem !important; margin-bottom: 0.5rem !important; border: 2px solid #112d4e !important; border-radius: 10px !important; } }
        .stMarkdown, .stText, p, h1, h2, h3, label { color: #112d4e !important; font-family: 'Montserrat', sans-serif !important; }
        
        /* CSS CHỈNH BO GÓC CHO BANNER */
        [data-testid="stImage"] img { border-radius: 12px !important; box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important; margin-bottom: 5px !important; }
        
        div[data-baseweb="tab-list"] { position: sticky; top: 0; z-index: 999; background-color: #ffffff; padding-top: 15px; border-bottom: 2px solid #e0e0e0; gap: 8px; }
        .stTabs [data-baseweb="tab"] { height: 40px; padding: 0 20px; background-color: transparent; border-radius: 8px 8px 0 0; color: #7f8c8d !important; font-size: 14px; font-weight: 700; border: none; transition: all 0.3s ease; font-family: 'Montserrat', sans-serif; }
        .stTabs [aria-selected="true"] { background-color: #f8f9fa !important; color: #0b2545 !important; border-top: 3px solid #134074 !important; border-left: 1px solid #e0e0e0 !important; border-right: 1px solid #e0e0e0 !important; }
        
        /* THE BLUE BOX HEADER GOM NHÓM TẤT CẢ */
        div[data-testid="stHorizontalBlock"]:has(.header-marker) {
            background-color: #031c36 !important;
            padding: 10px 15px !important;
            border-radius: 10px !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
            align-items: center !important;
            margin-bottom: 20px !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.header-marker) > div[data-testid="column"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
        }
        /* Tùy chỉnh Nút Đăng Xuất bên trong Khung Xanh */
        div[data-testid="stHorizontalBlock"]:has(.header-marker) button {
            background-color: transparent !important;
            border: 1px solid #e63946 !important;
            padding: 0px 5px !important;
            min-height: 28px !important;
            height: 28px !important;
            border-radius: 6px !important;
            margin-top: 5px !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.header-marker) button p {
            color: #e63946 !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            margin: 0 !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.header-marker) button:hover {
            background-color: #e63946 !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.header-marker) button:hover p {
            color: white !important;
        }
        
        .question-box { background: #f8f9fa; padding: 20px; border-left: 5px solid #134074; border-radius: 8px; font-weight: 600; color: #112d4e !important; margin-bottom: 15px; font-size: 16px; line-height: 1.6; box-shadow: 0 4px 10px rgba(0,0,0,0.04); }
        .stRadio div[role="radiogroup"] label p { color: #2c3e50 !important; font-weight: 600; font-size: 15px; }
        .explain-box { background: #e8f4f8; padding: 15px; border-radius: 8px; color: #0c5460 !important; font-size: 14px; font-weight: 600; border: 1px solid #bee5eb; margin-top: 10px; }
        .timer-box { font-family: 'Courier New', monospace !important; font-size: 24px; font-weight: bold; color: white !important; background: linear-gradient(135deg, #e63946, #d62828); padding: 5px 20px; border-radius: 20px; width: fit-content; margin: 0 auto 15px auto; box-shadow: 0 4px 10px rgba(230, 57, 70, 0.3); }
        
        .stButton button { background: linear-gradient(135deg, #134074, #0b2545) !important; border: none !important; border-radius: 6px !important; box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important; transition: all 0.2s ease-in-out !important; }
        .stButton button p { color: white !important; font-weight: 700 !important; font-size: 14px !important; text-align: center; width: 100%;}
        .stButton button:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important; }
        
        div[data-testid="column"] button:has(div:contains("DỪNG LÀM BÀI")), button:has(div:contains("BỎ KHÔNG THI NỮA")) { background: transparent !important; border: 2px solid #e63946 !important; box-shadow: none !important; }
        div[data-testid="column"] button:has(div:contains("DỪNG LÀM BÀI")) p, button:has(div:contains("BỎ KHÔNG THI NỮA")) p { color: #e63946 !important; }
        div[data-testid="column"] button:has(div:contains("DỪNG LÀM BÀI")):hover, button:has(div:contains("BỎ KHÔNG THI NỮA")):hover { background: #e63946 !important; }
        div[data-testid="column"] button:has(div:contains("DỪNG LÀM BÀI")):hover p, button:has(div:contains("BỎ KHÔNG THI NỮA")):hover p { color: white !important; }
        
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

@st.cache_data(ttl=120)
def get_thong_bao(_db):
    try: return _db.worksheet("ThongBao").get_all_records()
    except: return []

def get_exams(_db):
    try: return _db.worksheet("CauHoi").get_all_values()
    except: return []

def get_giao_trinh(_db):
    try: return _db.worksheet("GiaoTrinh").get_all_records()
    except: return []

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
    if 'vai_tro' not in st.session_state: st.session_state.vai_tro = None
    if 'bat_dau' not in st.session_state: st.session_state.bat_dau = False
    if 'diem_so' not in st.session_state: st.session_state.diem_so = 0
    if 'chi_so' not in st.session_state: st.session_state.chi_so = 0
    if 'ds_cau_hoi' not in st.session_state: st.session_state.ds_cau_hoi = []
    if 'da_nop' not in st.session_state: st.session_state.da_nop = False
    if 'time_end' not in st.session_state: st.session_state.time_end = None
    if 'choice' not in st.session_state: st.session_state.choice = None
    if 'da_luu_ket_qua' not in st.session_state: st.session_state.da_luu_ket_qua = False 

    db = ket_noi_csdl()
    if not db: 
        st.error("Không thể kết nối Database. Vui lòng kiểm tra lại.")
        st.stop()

    # ==========================================
    # --- A. GIAO DIỆN LOGIN ---
    # ==========================================
    if st.session_state.vai_tro is None:
        inject_login_css()
        
        with st.form("login_form"):
            st.markdown("""
                <div class="login-header">
                    <div class="gcpd-logo">FTO</div>
                    <div class="gcpd-title">GACHA CITY POLICE DEPARTMENT</div>
                    <div class="gcpd-subtitle">HỌC & THI TRẮC NGHIỆM LÝ THUYẾT</div>
                </div>
            """, unsafe_allow_html=True)
            
            u = st.text_input("SỐ MOMO", placeholder="Nhập số MOMO (ID) của bạn vào đây")
            p = st.text_input("MÃ BẢO MẬT", type="password", placeholder="Nhập 123")
            
            submit = st.form_submit_button("ĐĂNG NHẬP")
            if submit:
                role, name, stt = check_login(db, u, p)
                if role:
                    st.session_state.vai_tro = role
                    st.session_state.user = u
                    st.session_state.ho_ten = name
                    st.rerun()
                else: 
                    st.error("SỐ MOMO HOẶC MÃ BẢO MẬT KHÔNG CHÍNH XÁC!")

    # ==========================================
    # --- B. DASHBOARD SAU KHI ĐĂNG NHẬP ---
    # ==========================================
    else:
        inject_dashboard_css()
        role = st.session_state.vai_tro
        
        # --- LẤY DỮ LIỆU LIVE ---
        if not st.session_state.bat_dau:
            ws_hocvien = db.worksheet("HocVien")
            all_hv_vals = ws_hocvien.get_all_values()
            st.session_state.all_hv_vals_cache = all_hv_vals
            
            user_row_idx = None
            user_row_data = []
            for i, r in enumerate(all_hv_vals):
                if len(r) > 0 and str(r[0]).strip() == st.session_state.user:
                    user_row_idx = i + 1
                    user_row_data = r
                    break
            
            st.session_state.user_row_idx = user_row_idx
            
            while len(user_row_data) < 10: user_row_data.append("")
            
            st.session_state.stt = user_row_data[4]
            st.session_state.diem_cu = int(user_row_data[5]) if str(user_row_data[5]).strip().isdigit() else 0
            st.session_state.lan_thu = int(user_row_data[6]) if str(user_row_data[6]).strip().isdigit() else 0
            st.session_state.lan_that = int(user_row_data[7]) if str(user_row_data[7]).strip().isdigit() else 0
            st.session_state.luot_chinh_thuc = int(user_row_data[8]) if str(user_row_data[8]).strip().isdigit() else 0
            
            st.session_state.thi_thu_con_thieu = 5 - (st.session_state.lan_thu % 5)
            if st.session_state.stt == "Khoa": st.session_state.luot_chinh_thuc = 0
            
        else:
            user_row_idx = st.session_state.get('user_row_idx')
            all_hv_vals = st.session_state.get('all_hv_vals_cache', [])

        stt = st.session_state.get('stt', 'ChuaDuocThi')
        diem_cu = st.session_state.get('diem_cu', 0)
        lan_thu = st.session_state.get('lan_thu', 0)
        lan_that = st.session_state.get('lan_that', 0)
        luot_chinh_thuc = st.session_state.get('luot_chinh_thuc', 0)
        thi_thu_con_thieu = st.session_state.get('thi_thu_con_thieu', 5)

        # --- BẪY LỖI F5 ---
        if stt == "DangThi" and not st.session_state.bat_dau:
            try:
                ws_hocvien = db.worksheet("HocVien")
                ws_hocvien.update_cell(user_row_idx, 5, "DaThi")
                st.session_state.stt = "DaThi" 
                st.error("🚨 HỆ THỐNG PHÁT HIỆN BẠN ĐÃ TẢI LẠI TRANG (F5) HOẶC THOÁT RA ĐỘT NGỘT!")
                st.warning("Bài thi đã bị hủy. Lượt thi đã bị trừ nhưng Điểm Kỷ Lục vẫn được giữ nguyên.")
            except: pass

        # --- HIỂN THỊ BANNER ---
        if not st.session_state.bat_dau:
            st.image(BANNER_URL, use_container_width=True)

        # --- HEADER DASHBOARD THU GỌN VÀO 1 KHUNG ---
        col1, col2, col3 = st.columns([3.3, 1.2, 4.5], gap="small")
        
        with col1:
            st.markdown(f"""
                <div class="header-marker" style="display: flex; align-items: center;">
                    <div style="background-color: #fccc04; color: #031c36; width: 45px; height: 45px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 14px; margin-right: 12px; font-family: Arial, sans-serif; flex-shrink: 0;">FTO</div>
                    <div>
                        <div style="color: white; font-weight: 800; font-size: 15px; margin-bottom: 2px; text-transform: uppercase; font-family: 'Montserrat', sans-serif; white-space: nowrap;">GCPD - THÔNG TIN</div>
                        <div style="color: #fccc04; font-size: 12px; font-weight: 700; font-family: 'Montserrat', sans-serif; white-space: nowrap;">👮 {st.session_state.ho_ten} | {role.upper()}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        with col2:
            # Chèn nút đăng xuất ngay sau cột Tên
            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
            if st.button("ĐĂNG XUẤT", key="logout", use_container_width=True):
                st.session_state.clear()
                st.rerun()
                
        with col3:
            stats_html = ""
            if role == "hocvien":
                stats_html = f"""
                <div style="background-color: rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 8px; text-align: right; margin-left: auto; width: fit-content;">
                    <div style="color: #e0e0e0; font-size: 12px; margin-bottom: 2px; font-family: 'Montserrat', sans-serif;">🏆 Điểm cao nhất của Sĩ Quan: <b style="color: #4ade80; font-size: 14px;">{diem_cu}/50</b> | Đã thi thử: <b style="color: white;">{lan_thu} lần</b></div>
                    <div style="color: #e0e0e0; font-size: 12px; font-family: 'Montserrat', sans-serif;">Thi chính thức còn: <b style="color: #fccc04;">{luot_chinh_thuc} lượt</b> ( {thi_thu_con_thieu} lần thi thử nữa sẽ thêm 1 lượt)</div>
                </div>
                """
            st.markdown(stats_html, unsafe_allow_html=True)
            
        st.write("")
        
        # --- TAB MENU ---
        if role == 'Admin':
            tabs = st.tabs(["📢 THÔNG TIN", "👥 USER", "⚙️ CÂU HỎI", "📚 TÀI LIỆU", "📝 THÔNG BÁO"])
            active_tab = "Admin"
        elif role == 'GiangVien':
            tabs = st.tabs(["📢 THÔNG TIN", "👥 CẤP QUYỀN", "⚙️ CÂU HỎI", "📚 TÀI LIỆU", "📝 THÔNG BÁO"])
            active_tab = "GV"
        else:
            tabs = st.tabs(["📢 THÔNG TIN", "📚 TÀI LIỆU", "📝 THI TRẮC NGHIỆM"])
            active_tab = "HV"

        # --- GIAO DIỆN CHÍNH ---
        if not st.session_state.bat_dau:
            # --- TAB 1: THÔNG TIN (Dành cho tất cả) ---
            with tabs[0]:
                col_tb, col_xh = st.columns([1, 1])
                
                with col_tb:
                    st.subheader("📢 THÔNG BÁO MỚI NHẤT")
                    tb_data = get_thong_bao(db)
                    if tb_data:
                        for tb in reversed(tb_data):
                            st.info(f"**🗓️ {tb.get('Ngay', '')} | {tb.get('TieuDe', '')}**\n\n{tb.get('NoiDung', '')}")
                    else:
                        st.write("Hiện chưa có thông báo nào từ Giảng viên.")
                        
                    st.markdown("---")
                    st.subheader("📌 QUY CHẾ THI FTO")
                    st.markdown("""
                    - **Điều kiện thi chính thức:** Hoàn thành trọn vẹn 5 bài thi thử (đạt tối thiểu **10/15 điểm**) sẽ tự động nhận được **1 lượt** thi chính thức.
                    - Thi chính thức đạt 45/50 câu là vượt qua kì thi. 
                    - Mọi hành vi tải lại trang (F5) hoặc đóng web giữa chừng trong lúc thi chính thức sẽ bị hủy bài thi và trừ 1 lượt thi.
                    """)

                with col_xh:
                    st.subheader("🏆 BẢNG VÀNG KỶ LỤC")
                    hv_list = [r for r in all_hv_vals[1:] if len(r) >= 8 and r[2] == 'hocvien']
                    hv_list.sort(key=lambda x: (int(x[5]) if str(x[5]).isdigit() else 0, -int(x[7]) if str(x[7]).isdigit() else 0), reverse=True)
                    
                    rank_data = []
                    for idx, r in enumerate(hv_list[:10]):
                        diem_kl = int(r[5]) if str(r[5]).isdigit() else 0
                        if diem_kl == 0: continue 
                        
                        rank_str = str(idx + 1)
                        if idx == 0: rank_str = "🥇 Top 1"
                        elif idx == 1: rank_str = "🥈 Top 2"
                        elif idx == 2: rank_str = "🥉 Top 3"
                        
                        rank_data.append({
                            "Xếp Hạng": rank_str, 
                            "Sĩ Quan": r[3], 
                            "Điểm Kỷ Lục": f"{diem_kl}/50", 
                            "Đã Thi": f"{r[7]} lần"
                        })
                    
                    if rank_data:
                        st.dataframe(pd.DataFrame(rank_data), use_container_width=True, hide_index=True)
                    else:
                        st.write("Chưa có sĩ quan nào ghi danh lên Bảng Vàng.")

            # --- CÁC TAB QUẢN LÝ ---
            if active_tab in ["Admin", "GV"]:
                with tabs[1]:
                    st.subheader("✅ DANH SÁCH HỌC VIÊN")
                    headers = ["Username","Password","Role","HoTen","TrangThai","DiemKyLuc","SoLanThiThu","SoLanThiThat","LuotThiChinhThuc","DuLieuCu"]
                    clean_data = [r[:10]+[""]*(10-len(r)) for r in all_hv_vals[1:]] if len(all_hv_vals)>1 else []
                    full_df = pd.DataFrame(clean_data, columns=headers)

                    if role == 'Admin':
                        view_df = full_df; role_ops = ["hocvien", "GiangVien", "Admin"]
                    else:
                        view_df = full_df[full_df['Role'] == 'hocvien']; role_ops = ["hocvien"]

                    edited = st.data_editor(
                        view_df, use_container_width=True, num_rows="dynamic", hide_index=True,
                        column_config={
                            "TrangThai": st.column_config.SelectboxColumn("Trạng Thái", options=["ChuaDuocThi","DuocThi","DangThi","DaThi","Khoa"], required=True),
                            "Role": st.column_config.SelectboxColumn("Vai Trò", options=role_ops, required=True),
                            "Password": st.column_config.TextColumn("Mật Khẩu"),
                            "DiemKyLuc": st.column_config.NumberColumn("Điểm Kỷ Lục"),
                            "SoLanThiThu": st.column_config.NumberColumn("Thi thử (>=10đ)"),
                            "SoLanThiThat": st.column_config.NumberColumn("Đã thi thật"),
                            "LuotThiChinhThuc": st.column_config.NumberColumn("Ví Lượt Thi"),
                            "DuLieuCu": st.column_config.TextColumn("Không dùng (Ẩn)", disabled=True)
                        }
                    )
                    if st.button("LƯU THAY ĐỔI", type="primary"):
                        final_df = edited if role == 'Admin' else pd.concat([full_df[full_df['Role'] != 'hocvien'], edited], ignore_index=True)
                        if save_to_sheet(db, "HocVien", final_df): st.success("✅ Đã cập nhật!"); time.sleep(1); st.rerun()

                with tabs[2]:
                    st.subheader("⚙️ NGÂN HÀNG CÂU HỎI TRẮC NGHIỆM")
                    q_vals = get_exams(db)
                    q_headers = ["CauHoi","A","B","C","D","DapAn_Dung","GiaiThich"]
                    q_data = [r[:7]+[""]*(7-len(r)) for r in q_vals[1:]] if len(q_vals)>1 else []
                    q_df = pd.DataFrame(q_data, columns=q_headers)
                    q_edit = st.data_editor(q_df, num_rows="dynamic", use_container_width=True)
                    if st.button("LƯU CÂU HỎI"):
                        if save_to_sheet(db, "CauHoi", q_edit): st.success("Đã lưu!"); time.sleep(1); st.rerun()

                with tabs[3]:
                    st.subheader("📚 TÀI LIỆU FTO GCPD")
                    data = get_giao_trinh(db)
                    if data:
                        for l in data:
                            with st.expander(f"📖 {l.get('BaiHoc','Bài học')}"):
                                render_mixed_content(l.get('NoiDung',''))
                    else: st.warning("Chưa có giáo trình.")

                with tabs[4]:
                    st.subheader("📝 QUẢN LÝ THÔNG BÁO TRANG CHỦ")
                    try:
                        ws_tb = db.worksheet("ThongBao")
                        tb_vals = ws_tb.get_all_values()
                    except:
                        ws_tb = db.add_worksheet(title="ThongBao", rows="50", cols="3")
                        ws_tb.append_row(["Ngay", "TieuDe", "NoiDung"])
                        tb_vals = ws_tb.get_all_values()
                        
                    tb_headers = ["Ngay", "TieuDe", "NoiDung"]
                    tb_data = [r[:3]+[""]*(3-len(r)) for r in tb_vals[1:]] if len(tb_vals) > 1 else []
                    tb_df = pd.DataFrame(tb_data, columns=tb_headers)
                    tb_edit = st.data_editor(tb_df, num_rows="dynamic", use_container_width=True)
                    if st.button("LƯU THÔNG BÁO"):
                        if save_to_sheet(db, "ThongBao", tb_edit): 
                            st.success("Đã đăng thông báo thành công!")
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()

            elif active_tab == "HV":
                with tabs[1]: 
                    st.subheader("📚 TÀI LIỆU ÔN TẬP FTO GCPD")
                    data = get_giao_trinh(db)
                    if data:
                        for l in data:
                            with st.expander(f"📖 {l.get('BaiHoc','Bài học')}"):
                                render_mixed_content(l.get('NoiDung',''))
                    else: st.warning("Chưa có dữ liệu.")

                with tabs[2]:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("📝 THI THỬ (Yêu cầu >= 10đ)"):
                            all_qs = get_exams(db)[1:] 
                            if len(all_qs)>0: 
                                qs = random.sample(all_qs, min(15, len(all_qs))) 
                            st.session_state.bat_dau = True; st.session_state.ds_cau_hoi = qs
                            st.session_state.chi_so = 0; st.session_state.diem_so = 0; st.session_state.mode = 'thu'
                            st.session_state.da_luu_ket_qua = False
                            st.rerun()
                    with c2:
                        if st.button("🚨 BẮT ĐẦU THI CHÍNH THỨC"):
                            try:
                                all_qs = get_exams(db)[1:]

                                if stt == "DaThi" and diem_cu >= 45:
                                    st.success("🎉 Bạn đã THI ĐỖ kỳ thi này rồi, không cần thi lại nữa!")
                                elif stt == "Khoa":
                                    st.error("⛔ Tài khoản của bạn đang bị KHÓA.")
                                elif luot_chinh_thuc <= 0:
                                    st.error(f"⛔ Bạn đã hết lượt thi. Hãy hoàn thành thêm {thi_thu_con_thieu} bài thi thử (>=10 điểm) nữa hoặc nhờ Giảng viên nạp thêm lượt!")
                                else:
                                    if len(all_qs) > 0: 
                                        qs = random.sample(all_qs, min(50, len(all_qs)))
                                        new_lan_that = lan_that + 1
                                        new_luot_chinh_thuc = luot_chinh_thuc - 1 
                                        
                                        ws_hocvien = db.worksheet("HocVien")
                                        ws_hocvien.update_cell(user_row_idx, 5, "DangThi")
                                        ws_hocvien.update_cell(user_row_idx, 8, str(new_lan_that))   
                                        ws_hocvien.update_cell(user_row_idx, 9, str(new_luot_chinh_thuc))   
                                        st.cache_data.clear() 
                                        
                                        st.session_state.bat_dau = True
                                        st.session_state.ds_cau_hoi = qs
                                        st.session_state.chi_so = 0
                                        st.session_state.diem_so = 0
                                        st.session_state.mode = 'that'
                                        st.session_state.da_luu_ket_qua = False
                                        st.rerun()
                                    else: st.error("Ngân hàng câu hỏi đang trống!")
                            except Exception as e: 
                                st.error(f"Lỗi: {str(e)}")

        # ==========================================
        # --- MÀN HÌNH ĐANG TRONG PHÒNG THI ---
        # ==========================================
        if st.session_state.bat_dau:
            qs = st.session_state.ds_cau_hoi
            idx = st.session_state.chi_so
            
            if st.session_state.mode == 'thu':
                st.info("📝 ĐANG THI THỬ")
                if st.button("❌ DỪNG LÀM BÀI", key="stop_exam"):
                    st.session_state.bat_dau = False
                    st.session_state.ds_cau_hoi = []
                    st.session_state.da_luu_ket_qua = False
                    st.rerun()
            else:
                st.error("🚨 ĐANG THI CHÍNH THỨC (CẤM TẢI LẠI TRANG)")
                if st.button("🏳️ KHÓ QUÁ BỎ KHÔNG THI NỮA", key="give_up_exam"):
                    try:
                        ws_hocvien = db.worksheet("HocVien")
                        ws_hocvien.update_cell(user_row_idx, 5, "DaThi")
                        if st.session_state.diem_so > diem_cu:
                            ws_hocvien.update_cell(user_row_idx, 6, str(st.session_state.diem_so))
                        st.cache_data.clear() 
                    except: pass
                    st.session_state.bat_dau = False
                    st.session_state.ds_cau_hoi = []
                    st.session_state.da_luu_ket_qua = False
                    st.rerun()

            # --- KHI HOÀN THÀNH BÀI THI ---
            if idx >= len(qs):
                if not st.session_state.get('da_luu_ket_qua', False):
                    try:
                        ws_hocvien = db.worksheet("HocVien")
                        if st.session_state.get('mode') == 'that':
                            ws_hocvien.update_cell(user_row_idx, 5, "DaThi")
                            if st.session_state.diem_so > diem_cu:
                                ws_hocvien.update_cell(user_row_idx, 6, str(st.session_state.diem_so))
                        else:
                            if st.session_state.diem_so >= 10:
                                new_lan_thu = lan_thu + 1
                                ws_hocvien.update_cell(user_row_idx, 7, str(new_lan_thu))
                                if new_lan_thu % 5 == 0:
                                    new_luot_chinh_thuc = luot_chinh_thuc + 1
                                    ws_hocvien.update_cell(user_row_idx, 9, str(new_luot_chinh_thuc))
                        st.cache_data.clear() 
                    except: pass
                    st.session_state.da_luu_ket_qua = True

                if st.session_state.get('mode') == 'that':
                    if st.session_state.diem_so >= 45:
                        st.balloons()
                        st.success(f"KẾT QUẢ: {st.session_state.diem_so}/{len(qs)}")
                        st.success("🎉 CHÚC MỪNG BẠN ĐÃ VƯỢT QUA KÌ THI CHÍNH THỨC!")
                    else:
                        st.error(f"KẾT QUẢ: {st.session_state.diem_so}/{len(qs)}")
                        st.warning("❌ Bạn đã rớt kỳ thi này.")
                        
                    if st.session_state.diem_so > diem_cu:
                        st.success("🏆 CHÚC MỪNG! BẠN ĐÃ PHÁ KỶ LỤC ĐIỂM SỐ CỦA CHÍNH MÌNH!")
                else:
                    st.balloons()
                    st.success(f"KẾT QUẢ THI THỬ: {st.session_state.diem_so}/{len(qs)}")
                    
                    if st.session_state.diem_so >= 10:
                        st.success("💡 Tuyệt vời! Điểm của bạn >= 10. Hệ thống đã cộng cho bạn 1 lượt hoàn thành thi thử hợp lệ.")
                    else:
                        st.warning("⚠️ Rất tiếc, bạn cần đạt tối thiểu 10/15 điểm để được tính là 1 lần hoàn thành thi thử hợp lệ. Lần thi này sẽ không được cộng dồn.")

                if st.button("🏠 QUAY VỀ BẢNG ĐIỀU KHIỂN"):
                    st.session_state.bat_dau = False
                    st.session_state.ds_cau_hoi = []
                    st.session_state.da_luu_ket_qua = False
                    st.rerun()
                st.stop()

            # --- GIAO DIỆN LÀM BÀI ---
            q = qs[idx]
            while len(q)<7: q.append("")
            
            if not st.session_state.da_nop:
                if not st.session_state.time_end: st.session_state.time_end = time.time() + THOI_GIAN_THI
                left = int(st.session_state.time_end - time.time())
                if left <= 0: st.session_state.da_nop = True; st.session_state.choice = None; st.rerun()

                st.markdown(f"<div class='timer-box'>⏳ {left}</div>", unsafe_allow_html=True)
                st.markdown(f"**Câu {idx+1}/{len(qs)}:**")
                st.markdown(f"<div class='question-box'>{q[0]}</div>", unsafe_allow_html=True)
                
                ans = st.radio("Chọn:", [f"A. {q[1]}", f"B. {q[2]}", f"C. {q[3]}", f"D. {q[4]}"], key=f"q_{idx}")
                
                st.write("")
                if st.button("CHỐT ĐÁP ÁN"):
                    st.session_state.choice = ans.split('.')[0] if ans else None
                    st.session_state.da_nop = True; st.rerun()
                time.sleep(1); st.rerun()
            else:
                st.markdown(f"**Câu {idx+1}/{len(qs)}:**")
                st.markdown(f"<div class='question-box'>{q[0]}</div>", unsafe_allow_html=True)
                res = st.session_state.choice
                true = str(q[5]).strip().upper()
                if res == true: st.success(f"✅ CHÍNH XÁC! ({res})")
                else: st.error(f"❌ SAI! Chọn: {res} | Đúng: {true}")
                if str(q[6]).strip(): st.markdown(f"<div class='explain-box'>💡 {q[6]}</div>", unsafe_allow_html=True)
                st.write("")
                
                if st.button("TIẾP THEO ➡️"):
                    if res == true: st.session_state.diem_so += 1
                    st.session_state.chi_so += 1
                    st.session_state.da_nop = False; st.session_state.time_end = None; st.rerun()

if __name__ == "__main__":
    main()




