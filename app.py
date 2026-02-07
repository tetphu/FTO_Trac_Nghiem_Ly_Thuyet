import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# --- CẤU HÌNH ---
THOI_GIAN_MOI_CAU = 30  # Thời gian đếm ngược (giây)

# --- KẾT NỐI GOOGLE SHEET ---
def connect_db():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
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
    try:
        users_ws = sheet.worksheet("Users")
        records = users_ws.get_all_records()
        for record in records:
            if str(record['Username']) == user and str(record['Password']) == pwd:
                return record['Role'], record['HoTen']
    except:
        return None, None
    return None, None

def luu_diem(sheet, user, diem, hoten):
    try:
        scores_ws = sheet.worksheet("Scores")
        scores_ws.append_row([user, hoten, diem, str(datetime.now())])
    except:
        pass

def get_questions(sheet):
    ws = sheet.worksheet("Questions")
    return ws.get_all_records()

# --- GIAO DIỆN CHÍNH ---
def main():
    st.set_page_config(page_title="Thi Trắc Nghiệm", page_icon="📝")
    st.markdown("""<style>.stAlert { padding: 1rem; border-radius: 0.5rem; }</style>""", unsafe_allow_html=True)

    try:
        db = connect_db()
    except:
        st.error("Lỗi kết nối Database. Vui lòng kiểm tra lại file credentials và tên Sheet.")
        st.stop()

    # Khởi tạo Session State
    if 'role' not in st.session_state: st.session_state['role'] = None
    if 'current_index' not in st.session_state: st.session_state['current_index'] = 0
    if 'score' not in st.session_state: st.session_state['score'] = 0
    if 'questions' not in st.session_state: st.session_state['questions'] = []
    if 'submitted_answer' not in st.session_state: st.session_state['submitted_answer'] = False
    if 'user_choice' not in st.session_state: st.session_state['user_choice'] = None
    if 'end_time_question' not in st.session_state: st.session_state['end_time_question'] = None

    # --- MÀN HÌNH ĐĂNG NHẬP ---
    if st.session_state['role'] is None:
        st.title("🎓 Đăng Nhập")
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password")
            if st.form_submit_button("Vào thi"):
                role, hoten = login(db, username, password)
                if role:
                    st.session_state['role'] = role
                    st.session_state['user'] = username
                    st.session_state['hoten'] = hoten
                    st.session_state['current_index'] = 0
                    st.session_state['score'] = 0
                    st.session_state['questions'] = [] # Reset lại câu hỏi mới nhất
                    st.session_state['submitted_answer'] = False
                    st.rerun()
                else:
                    st.error("Sai tài khoản hoặc mật khẩu!")

    # --- GIAO DIỆN ADMIN (Cập nhật thêm đáp án D) ---
    elif st.session_state['role'] == 'admin':
        st.sidebar.markdown(f"👤 Admin: **{st.session_state['hoten']}**")
        if st.sidebar.button("Đăng xuất"):
            st.session_state['role'] = None
            st.rerun()
        
        st.header("⚙️ Thêm Câu Hỏi (4 Đáp Án)")
        with st.form("them_cau_hoi"):
            q = st.text_input("Câu hỏi")
            col1, col2 = st.columns(2)
            with col1:
                a = st.text_input("Đáp án A")
                b = st.text_input("Đáp án B")
            with col2:
                c = st.text_input("Đáp án C")
                d = st.text_input("Đáp án D") # Thêm ô nhập D
            
            # Chọn đáp án đúng A, B, C, D
            correct = st.selectbox("Đáp án đúng", ["A", "B", "C", "D"])
            explain = st.text_area("Lời giải thích")
            
            if st.form_submit_button("Lưu câu hỏi"):
                ws = db.worksheet("Questions")
                # Lưu theo thứ tự cột mới: Q, A, B, C, D, Correct, Explain
                ws.append_row([q, a, b, c, d, correct, explain])
                st.success("Đã lưu câu hỏi thành công!")

    # --- GIAO DIỆN HỌC VIÊN ---
    elif st.session_state['role'] == 'student':
        if not st.session_state['questions']:
            st.session_state['questions'] = get_questions(db)
        
        questions = st.session_state['questions']
        idx = st.session_state['current_index']

        st.sidebar.markdown(f"Thí sinh: **{st.session_state['hoten']}**")
        st.sidebar.markdown(f"Điểm số: **{st.session_state['score']}**")
        
        if idx >= len(questions):
            st.balloons()
            st.success(f"🎉 Hoàn thành bài thi! Điểm: {st.session_state['score']} / {len(questions)}")
            if st.button("Lưu kết quả và Thoát"):
                luu_diem(db, st.session_state['user'], st.session_state['score'], st.session_state['hoten'])
                st.session_state['role'] = None
                st.rerun()
            return

        q_data = questions[idx]
        giai_thich = q_data.get('GiaiThich', 'Không có giải thích chi tiết.')

        st.markdown(f"### Câu {idx + 1}: {q_data['CauHoi']}")

        # --- ĐANG LÀM BÀI ---
        if not st.session_state['submitted_answer']:
            if st.session_state['end_time_question'] is None:
                st.session_state['end_time_question'] = time.time() + THOI_GIAN_MOI_CAU
            
            time_left = st.session_state['end_time_question'] - time.time()
            
            if time_left <= 0:
                st.session_state['submitted_answer'] = True
                st.session_state['user_choice'] = None
                st.rerun()

            st.progress(max(0.0, min(1.0, time_left / THOI_GIAN_MOI_CAU)))
            st.caption(f"⏱️ Còn lại: {int(time_left)} giây")

            with st.form(key=f"q_{idx}"):
                # Cập nhật thêm lựa chọn D vào đây
                options = [
                    f"A. {q_data['DapAn_A']}", 
                    f"B. {q_data['DapAn_B']}", 
                    f"C. {q_data['DapAn_C']}",
                    f"D. {q_data.get('DapAn_D', '')}" # Lấy cột D, nếu không có thì để trống
                ]
                choice = st.radio("Chọn đáp án:", options, index=None)
                if st.form_submit_button("Chốt Đáp Án"):
                    if choice:
                        st.session_state['user_choice'] = choice.split(".")[0]
                        st.session_state['submitted_answer'] = True
                        st.rerun()
                    else:
                        st.warning("Bạn chưa chọn đáp án!")
            time.sleep(1)
            st.rerun()

        # --- XEM KẾT QUẢ ---
        else:
            user_ans = st.session_state['user_choice']
            correct_ans = str(q_data['DapAn_Dung']).strip()

            if user_ans == correct_ans:
                st.success(f"✅ **Chính xác!**\n\n{giai_thich}")
                is_correct = True
            elif user_ans is None:
                st.error(f"⌛ **Hết giờ!**\n\n👉 Đáp án đúng: **{correct_ans}**.\n\n{giai_thich}")
                is_correct = False
            else:
                st.error(f"❌ **Sai rồi!** Bạn chọn {user_ans}.\n\n👉 Đáp án đúng: **{correct_ans}**.\n\n{giai_thich}")
                is_correct = False

            if st.button("Câu tiếp theo ➡️"):
                if is_correct: st.session_state['score'] += 1
                st.session_state['current_index'] += 1
                st.session_state['submitted_answer'] = False
                st.session_state['end_time_question'] = None
                st.session_state['user_choice'] = None
                st.rerun()

if __name__ == "__main__":
    main()