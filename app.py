import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- KIỂM TRA THƯ VIỆN PANDAS (CHỐNG LỖI TRẮNG MÀN HÌNH) ---
try:
    import pandas as pd
except ImportError:
    st.error("⚠️ LỖI: Thiếu thư viện 'pandas'. Bạn hãy vào file requirements.txt trên GitHub và thêm chữ 'pandas' vào đó nhé!")
    st.stop()

# --- 1. CẤU HÌNH ---
THOI_GIAN_MOI_CAU = 30

# --- 2. HÀM GIAO DIỆN (ĐÃ TỐI ƯU CHO MOBILE) ---
def inject_css():
    st.markdown("""
        <style>
        /* Tối ưu lề cho điện thoại */
        .block-container { 
            padding-top: 1rem; 
            padding-bottom: 3rem; 
            padding-left: 0.5rem; 
            padding-right: 0.5rem;
        }
        header, footer { visibility: hidden; }
        .stApp { background-color: #ffffff; }
        
        .gcpd-title {
            font-family: 'Arial Black', sans-serif; color: #002147; 
            font-size: 24px; /* Giảm cỡ chữ tiêu đề */
            text-transform: uppercase;
            margin-top: 5px; line-height: 1.2; font-weight: 900;
            text-align: center;
        }
        
        [data-testid="stForm"] {
            border: 2px solid #002147; border-radius: 10px; padding: 10px;
            background-image: url("https://raw.githubusercontent.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/refs/heads/main/nen.png");
            background-size: cover; background-position: center;
            background-color: rgba(255, 255, 255, 0.9); background-blend-mode: overlay;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        /* Input và Button to rõ dễ bấm */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
            border: 2px solid #002147 !important; border-radius: 5px !important;
            font-weight: bold; color: #000 !important;
        }
        .stButton button {
            background-color: #002147 !important; color: #FFD700 !important;
            font-weight: bold !important; width: 100%; 
            padding: 12px !important;
            font-size: 16px !important;
        }
        
        .lesson-card {
            background-color: #f8f9fa; border-left: 4px solid #002147;
            padding: 10px; margin-bottom: 10px; border-radius: 5px;
        }
        .lesson-title { color: #002147; font-size: 18px; font-weight: bold; margin-bottom: 5px; }
        .lesson-content { font-size: 14px; line-height: 1.5; color: #333; white-space: pre-wrap; }
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
            if str(row[0]).strip() == str(user).strip() and str(row[1]).strip() == str(pwd).strip():
                status = str(row[4]).strip() if len(row) > 4 else ""
                if status == 'DaThi': return "DA_KHOA", None
                if status == 'DangThi': return "VI_PHAM", None
                return str(row[2]).strip(), str(row[3]).strip()
    except: pass
    return None, None

def danh_dau_dang_thi(db, user):
    try:
        ws = db.worksheet("HocVien")
        cell = ws.find(user)
        ws.update_cell(cell.row, 5, "DangThi")
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
    # QUAN TRỌNG: layout="centered" ĐỂ TỐI ƯU CHO ĐIỆN THOẠI
    st.set_page_config(page_title="FTO System", page_icon="🚓", layout="centered")
    inject_css() 

    if 'vai_tro' not in st.session_state: 
        st.session_state.update(vai_tro=None, chi_so=0, diem_so=0, ds_cau_hoi=[], da_nop_cau=False, bat_dau=False, thoi_gian_het=None, lua_chon=None)

    db = ket_noi_csdl()
    if not db: st.stop()

    # --- A. MÀN HÌNH ĐĂNG NHẬP ---
    if st.session_state['vai_tro'] is None:
        with st.form("login"):
            c1, c2 = st.columns([1, 2.5])
            with c1: st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", use_column_width=True)
            with c2: st.markdown('<div class="gcpd-title">GACHA CITY<BR>POLICE DEPT<BR>ACADEMY</div>', unsafe_allow_html=True)
            st.divider()
            st.markdown("<h4 style='text-align: center;'>▼ ĐĂNG NHẬP HỆ THỐNG</h4>", unsafe_allow_html=True)
            u = st.text_input("SỐ HIỆU (Momo)")
            p = st.text_input("MÃ BẢO MẬT", type="password")
            
            if st.form_submit_button("XÁC THỰC DANH TÍNH"):
                vt, ten = kiem_tra_dang_nhap(db, u, p)
                if vt == "DA_KHOA": st.error("⛔ ĐÃ HOÀN THÀNH BÀI THI.")
                elif vt == "VI_PHAM": 
                    st.error("🚨 CẢNH BÁO VI PHẠM!")
                    st.warning("Hồ sơ bị khóa do thoát khi đang thi.")
                elif vt:
                    st.session_state.update(vai_tro=vt, user=u, ho_ten=ten)
                    st.rerun()
                else: st.error("❌ SAI THÔNG TIN")

    # --- B. ĐÃ ĐĂNG NHẬP ---
    else:
        with st.sidebar:
            st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", width=100)
            st.markdown(f"### 👮 Sĩ quan: {st.session_state['ho_ten']}")
            st.code(f"Vai trò: {st.session_state['vai_tro']}") 
            
            if st.session_state['bat_dau']:
                st.divider()
                st.metric("🏆 ĐIỂM", f"{st.session_state['diem_so']}")
            st.divider()
            
            # PHÂN QUYỀN MENU
            if st.session_state['vai_tro'] == 'GiangVien':
                ds_chuc_nang = ["📖 GIÁO TRÌNH FTO (GV)", "⚙️ QUẢN LÝ CÂU HỎI (GV)"]
            else:
                ds_chuc_nang = ["📝 SÁT HẠCH LÝ THUYẾT"]
            
            menu = st.radio("MENU CHỨC NĂNG", ds_chuc_nang)
            st.write(""); st.write("")
            if st.button("ĐĂNG XUẤT"):
                for key in list(st.session_state.keys()): del st.session_state[key]
                st.rerun()

        # --- LOGIC CÁC CHỨC NĂNG ---
        
        # 1. GIÁO TRÌNH
        if "GIÁO TRÌNH FTO" in menu:
            st.title("📚 TÀI LIỆU NỘI BỘ")
            ds_bai = lay_giao_trinh(db)
            if not ds_bai: st.warning("Chưa có bài giảng.")
            else:
                for bai in ds_bai:
                    with st.container():
                        st.markdown(f"""<div class="lesson-card"><div class="lesson-title">{bai['BaiHoc']}</div><div class="lesson-content">{bai['NoiDung']}</div></div>""", unsafe_allow_html=True)
                        if str(bai['HinhAnh']).startswith("http"): st.image(bai['HinhAnh'], use_column_width=True)
                        st.divider()

        # 2. QUẢN LÝ CÂU HỎI
        elif "QUẢN LÝ CÂU HỎI" in menu:
            st.title("⚙️ NGÂN HÀNG CÂU HỎI")
            st.caption("💡 Hướng dẫn: Bấm vào ô để sửa. Chọn dòng và bấm Delete để xóa. Bấm nút '+' để thêm.")
            
            ws_cauhoi = db.worksheet("CauHoi")
            data = ws_cauhoi.get_all_records()
            df = pd.DataFrame(data)

            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, height=500)

            if st.button("💾 LƯU THAY ĐỔI", type="primary"):
                with st.spinner("Đang lưu..."):
                    try:
                        ws_cauhoi.clear()
                        rows_to_update = [edited_df.columns.values.tolist()] + edited_df.values.tolist()
                        ws_cauhoi.update(rows_to_update)
                        st.success("✅ Đã cập nhật!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi khi lưu: {e}")

        # 3. THI SÁT HẠCH
        elif "SÁT HẠCH LÝ THUYẾT" in menu:
            # A. CHƯA BẮT ĐẦU
            if not st.session_state['bat_dau']:
                with st.form("start_exam"):
                    c1, c2 = st.columns([1, 2])
                    with c1: st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", use_column_width=True)
                    with c2: st.markdown("### BÀI THI SÁT HẠCH")
                    st.warning("⚠️ LƯU Ý: Thoát ra giữa chừng sẽ bị KHÓA HỒ SƠ.")
                    if st.form_submit_button("BẮT ĐẦU LÀM BÀI", type="primary"):
                        danh_dau_dang_thi(db, st.session_state['user'])
                        st.session_state['bat_dau'] = True
                        st.rerun()
            
            # B. ĐANG LÀM BÀI
            else:
                if not st.session_state['ds_cau_hoi']:
                    raw = db.worksheet("CauHoi").get_all_values()
                    st.session_state['ds_cau_hoi'] = raw[1:] if len(raw) > 1 else []
                
                ds = st.session_state['ds_cau_hoi']
                idx = st.session_state['chi_so']

                if idx >= len(ds):
                    st.balloons(); st.success(f"KẾT QUẢ: {st.session_state['diem_so']}/{len(ds)}")
                    if st.button("NỘP HỒ SƠ"):
                        luu_ket_qua(db, st.session_state['user'], st.session_state['diem_so'])
                        for key in list(st.session_state.keys()): del st.session_state[key]
                        st.rerun()
                    st.stop()

                cau = ds[idx]
                while len(cau) < 7: cau.append("")

                # TRẠNG THÁI: CHƯA CHỐT ĐÁP ÁN
                if not st.session_state['da_nop_cau']:
                    if st.session_state['thoi_gian_het'] is None: 
                        st.session_state['thoi_gian_het'] = time.time() + THOI_GIAN_MOI_CAU
                    con_lai = int(st.session_state['thoi_gian_het'] - time.time())
                    if con_lai <= 0: st.session_state['da_nop_cau'] = True; st.session_state['lua_chon'] = None; st.rerun()

                    c_time, c_score = st.columns([2.5,1]) # Chỉnh tỷ lệ cột cho mobile
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
                
                # TRẠNG THÁI: ĐÃ CHỐT
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
