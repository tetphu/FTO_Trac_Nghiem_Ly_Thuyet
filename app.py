import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import time
import random

# --- 1. CẤU HÌNH ---
THOI_GIAN_MOI_CAU = 30

# --- 2. HÀM GIAO DIỆN ---
def inject_css():
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem; padding-bottom: 3rem; padding-left: 0.5rem; padding-right: 0.5rem; }
        header, footer { visibility: hidden; }
        .stApp { background-color: #ffffff; }
        
        .gcpd-title {
            font-family: 'Arial Black', sans-serif; color: #002147; 
            font-size: 24px; text-transform: uppercase;
            margin-top: 5px; line-height: 1.2; font-weight: 900; text-align: center;
        }
        
        [data-testid="stForm"] {
            border: 2px solid #002147; border-radius: 10px; padding: 15px;
            background-color: #ffffff;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .stButton button {
            background-color: #002147 !important; color: #FFD700 !important;
            font-weight: bold !important; width: 100%; padding: 12px !important; border-radius: 8px !important;
        }
        
        .lesson-card {
            background-color: #f8f9fa; border-left: 4px solid #002147;
            padding: 10px; margin-bottom: 10px; border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 3. KẾT NỐI GOOGLE SHEET ---
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
        st.error(f"Lỗi kết nối: {str(e)}")
        return None

# --- 4. CÁC HÀM XỬ LÝ DỮ LIỆU ---
def kiem_tra_dang_nhap(db, user, pwd):
    try:
        ws = db.worksheet("HocVien")
        rows = ws.get_all_values()
        for row in rows[1:]:
            if len(row) < 4: continue
            # Cột A: User, B: Pass, C: Role, D: Name, E: Status
            if str(row[0]).strip() == str(user).strip() and str(row[1]).strip() == str(pwd).strip():
                status = str(row[4]).strip() if len(row) > 4 else "ChuaDuocThi"
                role = str(row[2]).strip()
                name = str(row[3]).strip()
                return role, name, status
    except: pass
    return None, None, None

def cap_nhat_trang_thai(db, user, status_moi):
    try:
        ws = db.worksheet("HocVien")
        cell = ws.find(user)
        ws.update_cell(cell.row, 5, status_moi)
        return True
    except: return False

def luu_ket_qua(db, user, diem):
    try:
        ws = db.worksheet("HocVien")
        cell = ws.find(user)
        ws.update_cell(cell.row, 5, "DaThi")
        ws.update_cell(cell.row, 6, str(diem))
        return True
    except: return False

def lay_giao_trinh(db):
    try:
        ws = db.worksheet("GiaoTrinh")
        return ws.get_all_records()
    except: return []

# --- 5. CHƯƠNG TRÌNH CHÍNH ---
def main():
    st.set_page_config(page_title="FTO System", page_icon="🚓", layout="centered")
    inject_css() 

    if 'vai_tro' not in st.session_state: 
        st.session_state.update(
            vai_tro=None, trang_thai_hien_tai=None, loai_thi=None,
            chi_so=0, diem_so=0, ds_cau_hoi=[], da_nop_cau=False, 
            bat_dau=False, thoi_gian_het=None, lua_chon=None
        )

    db = ket_noi_csdl()
    if not db: st.stop()

    # --- A. MÀN HÌNH ĐĂNG NHẬP ---
    if st.session_state['vai_tro'] is None:
        with st.form("login"):
            c1, c2 = st.columns([1, 2.5])
            with c1: st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", use_column_width=True)
            with c2: st.markdown('<div class="gcpd-title">GACHA CITY<BR>POLICE DEPT<BR>ACADEMY</div>', unsafe_allow_html=True)
            st.divider()
            st.markdown("<h4 style='text-align: center; color: #002147;'>▼ ĐĂNG NHẬP HỆ THỐNG</h4>", unsafe_allow_html=True)
            u = st.text_input("SỐ HIỆU (Momo)")
            p = st.text_input("MÃ BẢO MẬT", type="password")
            
            if st.form_submit_button("XÁC THỰC DANH TÍNH"):
                vt, ten, stt = kiem_tra_dang_nhap(db, u, p)
                if vt:
                    st.session_state.update(vai_tro=vt, user=u, ho_ten=ten, trang_thai_hien_tai=stt)
                    st.rerun()
                else: 
                    st.error("❌ SAI THÔNG TIN ĐĂNG NHẬP")

    # --- B. ĐÃ ĐĂNG NHẬP ---
    else:
        with st.sidebar:
            st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", width=100)
            st.markdown(f"### 👮 {st.session_state['ho_ten']}")
            st.markdown(f"<span style='background-color:#002147; color:#FFD700; padding: 4px 8px; border-radius: 4px; font-weight:bold; font-size: 12px;'>{st.session_state['vai_tro']}</span>", unsafe_allow_html=True)
            
            if st.session_state['bat_dau']:
                st.divider()
                st.metric("🏆 ĐIỂM", f"{st.session_state['diem_so']}")
            st.divider()
            
            role = st.session_state['vai_tro']
            if role == 'Admin':
                ds_chuc_nang = ["📖 GIÁO TRÌNH", "⚙️ QUẢN LÝ CÂU HỎI", "✅ QUẢN TRỊ USER (FULL)"]
            elif role == 'GiangVien':
                ds_chuc_nang = ["📖 GIÁO TRÌNH", "⚙️ QUẢN LÝ CÂU HỎI", "✅ CẤP QUYỀN THI"]
            else:
                ds_chuc_nang = ["📝 THI THỬ (LUYỆN TẬP)", "🚨 THI SÁT HẠCH (CHÍNH THỨC)"]
            
            if st.session_state['bat_dau']:
                 st.info("⚠️ Đang làm bài thi...")
                 menu = st.session_state.get('last_menu', ds_chuc_nang[0])
            else:
                menu = st.radio("MENU CHỨC NĂNG", ds_chuc_nang)
                st.session_state['last_menu'] = menu
                st.write(""); st.write("")
                if st.button("ĐĂNG XUẤT"):
                    for key in list(st.session_state.keys()): del st.session_state[key]
                    st.rerun()

        # ============================================================
        # 1. CHỨC NĂNG GIÁO TRÌNH & CÂU HỎI
        # ============================================================
        if "GIÁO TRÌNH" in menu:
            st.title("📚 TÀI LIỆU NỘI BỘ")
            ds_bai = lay_giao_trinh(db)
            if not ds_bai: st.warning("Chưa có bài giảng.")
            else:
                for bai in ds_bai:
                    with st.container():
                        st.markdown(f"""<div class="lesson-card"><div class="lesson-title">{bai['BaiHoc']}</div><div class="lesson-content">{bai['NoiDung']}</div></div>""", unsafe_allow_html=True)
                        if str(bai['HinhAnh']).startswith("http"): st.image(bai['HinhAnh'], use_column_width=True)

        elif "QUẢN LÝ CÂU HỎI" in menu:
            st.title("⚙️ NGÂN HÀNG CÂU HỎI")
            ws_cauhoi = db.worksheet("CauHoi")
            all_values = ws_cauhoi.get_all_values()
            headers = ["CauHoi", "A", "B", "C", "D", "DapAn_Dung", "GiaiThich"]
            if len(all_values) > 1: df = pd.DataFrame(all_values[1:], columns=headers)
            else: df = pd.DataFrame(columns=headers)
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, height=400)
            if st.button("💾 LƯU THAY ĐỔI", type="primary"):
                try:
                    ws_cauhoi.clear()
                    ws_cauhoi.update([headers] + edited_df.values.tolist())
                    st.success("✅ Đã cập nhật!"); time.sleep(1); st.rerun()
                except Exception as e: st.error(f"Lỗi: {e}")

        # ============================================================
        # 2. CHỨC NĂNG QUẢN TRỊ / CẤP QUYỀN (ĐÃ FIX LỖI KEYERROR)
        # ============================================================
        elif "QUẢN TRỊ USER" in menu or "CẤP QUYỀN THI" in menu:
            is_admin = (st.session_state['vai_tro'] == 'Admin')
            
            st.title("✅ QUẢN LÝ THI")
            st.info("Chỉ huy có thể cấp quyền thi cho học viên tại đây.")
            
            ws_hv = db.worksheet("HocVien")
            
            # --- [FIX QUAN TRỌNG] LẤY DỮ LIỆU & ÉP TÊN CỘT ---
            all_rows = ws_hv.get_all_values()
            # Bắt buộc đặt tên cột chuẩn để tránh lỗi KeyError
            std_headers = ["Username", "Password", "Role", "HoTen", "TrangThai", "Diem"]
            
            if len(all_rows) > 1:
                # Nếu file có dữ liệu, ép vào DataFrame với cột chuẩn
                # Nếu cột thiếu, pandas sẽ báo lỗi, nhưng thường sheet sẽ đủ.
                # Cách an toàn: Chỉ lấy 6 cột đầu tiên
                data_clean = [r[:6] + [""]*(6-len(r)) for r in all_rows[1:]] 
                df_hv = pd.DataFrame(data_clean, columns=std_headers)
            else:
                df_hv = pd.DataFrame(columns=std_headers)

            if not df_hv.empty:
                # --- LOGIC LỌC ---
                if is_admin:
                    df_display = df_hv # Admin thấy hết
                else:
                    # Giảng viên chỉ thấy Role = 'hocvien'
                    df_display = df_hv[df_hv['Role'] == 'hocvien']
                
                # --- HIỂN THỊ BẢNG ---
                edited_df = st.data_editor(
                    df_display,
                    use_container_width=True,
                    height=400,
                    column_config={
                        "TrangThai": st.column_config.SelectboxColumn(
                            "Trạng Thái Thi",
                            options=["ChuaDuocThi", "DuocThi", "DangThi", "DaThi", "Khoa"],
                            required=True,
                            width="medium"
                        ),
                        "Role": st.column_config.SelectboxColumn(
                            "Vai Trò",
                            options=["hocvien", "GiangVien", "Admin"],
                            disabled=not is_admin # GV không sửa được Role
                        ),
                        # Ẩn mật khẩu với GV
                        "Password": st.column_config.TextColumn(
                            "Mật khẩu",
                            disabled=not is_admin,
                            type="password" if not is_admin else "text" # GV thấy dấu ***
                        )
                    }
                )
                
                if st.button("💾 LƯU CẬP NHẬT", type="primary"):
                    try:
                        # Logic lưu: Merge dữ liệu sửa vào dữ liệu gốc
                        if is_admin:
                            final_df = edited_df
                        else:
                            final_df = df_hv.copy()
                            final_df.set_index("Username", inplace=True)
                            edited_df.set_index("Username", inplace=True)
                            final_df.update(edited_df)
                            final_df.reset_index(inplace=True)
                            edited_df.reset_index(inplace=True)
                        
                        ws_hv.clear()
                        ws_hv.update([std_headers] + final_df.values.tolist())
                        st.success("✅ Đã cập nhật thành công!")
                        time.sleep(1); st.rerun()
                    except Exception as e: st.error(f"Lỗi: {e}")

        # ============================================================
        # 3. CHỨC NĂNG THI
        # ============================================================
        elif "THI THỬ" in menu or "THI SÁT HẠCH" in menu:
            is_practice = "THI THỬ" in menu
            exam_title = "LUYỆN TẬP (THI THỬ)" if is_practice else "SÁT HẠCH CHÍNH THỨC"
            
            if not st.session_state['bat_dau']:
                with st.form("start_exam"):
                    c1, c2 = st.columns([1, 2.5])
                    with c1: st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", use_column_width=True)
                    with c2: st.markdown(f'<div class="gcpd-title">{exam_title}</div>', unsafe_allow_html=True)
                    st.divider()
                    
                    if is_practice: st.info("ℹ️ Chế độ luyện tập: Random 10 câu. Không lưu điểm.")
                    else: st.warning("⚠️ BÀI THI CH
