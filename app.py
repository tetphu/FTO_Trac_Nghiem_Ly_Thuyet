import streamlit as st
import time

# --- 1. KHỞI TẠO TRANG (BẮT BUỘC DÒNG ĐẦU) ---
st.set_page_config(page_title="FTO System", page_icon="🚓", layout="centered")

# --- 2. KIỂM TRA HỆ THỐNG (DEBUG) ---
st.write("### ⏳ ĐANG KẾT NỐI MÁY CHỦ...")

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    import pandas as pd
    import random
    st.success("✅ Đã tải xong thư viện!")
    time.sleep(0.5)
    st.empty() # Xóa thông báo loading
except ImportError as e:
    st.error(f"❌ LỖI NGHIÊM TRỌNG: Thiếu thư viện. Bạn hãy kiểm tra file requirements.txt.\nChi tiết: {e}")
    st.stop()

# --- 3. CẤU HÌNH ---
THOI_GIAN_MOI_CAU = 30

# --- 4. HÀM GIAO DIỆN ---
def inject_css():
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem; }
        header, footer { visibility: hidden; }
        .gcpd-title {
            font-family: sans-serif; color: #002147; 
            font-size: 22px; font-weight: 900; text-align: center;
            text-transform: uppercase;
        }
        [data-testid="stForm"] {
            border: 2px solid #002147; border-radius: 10px; padding: 15px;
        }
        .stButton button {
            background-color: #002147 !important; color: #FFD700 !important;
            font-weight: bold !important; width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 5. KẾT NỐI DATABASE ---
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
        st.error(f"❌ LỖI KẾT NỐI GOOGLE SHEET: {e}")
        return None

# --- 6. HÀM XỬ LÝ ---
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

# --- 7. CHƯƠNG TRÌNH CHÍNH ---
def main():
    inject_css()
    if 'vai_tro' not in st.session_state:
        st.session_state.update(vai_tro=None, diem_so=0, chi_so=0, bat_dau=False, da_nop_cau=False, ds_cau_hoi=[], thoi_gian_het=None, lua_chon=None, loai_thi=None)

    db = ket_noi_csdl()
    if not db: st.stop()

    # A. ĐĂNG NHẬP
    if st.session_state['vai_tro'] is None:
        c1, c2 = st.columns([1,2.5])
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

    # B. DASHBOARD
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
            
            edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            if st.button("LƯU"):
                ws.clear()
                ws.update([headers] + edited.values.tolist())
                st.success("Đã lưu!")

        # 2. QUẢN TRỊ USER
        elif menu == "QUẢN TRỊ USER" or menu == "CẤP QUYỀN THI":
            st.info("✅ QUẢN LÝ TRẠNG THÁI")
            ws = db.worksheet("HocVien")
            vals = ws.get_all_values()
            headers = ["Username","Password","Role","HoTen","TrangThai","Diem"]
            
            clean = [r[:6]+[""]*(6-len(r)) for r in vals[1:]] if len(vals)>1 else []
            df = pd.DataFrame(clean, columns=headers)
            
            if role != 'Admin': df = df[df['Role'] == 'hocvien']
            
            # Cấu hình bảng (Bỏ type='password' để tránh lỗi)
            edited = st.data_editor(
                df, 
                use_container_width=True,
                column_config={
                    "TrangThai": st.column_config.SelectboxColumn(
                        "Trạng Thái", options=["ChuaDuocThi", "DuocThi", "DangThi", "DaThi", "Khoa"], required=True
                    ),
                    "Role": st.column_config.SelectboxColumn(
                        "Vai Trò", options=["hocvien", "GiangVien", "Admin"], disabled=(role != 'Admin')
                    )
                }
            )
            
            if st.button("LƯU TRẠNG THÁI"):
                # Cập nhật thông minh
                full_df = pd.DataFrame([r[:6]+[""]*(6-len(r)) for r in vals[1:]], columns=headers)
                full_df.set_index("Username", inplace=True)
                edited.set_index("Username", inplace=True)
                full_df.update(edited)
                full_df.reset_index(inplace=True)
                
                ws.clear()
                ws.update([headers] + full_df.values.tolist())
                st.success("Đã cập nhật!")
                time.sleep(1); st.rerun()

        # 3. GIÁO TRÌNH
        elif menu == "GIÁO TRÌNH":
            st.title("📚 TÀI LIỆU")
            try:
                data = db.worksheet("GiaoTrinh").get_all_records()
                for l in data:
                    with st.expander(f"📖 {l.get('BaiHoc','Bài học')}"):
                        st.write(l.get('NoiDung',''))
                        if str(l.get('HinhAnh','')).startswith('http'): st.image(l['HinhAnh'])
            except: st.warning("Chưa có giáo trình.")

        # 4. THI CỬ
        elif "THI" in menu or menu == "ĐANG THI":
            if not st.session_state['bat_dau']:
                mode = 'thu' if "THỬ" in menu else 'that'
                st.subheader("LUYỆN TẬP" if mode=='thu' else "SÁT HẠCH CHÍNH THỨC")
                
                if st.button("BẮT ĐẦU"):
                    if mode == 'that':
                        # Check status
                        try:
                            c = db.worksheet("HocVien").find(st.session_state['user'])
                            s = db.worksheet("HocVien").cell(c.row, 5).value
                            if s != "DuocThi":
                                st.error(f"Chưa được cấp quyền! (Trạng thái: {s})"); st.stop()
                            cap_nhat_trang_thai(db, st.session_state['user'], "DangThi")
                        except: st.error("Lỗi tìm user"); st.stop()

                    qs = db.worksheet("CauHoi").get_all_values()
                    lst = qs[1:] if len(qs)>1 else []
                    if mode=='thu' and len(lst)>0: lst = random.sample(lst, min(10, len(lst)))
                    
                    st.session_state.update(bat_dau=True, ds_cau_hoi=lst, chi_so=0, diem_so=0, loai_thi=mode)
                    st.rerun()
            else:
                qs = st.session_state['ds_cau_hoi']
                idx = st.session_state['chi_so']
                
                if idx >= len(qs):
                    st.success(f"KẾT QUẢ: {st.session_state['diem_so']}")
                    if st.button("KẾT THÚC"):
                        if st.session_state['loai_thi'] == 'that':
                            luu_ket_qua(db, st.session_state['user'], st.session_state['diem_so'])
                        st.session_state.clear()
                        st.rerun()
                    st.stop()
                
                q = qs[idx]
                while len(q)<7: q.append("")
                
                if not st.session_state['da_nop_cau']:
                    if not st.session_state['thoi_gian_het']: st.session_state['thoi_gian_het'] = time.time()+30
                    left = int(st.session_state['thoi_gian_het'] - time.time())
                    
                    if left<=0: 
                        st.session_state.update(da_nop_cau=True, lua_chon=None)
                        st.rerun()
                    
                    st.progress(max(0.0, min(1.0, left/30)))
                    st.write(f"**Câu {idx+1}: {q[0]}**")
                    ans = st.radio("Chọn:", [f"A. {q[1]}", f"B. {q[2]}", f"C. {q[3]}", f"D. {q[4]}"])
                    
                    if st.button("CHỐT"):
                        st.session_state.update(da_nop_cau=True, lua_chon=ans.split('.')[0] if ans else None)
                        st.rerun()
                    time.sleep(1); st.rerun()
                else:
                    res = st.session_state['lua_chon']
                    true = str(q[5]).strip().upper()
                    if res == true: st.success("ĐÚNG!")
                    else: st.error(f"SAI! Đáp án: {true}")
                    if st.button("TIẾP"):
                        if res == true: st.session_state['diem_so'] += 1
                        st.session_state.update(chi_so=idx+1, da_nop_cau=False, thoi_gian_het=None)
                        st.rerun()

if __name__ == "__main__":
    main()
