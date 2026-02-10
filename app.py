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
except ImportError:
    st.error("Lỗi: Thiếu thư viện. Hãy kiểm tra file requirements.txt")
    st.stop()

THOI_GIAN = 30

# --- 3. CSS (ĐÃ RÚT GỌN ĐỂ TRÁNH LỖI) ---
def inject_css():
    st.markdown("""
        <style>
        .block-container {padding-top:1rem;}
        .gcpd-title {color:#002147;font-size:24px;font-weight:900;text-align:center;margin-bottom:10px;}
        .user-info {background:#e3f2fd;padding:10px;border-radius:8px;text-align:center;font-weight:bold;color:#0d47a1;}
        .timer-box {font-size:40px;font-weight:900;color:#d32f2f;text-align:center;background:#ffebee;border:2px solid #d32f2f;border-radius:10px;width:100px;margin:0 auto 15px auto;}
        .question-box {background:#fff;padding:15px;border:2px solid #002147;border-radius:10px;font-weight:bold;color:#002147;margin-bottom:15px;}
        .explain-box {background:#e8f5e9;padding:15px;border-left:5px solid #4caf50;color:#1b5e20;margin-top:10px;}
        .stButton button {background:#002147!important;color:#FFD700!important;font-weight:bold!important;width:100%;}
        div.row-widget.stRadio > div {flex-direction:row;justify-content:center;}
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
                # Col 2=Role, 3=Name, 4=Status
                return str(r[2]).strip(), str(r[3]).strip(), (str(r[4]).strip() if len(r)>4 else "ChuaDuocThi")
    except: pass
    return None, None, None

def save_data(db, sheet_name, data):
    try:
        ws = db.worksheet(sheet_name)
        ws.clear()
        ws.update(data)
        return True
    except: return False

def update_status(db, user, stt):
    try:
        ws = db.worksheet("HocVien")
        cell = ws.find(user)
        ws.update_cell(cell.row, 5, stt)
    except: pass

def get_exams(db):
    try: return db.worksheet("CauHoi").get_all_values()
    except: return []

# --- 6. MAIN ---
def main():
    inject_css()
    
    # Khởi tạo Session State từng dòng để tránh lỗi Syntax
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

    # --- MÀN HÌNH LOGIN ---
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

    # --- MÀN HÌNH CHÍNH ---
    else:
        c_info, c_logout = st.columns([3, 1])
        with c_info: st.markdown(f"<div class='user-info'>👮 {st.session_state.ho_ten} ({st.session_state.vai_tro})</div>", unsafe_allow_html=True)
        with c_logout:
            if st.button("THOÁT"):
                st.session_state.clear()
                st.rerun()
        
        st.divider()
        
        role = st.session_state.vai_tro
        menu_items = ["THI THỬ", "THI SÁT HẠCH"]
        if role == 'Admin': menu_items = ["QUẢN TRỊ USER", "QUẢN LÝ CÂU HỎI", "GIÁO TRÌNH"]
        elif role == 'GiangVien': menu_items = ["CẤP QUYỀN THI", "QUẢN LÝ CÂU HỎI", "GIÁO TRÌNH"]

        if st.session_state.bat_dau:
            menu = "ĐANG THI"
            st.info("⚠️ ĐANG LÀM BÀI...")
        else:
            menu = st.radio("CHỨC NĂNG:", menu_items, horizontal=True)
        
        st.write("")

        # --- 1. QUẢN LÝ CÂU HỎI ---
        if menu == "QUẢN LÝ CÂU HỎI":
            st.subheader("⚙️ NGÂN HÀNG CÂU HỎI")
            vals = get_exams(db)
            headers = ["CauHoi","A","B","C","D","DapAn_Dung","GiaiThich"]
            # Fix lỗi cột
            data = [r[:7]+[""]*(7-len(r)) for r in vals[1:]] if len(vals)>1 else []
            df = pd.DataFrame(data, columns=headers)
            edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            if st.button("LƯU CÂU HỎI"):
                save_data(db, "CauHoi", [headers] + edited.values.tolist())
                st.success("Đã lưu!")

        # --- 2. QUẢN TRỊ USER ---
        elif menu in ["QUẢN TRỊ USER", "CẤP QUYỀN THI"]:
            st.subheader("✅ QUẢN LÝ HỌC VIÊN")
            vals = db.worksheet("HocVien").get_all_values()
            headers = ["Username","Password","Role","HoTen","TrangThai","Diem"]
            data = [r[:6]+[""]*(6-len(r)) for r in vals[1:]] if len(vals)>1 else []
            
            full_df = pd.DataFrame(data, columns=headers)
            view_df = full_df if role == 'Admin' else full_df[full_df['Role'] == 'hocvien']

            edited = st.data_editor(
                view_df,
                use_container_width=True,
                num_rows="dynamic",
                hide_index=True,
                column_config={
                    "TrangThai": st.column_config.SelectboxColumn("Status", options=["ChuaDuocThi","DuocThi","DangThi","DaThi","Khoa"], required=True),
                    "Role": st.column_config.SelectboxColumn("Role", options=["hocvien","GiangVien","Admin"], disabled=(role!='Admin')),
                    "Password": st.column_config.TextColumn("Pass") # Bỏ type=password để fix lỗi TypeError
                }
            )

            if st.button("LƯU THAY ĐỔI"):
                if role == 'Admin':
                    final_data = [headers] + edited.values.tolist()
                else:
                    full_df.set_index("Username", inplace=True)
                    edited.set_index("Username", inplace=True)
                    full_df.update(edited)
                    # Thêm dòng mới
                    new_rows = edited.index.difference(full_df.index)
                    if not new_rows.empty: full_df = pd.concat([full_df, edited.loc[new_rows]])
                    full_df.reset_index(inplace=True)
                    final_data = [headers] + full_df.values.tolist()
                
                save_data(db, "HocVien", final_data)
                st.success("Đã cập nhật!")
                time.sleep(1); st.rerun()

        # --- 3. GIÁO TRÌNH ---
        elif menu == "GIÁO TRÌNH":
            st.subheader("📚 TÀI LIỆU")
            try:
                data = db.worksheet("GiaoTrinh").get_all_records()
                for l in data:
                    with st.expander(f"📖 {l.get('BaiHoc','Bài học')}"):
                        st.write(l.get('NoiDung',''))
                        if str(l.get('HinhAnh','')).startswith('http'): st.image(l['HinhAnh'])
            except: st.warning("Chưa có dữ liệu.")

        # --- 4. THI CỬ ---
        elif "THI" in menu or menu == "ĐANG THI":
            # CHUẨN BỊ
            if not st.session_state.bat_dau:
                mode = 'thu' if "THỬ" in menu else 'that'
                st.subheader("LUYỆN TẬP" if mode=='thu' else "SÁT HẠCH")
                
                if st.button("BẮT ĐẦU"):
                    if mode == 'that':
                        try:
                            ws = db.worksheet("HocVien")
                            cell = ws.find(st.session_state.user)
                            stt = ws.cell(cell.row, 5).value
                            if stt != "DuocThi": st.error(f"Chưa được cấp quyền! ({stt})"); st.stop()
                            update_status(db, st.session_state.user, "DangThi")
                        except: st.error("Lỗi User"); st.stop()

                    qs = get_exams(db)[1:]
                    if mode=='thu' and len(qs)>0: qs = random.sample(qs, min(10, len(qs)))
                    
                    st.session_state.bat_dau = True
                    st.session_state.ds_cau_hoi = qs
                    st.session_state.chi_so = 0
                    st.session_state.diem_so = 0
                    st.session_state.loai_thi = mode
                    st.rerun()

            # ĐANG LÀM
            else:
                qs = st.session_state.ds_cau_hoi
                idx = st.session_state.chi_so
                
                # KẾT THÚC
                if idx >= len(qs):
                    st.balloons()
                    st.success(f"KẾT QUẢ: {st.session_state.diem_so}/{len(qs)}")
                    if st.button("KẾT THÚC"):
                        if st.session_state.loai_thi == 'that':
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
                
                # CHƯA CHỐT
                if not st.session_state.da_nop:
                    if not st.session_state.time_end:
                        st.session_state.time_end = time.time() + THOI_GIAN
                    
                    left = int(st.session_state.time_end - time.time())
                    if left <= 0:
                        st.session_state.da_nop = True
                        st.session_state.choice = None
                        st.rerun()

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

                # ĐÃ CHỐT -> HIỆN KẾT QUẢ
                else:
                    st.markdown(f"**Câu {idx+1}:**")
                    st.markdown(f"<div class='question-box'>{q[0]}</div>", unsafe_allow_html=True)
                    
                    user_ans = st.session_state.choice
                    true_ans = str(q[5]).strip().upper()
                    
                    st.info(f"Bạn chọn: {user_ans}")
                    if user_ans == true_ans: st.success(f"✅ CHÍNH XÁC! Đáp án: {true_ans}")
                    else: st.error(f"❌ SAI! Đáp án đúng: {true_ans}")
                    
                    if str(q[6]).strip():
                        st.markdown(f"<div class='explain-box'>💡 {q[6]}</div>", unsafe_allow_html=True)
                    
                    st.write("")
                    if st.button("TIẾP THEO ➡️"):
                        if user_ans == true_ans: st.session_state.diem_so += 1
                        st.session_state.chi_so += 1
                        st.session_state.da_nop = False
                        st.session_state.time_end = None
                        st.rerun()

if __name__ == "__main__":
    main()
