import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# --- CẤU HÌNH ---
THOI_GIAN_MOI_CAU = 15  # Số giây cho mỗi câu hỏi

# --- KẾT NỐI GOOGLE SHEET ---
def connect_db():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Kiểm tra xem đang chạy trên Cloud hay dưới máy
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        
    client = gspread.authorize(creds)
    sheet = client.open("HeThongTracNghiem")
    return sheet

# --- HÀM XỬ LÝ ---
def login(sheet, user, pwd):
    users_ws = sheet.worksheet("Users")
    records = users_ws.get_all_records()
    for record in records:
        if str(record['Username']) == user and str(record['Password']) == pwd:
            return record['Role'], record['HoTen']
    return None, None

def luu_diem(sheet, user, diem, hoten):
    scores_ws = sheet.worksheet("Scores")
    scores_ws.append_row([user, hoten, diem, str(datetime.now())])

def get_questions(sheet):
    ws = sheet.worksheet("Questions")
    return ws.get_all_records()

# --- GIAO DIỆN CHÍNH ---
def main():
    st.set_page_config(page_title="Thi Trắc Nghiệm", page_icon="⏱️")
    
    # CSS để ẩn nút 'Running' và làm đẹp giao diện
    st.markdown("""
        <style>
        .stButton button {width: 100%;}
        </style>
    """, unsafe_allow_html=True)

    try:
        db = connect_db()
    except Exception as e:
        st.error("Lỗi kết nối Database. Vui lòng kiểm tra lại file credentials.")
        st.stop()

    # Khởi tạo Session State
    if 'role' not in st.session_state: st.session_state['role'] = None
    if 'current_index' not in st.session_state: st.session_state['current_index'] = 0
    if 'score' not in st.session_state: st.session_state['score'] = 0
    if 'questions' not in st.session_state: st.session_state['questions'] = []
    if 'end_time_question' not in st.session_state: st.session_state['end_time_question'] = None

    # --- MÀN HÌNH ĐĂNG NHẬP ---
    if st.session_state['role'] is None:
        st.title("🎓 Đăng Nhập")
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password")
            submit = st.form_submit_button("Vào thi")
            
            if submit:
                role, hoten = login(db, username, password)
                if role:
                    st.session_state['role'] = role
                    st.session_state['user'] = username
                    st.session_state['hoten'] = hoten
                    # Reset trạng thái thi
                    st.session_state['current_index'] = 0
                    st.session_state['score'] = 0
                    st.rerun()
                else:
                    st.error("Sai tài khoản hoặc mật khẩu!")

    # --- GIAO DIỆN ADMIN (Giữ nguyên) ---
    elif st.session_state['role'] == 'admin':
        st.sidebar.markdown(f"👤 Admin: **{st.session_state['hoten']}**")
        if st.sidebar.button("Đăng xuất"):
            st.session_state['role'] = None
            st.rerun()
        
        st.header("⚙️ Thêm Câu Hỏi")
        with st.form("them_cau_hoi"):
            q = st.text_input("Câu hỏi")
            col1, col2, col3 = st.columns(3)
            with col1: a = st.text_input("Đáp án A")
            with col2: b = st.text_input("Đáp án B")
            with col3: c = st.text_input("Đáp án C")
            correct = st.selectbox("Đáp án đúng", ["A", "B", "C"])
            if st.form_submit_button("Lưu câu hỏi"):
                ws = db.worksheet("Questions")
                ws.append_row([q, a, b, c, correct])
                st.success("Đã lưu!")

    # --- GIAO DIỆN HỌC VIÊN (Cải tiến) ---
    elif st.session_state['role'] == 'student':
        # Tải câu hỏi nếu chưa có
        if not st.session_state['questions']:
            st.session_state['questions'] = get_questions(db)
        
        questions = st.session_state['questions']
        current_idx = st.session_state['current_index']

        # Sidebar thông tin
        st.sidebar.markdown(f"👋 Thí sinh: **{st.session_state['hoten']}**")
        if st.sidebar.button("Thoát"):
            st.session_state['role'] = None
            st.rerun()

        # KIỂM TRA: Nếu đã hết câu hỏi -> Hiện kết quả
        if current_idx >= len(questions):
            st.balloons()
            st.title("🏆 Kết Thúc Bài Thi!")
            st.success(f"Điểm số của bạn: {st.session_state['score']} / {len(questions)}")
            
            if st.button("Lưu điểm và Thoát"):
                luu_diem(db, st.session_state['user'], st.session_state['score'], st.session_state['hoten'])
                st.session_state['role'] = None
                st.session_state['questions'] = [] # Reset câu hỏi
                st.rerun()
            return

        # LOGIC ĐẾM NGƯỢC
        # Nếu chưa đặt giờ cho câu hiện tại thì đặt giờ
        if st.session_state['end_time_question'] is None:
            st.session_state['end_time_question'] = time.time() + THOI_GIAN_MOI_CAU

        # Tính thời gian còn lại
        time_left = st.session_state['end_time_question'] - time.time()

        # XỬ LÝ KHI HẾT GIỜ
        if time_left <= 0:
            st.warning("⏳ Đã hết thời gian cho câu này!")
            time.sleep(1) # Dừng 1 xíu để học viên kịp nhìn thông báo
            st.session_state['current_index'] += 1 # Chuyển câu tiếp
            st.session_state['end_time_question'] = None # Reset giờ
            st.rerun()

        # HIỂN THỊ CÂU HỎI
        q_data = questions[current_idx]
        st.markdown(f"### Câu {current_idx + 1}: {q_data['CauHoi']}")
        
        # Thanh đếm ngược (Progress bar)
        progress_val = max(0.0, min(1.0, time_left / THOI_GIAN_MOI_CAU))
        st.progress(progress_val)
        st.caption(f"⏱️ Còn lại: {int(time_left)} giây")

        # Form trả lời
        with st.form(key=f"form_{current_idx}"):
            options = [f"A. {q_data['DapAn_A']}", f"B. {q_data['DapAn_B']}", f"C. {q_data['DapAn_C']}"]
            # Lưu ý: Radio cần key unique để không bị lỗi duplicate
            choice = st.radio("Chọn đáp án:", options, index=None)
            
            submit_btn = st.form_submit_button("Chốt đáp án")

            if submit_btn:
                if choice:
                    # Kiểm tra đáp án
                    user_ans = choice.split(".")[0] # Lấy A, B hoặc C
                    if user_ans == str(q_data['DapAn_Dung']):
                        st.session_state['score'] += 1
                        st.success("✅ Chính xác!")
                    else:
                        st.error(f"❌ Sai rồi! Đáp án đúng là {q_data['DapAn_Dung']}")
                    
                    time.sleep(0.5) # Dừng xíu để xem kết quả
                    st.session_state['current_index'] += 1
                    st.session_state['end_time_question'] = None
                    st.rerun()
                else:
                    st.warning("Vui lòng chọn một đáp án!")

        # Tự động refresh trang mỗi giây để cập nhật đồng hồ
        time.sleep(1)
        st.rerun()

if __name__ == "__main__":
    main()