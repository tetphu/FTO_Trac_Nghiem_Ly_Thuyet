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
        .block-container {padding-top: 3rem !important; padding-bottom: 5rem !important;}
        
        .gcpd-title {
            color:#002147; font-size:28px; font-weight:900; 
            text-align:center; text-transform:uppercase; margin-bottom:20px;
        }
        
        .user-info {
            background-color: #f0f2f6; color: #002147;
            padding: 10px 20px; border-radius: 10px;
            font-weight: bold; text-align: center;
            border-left: 5px solid #002147;
            display: block; margin-bottom: 15px;
        }
        
        .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: transparent; }
        .stTabs [data-baseweb="tab"] {
            background-color: #ffffff; border-radius: 5px 5px 0 0;
            color: #002147; font-weight: 600;
            border: 1px solid #e0e0e0; border-bottom: none;
            padding: 10px 20px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #002147 !important; color: #FFD700 !important;
        }

        .timer-box {
            font-size:45px; font-weight:900; color:#d32f2f;
            text-align:center; background:#fff5f5; border:2px solid #d32f2f;
            border-radius:15px; width:120px; margin:0 auto 20px auto;
        }
        
        .question-box {
            background:#fff; padding:20px; border:2px solid #002147;
            border-radius:10px; font-weight:bold; color:#002147; 
            margin-bottom:20px; font-size: 18px;
        }
        
        .explain-box {
            background:#e8f5e9; padding:15px; border-radius:8px;
            border-left:5px solid #4caf50; color:#1b5e20; margin-top:15px;
        }
        
        .stButton button {
            background-color:#002147 !important; color:#FFD700 !important;
            font-weight:bold !important; width:100%; border-radius:8px !important;
            height: 50px; font-size: 16px !important;
        }
        
        #MainMenu {visibility: hidden;} footer {visibility: hidden;}
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
        return gspread.authorize(creds).open("HeThongTracNghiem")
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return None

# --- 5. HÀM XỬ LÝ ---
def check_login(db, u, p):
    try:
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
        return True
    except Exception as e:
        st.error(f"Lỗi lưu: {e}")
        return False

def get_exams(db):
    try: return db.worksheet("CauHoi").get_all_values()
    except: return []

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
    if not db: st.stop()

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
        # HEADER
        c1, c2 = st.columns([4, 1])
        with c1:
            st.markdown(f"<div class='user-info'>👮 {st.session_state.ho_ten} | {st.session_state.vai_tro}</div>", unsafe_allow_html=True)
        with c2:
            if st.button("THOÁT"):
                st.session_state.clear()
                st.rerun()
        
        st.write("")

        role = st.session_state.vai_tro
        
        # --- TAB MENU ---
        if role == 'Admin':
            tabs = st.tabs(["👥 QUẢN LÝ USER", "⚙️ CÂU HỎI", "📚 GIÁO TRÌNH"])
            active_tab = "Admin"
        elif role == 'GiangVien':
            tabs = st.tabs(["👥 CẤP QUYỀN THI", "⚙️ CÂU HỎI", "📚 GIÁO TRÌNH"])
            active_tab = "GV"
        else:
            tabs = st.tabs(["📝 LÀM BÀI THI"])
            active_tab = "HV"

        # --- LOGIC THI (MÀN HÌNH ĐANG LÀM BÀI) ---
        if st.session_state.bat_dau:
            st.info("⚠️ ĐANG LÀM BÀI THI")
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
                ans = st.radio("Chọn:", [f"A. {q[1]}", f"B. {q[2]}", f"C. {q[3]}", f"D. {q[4]}"], key="run")
                st.write("")
                if st.button("CHỐT ĐÁP ÁN"):
                    st.session_state.choice = ans.split('.')[0] if ans else None
                    st.session_state.da_nop = True
                    st.rerun()
                time.sleep(1); st.rerun()
            else:
                st.markdown(f"**Câu {idx+1}:**")
                st.markdown(f"<div class='question-box'>{q[0]}</div>", unsafe_allow_html=True)
                res = st.session_state.choice
                true = str(q[5]).strip().upper()
                if res == true: st.success(f"✅ CHÍNH XÁC! ({res})")
                else: st.error(f"❌ SAI! Bạn chọn: {res} | Đúng: {true}")
                if str(q[6]).strip(): st.markdown(f"<div class='explain-box'>💡 {q[6]}</div>", unsafe_allow_html=True)
                st.write("")
                if st.button("TIẾP THEO ➡️"):
                    if res == true: st.session_state.diem_so += 1
                    st.session_state.chi_so += 1
                    st.session_state.da_nop = False
                    st.session_state.time_end = None
                    st.rerun()

        else:
            # --- NỘI DUNG TAB KHI KHÔNG THI ---
            
            # 1. QUẢN LÝ (Admin + GV)
            if active_tab in ["Admin", "GV"]:
                with tabs[0]:
                    st.subheader("✅ DANH SÁCH HỌC VIÊN")
                    vals = db.worksheet("HocVien").get_all_values()
                    headers = ["Username","Password","Role","HoTen","TrangThai","Diem"]
                    clean_data = [r[:6]+[""]*(6-len(r)) for r in vals[1:]] if len(vals)>1 else []
                    full_df = pd.DataFrame(clean_data, columns=headers)

                    if role == 'Admin':
                        view_df = full_df
                        role_ops = ["hocvien", "GiangVien", "Admin"]
                    else:
                        view_df = full_df[full_df['Role'] == 'hocvien']
                        role_ops = ["hocvien"] # GV chỉ được chọn hocvien

                    edited = st.data_editor(
                        view_df,
                        use_container_width=True,
                        num_rows="dynamic",
                        hide_index=True,
                        column_config={
                            "TrangThai": st.column_config.SelectboxColumn("Trạng Thái", options=["ChuaDuocThi","DuocThi","DangThi","DaThi","Khoa"], required=True),
                            "Role": st.column_config.SelectboxColumn("Vai Trò", options=role_ops, required=True),
                            "Password": st.column_config.TextColumn("Mật Khẩu")
                        }
                    )

                    if st.button("LƯU THAY ĐỔI", type="primary"):
                        if role == 'Admin':
                            final_df = edited
                        else:
                            df_hidden = full_df[full_df['Role'] != 'hocvien']
                            final_df = pd.concat([df_hidden, edited], ignore_index=True)
                        
                        if save_to_sheet(db, "HocVien", final_df):
                            st.success("✅ Đã cập nhật thành công!")
                            time.sleep(1); st.rerun()

                # 2. CÂU HỎI
                with tabs[1]:
                    st.subheader("⚙️ NGÂN HÀNG CÂU HỎI")
                    q_vals = get_exams(db)
                    q_headers = ["CauHoi","A","B","C","D","DapAn_Dung","GiaiThich"]
                    q_data = [r[:7]+[""]*(7-len(r)) for r in q_vals[1:]] if len(q_vals)>1 else []
                    q_df = pd.DataFrame(q_data, columns=q_headers)
                    q_edit = st.data_editor(q_df, num_rows="dynamic", use_container_width=True)
                    if st.button("LƯU CÂU HỎI"):
                        if save_to_sheet(db, "CauHoi", q_edit):
                            st.success("Đã lưu!"); time.sleep(1); st.rerun()

                # 3. GIÁO TRÌNH
                with tabs[2]:
                    st.subheader("📚 TÀI LIỆU")
                    try:
                        g_data = db.worksheet("GiaoTrinh").get_all_records()
                        for l in g_data:
                            with st.expander(f"📖 {l.get('BaiHoc','Bài học')}"):
                                st.write(l.get('NoiDung',''))
                                if str(l.get('HinhAnh','')).startswith('http'): st.image(l['HinhAnh'])
                    except: st.warning("Chưa có giáo trình.")

            # 4. HỌC VIÊN
            elif active_tab == "HV":
                with tabs[0]:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("📝 THI THỬ (LUYỆN TẬP)"):
                            qs = get_exams(db)[1:]
                            if len(qs)>0: qs = random.sample(qs, min(10, len(qs)))
                            st.session_state.bat_dau = True
                            st.session_state.ds_cau_hoi = qs
                            st.session_state.chi_so = 0; st.session_state.diem_so = 0
                            st.session_state.mode = 'thu'
                            st.rerun()
                    with c2:
                        # --- LOGIC NÚT BẮT ĐẦU CHÍNH THỨC (ĐÃ SỬA LỖI 2 LẦN CLICK) ---
                        if st.button("🚨 SÁT HẠCH CHÍNH THỨC"):
                            allow_start = False
                            error_msg = ""
                            try:
                                ws = db.worksheet("HocVien")
                                cell = ws.find(st.session_state.user)
                                stt = ws.cell(cell.row, 5).value
                                
                                if stt == "DuocThi":
                                    ws.update_cell(cell.row, 5, "DangThi")
                                    allow_start = True
                                else:
                                    error_msg = f"⛔ Bạn chưa được cấp quyền! Trạng thái hiện tại: {stt}"
                            except Exception as e:
                                error_msg = f"Lỗi hệ thống: {str(e)}"

                            if allow_start:
                                qs = get_exams(db)[1:]
                                st.session_state.bat_dau = True
                                st.session_state.ds_cau_hoi = qs
                                st.session_state.chi_so = 0
                                st.session_state.diem_so = 0
                                st.session_state.mode = 'that'
                                st.rerun()
                            else:
                                st.error(error_msg)

if __name__ == "__main__":
    main()
