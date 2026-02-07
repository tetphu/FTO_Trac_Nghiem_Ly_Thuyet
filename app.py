import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import time

# --- CẤU HÌNH THỜI GIAN LÀM BÀI (PHÚT) ---
THOI_GIAN_LAM_BAI = 15  

# --- KẾT NỐI GOOGLE SHEET ---
# --- CODE CŨ (XÓA ĐI) ---
# def connect_db():
#     scope = ["..."]
#     creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
#     ...

# --- CODE MỚI (DÙNG CÁI NÀY) ---
def connect_db():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Kiểm tra xem đang chạy trên Cloud hay dưới máy
    if "gcp_service_account" in st.secrets:
        # Nếu trên Cloud: Lấy chìa khóa từ Secrets
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        # Nếu dưới máy: Lấy từ file json như cũ
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        
    client = gspread.authorize(creds)
    sheet = client.open("HeThongTracNghiem")
    return sheet

# --- HÀM ĐĂNG NHẬP (Lấy thêm Họ Tên) ---
def login(sheet, user, pwd):
    users_ws = sheet.worksheet("Users")
    records = users_ws.get_all_records()
    for record in records:
        # Chuyển đổi sang string để tránh lỗi so sánh số/chữ
        if str(record['Username']) == user and str(record['Password']) == pwd:
            return record['Role'], record['HoTen'] # Trả về cả Vai trò và Họ tên
    return None, None

def luu_diem(sheet, user, diem, hoten):
    scores_ws = sheet.worksheet("Scores")
    # Lưu thêm cột Họ Tên vào bảng điểm để dễ tra cứu
    scores_ws.append_row([user, hoten, diem, str(datetime.now())])

# --- GIAO DIỆN CHÍNH ---
def main():
    st.set_page_config(page_title="Thi Trắc Nghiệm", page_icon="📝")
    st.title("🎓 Hệ Thống Trắc Nghiệm Online")
    
    try:
        db = connect_db()
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        st.stop()

    # Khởi tạo Session State
    if 'role' not in st.session_state:
        st.session_state['role'] = None
    if 'start_time' not in st.session_state:
        st.session_state['start_time'] = None

    # --- MÀN HÌNH ĐĂNG NHẬP ---
    if st.session_state['role'] is None:
        with st.form("login_form"):
            st.subheader("Đăng Nhập Hệ Thống")
            username = st.text_input("Tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password")
            submit = st.form_submit_button("Vào thi")
            
            if submit:
                role, hoten = login(db, username, password)
                if role:
                    st.session_state['role'] = role
                    st.session_state['user'] = username
                    st.session_state['hoten'] = hoten
                    # Bắt đầu tính giờ khi học viên đăng nhập
                    if role == 'student':
                        st.session_state['start_time'] = datetime.now()
                    st.success("Đăng nhập thành công!")
                    st.rerun()
                else:
                    st.error("Sai thông tin đăng nhập!")

    # --- GIAO DIỆN ADMIN ---
    elif st.session_state['role'] == 'admin':
        st.sidebar.markdown(f"👤 **Admin:** {st.session_state['hoten']}")
        if st.sidebar.button("Đăng xuất"):
            st.session_state['role'] = None
            st.session_state['start_time'] = None
            st.rerun()

        st.header("⚙️ Thêm Câu Hỏi Mới")
        with st.form("them_cau_hoi"):
            q = st.text_input("Câu hỏi")
            col1, col2, col3 = st.columns(3)
            with col1: a = st.text_input("Đáp án A")
            with col2: b = st.text_input("Đáp án B")
            with col3: c = st.text_input("Đáp án C")
            correct = st.selectbox("Đáp án đúng", ["A", "B", "C"])
            if st.form_submit_button("Lưu vào Data"):
                ws = db.worksheet("Questions")
                ws.append_row([q, a, b, c, correct])
                st.success("Đã thêm xong!")

    # --- GIAO DIỆN HỌC VIÊN ---
    elif st.session_state['role'] == 'student':
        # 1. Tính toán thời gian
        hien_tai = datetime.now()
        thoi_gian_da_troi = (hien_tai - st.session_state['start_time']).total_seconds()
        thoi_gian_con_lai = (THOI_GIAN_LAM_BAI * 60) - thoi_gian_da_troi
        
        # Sidebar thông tin
        st.sidebar.markdown(f"👋 Xin chào: **{st.session_state['hoten']}**")
        
        # Hiển thị đồng hồ
        if thoi_gian_con_lai > 0:
            phut = int(thoi_gian_con_lai // 60)
            giay = int(thoi_gian_con_lai % 60)
            st.sidebar.metric(label="⏳ Thời gian còn lại", value=f"{phut} phút {giay} giây")
            st.sidebar.progress(max(0.0, min(1.0, thoi_gian_da_troi / (THOI_GIAN_LAM_BAI * 60))))
        else:
            st.sidebar.error("HẾT GIỜ LÀM BÀI!")
        
        if st.sidebar.button("Thoát"):
            st.session_state['role'] = None
            st.rerun()

        # 2. Hiển thị bài thi
        st.header("📝 Bài Thi")
        ws = db.worksheet("Questions")
        questions = ws.get_all_records()
        
        if not questions:
            st.info("Chưa có câu hỏi nào.")
        else:
            with st.form("bai_thi"):
                answers = {}
                for i, q in enumerate(questions):
                    st.write(f"**Câu {i+1}:** {q['CauHoi']}")
                    options = [f"A. {q['DapAn_A']}", f"B. {q['DapAn_B']}", f"C. {q['DapAn_C']}"]
                    answers[i] = st.radio("Chọn đáp án:", options, key=i, label_visibility="collapsed")
                    st.write("---")
                
                # Chỉ cho nộp bài khi còn thời gian
                if thoi_gian_con_lai > 0:
                    nop_bai = st.form_submit_button("Nộp Bài")
                    if nop_bai:
                        score = 0
                        for i, q in enumerate(questions):
                            if answers[i].split(".")[0] == q['DapAn_Dung']:
                                score += 1
                        st.balloons()
                        st.success(f"Kết quả: {score}/{len(questions)} câu đúng!")
                        luu_diem(db, st.session_state['user'], score, st.session_state['hoten'])
                else:
                    st.error("Đã hết giờ! Bạn không thể nộp bài được nữa.")

if __name__ == "__main__":
    main()
