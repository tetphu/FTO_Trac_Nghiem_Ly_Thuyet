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
                # Trả về đúng vai trò trong sheet (GiangVien/hocvien)
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
# --- GIAO DIỆN CHÍNH (GCPD THEME REDESIGN) ---
# =============================================
def main():
    # Cấu hình trang với Icon Cảnh sát
    st.set_page_config(page_title="GCPD Training System", page_icon="👮‍♂️", layout="centered")
    
    # --- CSS TÙY CHỈNH (GCPD BLUE THEME) ---
    st.markdown("""
        <style>
        /* 1. Tổng thể nền ứng dụng - Màu xanh đậm cảnh sát */
        .stApp {
            background-color: #0a192f; /* Xanh navy rất đậm */
            background-image: linear-gradient(135deg, #0a192f 0%, #172a45 100%);
            color: #e6f1ff; /* Màu chữ trắng xanh nhẹ */
        }

        /* 2. Tiêu đề chính */
        h1, h2, h3 {
            font-family: 'Arial Black', sans-serif;
            color: #64ffda; /* Màu xanh ngọc nổi bật cho tiêu đề */
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* 3. GCPD FRAME - Khung chứa nội dung chuyên nghiệp */
        .gcpd-container {
            background-color: #112240; /* Nền khung tối hơn nền chính */
            border: 2px solid #1d3f72; /* Viền xanh cảnh sát */
            border-radius: 15px; /* Bo góc */
            padding: 30px;
            box-shadow: 0 10px 30px -15px rgba(2, 12, 27, 0.7); /* Đổ bóng tạo chiều sâu */
            margin-bottom: 25px;
        }

        /* 4. Tùy chỉnh các Input field (Ô nhập liệu) */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
            background-color: #1d3557 !important; /* Nền input tối */
            color: #ffffff !important; /* Chữ trắng */
            border: 1px solid #457b9d !important; /* Viền xanh sáng hơn */
            border-radius: 8px !important;
        }
        /* Màu chữ khi focus vào ô input */
        .stTextInput input:focus {
            border-color: #64ffda !important;
            box-shadow: 0 0 0 1px #64ffda !important;
        }

        /* 5. Tùy chỉnh Nút bấm (Buttons) */
        .stButton button {
            background-color: #0056b3 !important; /* Xanh dương đậm */
            color: white !important;
            font-weight: bold !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 12px 24px !important;
            transition: all 0.3s ease !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            width: 100%;
        }
        .stButton button:hover {
            background-color: #004494 !important; /* Đậm hơn khi di chuột */
            box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
            transform: translateY(-2px);
        }

        /* 6. Tùy chỉnh Radio Button (Chọn đáp án) */
        .stRadio > div {
            background-color: #1d3557;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #1d3f72;
        }
        /* Màu chữ của các lựa chọn */
        .stRadio label {
            color: #e6f1ff !important;
            font-size: 16px !important;
        }

        /* 7. Sidebar (Cột bên trái) */
        [data-testid="stSidebar"] {
            background-color: #172a45;
            border-right: 2px solid #1d3f72;
        }
        [data-testid="stSidebar"] h1 {
            color: #64ffda !important;
        }
        /* Metric (Điểm số) */
        [data-testid="stMetricValue"] {
            color: #64ffda !important;
            font-weight: bold;
        }

        /* 8. Thông báo (Alerts) */
        .stAlert {
            background-color: #1d3557;
            color: #e6f1ff;
            border: 1px solid #64ffda;
            border-radius: 8px;
        }
        
        /* Thanh tiến trình */
        .stProgress > div > div > div {
            background-color: #64ffda !important; /* Màu xanh ngọc cho thanh thời gian */
        }
        </style>
    """, unsafe_allow_html=True)

    # --- Header chung ---
    col1, col2 = st.columns([1, 5])
    with col1:
        # Bạn có thể thay bằng link ảnh logo GCPD thật nếu có
        st.image("https://cdn-icons-png.flaticon.com/512/921/921089.png", width=80) 
    with col2:
        st.title("GCPD GACHA CITY")
        st.markdown("### Hệ Thống Đào Tạo & Sát Hạch Sĩ Quan")
    st.divider()

    # Khởi tạo kết nối và Session
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
    # 1. MÀN HÌNH ĐĂNG NHẬP (GCPD LOGIN FRAME)
    # ==========================================
    if st.session_state['vai_tro'] is None:
        
        # Sử dụng container với class CSS tùy chỉnh để tạo khung
        st.markdown('<div class="gcpd-container">', unsafe_allow_html=True)
        st.subheader("🛡️ Cổng Đăng Nhập An Ninh")
        st.write("Vui lòng nhập mã định danh sĩ quan để truy cập.")
        
        with st.form("form_login"):
            u = st.text_input("Mã sĩ quan (Tên đăng nhập)", placeholder="Nhập mã số...")
            p = st.text_input("Mã bảo mật (Mật khẩu)", type="password", placeholder="Nhập mật khẩu...")
            btn = st.form_submit_button("TRUY CẬP HỆ THỐNG")
            
            if btn:
                vt, ten = kiem_tra_dang_nhap(db, u, p)
                if vt == "DA_KHOA":
                    st.error("⛔ CẢNH BÁO: Tài khoản này đã hoàn tất sát hạch và bị khóa.")
                elif vt:
                    st.session_state['vai_tro'] = vt
                    st.session_state['user'] = u
                    st.session_state['ho_ten'] = ten
                    st.session_state['chi_so'] = 0; st.session_state['diem_so'] = 0; st.session_state['ds_cau_hoi'] = []; st.session_state['da_nop_cau'] = False; st.session_state['lua_chon'] = None; st.session_state['thoi_gian_het'] = None
                    st.success(f"Xác thực thành công. Chào mừng sĩ quan {ten}.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Lỗi xác thực: Sai thông tin đăng nhập.")
        st.markdown('</div>', unsafe_allow_html=True) # Đóng thẻ div gcpd-container

    # ==========================================
    # 2. GIAO DIỆN GIẢNG VIÊN (GCPD ADMIN PANEL)
    # ==========================================
    elif st.session_state['vai_tro'] == 'GiangVien':
        st.sidebar.image("https://cdn-icons-png.flaticon.com/512/206/206856.png", width=100)
        st.sidebar.markdown(f"### 👮‍♂️ Chỉ huy: {st.session_state['ho_ten']}")
        st.sidebar.info("Chế độ: Quản trị hệ thống")
        if st.sidebar.button("Đăng xuất an toàn"):
            st.session_state['vai_tro'] = None
            st.rerun()
        
        # Khung nhập liệu câu hỏi
        st.markdown('<div class="gcpd-container">', unsafe_allow_html=True)
        st.header("📝 Bổ Sung Dữ Liệu Sát Hạch")
        with st.form("add"):
            q = st.text_input("Nội dung câu hỏi tình huống")
            c1, c2 = st.columns(2)
            a, b = c1.text_input("Phương án A"), c1.text_input("Phương án B")
            c, d = c2.text_input("Phương án C"), c2.text_input("Phương án D")
            dung = st.selectbox("Phương án xử lý ĐÚNG", ["A", "B", "C", "D"])
            gt = st.text_area("Giải thích nghiệp vụ")
            if st.form_submit_button("LƯU VÀO HỒ SƠ"):
                try:
                    db.worksheet("CauHoi").append_row([q, a, b, c, d, dung, gt])
                    st.success("✅ Đã cập nhật cơ sở dữ liệu thành công!")
                except Exception as e: st.error(f"Lỗi hệ thống: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    # ==========================================
    # 3. GIAO DIỆN HỌC VIÊN (GCPD EXAM INTERFACE)
    # ==========================================
    elif st.session_state['vai_tro'] == 'hocvien':
        # Sidebar thông tin học viên
        st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3262/3262474.png", width=100)
        st.sidebar.markdown(f"### 👮‍♀️ Sĩ quan: {st.session_state['ho_ten']}")
        st.sidebar.markdown("---")
        st.sidebar.metric("Điểm Tích Lũy", f"{st.session_state['diem_so']} điểm")
        st.sidebar.markdown("---")
        st.sidebar.warning("⚠️ Lưu ý: Giữ kết nối ổn định trong quá trình sát hạch.")

        # Tải dữ liệu
        if not st.session_state['ds_cau_hoi']:
            try: st.session_state['ds_cau_hoi'] = db.worksheet("CauHoi").get_all_values()[1:]
            except: st.error("Không tìm thấy dữ liệu câu hỏi."); st.stop()
        
        ds = st.session_state['ds_cau_hoi']
        idx = st.session_state['chi_so']
        if not ds: st.warning("Hệ thống chưa có dữ liệu sát hạch."); st.stop()

        # Kết thúc bài thi
        if idx >= len(ds):
            st.markdown('<div class="gcpd-container" style="text-align:center;">', unsafe_allow_html=True)
            st.balloons()
            st.header("🏁 HOÀN THÀNH SÁT HẠCH")
            st.success(f"Báo cáo kết quả cuối cùng: {st.session_state['diem_so']} / {len(ds)}")
            st.info("Đang lưu hồ sơ lên máy chủ GCPD và đăng xuất...")
            luu_ket_qua(db, st.session_state['user'], st.session_state['diem_so'])
            time.sleep(4)
            st.session_state['vai_tro'] = None
            st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            return

        # Hiển thị câu hỏi trong khung chuyên nghiệp
        cau = ds[idx]; 
        while len(cau) < 7: cau.append("")
        
        st.markdown(f'<div class="gcpd-container">', unsafe_allow_html=True)
        st.subheader(f"📑 Tình huống sát hạch số {idx + 1}:")
        st.markdown(f"**{cau[0]}**") # In đậm câu hỏi

        if not st.session_state['da_nop_cau']:
            # Đồng hồ đếm ngược
            if st.session_state['thoi_gian_het'] is None: st.session_state['thoi_gian_het'] = time.time() + THOI_GIAN_MOI_CAU
            con_lai = int(st.session_state['thoi_gian_het'] - time.time())
            if con_lai <= 0: st.session_state['da_nop_cau'] = True; st.rerun()
            
            st.progress(max(0.0, min(1.0, con_lai/THOI_GIAN_MOI_CAU)))
            st.caption(f"⏱️ Thời gian phản ứng còn lại: {con_lai} giây")

            with st.form(f"f_{idx}"):
                opts = [f"A. {cau[1]}", f"B. {cau[2]}", f"C. {cau[3]}"]
                if cau[4].strip(): opts.append(f"D. {cau[4]}")
                chon = st.radio("Lựa chọn phương án xử lý:", opts, index=None)
                st.markdown("<br>", unsafe_allow_html=True) # Khoảng cách
                if st.form_submit_button("XÁC NHẬN PHƯƠNG ÁN"):
                    if chon: st.session_state['lua_chon'] = chon.split(".")[0]; st.session_state['da_nop_cau'] = True; st.rerun()
                    else: st.warning("⚠️ Yêu cầu chọn một phương án trước khi xác nhận.")
            time.sleep(1); st.rerun()
        else:
            # Hiển thị kết quả
            nguoi_chon = st.session_state['lua_chon']; dung_an = str(cau[5]).strip().upper()
            if nguoi_chon == dung_an:
                st.success(f"✅ XỬ LÝ CHÍNH XÁC!\n\n💡 **Phân tích nghiệp vụ:** {cau[6]}")
                dung = True
            else:
                msg = f"❌ XỬ LÝ SAI QUY TRÌNH! (Bạn chọn: {nguoi_chon})" if nguoi_chon else "⌛ HẾT THỜI GIAN PHẢN ỨNG!"
                st.error(f"{msg}\n\n👉 **Phương án đúng:** {dung_an}\n\n💡 **Phân tích nghiệp vụ:** {cau[6]}")
                dung = False
            
            if st.button("CHUYỂN TÌNH HUỐNG TIẾP THEO ➡️"):
                if dung: st.session_state['diem_so'] += 1
                st.session_state['chi_so'] += 1; st.session_state['da_nop_cau'] = False; st.session_state['thoi_gian_het'] = None; st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True) # Đóng div gcpd-container

    # --- VAI TRÒ KHÔNG HỢP LỆ ---
    else:
        st.error(f"⚠️ Cảnh báo bảo mật: Vai trò '{st.session_state['vai_tro']}' không hợp lệ trong hệ thống GCPD.")
        if st.button("Quay lại cổng an ninh"): st.session_state['vai_tro'] = None; st.rerun()

if __name__ == "__main__":
    main()