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
        st.error(f"LỖI KẾT NỐI HỆ THỐNG: {str(e)}")
        return None

# --- XỬ LÝ ĐĂNG NHẬP ---
def kiem_tra_dang_nhap(bang_tinh, user, pwd):
    try:
        ws = bang_tinh.worksheet("HocVien")
        tat_ca_dong = ws.get_all_values()
        # Duyệt từ dòng 2
        for dong in tat_ca_dong[1:]:
            # Kiểm tra dòng rỗng
            if len(dong) < 4:
                continue
            
            u_sheet = str(dong[0]).strip()
            p_sheet = str(dong[1]).strip()
            
            if u_sheet == str(user).strip() and p_sheet == str(pwd).strip():
                trang_thai = str(dong[4]).strip() if len(dong) > 4 else ""
                if trang_thai == 'DaThi':
                    return "DA_KHOA", None
                
                # Trả về Vai trò và Họ tên
                return str(dong[2]).strip(), str(dong[3]).strip()
    except Exception as e:
        st.error(f"LỖI TRUY XUẤT DỮ LIỆU: {str(e)}")
    return None, None

# --- LƯU KẾT QUẢ ---
def luu_ket_qua(bang_tinh, user, diem):
    try:
        ws = bang_tinh.worksheet("HocVien")
        cell = ws.find(user)
        ws.update_cell(cell.row, 5, "DaThi")
        ws.update_cell(cell.row, 6, str(diem))
        return True
    except:
        return False

# --- LẤY CÂU HỎI ---
def lay_ds_cau_hoi(bang_tinh):
    return bang_tinh.worksheet("CauHoi").get_all_values()[1:]

# =============================================
# --- GIAO DIỆN: GACHA CITY POLICE DEPARTMENT ---
# =============================================
def main():
    st.set_page_config(page_title="GCPD System", page_icon="🚓", layout="centered")
    
    # --- CSS: PHONG CÁCH CẢNH SÁT MỸ (NỀN TRẮNG - KHUNG XANH) ---
    st.markdown("""
        <style>
        /* 1. NỀN TRANG WEB: Trắng */
        .stApp {
            background-color: #ffffff;
        }

        /* 2. KHUNG BAO BỌC (WRAPPER) */
        .gcpd-wrapper {
            border: 5px solid #002147; /* Viền Xanh Navy Đậm */
            border-radius: 6px;
            margin-top: 10px;
            margin-bottom: 20px;
            box-shadow: 0px 10px 30px rgba(0,0,0,0.15);
            background-color: #f8f9fa; /* Màu xám rất nhạt bên trong */
            overflow: hidden;
        }

        /* 3. HEADER CỦA KHUNG */
        .gcpd-header {
            background-color: #002147; /* Nền Xanh Navy */
            color: #FFD700; /* Chữ Vàng Đồng */
            padding: 25px;
            text-align: center;
            font-family: 'Arial Black', sans-serif;
            font-size: 24px;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 5px solid #FFD700;
        }

        .gcpd-subheader {
            background-color: #e9ecef;
            color: #002147;
            text-align: center;
            padding: 10px;
            font-weight: bold;
            font-family: 'Courier New', monospace;
            text-transform: uppercase;
            border-bottom: 1px solid #ccc;
            font-size: 14px;
        }

        /* 4. NỘI DUNG BÊN TRONG */
        .gcpd-body {
            padding: 30px;
        }

        /* 5. INPUT FIELDS (HỒ SƠ) */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
            border: 2px solid #002147 !important;
            border-radius: 4px !important;
            background-color: #ffffff !important;
            color: #000 !important;
            font-family: 'Courier New', monospace;
            font-weight: bold;
        }
        
        /* 6. BUTTON (NÚT BẤM) */
        .stButton button {
            background-color: #002147 !important;
            color: #FFD700 !important;
            border: none !important;
            border-radius: 4px !important;
            font-weight: bold !important;
            text-transform: uppercase;
            padding: 12px 0px !important;
            width: 100%;
            font-size: 16px !important;
            transition: 0.3s;
        }
        .stButton button:hover {
            background-color: #003366 !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        }

        /* 7. RADIO BUTTON (ĐÁP ÁN) */
        .stRadio div[role="radiogroup"] > label {
            background-color: #ffffff;
            padding: 12px;
            border: 1px solid #ccc;
            border-left: 6px solid #002147;
            margin-bottom: 8px;
            color: #000 !important;
            font-weight: 500;
        }

        /* 8. SIDEBAR */
        [data-testid="stSidebar"] {
            background-color: #f0f2f6;
            border-right: 3px solid #002147;
        }
        </style>
    """, unsafe_allow_html=True)

    # Khởi tạo Session State
    if 'vai_tro' not in st.session_state: st.session_state['vai_tro'] = None
    if 'chi_so' not in st.session_state: st.session_state['chi_so'] = 0
    if 'diem_so' not in st.session_state: st.session_state['diem_so'] = 0
    if 'ds_cau_hoi' not in st.session_state: st.session_state['ds_cau_hoi'] = []
    if 'da_nop_cau' not in st.session_state: st.session_state['da_nop_cau'] = False
    if 'lua_chon' not in st.session_state: st.session_state['lua_chon'] = None
    if 'thoi_gian_het' not in st.session_state: st.session_state['thoi_gian_het'] = None

    # Kết nối Database
    db = ket_noi_csdl()
    if db is None:
        st.stop()

    # ==========================================
    # 1. MÀN HÌNH ĐĂNG NHẬP
    # ==========================================
    if st.session_state['vai_tro'] is None:
        
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            st.image("https://github.com/tetphu/FTO_Trac_Nghiem_Ly_Thuyet/blob/main/GCPD%20(2).png?raw=true", use_container_width=True)

        # MỞ KHUNG GACHA CITY
        st.markdown("""
            <div class="gcpd-wrapper">
                <div class="gcpd-header">GACHA CITY POLICE DEPARTMENT</div>
                <div class="gcpd-subheader">HỆ THỐNG ĐÀO TẠO & SÁT HẠCH TRỰC TUYẾN</div>
                <div class="gcpd-body">
        """, unsafe_allow_html=True)

        st.write("Vui lòng nhập thông tin định danh để truy cập hệ thống.")
        
        with st.form("form_login"):
            u = st.text_input("SỐ HIỆU SĨ QUAN (TÊN ĐĂNG NHẬP)", placeholder="Nhập mã số...")
            p = st.text_input("MÃ BẢO MẬT (MẬT KHẨU)", type="password", placeholder="Nhập mật khẩu...")
            st.markdown("<br>", unsafe_allow_html=True)
            btn = st.form_submit_button("XÁC THỰC DANH TÍNH")
            
            if btn:
                vt, ten = kiem_tra_dang_nhap(db, u, p)
                if vt == "DA_KHOA":
                    st.error("⛔ TỪ CHỐI: HỒ SƠ ĐÃ BỊ KHÓA (ĐÃ HOÀN THÀNH)")
                elif vt:
                    st.session_state['vai_tro'] = vt
                    st.session_state['user'] = u
                    st.session_state['ho_ten'] = ten
                    # Reset
                    st.session_state['chi_so'] = 0
                    st.session_state['diem_so'] = 0
                    st.session_state['ds_cau_hoi'] = []
                    st.session_state['da_nop_cau'] = False
                    st.session_state['lua_chon'] = None
                    st.session_state['thoi_gian_het'] = None
                    st.success(f"XÁC THỰC THÀNH CÔNG. CHÀO MỪNG {ten}.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ XÁC THỰC THẤT BẠI: SAI THÔNG TIN")
        
        # ĐÓNG KHUNG
        st.markdown('</div></div>', unsafe_allow_html=True)

    # ==========================================
    # 2. GIAO DIỆN GIẢNG VIÊN (GiangVien)
    # ==========================================
    elif st.session_state['vai_tro'] == 'GiangVien':
        st.sidebar.markdown(f"### CHỈ HUY: {st.session_state['ho_ten']}")
        st.sidebar.info("CẤP ĐỘ: QUẢN TRỊ VIÊN")
        if st.sidebar.button("ĐĂNG XUẤT"):
            st.session_state['vai_tro'] = None
            st.rerun()
        
        st.markdown("""
            <div class="gcpd-wrapper">
                <div class="gcpd-header">GACHA CITY POLICE DEPARTMENT</div>
                <div class="gcpd-subheader">BẢNG ĐIỀU KHIỂN CHỈ HUY - CẬP NHẬT DỮ LIỆU</div>
                <div class="gcpd-body">
        """, unsafe_allow_html=True)
        
        with st.form("add"):
            q = st.text_input("NỘI DUNG CÂU HỎI / TÌNH HUỐNG")
            c1, c2 = st.columns(2)
            with c1:
                a = st.text_input("PHƯƠNG ÁN A")
                b = st.text_input("PHƯƠNG ÁN B")
            with c2:
                c = st.text_input("PHƯƠNG ÁN C")
                d = st.text_input("PHƯƠNG ÁN D")
            
            dung = st.selectbox("ĐÁP ÁN ĐÚNG", ["A", "B", "C", "D"])
            gt = st.text_area("GIẢI THÍCH NGHIỆP VỤ")
            
            if st.form_submit_button("LƯU VÀO MÁY CHỦ"):
                try:
                    ws = db.worksheet("CauHoi")
                    ws.append_row([q, a, b, c, d, dung, gt])
                    st.success("✅ ĐÃ CẬP NHẬT CƠ SỞ DỮ LIỆU THÀNH CÔNG.")
                except Exception as e:
                    st.error(f"LỖI TẢI LÊN: {e}")
        
        st.markdown('</div></div>', unsafe_allow_html=True)

    # ==========================================
    # 3. GIAO DIỆN HỌC VIÊN (hocvien)
    # ==========================================
    elif st.session_state['vai_tro'] == 'hocvien':
        # Sidebar
        st.sidebar.markdown(f"### SĨ QUAN: {st.session_state['ho_ten']}")
        st.sidebar.markdown("---")
        st.sidebar.metric("ĐIỂM TÍCH LŨY", f"{st.session_state['diem_so']}")
        st.sidebar.markdown("---")
        st.sidebar.write("TRẠNG THÁI: ĐANG LÀM NHIỆM VỤ")
        
        # Tải dữ liệu an toàn
        if not st.session_state['ds_cau_hoi']:
            try:
                raw_data = db.worksheet("CauHoi").get_all_values()
                if len(raw_data) > 1:
                    st.session_state['ds_cau_hoi'] = raw_data[1:]
                else:
                    st.error("CHƯA CÓ DỮ LIỆU CÂU HỎI.")
                    st.stop()
            except Exception as e:
                st.error(f"LỖI KẾT NỐI MÁY CHỦ: {e}")
                st.stop()
        
        ds = st.session_state['ds_cau_hoi']
        idx = st.session_state['chi_so']

        # Kết thúc bài thi
        if idx >= len(ds):
            st.markdown("""
                <div class="gcpd-wrapper">
                    <div class="gcpd-header">BÁO CÁO KẾT QUẢ</div>
                    <div class="gcpd-body" style="text-align:center;">
            """, unsafe_allow_html=True)
            st.balloons()
            st.markdown(f"<h1>KẾT QUẢ: {st.session_state['diem_so']} / {len(ds)}</h1>", unsafe_allow_html=True)
            st.info("ĐANG LƯU HỒ SƠ VỀ MÁY CHỦ TRUNG TÂM...")
            luu_ket_qua(db, st.session_state['user'], st.session_state['diem_so'])
            time.sleep(3)
            st.session_state['vai_tro'] = None
            st.rerun()
            st.markdown('</div></div>', unsafe_allow_html=True)
            return

        # Hiển thị câu hỏi
        cau = ds[idx]
        while len(cau) < 7:
            cau.append("")
        
        # --- KHUNG BAO BỌC CÂU HỎI ---
        st.markdown(f"""
            <div class="gcpd-wrapper">
                <div class="gcpd-header">HỒ SƠ TÌNH HUỐNG SỐ {idx + 1}</div>
                <div class="gcpd-body">
        """, unsafe_allow_html=True)
        
        # Nội dung câu hỏi
        st.markdown(f"<div style='background:#f0f2f6; padding:15px; border-left:5px solid #FFD700; margin-bottom:20px; font-weight:bold; font-size:18px; color:#000;'>{cau[0]}</div>", unsafe_allow_html=True)

        if not st.session_state['da_nop_cau']:
            if st.session_state['thoi_gian_het'] is None:
                st.session_state['thoi_gian_het'] = time.time() + THOI_GIAN_MOI_CAU
            
            con_lai = int(st.session_state['thoi_gian_het'] - time.time())
            if con_lai <= 0:
                st.session_state['da_nop_cau'] = True
                st.rerun()
            
            st.progress(max(0.0, min(1.0, con_lai/THOI_GIAN_MOI_CAU)))
            st.caption(f"THỜI GIAN PHẢN ỨNG CÒN LẠI: {con_lai} GIÂY")

            with st.form(f"f_{idx}"):
                opts = [f"A. {cau[1]}", f"B. {cau[2]}", f"C. {cau[3]}"]
                if str(cau[4]).strip():
                    opts.append(f"D. {cau[4]}")
                
                chon = st.radio("LỰA CHỌN PHƯƠNG ÁN XỬ LÝ:", opts, index=None)
                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.form_submit_button("THỰC THI PHƯƠNG ÁN"):
                    if chon:
                        st.session_state['lua_chon'] = chon.split(".")[0]
                        st.session_state['da_nop_cau'] = True
                        st.rerun()
                    else:
                        st.warning("YÊU CẦU CHỌN PHƯƠNG ÁN.")
            time.sleep(1)
            st.rerun()
        else:
            nguoi_chon = st.session_state['lua_chon']
            dap_an_dung = str(cau[5]).strip().upper()
            
            dung = False
            if nguoi_chon == dap_an_dung:
                st.success(f"✅ CHÍNH XÁC: ĐÚNG QUY TRÌNH.\n\n💡 PHÂN TÍCH: {cau[6]}")
                dung = True
            else:
                msg = f"❌ SAI QUY TRÌNH (BẠN CHỌN {nguoi_chon})" if nguoi_chon else "⌛ HẾT GIỜ"
                st.error(f"{msg}\n\n👉 ĐÁP ÁN ĐÚNG: {dap_an_dung}\n\n💡 PHÂN TÍCH: {cau[6]}")
                dung = False
            
            if st.button("CHUYỂN HỒ SƠ TIẾP THEO ➡️"):
                if dung:
                    st.session_state['diem_so'] += 1
                st.session_state['chi_so'] += 1
                st.session_state['da_nop_cau'] = False
                st.session_state['thoi_gian_het'] = None
                st.rerun()
        
        st.markdown('</div></div>', unsafe_allow_html=True)

    # --- LỖI VAI TRÒ ---
    else:
        st.error(f"LỖI QUYỀN TRUY CẬP: {st.session_state['vai_tro']}")
        st.info("Vui lòng kiểm tra lại cột 'Vai Trò' trong Google Sheet (Phải là 'GiangVien' hoặc 'hocvien').")
        if st.button("QUAY LẠI"):
            st.session_state['vai_tro'] = None
            st.rerun()

if __name__ == "__main__":
    main()