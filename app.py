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
GIOI_HAN_RELOAD = 3 # Giới hạn tối đa số lần F5 / tải lại trang

# --- 3. CSS GIAO DIỆN ĐĂNG NHẬP ---
def inject_login_css():
    st.markdown("""
        <style>
        .stApp { background-color: #e9ecef !important; font-family: 'Segoe UI', sans-serif; }
        .block-container { max-width: 450px !important; padding-top: 8vh !important; background: transparent !important; border: none !important; box-shadow: none !important; }
        [data-testid="stForm"] { background-color: white !important; border-radius: 12px !important; border: none !important; box-shadow: 0 10px 30px rgba(0,0,0,0.15) !important; overflow: hidden !important; padding: 0 !important; }
        .login-header { background-color: #031c36; padding: 40px 20px 30px 20px; text-align: center; margin-bottom: 20px; margin-top: -1rem; }
        .gcpd-logo { background-color: #fccc04; color: #031c36; width: 85px; height: 85px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 24px; margin: 0 auto 20px auto; }
        .gcpd-title { color: white; font-size: 22px; font-weight: 800; text-transform: uppercase; margin-bottom: 8px; line-height: 1.3; }
        .gcpd-subtitle { color: #94a3b8; font-size: 13px; font-weight: 600; letter-spacing: 1.5px; }
        .stTextInput { padding: 0 30px !important; margin-bottom: 5px !important; }
        .stTextInput label p { color: #64748b !important; font-size: 13px !important; font-weight: 700 !important; text-transform: uppercase; }
        .stTextInput input { border-radius: 8px !important; border: 1px solid #e2e8f0 !important; padding: 12px 15px !important; font-size: 15px !important;}
        .stTextInput input:focus { border-color: #031c36 !important; box-shadow: 0 0 0 1px #031c36 !important; }
        .stButton { padding: 15px 30px 35px 30px !important; }
        .stButton button { width: 100% !important; background-color: #031c36 !important; border-radius: 8px !important; padding: 12px !important; border: none !important; }
        .stButton button p { color: #fccc04 !important; font-weight: 800 !important; font-size: 16px !important; margin: 0; text-transform: uppercase; }
        .stButton button:hover { background-color: #021224 !important; }
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

# --- 3.1 CSS GIAO DIỆN QUẢN LÝ / THI CỬ (DASHBOARD) ---
def inject_dashboard_css():
    st.markdown("""
        <style>
        .stApp { background-color: #dbe2ef !important; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
        .block-container { background-color: #ffffff !important; border: 3px solid #112d4e !important; border-radius: 15px !important; box-shadow: 0 10px 30px rgba(0,0,0,0.15) !important; padding: 2.5rem 2rem !important; margin-top: 2rem !important; margin-bottom: 2rem !important; max-width: 900px; }
        @media (max-width: 768px) { .block-container { padding: 1.5rem 1rem !important; margin-top: 0.5rem !important; margin-bottom: 0.5rem !important; border: 2px solid #112d4e !important; border-radius: 10px !important; } }
        .stMarkdown, .stText, p, h1, h2, h3, label { color: #112d4e !important; }
        
        /* Chỉnh Tabs */
        div[data-baseweb="tab-list"] { position: sticky; top: 0; z-index: 999; background-color: #ffffff; padding-top: 15px; border-bottom: 2px solid #e0e0e0; gap: 8px; }
        .stTabs [data-baseweb="tab"] { height: 40px; padding: 0 20px; background-color: transparent; border-radius: 8px 8px 0 0; color: #7f8c8d !important; font-size: 14px; font-weight: 700; border: none; transition: all 0.3s ease; }
        .stTabs [aria-selected="true"] { background-color: #f8f9fa !important; color: #0b2545 !important; border-top: 3px solid #134074 !important; border-left: 1px solid #e0e0e0 !important; border-right: 1px solid #e0e0e0 !important; }
        
        /* Hộp câu hỏi */
        .question-box { background: #f8f9fa; padding: 20px; border-left: 5px solid #134074; border-radius: 8px; font-weight: 600; color: #112d4e !important; margin-bottom: 15px; font-size: 16px; line-height: 1.6; box-shadow: 0 4px 10px rgba(0,0,0,0.04); }
        .stRadio div[role="radiogroup"] label p { color: #2c3e50 !important; font-weight: 500; font-size: 15px; }
        .explain-box { background: #e8f4f8; padding: 15px; border-radius: 8px; color: #0c5460 !important; font-size: 14px; font-weight: 500; border: 1px solid #bee5eb; margin-top: 10px; }
        .timer-box { font-family: 'Courier New', monospace; font-size: 24px; font-weight: bold; color: white !important; background: linear-gradient(135deg, #e63946, #d62828); padding: 5px 20px; border-radius: 20px; width: fit-content; margin: 0 auto 15px auto; box-shadow: 0 4px 10px rgba(230, 57, 70, 0.3); }
        
        /* Buttons */
        .stButton button { background: linear-gradient(135deg, #134074, #0b2545) !important; border: none !important; border-radius: 6px !important; box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important; transition: all 0.2s ease-in-out !important; }
        .stButton button p { color: white !important; font-weight: 600 !important; font-size: 14px !important; }
        .stButton button:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important; }
        
        /* Nút phụ (Đăng xuất, Dừng thi) */
        div[data-testid="column"] button:has(div:contains("ĐĂNG XUẤT")), button:has(div:contains("DỪNG LÀM BÀI")) { background: transparent !important; border: 2px solid #e63946 !important; box-shadow: none !important; }
        div[data-testid="column"] button:has(div:contains("ĐĂNG XUẤT")) p, button:has(div:contains("DỪNG LÀM BÀI")) p { color: #e63946 !important; }
        div[data-testid="column"] button:has(div:contains("ĐĂNG XUẤT")):hover, button:has(div:contains("DỪNG LÀM BÀI")):hover { background: #e63946 !important; }
        div[data-testid="column"] button:has(div:contains("ĐĂNG XUẤT")):hover p, button:has(div:contains("DỪNG LÀM BÀI")):hover p { color: white !important; }
        
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
    if 'vai_tro' not in st.session_state: st.session_state.vai_tro = None
    if 'bat_dau' not in st.session_state: st.session_state.bat_dau = False
    if 'diem_so' not in st.session_state: st.session_state.diem_so = 0
    if 'chi_so' not in st.session_state: st.session_state.chi_so = 0
    if 'ds_cau_hoi' not in st.session_state: st.session_state.ds_cau_hoi = []
    if 'da_nop' not in st.session_state: st.session_state.da_nop = False
    if 'time_end' not in st.session_state: st.session_state.time_end = None
    if 'choice' not in st.session_state: st.session_state.choice = None
    if 'reload_count' not in st.session_state: st.session_state.reload_count = 0

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
                    <div class="gcpd-logo">GCPD</div>
                    <div class="gcpd-title">FTO GACHA CITY<br>POLICE DEPARTMENT</div>
                    <div class="gcpd-subtitle">TRAINING & ASSESSMENT</div>
                </div>
            """, unsafe_allow_html=True)
            
            u = st.text_input("SỐ HIỆU", placeholder="Nhập số hiệu của bạn...")
            p = st.text_input("MÃ BẢO MẬT", type="password", placeholder="••••••••")
            
            submit = st.form_submit_button("ĐĂNG NHẬP")
            if submit:
                role, name, stt = check_login(db, u, p)
                if role:
                    st.session_state.vai_tro = role
                    st.session_state.user = u
                    st.session_state.ho_ten = name
                    st.rerun()
                else: 
                    st.error("SỐ HIỆU HOẶC MÃ BẢO MẬT KHÔNG CHÍNH XÁC!")


    # ==========================================
    # --- B. DASHBOARD SAU KHI ĐĂNG NHẬP ---
    # ==========================================
    else:
        inject_dashboard_css()
        
        # --- HEADER DASHBOARD ĐỒNG BỘ MỚI ---
        col1, col2 = st.columns([4, 1.5])
        with col1:
            st.markdown(f"""
                <div style="background-color: #031c36; padding: 12px 20px; border-radius: 10px; display: flex; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <div style="background-color: #fccc04; color: #031c36; width: 45px; height: 45px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 14px; margin-right: 15px;">GCPD</div>
                    <div>
                        <div style="color: white; font-weight: 800; font-size: 16px; margin-bottom: 2px; text-transform: uppercase;">GCPD DASHBOARD</div>
                        <div style="color: #fccc04; font-size: 13px; font-weight: 600;">👮 {st.session_state.ho_ten} | {st.session_state.vai_tro.upper()}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True) # Căn lề cho nút
            if st.button("🚪 ĐĂNG XUẤT", key="logout", use_container_width=True):
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
                    if st.session_state.get('mode') == 'that':
                        try:
                            ws = db.worksheet("HocVien")
                            cell = ws.find(st.session_state.user)
                            ws.update_cell(cell.row, 5, "DaThi")
                            ws.update_cell(cell.row, 6, str(st.session_state.diem_so))
                            ws.update_cell(cell.row, 7, "") # Xóa tiến trình thi
                        except: pass
                    st.session_state.bat_dau = False
                    st.session_state.ds_cau_hoi = []
                    st.rerun()
                st.stop()

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
                    
                    # --- LƯU TIẾN TRÌNH & SỐ LẦN RELOAD ---
                    if st.session_state.get('mode') == 'that':
                        try:
                            ws = db.worksheet("HocVien")
                            cell = ws.find(st.session_state.user)
                            idx_str = ','.join(map(str, st.session_state.selected_indices))
                            
                            # Cấu trúc: chi_so | diem_so | idx_str | reload_count
                            new_tien_trinh = f"{st.session_state.chi_so}|{st.session_state.diem_so}|{idx_str}|{st.session_state.get('reload_count', 0)}"
                            ws.update_cell(cell.row, 7, new_tien_trinh)
                        except: pass

                    st.session_state.da_nop = False; st.session_state.time_end = None; st.rerun()

        else:
            if active_tab in ["Admin", "GV"]:
                with tabs[0]:
                    st.subheader("✅ DANH SÁCH HỌC VIÊN")
                    vals = db.worksheet("HocVien").get_all_values()
                    headers = ["Username","Password","Role","HoTen","TrangThai","Diem","TienTrinh"]
                    clean_data = [r[:7]+[""]*(7-len(r)) for r in vals[1:]] if len(vals)>1 else []
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
                            "TienTrinh": st.column_config.TextColumn("Tiến Trình (Ẩn)", disabled=True)
                        }
                    )
                    if st.button("LƯU THAY ĐỔI", type="primary"):
                        final_df = edited if role == 'Admin' else pd.concat([full_df[full_df['Role'] != 'hocvien'], edited], ignore_index=True)
                        if save_to_sheet(db, "HocVien", final_df): st.success("✅ Đã cập nhật!"); time.sleep(1); st.rerun()

                with tabs[1]:
                    st.subheader("⚙️ NGÂN HÀNG CÂU HỎI TRẮC NGHIỆM")
                    q_vals = get_exams(db)
                    q_headers = ["CauHoi","A","B","C","D","DapAn_Dung","GiaiThich"]
                    q_data = [r[:7]+[""]*(7-len(r)) for r in q_vals[1:]] if len(q_vals)>1 else []
                    q_df = pd.DataFrame(q_data, columns=q_headers)
                    q_edit = st.data_editor(q_df, num_rows="dynamic", use_container_width=True)
                    if st.button("LƯU CÂU HỎI"):
                        if save_to_sheet(db, "CauHoi", q_edit): st.success("Đã lưu!"); time.sleep(1); st.rerun()

                with tabs[2]:
                    st.subheader("📚 TÀI LIỆU FTO GCPD")
                    data = get_giao_trinh(db)
                    if data:
                        for l in data:
                            with st.expander(f"📖 {l.get('BaiHoc','Bài học')}"):
                                render_mixed_content(l.get('NoiDung',''))
                    else: st.warning("Chưa có giáo trình.")

            elif active_tab == "HV":
                with tabs[0]: 
                    st.subheader("📚 TÀI LIỆU ÔN TẬP FTO GCPD")
                    data = get_giao_trinh(db)
                    if data:
                        for l in data:
                            with st.expander(f"📖 {l.get('BaiHoc','Bài học')}"):
                                render_mixed_content(l.get('NoiDung',''))
                    else: st.warning("Chưa có dữ liệu.")

                with tabs[1]:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("📝 THI THỬ"):
                            all_qs = get_exams(db)[1:] 
                            if len(all_qs)>0: 
                                qs = random.sample(all_qs, min(30, len(all_qs)))
                            st.session_state.bat_dau = True; st.session_state.ds_cau_hoi = qs
                            st.session_state.chi_so = 0; st.session_state.diem_so = 0; st.session_state.mode = 'thu'
                            st.rerun()
                    with c2:
                        if st.button("🚨 THI CHÍNH THỨC / TIẾP TỤC THI"):
                            try:
                                ws = db.worksheet("HocVien")
                                cell = ws.find(st.session_state.user)
                                row_data = ws.row_values(cell.row)
                                
                                stt = row_data[4] if len(row_data) >= 5 else "ChuaDuocThi"
                                tien_trinh = row_data[6] if len(row_data) >= 7 else ""
                                
                                all_qs = get_exams(db)[1:]

                                if stt == "DuocThi":
                                    if len(all_qs) > 0: 
                                        selected_indices = random.sample(range(len(all_qs)), min(50, len(all_qs)))
                                        qs = [all_qs[i] for i in selected_indices]
                                        
                                        idx_str = ','.join(map(str, selected_indices))
                                        
                                        # Bắt đầu thi lần đầu -> reload_count = 0
                                        st.session_state.reload_count = 0 
                                        new_tien_trinh = f"0|0|{idx_str}|0"
                                        
                                        ws.update_cell(cell.row, 5, "DangThi")
                                        ws.update_cell(cell.row, 7, new_tien_trinh)
                                        
                                        st.session_state.bat_dau = True
                                        st.session_state.ds_cau_hoi = qs
                                        st.session_state.chi_so = 0
                                        st.session_state.diem_so = 0
                                        st.session_state.mode = 'that'
                                        st.session_state.selected_indices = selected_indices
                                        st.rerun()
                                    else:
                                        st.error("Ngân hàng câu hỏi đang trống!")

                                elif stt == "DangThi":
                                    if tien_trinh:
                                        parts = tien_trinh.split('|')
                                        if len(parts) >= 3:
                                            saved_chi_so = int(parts[0])
                                            saved_diem_so = int(parts[1])
                                            saved_indices = [int(x) for x in parts[2].split(',') if x.strip()]
                                            
                                            # Đọc số lần reload từ Sheet
                                            reload_count = int(parts[3]) if len(parts) >= 4 else 0
                                            
                                            # KIỂM TRA GIỚI HẠN
                                            if reload_count >= GIOI_HAN_RELOAD:
                                                st.error("⛔ BẠN ĐÃ VƯỢT QUÁ SỐ LẦN TẢI LẠI TRANG (TỐI ĐA 3 LẦN)!")
                                                st.error("Hệ thống phát hiện dấu hiệu bất thường. Tài khoản đã bị KHÓA. Vui lòng liên hệ Giảng viên.")
                                                try: ws.update_cell(cell.row, 5, "Khoa") # Khóa luôn user
                                                except: pass
                                            else:
                                                # Cho phép thi tiếp & cộng thêm 1 lần reload
                                                reload_count += 1
                                                st.session_state.reload_count = reload_count
                                                
                                                qs = [all_qs[i] for i in saved_indices if i < len(all_qs)]
                                                
                                                st.session_state.bat_dau = True
                                                st.session_state.ds_cau_hoi = qs
                                                st.session_state.chi_so = saved_chi_so
                                                st.session_state.diem_so = saved_diem_so
                                                st.session_state.mode = 'that'
                                                st.session_state.selected_indices = saved_indices
                                                
                                                # Cập nhật số lần reload mới lên sheet
                                                new_tien_trinh = f"{saved_chi_so}|{saved_diem_so}|{parts[2]}|{reload_count}"
                                                try: ws.update_cell(cell.row, 7, new_tien_trinh)
                                                except: pass
                                                
                                                st.warning(f"🔄 Đã khôi phục bài thi! (Bạn còn {GIOI_HAN_RELOAD - reload_count} lần tải lại trang)")
                                                time.sleep(2.5)
                                                st.rerun()
                                        else:
                                            st.error("Dữ liệu tiến trình bị lỗi. Báo Giảng viên đổi Trạng thái thành 'DuocThi' để thi lại.")
                                    else:
                                        st.error("Không tìm thấy tiến trình cũ. Báo Giảng viên đổi Trạng thái thành 'DuocThi' để thi lại.")
                                else:
                                    st.error(f"⛔ Bạn chưa được cấp quyền Thi lúc này! (Trạng thái: {stt})")
                            except Exception as e: 
                                st.error(f"Lỗi: {str(e)}")

if __name__ == "__main__":
    main()
