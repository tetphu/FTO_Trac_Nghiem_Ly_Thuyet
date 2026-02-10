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
    st.error("Lỗi thư viện. Hãy kiểm tra requirements.txt (cần: streamlit, gspread, oauth2client, pandas)")
    st.stop()

THOI_GIAN_THI = 30

# --- 3. CSS GIAO DIỆN ---
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

# --- 5. HÀM XỬ LÝ DỮ LIỆU ---
def check_login(db, u, p):
    try:
        # Lấy toàn bộ dữ liệu để tránh lỗi sót dòng
        rows = db.worksheet("HocVien").get_all_values()
        for r in rows[1:]:
            if len(r) < 3: continue
            # Col 0=User, 1=Pass, 2=Role, 3=Name, 4=Status
            if str(r[0]).strip() == str(u).strip() and str(r[1]).strip() == str(p).strip():
                return str(r[2]).strip(), str(r[3]).strip(), (str(r[4]).strip() if len(r)>4 else "ChuaDuocThi")
    except: pass
    return None, None, None

def save_to_sheet(db, sheet_name, df_to_save):
    try:
        ws = db.worksheet(sheet_name)
        ws.clear()
        # Chuyển DataFrame thành list để ghi vào Sheet (bao gồm cả Header)
        data = [df_to_save.columns.tolist()] + df_to_save.values.tolist()
        ws.update(data)
        return True
    except Exception as e:
        st.error(f"Lỗi khi lưu: {e}")
        return False

def get_exams(db):
    try: return db.worksheet("CauHoi").get_all_values()
    except: return []

# --- 6. MAIN ---
def main():
    inject_css()
    
    # Khởi tạo Session State
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

    # --- MÀN HÌNH ĐĂNG NHẬP ---
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
        # Header
        c_info, c_logout = st.columns([3, 1])
        with c_info: st.markdown(f"<div class='user-info'>👮 {st.session_state.ho_ten} ({st.session_state.vai_tro})</div>", unsafe_allow_html=True)
        with c_logout:
            if st.button("THOÁT"):
                st.session_state.clear()
                st.rerun()
        st.divider()
        
        # Menu Navigation
        role = st.session_state.vai_tro
        if role == 'Admin': menu_items = ["QUẢN TRỊ USER", "QUẢN LÝ CÂU HỎI", "GIÁO TRÌNH"]
        elif role == 'GiangVien': menu_items = ["CẤP QUYỀN THI", "QUẢN LÝ CÂU HỎI", "GIÁO TRÌNH"]
        else: menu_items = ["THI THỬ", "THI SÁT HẠCH"]

        if st.session_state.bat_dau:
            menu = "ĐANG THI"
            st.info("⚠️ ĐANG LÀM BÀI...")
        else:
            menu = st.radio("CHỨC NĂNG:", menu_items, horizontal=True)
        st.write("")

        # =========================================================
        # CHỨC NĂNG 1: QUẢN TRỊ USER / CẤP QUYỀN (ĐÃ SỬA LỖI)
        # =========================================================
        if menu in ["QUẢN TRỊ USER", "CẤP QUYỀN THI"]:
            st.subheader("✅ QUẢN LÝ HỌC VIÊN")
            
            # 1. Lấy toàn bộ dữ liệu
            vals = db.worksheet("HocVien").get_all_values()
            headers = ["Username","Password","Role","HoTen","TrangThai","Diem"]
            
            # Ép dữ liệu vào đúng 6 cột để tránh lỗi lệch cột
            clean_data = [r[:6]+[""]*(6-len(r)) for r in vals[1:]] if len(vals)>1 else []
            full_df = pd.DataFrame(clean_data, columns=headers)
            
            # 2. Phân chia dữ liệu hiển thị
            if role == 'Admin':
                # Admin thấy hết
                df_to_edit = full_df
            else:
                # Giảng viên chỉ thấy 'hocvien', ẩn Admin/GiangVien khác
                df_to_edit = full_df[full_df['Role'] == 'hocvien']
                # Lưu lại phần bị ẩn để lát nữa gộp lại
                df_hidden = full_df[full_df['Role'] != 'hocvien']

            # 3. Hiển thị bảng Editor
            edited_df = st.data_editor(
                df_to_edit,
                use_container_width=True,
                num_rows="dynamic", # Cho phép THÊM/XÓA dòng
                hide_index=True,
                column_config={
                    "TrangThai": st.column_config.SelectboxColumn("Status", options=["ChuaDuocThi","DuocThi","DangThi","DaThi","Khoa"], required=True),
                    "Role": st.column_config.SelectboxColumn("Role", options=["hocvien","GiangVien","Admin"], required=True),
                    "Password": st.column_config.TextColumn("Password") 
                }
            )

            # 4. Nút Lưu (LOGIC QUAN TRỌNG)
            if st.button("LƯU THAY ĐỔI"):
                if role == 'Admin':
                    # Admin ghi đè tất cả (bao gồm cả dòng xóa/thêm)
                    final_df = edited_df
                else:
                    # Giảng viên: Gộp phần ẩn + phần vừa sửa
                    # Dòng nào bị xóa trong edited_df sẽ mất luôn -> Đúng logic xóa
                    # Dòng nào thêm mới trong edited_df sẽ được gộp vào -> Đúng logic thêm
                    final_df = pd.concat([df_hidden, edited_df], ignore_index=True)
                
                # Ghi vào Google Sheet
                if save_to_sheet(db, "HocVien", final_df):
                    st.success("✅ Đã cập nhật thành công! (Đã xóa/thêm/sửa)")
                    time.sleep(1)
                    st.rerun()

        # =========================================================
        # CHỨC NĂNG 2: QUẢN LÝ CÂU HỎI
        # =========================================================
        elif menu == "QUẢN LÝ CÂU HỎI":
            st.subheader("⚙️ NGÂN HÀNG CÂU HỎI")
            vals = get_exams(db)
            headers = ["CauHoi","A","B","C","D","DapAn_Dung","GiaiThich"]
            data = [r[:7]+[""]*(7-len(r)) for r in vals[1:]] if len(vals)>1 else []
            df = pd.DataFrame(data, columns=headers)
            
            edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            if st.button("LƯU CÂU HỎI"):
                if save_to_sheet(db, "CauHoi", edited):
                    st.success("Đã lưu!")
                    time.sleep(1); st.rerun()

        # =========================================================
        # CHỨC NĂNG 3: GIÁO TRÌNH
        # =========================================================
        elif menu == "GIÁO TRÌNH":
            st.subheader("📚 TÀI LIỆU")
            try:
                data = db.worksheet("GiaoTrinh").get_all_records()
                for l in data:
                    with st.expander(f"📖 {l.get('BaiHoc','Bài học')}"):
                        st.write(l.get('NoiDung',''))
                        if str(l.get('HinhAnh','')).startswith('http'): st.image(l['HinhAnh'])
            except: st.warning("Chưa có dữ liệu.")

        # =========================================================
        # CHỨC NĂNG 4: THI CỬ
        # =========================================================
        elif "THI" in menu or menu == "ĐANG THI":
            # CHUẨN BỊ
            if not st.session_state.bat_dau:
                mode = 'thu' if "THỬ" in menu else 'that'
                st.subheader("LUYỆN TẬP" if mode=='thu' else "SÁT HẠCH")
                
                if st.button("BẮT ĐẦU"):
                    if mode == 'that':
                        try:
                            # Check trạng thái real-time từ sheet
                            ws = db.worksheet("HocVien")
                            cell = ws.find(st.session_state.user)
                            stt = ws.cell(cell.row, 5).value
                            if stt != "DuocThi": 
                                st.error(f"Chưa được cấp quyền! Trạng thái hiện tại: {stt}")
                                st.stop()
                            # Cập nhật DangThi
                            ws.update_cell(cell.row, 5, "DangThi")
                        except: st.error("Lỗi User"); st.stop()

                    qs = get_exams(db)[1:]
                    if mode=='thu' and len(qs)>0: qs = random.sample(qs, min(10, len(qs)))
                    
                    st.session_state.bat_dau = True
                    st.session_state.ds_cau_hoi = qs
                    st.session_state.chi_so = 0
                    st.session_state.diem_so = 0
                    st.session_state.loai_thi = mode
                    st.rerun()

            # ĐANG LÀM BÀI
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
                        st.session_state.time_end = time.time() + THOI_GIAN_THI
                    
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
