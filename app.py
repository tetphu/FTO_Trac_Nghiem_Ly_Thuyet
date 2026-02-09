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
            # row[0]: User, row[1]: Pass, row[2]: Role, row[3]: Name, row[4]: Status
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
            
            # --- MENU PHÂN QUYỀN ---
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
        # 1. CHỨC NĂNG QUẢN LÝ (ADMIN & GIẢNG VIÊN)
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

        # --- CHỨC NĂNG QUẢN LÝ USER / CẤP QUYỀN ---
        elif "QUẢN TRỊ USER" in menu or "CẤP QUYỀN THI" in menu:
            is_admin = (st.session_state['vai_tro'] == 'Admin')
            
            if is_admin:
                st.title("🛡️ QUẢN TRỊ HỆ THỐNG (ADMIN)")
                st.info("Bạn có toàn quyền chỉnh sửa tất cả tài khoản.")
            else:
                st.title("✅ CẤP QUYỀN THI")
                st.info("Giảng viên chỉ thấy và chỉnh sửa danh sách Học viên.")
            
            ws_hv = db.worksheet("HocVien")
            data_hv = ws_hv.get_all_records()
            df_hv = pd.DataFrame(data_hv)
            
            if not df_hv.empty:
                # --- LOGIC LỌC DỮ LIỆU ---
                if is_admin:
                    # Admin thấy hết
                    df_display = df_hv
                else:
                    # Giảng viên: Lọc bỏ Admin và GiangVien khác, chỉ lấy hocvien
                    # (Giả sử role trong sheet ghi là 'hocvien', 'GiangVien', 'Admin')
                    df_display = df_hv[df_hv['Role'] == 'hocvien']
                
                # --- HIỂN THỊ BẢNG SỬA VỚI DROPDOWN ---
                edited_df = st.data_editor(
                    df_display,
                    use_container_width=True,
                    height=400,
                    column_config={
                        "TrangThai": st.column_config.SelectboxColumn(
                            "Trạng Thái Thi",
                            help="Chọn trạng thái thi cho học viên",
                            width="medium",
                            options=[
                                "ChuaDuocThi", # Chưa được phép
                                "DuocThi",     # Đã cấp quyền
                                "DangThi",     # Đang làm bài
                                "DaThi",       # Đã xong
                                "Khoa"         # Khóa tài khoản
                            ],
                            required=True,
                        ),
                        "Role": st.column_config.SelectboxColumn(
                            "Vai Trò",
                            options=["hocvien", "GiangVien", "Admin"],
                            required=True,
                            disabled=not is_admin # Chỉ Admin mới sửa được Role
                        )
                    }
                )
                
                if st.button("💾 LƯU CẬP NHẬT", type="primary"):
                    try:
                        # LOGIC LƯU THÔNG MINH:
                        # 1. Nếu là Admin: Lưu đè toàn bộ vì Admin thấy toàn bộ.
                        # 2. Nếu là GV: Phải update các dòng đã sửa vào DataFrame gốc (df_hv)
                        #    để không làm mất dữ liệu của Admin/GV khác.
                        
                        if is_admin:
                            final_df = edited_df
                        else:
                            # Cập nhật các dòng của học viên vào bảng gốc
                            # Dùng Username làm khóa chính để map
                            final_df = df_hv.copy()
                            final_df.set_index(df_hv.columns[0], inplace=True) # Cột 0 là User
                            edited_df.set_index(edited_df.columns[0], inplace=True)
                            
                            final_df.update(edited_df)
                            final_df.reset_index(inplace=True)
                            edited_df.reset_index(inplace=True) # Reset lại để UI không lỗi
                        
                        # Ghi vào Sheet
                        ws_hv.clear()
                        # Lấy header
                        headers_hv = list(data_hv[0].keys()) if data_hv else ["Username","Password","Role","HoTen","TrangThai","Diem"]
                        rows_to_update = [headers_hv] + final_df.values.tolist()
                        
                        ws_hv.update(rows_to_update)
                        st.success("✅ Đã cập nhật thành công!")
                        time.sleep(1); st.rerun()
                    except Exception as e: st.error(f"Lỗi cập nhật: {e}")

        # ============================================================
        # 2. CHỨC NĂNG THI (HỌC VIÊN)
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
                    
                    if is_practice:
                        st.info("ℹ️ Chế độ luyện tập: Random 10 câu. Không lưu điểm.")
                    else:
                        st.warning("⚠️ BÀI THI CHÍNH THỨC.\n\n- Yêu cầu trạng thái: 'DuocThi'.\n- Thoát ra = VI PHẠM.")
                    
                    if st.form_submit_button("BẮT ĐẦU NGAY", type="primary"):
                        if is_practice:
                            st.session_state['loai_thi'] = 'thu'
                            all_qs = db.worksheet("CauHoi").get_all_values()
                            if len(all_qs) > 1:
                                selected_qs = random.sample(all_qs[1:], min(10, len(all_qs[1:])))
                                st.session_state['ds_cau_hoi'] = selected_qs
                                st.session_state['bat_dau'] = True
                                st.rerun()
                            else: st.error("Lỗi dữ liệu câu hỏi.")
                            
                        else:
                            # Check trạng thái realtime
                            try:
                                cell = db.worksheet("HocVien").find(st.session_state['user'])
                                status_now = db.worksheet("HocVien").cell(cell.row, 5).value
                            except: status_now = "Loi"

                            if status_now == "DuocThi":
                                st.session_state['loai_thi'] = 'that'
                                cap_nhat_trang_thai(db, st.session_state['user'], "DangThi")
                                all_qs = db.worksheet("CauHoi").get_all_values()
                                st.session_state['ds_cau_hoi'] = all_qs[1:] if len(all_qs) > 1 else []
                                st.session_state['bat_dau'] = True
                                st.rerun()
                                
                            elif status_now == "DaThi": st.error("⛔ Bạn đã thi xong rồi.")
                            elif status_now == "DangThi" or status_now == "VI_PHAM": st.error("🚨 Tài khoản đang bị khóa.")
                            else: st.error("⛔ Bạn CHƯA ĐƯỢC CẤP QUYỀN (Trạng thái phải là 'DuocThi').")

            else:
                ds = st.session_state['ds_cau_hoi']
                idx = st.session_state['chi_so']

                if idx >= len(ds):
                    st.balloons()
                    st.success(f"🏁 KẾT QUẢ: {st.session_state['diem_so']} / {len(ds)}")
                    if st.button("KẾT THÚC", type="primary"):
                        if st.session_state['loai_thi'] == 'that':
                            luu_ket_qua(db, st.session_state['user'], st.session_state['diem_so'])
                        for key in list(st.session_state.keys()): del st.session_state[key]
                        st.rerun()
                    st.stop()

                cau = ds[idx]
                while len(cau) < 7: cau.append("")

                if not st.session_state['da_nop_cau']:
                    if st.session_state['thoi_gian_het'] is None: 
                        st.session_state['thoi_gian_het'] = time.time() + THOI_GIAN_MOI_CAU
                    con_lai = int(st.session_state['thoi_gian_het'] - time.time())
                    if con_lai <= 0: st.session_state['da_nop_cau'] = True; st.session_state['lua_chon'] = None; st.rerun()

                    c_time, c_score = st.columns([2.5,1])
                    c_time.progress(max(0.0, min(1.0, con_lai/THOI_GIAN_MOI_CAU))); c_time.caption(f"⏳ {con_lai}s")
                    c_score.markdown(f"**Đ: {st.session_state['diem_so']}**")

                    with st.form(f"q_{idx}"):
                        st.markdown(f"**Câu {idx+1}: {cau[0]}**")
                        opts = [f"A. {cau[1]}", f"B. {cau[2]}", f"C. {cau[3]}"]
                        if str(cau[4]).strip(): opts.append(f"D. {cau[4]}")
                        chon = st.radio("Đáp án:", opts, index=None)
                        if st.form_submit_button("CHỐT ĐÁP ÁN"):
                            if chon: 
                                st.session_state['lua_chon'] = chon.split(".")[0]
                                st.session_state['da_nop_cau'] = True
                                st.rerun()
                            else: st.warning("Chọn đáp án!")
                    time.sleep(1); st.rerun()
                
                else:
                    nguoi_chon = st.session_state['lua_chon']
                    dap_an_dung = str(cau[5]).strip().upper()
                    if nguoi_chon == dap_an_dung: st.success("✅ CHÍNH XÁC!")
                    else: st.error(f"❌ SAI RỒI! Đáp án đúng: {dap_an_dung}")
                    if str(cau[6]).strip(): st.info(f"💡 {cau[6]}")
                    
                    if st.button("CÂU TIẾP"):
                        if nguoi_chon == dap_an_dung: st.session_state['diem_so'] += 1
                        st.session_state['chi_so'] += 1; st.session_state['da_nop_cau'] = False
                        st.session_state['thoi_gian_het'] = None
                        st.rerun()

if __name__ == "__main__":
    main()
