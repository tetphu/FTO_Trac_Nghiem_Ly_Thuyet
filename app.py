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
    sheet = client.open("HeThongTracNghiem") 
    return sheet

# --- HÀM ĐĂNG NHẬP ---
def login(sheet, user, pwd):
    try:
        users_ws = sheet.worksheet("Users")
        records = users_ws.get_all_records()
        for record in records:
            if str(record['Username']).strip() == str(user).strip() and str(record['Password']).strip() == str(pwd).strip():
                return record['Role'], record['HoTen']
    except Exception as e:
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
    
    # CSS tùy chỉnh
    st.markdown("""
        <style>
        .stAlert { padding: 1rem; border-radius: 0.5rem; margin-top: 1rem;}
        .stButton button { width: 100%; margin-top: 10px; font-weight: bold;}
        </style>
    """, unsafe_allow_html=True)

    # Kết nối Database
    try:
        db = connect_db()
    except Exception as e:
        st.error(f"❌ KHÔNG KẾT NỐI ĐƯỢC GOOGLE SHEET!\nLỗi: {e}")
        st.stop()

    # --- KHỞI TẠO SESSION STATE ---
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
                    # Reset dữ liệu cũ
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
        # Tải câu hỏi
        if not st.session_state['questions']:
            try:
                st.session_state['questions'] = get_questions(db)
            except Exception as e:
                st.error(f"Lỗi tải câu hỏi: {e}")
                st.stop()
        
        questions = st.session_state['questions']
        idx = st.session_state['current_index']

        st.sidebar.markdown(f"👋 Xin chào: **{st.session_state['hoten']}**")
        st.sidebar.metric("Điểm số", st.session_state['score'])
        
        # --- [TÍNH NĂNG MỚI] TỰ ĐỘNG LƯU VÀ THOÁT ---
        if idx >= len(questions):
            # 1. Lưu điểm ngay lập tức
            luu_diem(db, st.session_state['user'], st.session_state['score'], st.session_state['hoten'])
            
            # 2. Hiệu ứng chúc mừng
            st.balloons()
            st.success(f"🎉 BẠN ĐÃ HOÀN THÀNH BÀI THI!")
            st.info(f"💾 Kết quả: {st.session_state['score']}/{len(questions)} đã được lưu. Đang tự động đăng xuất...")
            
            # 3. Đợi 3 giây để học viên kịp nhìn điểm
            time.sleep(3)
            
            # 4. Đăng xuất và Quay về màn hình chính
            st.session_state['role'] = None
            st.rerun()
            return

        # --- HIỂN THỊ CÂU HỎI ---
        q_data = questions[idx]
        
        # Tìm cột giải thích
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
        # TRẠNG THÁI A: ĐANG LÀM BÀI
        # ----------------------------------------------
        if not st.session_state['submitted_answer']:
            if st.session_state['end_time_question'] is None:
                st.session_state['end_time_question'] = time.time() + THOI_GIAN_MOI_CAU
            
            time_left = st.session_state['end_time_question'] - time.time()
            
            if time_left <= 0:
                st.session_state['submitted_answer'] = True
                st.session_state['user_choice'] = None 
                st.rerun()

            st.progress(max(0.0, min(1.0, time_left / THOI_GIAN_MOI_CAU)))
            st.caption(f"⏱️ Thời gian còn lại: {int(time_left)} giây")

            with st.form(key=f"form_{idx}"):
                options = [f"A. {q_data['DapAn_A']}", f"B. {q_data['DapAn_B']}", f"C. {q_data['DapAn_C']}"]
                if 'DapAn_D' in q_data and str(q_data['DapAn_D']).strip():
                    options.append(f"D. {q_data['DapAn_D']}")

                choice = st.radio("Chọn đáp án:", options, index=None)
                
                if st.form_submit_button("Chốt đáp án"):
                    if choice:
                        st.session_state['user_choice'] = choice.split(".")[0]
                        st.session_state['submitted_answer'] = True
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng chọn đáp án!")

            time.sleep(1)
            st.rerun()

        # ----------------------------------------------
        # TRẠNG THÁI B: XEM KẾT QUẢ
        # ----------------------------------------------
        else:
            user_ans = st.session_state['user_choice']
            correct_ans = str(q_data['DapAn_Dung']).strip().upper()

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
                
                st.session_state['current_index'] += 1
                st.session_state['submitted_answer'] = False
                st.session_state['user_choice'] = None
                st.session_state['end_time_question'] = None
                st.rerun()

if __name__ == "__main__":
    main()