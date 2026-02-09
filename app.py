import streamlit as st
import time

# --- MỒI LỬA: KIỂM TRA HỆ THỐNG ---
st.empty() # Placeholder

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    import pandas as pd
    import random
except ImportError as e:
    st.error(f"⚠️ LỖI: Thiếu thư viện. Hãy kiểm tra requirements.txt. Chi tiết: {e}")
    st.stop()

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="FTO System", page_icon="🚓", layout="centered")
THOI_GIAN_MOI_CAU = 30

# --- 2. HÀM GIAO DIỆN ---
def inject_css():
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem; padding-bottom: 5rem; }
        header, footer { visibility: hidden; }
        .stApp { background-color: #ffffff; }
        .gcpd-title {
            font-family: 'Arial Black', sans-serif; color: #002147; 
            font-size: 22px; text-transform: uppercase; font-weight: 900; text-align: center;
        }
        [data-testid="stForm"] {
            border: 2px solid #002147; border-radius: 10px; padding: 15px;
            background-color: #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stButton button {
            background-color: #002147 !important; color: #FFD700 !important;
            font-weight: bold !important; width: 100%; padding: 12px !important;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 3. KẾT NỐI DATABASE ---
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
        st.error(f"⚠️ LỖI KẾT NỐI: {str(e)}")
        return None

# --- 4. HÀM XỬ LÝ ---
def kiem_tra_dang_nhap(db, user, pwd):
    try:
        ws = db.worksheet("HocVien")
        rows = ws.get_all_values()
        for row in rows[1:]:
            if len(row) < 3: continue
            # A=User, B=Pass, C=Role, D=Name, E=Status
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

# --- 5. CHƯƠNG TRÌNH CHÍNH ---
def main():
    inject_css()
    if 'vai_tro' not in st.session_state:
        st.session_state.update(vai_tro=None, diem_so=0, chi_so=0, bat_dau=False, da_nop_cau=False, ds_cau_hoi=[], thoi_gian_het=None, lua_chon=None)

    db = ket_noi_csdl()
    if not db: st.stop()

    # --- A. ĐĂNG NHẬP ---
    if st.session_state['vai_tro'] is None:
        with st.form("login"):
            st.markdown('<div class="gcpd-title">FTO ACADEMY</div>', unsafe_allow_html=True)
            u = st.text_input("SỐ HIỆU (Momo)")
            p = st.text_input("MÃ BẢO MẬT", type="password")
            if st.form_submit_button("ĐĂNG NHẬP"):
                vt, ten, stt = kiem_tra_dang_nhap(db, u, p)
                if vt:
                    st.session_state.update(vai_tro=vt, user=u, ho_ten=ten, trang_thai_hien_tai=stt)
                    st.rerun()
                else: st.error("❌ Sai thông tin!")

    # --- B. DASHBOARD ---
    else:
        with st.sidebar:
            st.markdown(f"### 👮 {st.session_state['ho_ten']}")
            st.code(st.session_state['vai_tro'])
            if st.button("ĐĂNG XUẤT"):
                st.session_state.clear()
                st.rerun()

        # PHÂN QUYỀN
        role = st.session_state['vai_tro']
        if role == 'Admin': menu_opts = ["QUẢN TRỊ USER", "QUẢN LÝ CÂU HỎI"]
        elif role == 'GiangVien': menu_opts = ["CẤP QUYỀN THI", "QUẢN LÝ CÂU HỎI"]
        else: menu_opts = ["THI THỬ", "THI SÁT HẠCH"]
        
        if st.session_state['bat_dau']: 
            st.info("⚠️ Đang làm bài thi...")
            menu = "ĐANG THI" # Khóa menu
        else: 
            menu = st.radio("MENU", menu_opts)

        # ----------------------------------------------------
        # 1. QUẢN LÝ CÂU HỎI
        # ----------------------------------------------------
        if menu == "QUẢN LÝ CÂU HỎI":
            st.info("⚙️ CHỈNH SỬA CÂU HỎI")
            ws = db.worksheet("CauHoi")
            vals = ws.get_all_values()
            headers = ["CauHoi","A","B","C","D","DapAn_Dung","GiaiThich"]
            
            clean_data = [r[:7] + [""]*(7-len(r)) for r in vals[1:]] if len(vals)>1 else []
            df = pd.DataFrame(clean_data, columns=headers)
            
            edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            if st.button("LƯU THAY ĐỔI"):
                ws.clear()
                ws.update([headers] + edited.values.tolist())
                st.success("Đã lưu!")

        # ----------------------------------------------------
        # 2. QUẢN TRỊ USER / CẤP QUYỀN (CÓ MENU DROPDOWN)
        # ----------------------------------------------------
        elif menu == "QUẢN TRỊ USER" or menu == "CẤP QUYỀN THI":
            st.info("✅ QUẢN LÝ TRẠNG THÁI THI")
            ws = db.worksheet("HocVien")
            vals = ws.get_all_values()
            headers = ["Username","Password","Role","HoTen","TrangThai","Diem"]
            
            clean_data = [r[:6] + [""]*(6-len(r)) for r in vals[1:]] if len(vals)>1 else []
            df = pd.DataFrame(clean_data, columns=headers)
            
            if role != 'Admin': df = df[df['Role'] == 'hocvien']
            
            # --- CẤU HÌNH CỘT DROP-DOWN ---
            column_config = {
                "TrangThai": st.column_config.SelectboxColumn(
                    "Trạng Thái Thi",
                    help="Chọn trạng thái thi",
                    width="medium",
                    options=[
                        "ChuaDuocThi",
                        "DuocThi",
                        "DangThi",
                        "DaThi",
                        "Khoa"
                    ],
                    required=True
                ),
                "Role": st.column_config.SelectboxColumn(
                    "Vai Trò",
                    options=["hocvien", "GiangVien", "Admin"],
                    width="small",
                    disabled=(role != 'Admin') # Chỉ Admin mới sửa được Role
                ),
                 "Password": st.column_config.TextColumn(
                    "Mật Khẩu",
                    type="password" if role != 'Admin' else "text" # Ẩn pass nếu ko phải Admin
                )
            }
            
            edited = st.data_editor(
                df, 
                use_container_width=True, 
                num_rows="dynamic", 
                column_config=column_config # <--- ÁP DỤNG CẤU HÌNH DROP-DOWN TẠI ĐÂY
            )
            
            if st.button("LƯU TRẠNG THÁI"):
                # Cập nhật thông minh
                # 1. Lấy lại dữ liệu gốc đầy đủ (bao gồm cả Admin/GV khác mà GV này ko thấy)
                full_df = pd.DataFrame([r[:6] + [""]*(6-len(r)) for r in vals[1:]], columns=headers)
                
                # 2. Update các dòng đã sửa vào bảng gốc dựa trên Username
                # Chuyển thành dictionary để map cho nhanh
                full_df.set_index("Username", inplace=True)
                edited.set_index("Username", inplace=True)
                full_df.update(edited)
                full_df.reset_index(inplace=True)
                
                # 3. Ghi lại vào Sheet
                ws.clear()
                ws.update([headers] + full_df.values.tolist())
                st.success("Đã cập nhật trạng thái thành công!")
                time.sleep(1); st.rerun()

        # ----------------------------------------------------
        # 3. THI CỬ
        # ----------------------------------------------------
        elif "THI" in menu or menu == "ĐANG THI":
            if not st.session_state['bat_dau']:
                if st.button("BẮT ĐẦU LÀM BÀI"):
                    mode = 'thu' if "THỬ" in menu else 'that'
                    
                    if mode == 'that':
                        # Check quyền realtime
                        try:
                            cell = db.worksheet("HocVien").find(st.session_state['user'])
                            stt = db.worksheet("HocVien").cell(cell.row, 5).value
                        except: stt = "Loi"
                        
                        if stt != "DuocThi":
                            st.error(f"⛔ Chưa được cấp quyền! (Trạng thái hiện tại: {stt})")
                            st.stop()
                        cap_nhat_trang_thai(db, st.session_state['user'], "DangThi")
                    
                    # Lấy câu hỏi
                    qs = db.worksheet("CauHoi").get_all_values()
                    st.session_state['ds_cau_hoi'] = qs[1:] if len(qs)>1 else []
                    
                    if mode == 'thu' and len(st.session_state['ds_cau_hoi']) > 0: 
                        st.session_state['ds_cau_hoi'] = random.sample(st.session_state['ds_cau_hoi'], min(10, len(st.session_state['ds_cau_hoi'])))
                    
                    st.session_state.update(bat_dau=True, loai_thi=mode, diem_so=0, chi_so=0)
                    st.rerun()
            else:
                # Đang làm bài
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
                while len(q) < 7: q.append("")
                
                # Time logic
                if not st.session_state['da_nop_cau']:
                    if not st.session_state['thoi_gian_het']:
                        st.session_state['thoi_gian_het'] = time.time() + 30
                    
                    left = int(st.session_state['thoi_gian_het'] - time.time())
                    if left <= 0:
                        st.session_state.update(da_nop_cau=True, lua_chon=None)
                        st.rerun()
                    
                    st.progress(max(0.0, min(1.0, left/30)))
                    st.markdown(f"**Câu {idx+1}: {q[0]}**")
                    ans = st.radio("Chọn:", [f"A. {q[1]}", f"B. {q[2]}", f"C. {q[3]}", f"D. {q[4]}"])
                    if st.button("CHỐT"):
                        st.session_state.update(da_nop_cau=True, lua_chon=ans.split('.')[0] if ans else None)
                        st.rerun()
                    time.sleep(1); st.rerun()
                else:
                    # Kết quả câu
                    res = st.session_state['lua_chon']
                    true_ans = str(q[5]).strip().upper()
                    
                    if res == true_ans: st.success("✅ CHÍNH XÁC!")
                    else: st.error(f"❌ SAI RỒI! Đáp án đúng: {true_ans}")
                    
                    if str(q[6]).strip(): st.info(f"💡 {q[6]}")
                    
                    if st.button("TIẾP THEO"):
                        if res == true_ans: st.session_state['diem_so'] += 1
                        st.session_state.update(chi_so=idx+1, da_nop_cau=False, thoi_gian_het=None)
                        st.rerun()

if __name__ == "__main__":
    main()
