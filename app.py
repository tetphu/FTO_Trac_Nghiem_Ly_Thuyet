import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- CẤU HÌNH HỆ THỐNG ---
THOI_GIAN_MOI_CAU = 30

# --- KẾT NỐI GOOGLE SHEET ---
def ket_noi_csdl():
    try:
        pham_vi = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" in st.secrets:
            creds_dict = st.secrets["gcp_service_account"]
            chung_chi = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, pham_vi)
        else:
            chung_chi = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", pham_vi)
        khach_hang = gspread.authorize(chung_chi)
        return khach_hang.open("HeThongTracNghiem")
    except Exception as e:
        st.error(f"Lỗi kết nối hệ thống dữ liệu GCPD: {str(e)}")
        return None

# --- XỬ LÝ ĐĂNG NHẬP ---
def kiem_tra_dang_nhap(bang_tinh, user, pwd):
    try:
        ws = bang_tinh.worksheet("HocVien")
        tat_ca_dong = ws.get_all_values()
        for dong in tat_ca_dong[1:]:
            if len(dong) < 4: continue
            u_sheet = str(dong[0]).strip()
            p_sheet = str(dong[1]).strip()
            if u_sheet == str(user).strip() and p_sheet == str(pwd).strip():
                trang_thai = str(dong[4]).strip() if len(dong) > 4 else ""
                if trang_thai == 'DaThi': return "DA_KHOA", None
                return str(dong[2]).strip(), str(dong[3]).strip()
    except Exception as e:
        st.error(f"Lỗi truy xuất hồ sơ: {str(e)}")
    return None, None

# --- LƯU KẾT QUẢ ---
def luu_ket_qua(bang_tinh, user, diem):
    try:
        ws = bang_tinh.worksheet("HocVien")
        cell = ws.find(user)
        ws.update_cell(cell.row, 5, "DaThi")
        ws.update_cell(cell.row, 6, str(diem))
        return True
    except: return False

# --- LẤY CÂU HỎI ---
def lay_ds_cau_hoi(bang_tinh):
    return bang_tinh.worksheet("CauHoi").get_all_values()[1:]

# =============================================
# --- GIAO DIỆN CHÍNH (GCPD PRO THEME V2) ---
# =============================================
def main():
    st.set_page_config(page_title="GCPD Training System", page_icon="👮‍♂️", layout="centered")
    
    # --- CSS TÙY CHỈNH (NỀN TRẮNG - KHUNG XANH) ---
    st.markdown("""
        <style>
        /* 1. NỀN CHÍNH (BÊN NGOÀI): Màu trắng giấy hồ sơ */
        .stApp {
            background-color: #ffffff; 
            color: #0a192f; /* Chữ màu xanh đen đậm để dễ đọc trên nền trắng */
        }

        /* 2. LOGO & TIÊU ĐỀ (BÊN NGOÀI) */
        h1, h2, h3 {
            font-family: 'Arial Black', sans-serif;
            color: #0a192f !important; /* Tiêu đề bên ngoài màu đậm */
            text-transform: uppercase;
        }
        
        /* 3. KHUNG GCPD (BÊN TRONG): Giữ nguyên màu xanh cảnh sát */
        .gcpd-container {
            background-color: #0a192f; /* Nền xanh Navy đậm */
            color: #e6f1ff; /* Chữ trắng sáng bên trong khung */
            border: 3px solid #1d3f72; /* Viền xanh */
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.4); /* Đổ bóng mạnh cho nổi bật */
            margin-bottom: 25px;
        }

        /* Chỉnh màu tiêu đề KHI NẰM TRONG KHUNG GCPD thành màu sáng */
        .gcpd-container h1, .gcpd-container h2, .gcpd-container h3, .gcpd-container h4 {
            color: #64ffda !important; /* Xanh ngọc Neon */
            text-shadow: 0px 0px 5px rgba(100, 255, 218, 0.3);
        }

        /* 4. INPUT FIELDS (Chỉ ảnh hưởng bên trong khung) */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
            background-color: #172a45 !important; /* Nền input tối */
            color: #ffffff !important; /* Chữ trắng */
            border: 1px solid #305cde !important; /* Viền xanh sáng */
        }
        .stTextInput label, .stSelectbox label, .stTextArea label {
            color: #ccd6f6 !important; /* Màu nhãn (Label) sáng */
            font-weight: bold;
        }

        /* 5. NÚT BẤM (BUTTONS) */
        .stButton button {
            background-color: #0056b3 !important; /* Xanh cảnh sát */
            color: white !important;
            font-weight: bold !important;
            border: 2px solid #004494 !important;
            border-radius: 6px !important;
            padding: 10px 24px !important;
            text-transform: uppercase;
            width: 100%;
            transition: 0.3s;
        }
        .stButton button:hover {
            background-color: #003366 !important;
            border-color: #64ffda !important; /* Hover hiện viền xanh ngọc */
            transform: scale(1.02);
        }

        /* 6. RADIO BUTTONS (Trắc nghiệm) */
        .stRadio > div {
            background-color: transparent; 
        }
        .stRadio label {
            color: #e6f1ff !important; /* Màu chữ đáp án sáng */
            font-size: 16px !important;
        }

        /* 7. SIDEBAR */
        [data-testid="stSidebar"] {
            background-color: #f0f2f6; /* Sidebar màu xám sáng cho đồng bộ nền trắng */
            border-right: 1px solid #ddd;
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
             color: #0a192f !important;
        }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
             color: #333 !important;
        }
        
        /* 8. THÔNG BÁO (Alerts) */
        .stAlert {
            background-color: #e6fffa; /* Nền thông báo sáng */
            color: #0a192f;
            border: 1px solid #0a192f;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- Header Logo & Tiêu đề (Nền trắng, Chữ đậm) ---
    col1, col2 = st.columns([1, 4])
    with col1:
        # LOGO MỚI TỪ GITHUB
        st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", width=110)
    with col2:
        st.markdown("<h1 style='margin-bottom:0; padding-top:10px;'>GCPD GACHA CITY</h1>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#555;'>Hệ Thống Đào Tạo & Sát Hạch Nghiệp Vụ</h4>", unsafe_allow_html=True)
    
    st.markdown("---") # Đường kẻ ngang phân cách

    # Khởi tạo
    db = ket_noi_csdl()
    if db is None: st.stop()
    if 'vai_tro' not in st.session_state: st.session_state['vai_tro'] = None
    if 'chi_so' not in st.session_state: st.session_state['chi_so'] = 0
    if 'diem_so' not in st.session_state: st.session_state['diem_so'] = 0
    if 'ds_cau_hoi' not in st.session_state: st.session_state['ds_cau_hoi'] = []
    if 'da_nop_cau' not in st.session_state: st.session_state['da_nop_cau'] = False
    if 'lua_chon' not in st.session_state: st.session_state['lua_chon'] = None
    if 'thoi_gian_het' not in st.session_state: st.session_state['thoi_gian_het'] = None

    # ==========================================
    # 1. MÀN HÌNH ĐĂNG NHẬP
    # ==========================================
    if st.session_state['vai_tro'] is None:
        
        col_space1, col_center, col_space2 = st.columns([1, 6, 1])
        with col_center:
            # Bắt đầu khung GCPD
            st.markdown('<div class="gcpd-container">', unsafe_allow_html=True)
            st.markdown("<h3 style='text-align:center;'>🛡️ CỔNG AN NINH</h3>", unsafe_allow_html=True)
            st.write("Hệ thống yêu cầu xác thực danh tính sĩ quan trước khi truy cập.")
            
            with st.form("form_login"):
                u = st.text_input("Mã định danh (User)", placeholder="Nhập mã số...")
                p = st.text_input("Mã bảo mật (Pass)", type="password", placeholder="Nhập mật khẩu...")
                st.markdown("<br>", unsafe_allow_html=True)
                btn = st.form_submit_button("XÁC THỰC TRUY CẬP")
                
                if btn:
                    vt, ten = kiem_tra_dang_nhap(db, u, p)
                    if vt == "DA_KHOA":
                        st.error("⛔ CẢNH BÁO: Hồ sơ này đã bị khóa sau khi hoàn tất sát hạch.")
                    elif vt:
                        st.session_state['vai_tro'] = vt
                        st.session_state['user'] = u
                        st.session_state['ho_ten'] = ten
                        # Reset trạng thái
                        st.session_state['chi_so'] = 0; st.session_state['diem_so'] = 0; st.session_state['ds_cau_hoi'] = []; st.session_state['da_nop_cau'] = False; st.session_state['lua_chon'] = None; st.session_state['thoi_gian_het'] = None
                        st.success(f"Chấp nhận truy cập. Xin chào {ten}.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ TỪ CHỐI: Thông tin xác thực không hợp lệ.")
            st.markdown('</div>', unsafe_allow_html=True) # Kết thúc khung GCPD

    # ==========================================
    # 2. GIAO DIỆN GIẢNG VIÊN (ADMIN)
    # ==========================================
    elif st.session_state['vai_tro'] == 'GiangVien':
        st.sidebar.markdown(f"### 👮‍♂️ Chỉ huy: {st.session_state['ho_ten']}")
        st.sidebar.info("Trạng thái: Admin Mode")
        if st.sidebar.button("Đăng xuất"):
            st.session_state['vai_tro'] = None
            st.rerun()
        
        st.markdown('<div class="gcpd-container">', unsafe_allow_html=True)
        st.markdown("<h3>📝 BỔ SUNG DỮ LIỆU TÌNH HUỐNG</h3>", unsafe_allow_html=True)
        with st.form("add"):
            q = st.text_input("Nội dung tình huống / Câu hỏi")
            c1, c2 = st.columns(2)
            a, b = c1.text_input("Phương án A"), c1.text_input("Phương án B")
            c, d = c2.text_input("Phương án C"), c2.text_input("Phương án D")
            dung = st.selectbox("Đáp án chuẩn", ["A", "B", "C", "D"])
            gt = st.text_area("Giải thích nghiệp vụ")
            if st.form_submit_button("LƯU VÀO HỆ THỐNG"):
                try:
                    db.worksheet("CauHoi").append_row([q, a, b, c, d, dung, gt])
                    st.success("✅ Đã cập nhật cơ sở dữ liệu thành công.")
                except Exception as e: st.error(f"Lỗi hệ thống: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    # ==========================================
    # 3. GIAO DIỆN HỌC VIÊN
    # ==========================================
    elif st.session_state['vai_tro'] == 'hocvien':
        # Sidebar
        st.sidebar.markdown(f"### 👮‍♀️ Sĩ quan: {st.session_state['ho_ten']}")
        st.sidebar.markdown("---")
        st.sidebar.metric("Điểm Tích Lũy", f"{st.session_state['diem_so']} CP")
        st.sidebar.markdown("---")
        
        # Tải dữ liệu
        if not st.session_state['ds_cau_hoi']:
            try: st.session_state['ds_cau_hoi'] = db.worksheet("CauHoi").get_all_values()[1:]
            except: st.error("Lỗi dữ liệu."); st.stop()
        
        ds = st.session_state['ds_cau_hoi']
        idx = st.session_state['chi_so']
        if not ds: st.warning("Chưa có dữ liệu sát hạch."); st.stop()

        # Kết thúc
        if idx >= len(ds):
            st.markdown('<div class="gcpd-container" style="text-align:center;">', unsafe_allow_html=True)
            st.balloons()
            st.markdown("<h2>🏁 HOÀN TẤT NHIỆM VỤ</h2>", unsafe_allow_html=True)
            st.success(f"Kết quả sát hạch: {st.session_state['diem_so']} / {len(ds)}")
            st.info("Đang đồng bộ dữ liệu về máy chủ trung tâm...")
            luu_ket_qua(db, st.session_state['user'], st.session_state['diem_so'])
            time.sleep(3)
            st.session_state['vai_tro'] = None
            st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            return

        # Hiển thị câu hỏi
        cau = ds[idx]; 
        while len(cau) < 7: cau.append("")
        
        # Khung GCPD cho câu hỏi
        st.markdown(f'<div class="gcpd-container">', unsafe_allow_html=True)
        st.markdown(f"<h4>📑 Tình huống số {idx + 1}:</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{cau[0]}</p>", unsafe_allow_html=True)

        if not st.session_state['da_nop_cau']:
            if st.session_state['thoi_gian_het'] is None: st.session_state['thoi_gian_het'] = time.time() + THOI_GIAN_MOI_CAU
            con_lai = int(st.session_state['thoi_gian_het'] - time.time())
            if con_lai <= 0: st.session_state['da_nop_cau'] = True; st.rerun()
            
            st.progress(max(0.0, min(1.0, con_lai/THOI_GIAN_MOI_CAU)))
            st.caption(f"⏱️ Thời gian phản ứng: {con_lai}s")

            with st.form(f"f_{idx}"):
                opts = [f"A. {cau[1]}", f"B. {cau[2]}", f"C. {cau[3]}"]
                if cau[4].strip(): opts.append(f"D. {cau[4]}")
                chon = st.radio("Lựa chọn phương án:", opts, index=None)
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("XÁC NHẬN"):
                    if chon: st.session_state['lua_chon'] = chon.split(".")[0]; st.session_state['da_nop_cau'] = True; st.rerun()
                    else: st.warning("Vui lòng chọn phương án.")
            time.sleep(1); st.rerun()
        else:
            nguoi_chon = st.session_state['lua_chon']; dung_an = str(cau[5]).strip().upper()
            if nguoi_chon == dung_an:
                st.success(f"✅ CHÍNH XÁC!\n\n💡 Phân tích: {cau[6]}")
                dung = True
            else:
                msg = f"❌ SAI QUY TRÌNH (Chọn {nguoi_chon})" if nguoi_chon else "⌛ HẾT GIỜ"
                st.error(f"{msg}\n\n👉 Đáp án đúng: {dung_an}\n\n💡 Phân tích: {cau[6]}")
                dung = False
            
            if st.button("TIẾP TỤC ➡️"):
                if dung: st.session_state['diem_so'] += 1
                st.session_state['chi_so'] += 1; st.session_state['da_nop_cau'] = False; st.session_state['thoi_gian_het'] = None; st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True) # End div

    # --- LỖI VAI TRÒ ---
    else:
        st.error(f"Lỗi phân quyền: {st.session_state['vai_tro']}")
        if st.button("Quay lại"): st.session_state['vai_tro'] = None; st.rerun()

if __name__ == "__main__":
    main()