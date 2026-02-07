import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- CẤU HÌNH ---
THOI_GIAN_MOI_CAU = 30

# --- KẾT NỐI GOOGLE SHEET ---
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
        st.error(f"LỖI KẾT NỐI: {str(e)}")
        return None

# --- XỬ LÝ ĐĂNG NHẬP ---
def kiem_tra_dang_nhap(db, user, pwd):
    try:
        ws = db.worksheet("HocVien")
        rows = ws.get_all_values()
        for row in rows[1:]:
            if len(row) < 4: continue
            u_sheet = str(row[0]).strip()
            p_sheet = str(row[1]).strip()
            if u_sheet == str(user).strip() and p_sheet == str(pwd).strip():
                status = str(row[4]).strip() if len(row) > 4 else ""
                if status == 'DaThi': return "DA_KHOA", None
                return str(row[2]).strip(), str(row[3]).strip()
    except Exception as e:
        st.error(f"LỖI DỮ LIỆU: {e}")
    return None, None

# --- LƯU KẾT QUẢ ---
def luu_ket_qua(db, user, diem):
    try:
        ws = db.worksheet("HocVien")
        cell = ws.find(user)
        ws.update_cell(cell.row, 5, "DaThi")
        ws.update_cell(cell.row, 6, str(diem))
        return True
    except: return False

# --- GIAO DIỆN CHÍNH ---
def main():
    st.set_page_config(page_title="GCPD System", page_icon="🚓", layout="centered")

    # CSS GIAO DIỆN GCPD NỀN TRẮNG
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem; padding-bottom: 0rem; max-width: 800px; }
        header, footer { visibility: hidden; }
        .stApp { background-color: #ffffff; }
        
        /* KHUNG BAO BỌC */
        .gcpd-wrapper {
            border: 3px solid #002147;
            border-radius: 4px;
            background-color: #f8f9fa;
            margin-bottom: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .gcpd-header {
            background-color: #002147;
            color: #FFD700;
            padding: 10px 20px;
            display: flex;
            align-items: center;
            justify_content: space-between;
            border-bottom: 3px solid #FFD700;
        }
        .gcpd-title { font-weight: bold; font-size: 18px; margin: 0; }
        .gcpd-body { padding: 20px; }

        /* INPUT & BUTTON */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
            border: 2px solid #002147 !important;
            border-radius: 2px !important;
            background-color: #fff !important;
            color: #000 !important;
            font-weight: bold;
        }
        .stButton button {
            background-color: #002147 !important;
            color: #FFD700 !important;
            border: none !important;
            font-weight: bold !important;
            width: 100%;
        }
        
        /* SIDEBAR */
        [data-testid="stSidebar"] { background-color: #f0f2f6; border-right: 2px solid #002147; }
        </style>
    """, unsafe_allow_html=True)

    # KHỞI TẠO SESSION
    if 'vai_tro' not in st.session_state: st.session_state['vai_tro'] = None
    if 'chi_so' not in st.session_state: st.session_state['chi_so'] = 0
    if 'diem_so' not in st.session_state: st.session_state['diem_so'] = 0
    if 'ds_cau_hoi' not in st.session_state: st.session_state['ds_cau_hoi'] = []
    if 'da_nop_cau' not in st.session_state: st.session_state['da_nop_cau'] = False
    if 'lua_chon' not in st.session_state: st.session_state['lua_chon'] = None
    if 'thoi_gian_het' not in st.session_state: st.session_state['thoi_gian_het'] = None

    db = ket_noi_csdl()
    if not db: st.stop()

    # HEADER HTML
    header_html = """
    <div class="gcpd-wrapper">
        <div class="gcpd-header">
            <span class="gcpd-title">GACHA CITY POLICE DEPT.</span>
            <img src="https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true" height="30">
        </div>
        <div class="gcpd-body">
    """

    # --- 1. MÀN HÌNH ĐĂNG NHẬP ---
    if st.session_state['vai_tro'] is None:
        st.markdown(header_html, unsafe_allow_html=True)
        st.write("▼ XÁC THỰC DANH TÍNH")
        with st.form("login"):
            u = st.text_input("SỐ HIỆU (USER)")
            p = st.text_input("MÃ BẢO MẬT (PASS)", type="password")
            if st.form_submit_button("TRUY CẬP"):
                vt, ten = kiem_tra_dang_nhap(db, u, p)
                if vt == "DA_KHOA": st.error("⛔ HỒ SƠ ĐÃ KHÓA")
                elif vt:
                    st.session_state.update(vai_tro=vt, user=u, ho_ten=ten, chi_so=0, diem_so=0, ds_cau_hoi=[], da_nop_cau=False)
                    st.rerun()
                else: st.error("❌ SAI THÔNG TIN")
        st.markdown('</div></div>', unsafe_allow_html=True)

    # --- 2. GIẢNG VIÊN (GiangVien) ---
    elif st.session_state['vai_tro'] == 'GiangVien':
        st.sidebar.markdown(f"**CHỈ HUY:** {st.session_state['ho_ten']}")
        if st.sidebar.button("ĐĂNG XUẤT"): st.session_state['vai_tro'] = None; st.rerun()
        
        st.markdown(header_html, unsafe_allow_html=True)
        with st.form("add"):
            q = st.text_input("NỘI DUNG CÂU HỎI")
            c1, c2 = st.columns(2)
            a, b = c1.text_input("ĐÁP ÁN A"), c1.text_input("ĐÁP ÁN B")
            c, d = c2.text_input("ĐÁP ÁN C"), c2.text_input("ĐÁP ÁN D")
            dung = st.selectbox("ĐÁP ÁN ĐÚNG", ["A", "B", "C", "D"])
            gt = st.text_area("GIẢI THÍCH")
            if st.form_submit_button("LƯU DỮ LIỆU"):
                try:
                    db.worksheet("CauHoi").append_row([q, a, b, c, d, dung, gt])
                    st.success("ĐÃ LƯU")
                except Exception as e: st.error(str(e))
        st.markdown('</div></div>', unsafe_allow_html=True)

    # --- 3. HỌC VIÊN (hocvien) ---
    elif st.session_state['vai_tro'] == 'hocvien':
        st.sidebar.markdown(f"**SĨ QUAN:** {st.session_state['ho_ten']}")
        st.sidebar.metric("ĐIỂM", st.session_state['diem_so'])
        
        if not st.session_state['ds_cau_hoi']:
            try:
                raw = db.worksheet("CauHoi").get_all_values()
                if len(raw) > 1: st.session_state['ds_cau_hoi'] = raw[1:]
                else: st.error("KHÔNG CÓ DỮ LIỆU"); st.stop()
            except: st.error("LỖI TẢI DỮ LIỆU"); st.stop()

        ds = st.session_state['ds_cau_hoi']
        idx = st.session_state['chi_so']

        # --- [MỚI] MÀN HÌNH HOÀN THÀNH ---
        if idx >= len(ds):
            st.markdown(header_html, unsafe_allow_html=True)
            st.balloons()
            
            # Thông báo hoàn thành
            st.markdown("""
                <div style="text-align: center; color: #002147;">
                    <h2 style="color: #002147;">✅ NHIỆM VỤ HOÀN TẤT</h2>
                    <p style="font-size: 16px; font-weight: bold;">
                        Chúc mừng Sĩ Quan đã thi xong phần trắc nghiệm lý thuyết.<br>
                        Kết quả sẽ được thông báo tới Sĩ Quan ngay sau khi FTO Manager duyệt.
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            # Nút OK để lưu và thoát
            if st.button("XÁC NHẬN (OK)"):
                with st.spinner("Đang lưu hồ sơ..."):
                    luu_ket_qua(db, st.session_state['user'], st.session_state['diem_so'])
                    time.sleep(2)
                    st.session_state['vai_tro'] = None
                    st.rerun()
            
            st.markdown('</div></div>', unsafe_allow_html=True)
            return

        # HIỂN THỊ CÂU HỎI
        cau = ds[idx]
        while len(cau) < 7: cau.append("")

        st.markdown(header_html, unsafe_allow_html=True)
        st.markdown(f"<div style='background:#e9ecef; padding:10px; border-left:4px solid #FFD700; margin-bottom:10px; color:black; font-weight:bold'>CÂU {idx+1}: {cau[0]}</div>", unsafe_allow_html=True)

        if not st.session_state['da_nop_cau']:
            if st.session_state['thoi_gian_het'] is None: st.session_state['thoi_gian_het'] = time.time() + THOI_GIAN_MOI_CAU
            
            con_lai = int(st.session_state['thoi_gian_het'] - time.time())
            if con_lai <= 0: st.session_state['da_nop_cau'] = True; st.rerun()

            st.progress(max(0.0, min(1.0, con_lai / THOI_GIAN_MOI_CAU)))
            st.caption(f"THỜI GIAN: {con_lai}s")

            with st.form(f"f_{idx}"):
                opts = [f"A. {cau[1]}", f"B. {cau[2]}", f"C. {cau[3]}"]
                if str(cau[4]).strip(): opts.append(f"D. {cau[4]}")
                chon = st.radio("CHỌN PHƯƠNG ÁN:", opts, index=None)
                if st.form_submit_button("XÁC NHẬN"):
                    if chon: 
                        st.session_state['lua_chon'] = chon.split(".")[0]
                        st.session_state['da_nop_cau'] = True
                        st.rerun()
                    else: st.warning("CHƯA CHỌN ĐÁP ÁN")
            time.sleep(1); st.rerun()
        else:
            nguoi_chon = st.session_state['lua_chon']
            dap_an_dung = str(cau[5]).strip().upper()
            dung = (nguoi_chon == dap_an_dung)
            
            if dung: st.success(f"✅ CHÍNH XÁC.\n\n💡 {cau[6]}")
            else: st.error(f"❌ SAI (CHỌN {nguoi_chon}) | ĐÚNG: {dap_an_dung}\n\n💡 {cau[6]}")
            
            if st.button("TIẾP THEO"):
                if dung: st.session_state['diem_so'] += 1
                st.session_state['chi_so'] += 1
                st.session_state['da_nop_cau'] = False
                st.session_state['thoi_gian_het'] = None
                st.rerun()
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    else:
        st.error(f"LỖI VAI TRÒ: {st.session_state['vai_tro']}")
        if st.button("QUAY LẠI"): st.session_state['vai_tro'] = None; st.rerun()

if __name__ == "__main__":
    main()