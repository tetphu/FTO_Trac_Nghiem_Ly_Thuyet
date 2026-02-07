import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# --- CẤU HÌNH ---
THOI_GIAN_MOI_CAU = 30  # Số giây cho mỗi câu

# --- HÀM KẾT NỐI DATABASE ---
def connect_db():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Ưu tiên lấy từ Secrets (trên Cloud)
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    # Nếu không có thì lấy file local (trên máy tính)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        
    client = gspread.authorize(creds)
    sheet = client.open("HeThongTracNghiem") # Đảm bảo tên Sheet đúng 100%
    return sheet

# --- HÀM ĐĂNG NHẬP ---
def login(sheet, user, pwd):
    try:
        users_ws = sheet.worksheet("Users")
        records = users_ws.get_all_records()
        for record in records:
            # Chuyển về chuỗi để so sánh chính xác
            if str(record['Username']).strip() == str(user).strip() and str(record['Password']).strip() == str(pwd).strip():
                return record['Role'], record['HoTen']
    except Exception as e:
        st.error(f"Lỗi đăng nhập: {e}")
        return None, None
    return None, None

# --- HÀM LƯU ĐIỂM ---
def luu_diem(sheet, user, diem, hoten):
    try:
        scores_ws = sheet.worksheet("Scores")
        scores_ws.append_row([user, hoten, diem, str(datetime.now())])
    except Exception as e:
        st.error(f"Lỗi lưu điểm: {e}")

# --- HÀM LẤY CÂU HỎI ---
def get_questions(sheet):
    ws = sheet.worksheet("Questions")
    return ws.get_all_records()

# --- GIAO DIỆN CHÍNH ---
def main():
    st.set_page_config(page_title="Thi Trắc Nghiệm", page_icon="📝")
    
    # CSS tùy chỉnh để làm đẹp
    st.markdown("""
        <style>
        .stAlert { padding: 1rem; border-radius: 0.5rem; margin-top: 1rem;}
        .stButton button { width: 100%; margin-top: 10px; font-weight: bold;}
        </style>
    """, unsafe_allow_html=True)

    # Kết nối Database (Có bắt lỗi để không bị trắng màn hình)
    try:
        db = connect_db()
    except Exception as e:
        st.error(f"❌ KHÔNG KẾT NỐI ĐƯỢC GOOGLE SHEET!\nLỗi chi tiết: {e}")
        st.info("💡 Gợi ý: Kiểm tra lại file credentials.json hoặc tên file Google Sheet đã chia sẻ quyền chưa.")
        st.stop()

    # --- KHỞI TẠO SESSION STATE (Lưu trạng thái) ---
    if 'role' not in st.session_state: st.session_state['role'] = None
    if 'current_index' not in st.session_state: st.session_state['current_index'] = 0
    if 'score' not in st.session_state: st.session_state['score'] = 0
    if 'questions' not in st.session_state: st.session_state['questions'] = []
    
    # Biến trạng thái câu hỏi
    if 'submitted_answer' not in st.session_state: st.session_state['submitted_answer'] = False
    if 'user_choice' not in st.session_state: st.session_state['user_choice'] = None
    if 'end_time_question' not in st.session_state: st.session_state['end_time_question'] = None

    # ==========================================
    # 1. MÀN HÌNH ĐĂNG NHẬP
    # ==========================================
    if st.session_state['role'] is None:
        st.title("🎓 Đăng Nhập Hệ Thống")
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password")
            submit = st.form_submit_button("Đăng Nhập")
            
            if submit:
                role, hoten = login(db, username, password)
                if role:
                    st.session_state['role'] = role
                    st.session_state['user'] = username
                    st.session_state['hoten'] = hoten
                    # Reset toàn bộ dữ liệu cũ
                    st.session_state['current_index'] = 0
                    st.session_state['score'] = 0
                    st.session_state['questions'] = []
                    st.session_state['submitted_answer'] = False
                    st.session_state['end_time_question'] = None
                    st.rerun()
                else:
                    st.error("❌ Sai tên đăng nhập hoặc mật khẩu!")

    # ==========================================
    # 2. GIAO DIỆN ADMIN
    # ==========================================
    elif st.session_state['role'] == 'admin':
        st.sidebar.markdown(f"👤 Admin: **{st.session_state['hoten']}**")
        if st.sidebar.button("Đăng xuất"):
            st.session_state['role'] = None
            st.rerun()
        
        st.header("⚙️ Thêm Câu Hỏi Mới")
        with st.form("them_cau_hoi"):
            q = st.text_input("Câu hỏi")
            col1, col2 = st.columns(2)
            with col1:
                a = st.text_input("Đáp án A")
                b = st.text_input("Đáp án B")
            with col2:
                c = st.text_input("Đáp án C")
                d = st.text_input("Đáp án D")
            
            correct = st.selectbox("Đáp án ĐÚNG", ["A", "B", "C", "D"])
            explain = st.text_area("Lời giải thích (Hiện sau khi trả lời)")
            
            if st.form_submit_button("Lưu câu hỏi"):
                try:
                    ws = db.worksheet("Questions")
                    ws.append_row([q, a, b, c, d, correct, explain])
                    st.success("✅ Đã thêm câu hỏi thành công!")
                except Exception as e:
                    st.error(f"Lỗi khi lưu: {e}")

    # ==========================================
    # 3. GIAO DIỆN HỌC VIÊN
    # ==========================================
    elif st.session_state['role'] == 'student':
        # Tải câu hỏi lần đầu
        if not st.session_state['questions']:
            try:
                st.session_state['questions'] = get_questions(db)
            except Exception as e:
                st.error(f"Lỗi tải câu hỏi: {e}")
                st.stop()
        
        questions = st.session_state['questions']
        idx = st.session_state['current_index']

        # Sidebar
        st.sidebar.markdown(f"👋 Xin chào: **{st.session_state['hoten']}**")
        st.sidebar.metric("Điểm số", st.session_state['score'])
        
        # --- KIỂM TRA HẾT CÂU HỎI ---
        if idx >= len(questions):
            st.balloons()
            st.success("🎉 BẠN ĐÃ HOÀN THÀNH BÀI THI!")
            st.markdown(f"### Tổng điểm: {st.session_state['score']} / {len(questions)}")
            
            if st.button("Lưu kết quả & Thoát"):
                luu_diem(db, st.session_state['user'], st.session_state['score'], st.session_state['hoten'])
                st.session_state['role'] = None
                st.rerun()
            return

        # --- HIỂN THỊ CÂU HỎI ---
        q_data = questions[idx]
        
        # Tìm nội dung giải thích (Code thông minh: tự dò tên cột)
        giai_thich = ""
        possible_headers = ["GiaiThich", "Giải Thích", "Explain", "Giai thich"]
        for header in possible_headers:
            if header in q_data:
                giai_thich = str(q_data[header])
                break
        if not giai_thich: giai_thich = "Không có giải thích chi tiết."

        st.subheader(f"Câu hỏi {idx + 1}:")
        st.info(f"{q_data['CauHoi']}")

        # ----------------------------------------------
        # TRẠNG THÁI A: ĐANG LÀM BÀI (Chưa nộp)
        # ----------------------------------------------
        if not st.session_state['submitted_answer']:
            # 1. Logic Đếm ngược
            if st.session_state['end_time_question'] is None:
                st.session_state['end_time_question'] = time.time() + THOI_GIAN_MOI_CAU
            
            time_left = st.session_state['end_time_question'] - time.time()
            
            # Hết giờ -> Tự động nộp bài
            if time_left <= 0:
                st.session_state['submitted_answer'] = True
                st.session_state['user_choice'] = None 
                st.rerun()

            # Thanh thời gian
            st.progress(max(0.0, min(1.0, time_left / THOI_GIAN_MOI_CAU)))
            st.caption(f"⏱️ Thời gian còn lại: {int(time_left)} giây")

            # 2. Form Trả lời
            with st.form(key=f"form_{idx}"):
                # Tạo list đáp án (xử lý trường hợp D bị trống)
                options = [
                    f"A. {q_data['DapAn_A']}", 
                    f"B. {q_data['DapAn_B']}", 
                    f"C. {q_data['DapAn_C']}"
                ]
                # Nếu có đáp án D thì thêm vào
                if 'DapAn_D' in q_data and str(q_data['DapAn_D']).strip():
                    options.append(f"D. {q_data['DapAn_D']}")

                choice = st.radio("Chọn đáp án của bạn:", options, index=None)
                
                if st.form_submit_button("Chốt đáp án"):
                    if choice:
                        st.session_state['user_choice'] = choice.split(".")[0] # Lấy A,B,C,D
                        st.session_state['submitted_answer'] = True
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng chọn đáp án trước khi nộp!")

            time.sleep(1) # Refresh đồng hồ
            st.rerun()

        # ----------------------------------------------
        # TRẠNG THÁI B: XEM KẾT QUẢ & GIẢI THÍCH
        # ----------------------------------------------
        else:
            user_ans = st.session_state['user_choice']
            correct_ans = str(q_data['DapAn_Dung']).strip().upper()

            # Hiển thị kết quả
            is_correct = False
            if user_ans == correct_ans:
                st.success(f"✅ **CHÍNH XÁC!**\n\n💡 **Giải thích:** {giai_thich}")
                is_correct = True
            elif user_ans is None:
                st.error(f"⌛ **HẾT GIỜ!**\n\n👉 Đáp án đúng là: **{correct_ans}**\n\n💡 **Giải thích:** {giai_thich}")
            else:
                st.error(f"❌ **SAI RỒI!** Bạn chọn {user_ans}.\n\n👉 Đáp án đúng là: **{correct_ans}**\n\n💡 **Giải thích:** {giai_thich}")

            # Nút chuyển câu
            if st.button("Câu tiếp theo ➡️"):
                if is_correct:
                    st.session_state['score'] += 1
                
                # Reset sang câu mới
                st.session_state['current_index'] += 1
                st.session_state['submitted_answer'] = False
                st.session_state['user_choice'] = None
                st.session_state['end_time_question'] = None
                st.rerun()

# --- QUAN TRỌNG: DÒNG LỆNH CHẠY ỨNG DỤNG ---
if __name__ == "__main__":
    main()