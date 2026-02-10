import streamlit as st
import time

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="FTO System",
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

THOI_GIAN_THI = 30

# --- 3. CSS GIAO DIỆN ---
def inject_css():
    st.markdown("""
        <style>
        .block-container {
            padding-top: 5rem !important;
            padding-bottom: 3rem !important;
            max-width: 900px;
        }
        .gcpd-title {
            color: #002147; font-size: 22px; font-weight: 900; 
            text-align: center; text-transform: uppercase; 
            margin-bottom: 5px; letter-spacing: 1px;
        }
        .user-info {
            background-color: #f1f3f4; color: #002147;
            padding: 4px 12px; border-radius: 20px;
            font-size: 13px; font-weight: 700; text-align: center;
            border: 1px solid #dadce0; display: inline-block;
        }
        
        /* STICKY TABS */
        div[data-baseweb="tab-list"] {
            position: sticky; top: 3rem; z-index: 999;
            background-color: white; padding-top: 10px;
            border-bottom: 1px solid #eee; gap: 4px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 35px; padding: 0 12px;
            background-color: #fff; border-radius: 6px 6px 0 0;
            color: #555; font-size: 12px; font-weight: 700;
            border: 1px solid #eee; border-bottom: none;
        }
        .stTabs [aria-selected="true"] {
            background-color: #002147 !important; color: #FFD700 !important;
            border-top: 2px solid #FFD700 !important;
        }

        .question-box {
            background: #fff; padding: 15px; 
            border-left: 3px solid #002147;
            border-radius: 4px; font-weight: 600; color: #333; 
            margin-bottom: 10px; font-size: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .timer-box {
            font-family: monospace; font-size: 28px; font-weight: bold; color: #d32f2f;
            text-align: center; background: #fff; border: 2px solid #ffcdd2;
            border-radius: 8px; width: 80px; margin: 0 auto 10px auto;
        }
        .stButton button {
            background: #002147 !important; color: #FFD700 !important;
            font-weight: 700 !important; font-size: 13px !important;
            padding: 0.4rem 1rem !important; border-radius: 4px !important;
            border: none !important; box-shadow: 0 2px 4px rgba(0,0,0,0.15) !important;
        }
        .stButton button:hover { transform: translateY(-1px); }
        
        div[data-testid="column"] button[key="logout"], button[key="stop_exam"] {
             background: white !important; color: #d32f2f !important;
             border: 1px solid #d32f2f !important; box-shadow: none !important;
        }
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

# --- 4. KẾT NỐI DATABASE (CÓ CACHING ĐỂ SỬA LỖI 429) ---
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
        # Không cache login để đảm bảo bảo mật và cập nhật trạng thái mới nhất
        rows = db.worksheet("HocVien").get_all_values()
        for r in rows[1:]:
            if len(r) < 3: continue
            if str(r[0]).strip() == str(u).strip() and str(r[1]).strip() == str(p).strip():
                return str(r[2]).strip(), str(r[3]).strip(), (str(r[4]).strip() if len(r)>4 else "ChuaDuocThi")
    except: pass
    return None, None, None

def save_to_sheet(db, sheet_name, df_to_save):
    try:
        ws = db.worksheet(sheet_name)
        ws.clear()
        data = [df_to_save.columns.tolist()] + df_to_save.values.tolist()
        ws.update(data)
        st.cache_data.clear() # Xóa cache sau khi lưu để cập nhật dữ liệu mới
        return True
    except Exception as e:
        st.error(f"Lỗi lưu: {e}")
        return False

# Cache dữ liệu câu hỏi để tránh đọc liên tục gây lỗi 429
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
        if line.startswith(('http://', 'https://')):
            try: st.image(line, use_column_width=True)
            except: st.error("Lỗi ảnh")
        elif line: st.markdown(line, unsafe_allow_html=True)

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
        with c1: st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", use_column_width=True)
        with c2: st.markdown('<div class="gcpd-title">ACADEMY LOGIN</div>', unsafe_allow_html=True)
        
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
            tabs = st.tabs(["📚 TÀI LIỆU", "📝 THI CỬ"])
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
                st.error("🚨 SÁT HẠCH CHÍNH THỨC")

            qs = st.session_state.ds_cau_hoi
            idx = st.session_state.chi_so
            
            if idx >= len(qs):
                st.balloons()
                st.success(f"KẾT QUẢ: {st.session_state.diem_so}/{len(qs)}")
                if st.button("KẾT THÚC"):
                    if st.session_state.get('mode') == 'that':
                        try:
                            ws = db.worksheet("HocVien")
                            cell = ws.find(st.session_state.user)
                            ws.update_cell(cell.row, 5, "DaThi")
                            ws.update_cell(cell.row, 6, str(st.session_state.diem_so))
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
                st.markdown(f"**Câu {idx+1}:**")
                st.markdown(f"<div class='question-box'>{q[0]}</div>", unsafe_allow_html=True)
                
                # Dynamic Key để tránh lỗi duplicate ID
                ans = st.radio("Chọn:", [f"A. {q[1]}", f"B. {q[2]}", f"C. {q[3]}", f"D. {q[4]}"], key=f"q_{idx}")
                
                st.write("")
                if st.button("CHỐT ĐÁP ÁN"):
                    st.session_state.choice = ans.split('.')[0] if ans else None
                    st.session_state.da_nop = True; st.rerun()
                time.sleep(1); st.rerun()
            else:
                st.markdown(f"**Câu {idx+1}:**")
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

        else:
            if active_tab in ["Admin", "GV"]:
                with tabs[0]:
                    st.subheader("✅ DANH SÁCH HỌC VIÊN")
                    vals = db.worksheet("HocVien").get_all_values()
                    headers = ["Username","Password","Role","HoTen","TrangThai","Diem"]
                    clean_data = [r[:6]+[""]*(6-len(r)) for r in vals[1:]] if len(vals)>1 else []
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
                            "Password": st.column_config.TextColumn("Mật Khẩu")
                        }
                    )
                    if st.button("LƯU THAY ĐỔI", type="primary"):
                        final_df = edited if role == 'Admin' else pd.concat([full_df[full_df['Role'] != 'hocvien'], edited], ignore_index=True)
                        if save_to_sheet(db, "HocVien", final_df): st.success("✅ Đã cập nhật!"); time.sleep(1); st.rerun()

                with tabs[1]:
                    st.subheader("⚙️ NGÂN HÀNG CÂU HỎI")
                    q_vals = get_exams(db)
                    q_headers = ["CauHoi","A","B","C","D","DapAn_Dung","GiaiThich"]
                    q_data = [r[:7]+[""]*(7-len(r)) for r in q_vals[1:]] if len(q_vals)>1 else []
                    q_df = pd.DataFrame(q_data, columns=q_headers)
                    q_edit = st.data_editor(q_df, num_rows="dynamic", use_container_width=True)
                    if st.button("LƯU CÂU HỎI"):
                        if save_to_sheet(db, "CauHoi", q_edit): st.success("Đã lưu!"); time.sleep(1); st.rerun()

                with tabs[2]:
                    st.subheader("📚 TÀI LIỆU")
                    data = get_giao_trinh(db)
                    if data:
                        for l in data:
                            with st.expander(f"📖 {l.get('BaiHoc','Bài học')}"):
                                render_mixed_content(l.get('NoiDung',''))
                    else: st.warning("Chưa có giáo trình.")

            elif active_tab == "HV":
                with tabs[0]: 
                    st.subheader("📚 TÀI LIỆU ÔN TẬP")
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
                            qs = get_exams(db)[1:]; 
                            if len(qs)>0: qs = random.sample(qs, min(10, len(qs)))
                            st.session_state.bat_dau = True; st.session_state.ds_cau_hoi = qs
                            st.session_state.chi_so = 0; st.session_state.diem_so = 0; st.session_state.mode = 'thu'
                            st.rerun()
                    with c2:
                        if st.button("🚨 SÁT HẠCH"):
                            allow, msg = False, ""
                            try:
                                ws = db.worksheet("HocVien")
                                cell = ws.find(st.session_state.user)
                                stt = ws.cell(cell.row, 5).value
                                if stt == "DuocThi": ws.update_cell(cell.row, 5, "DangThi"); allow = True
                                else: msg = f"⛔ Chưa được cấp quyền! ({stt})"
                            except Exception as e: msg = f"Lỗi: {str(e)}"

                            if allow:
                                qs = get_exams(db)[1:]; st.session_state.bat_dau = True
                                st.session_state.ds_cau_hoi = qs; st.session_state.chi_so = 0
                                st.session_state.diem_so = 0; st.session_state.mode = 'that'; st.rerun()
                            else: st.error(msg)

if __name__ == "__main__":
    main()
