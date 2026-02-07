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
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("HeThongTracNghiem") 
    return sheet

# --- HÀM ĐĂNG NHẬP (CÓ KIỂM TRA ĐÃ THI CHƯA) ---
def login(sheet, user, pwd):
    try:
        users_ws = sheet.worksheet("Users")
        records = users_ws.get_all_records()
        for record in records:
            # So sánh Username và Password
            if str(record['Username']).strip() == str(user).strip() and str(record['Password']).strip() == str(pwd).strip():
                
                # [MỚI] Kiểm tra cột TrangThai
                trang_thai = str(record.get('TrangThai', '')).strip()
                if trang_thai == 'DaThi':
                    return "LOCKED", None # Trả về cờ báo đã bị khóa
                
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

# --- [MỚI] HÀM KHÓA TÀI KHOẢN ---
def khoa_tai_khoan(sheet, user):
    try:
        ws = sheet.worksheet("Users")
        # Tìm ô chứa username để biết nó nằm dòng nào
        cell = ws.find(user)
        # Cập nhật cột E (Cột thứ 5 - TrangThai) thành "DaThi"
        ws.update_cell(cell.row, 5, "DaThi")
    except Exception as e:
        print(f"Lỗi khóa tài khoản: {e}")

# --- HÀM LẤY CÂU HỎI ---
def get_questions(sheet):
    ws = sheet.worksheet("Questions")
    return ws.get_all_records()

# --- GIAO DIỆN CHÍNH ---
def main():
    st.set_page_config(page_title="Thi Trắc Nghiệm", page_icon="📝")
    st.markdown("""
        <style>
        .stAlert { padding: 1rem; border-radius: 0.5rem; margin-top: 1rem;}
        .stButton button { width: 100%; margin-top: 10px; font-weight: bold;}
        </style>
    """, unsafe_allow_html=True)

    try:
        db = connect_db()
    except Exception as e:
        st.error(f"❌ KHÔNG KẾT NỐI ĐƯỢC GOOGLE SHEET!\nLỗi: {e}")
        st.stop()

    if 'role' not in st.session_state: st.session_state['role'] = None
    if 'current_index' not in st.session_state: st.session_state['current_index'] = 0
    if 'score' not in st.session_state: st.session_state['score'] = 0
    if 'questions' not in st.session_state: st.session_state['questions'] = []
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
                
                # [MỚI] Xử lý trường hợp đã thi rồi
                if role == "LOCKED":
                    st.error("⛔ TÀI KHOẢN NÀY ĐÃ THI XONG!\nBạn chỉ được phép làm bài 1 lần duy nhất.")
                
                elif role:
                    st.session_state['role'] = role
                    st.session_state['user'] = username
                    st.session_state['hoten'] = hoten
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
            explain = st.text_area("Lời giải thích")
            
            if st.form_submit_button("Lưu câu hỏi"):
                try:
                    ws = db.worksheet("Questions")
                    ws.append_row([q, a, b, c, d, correct, explain])
                    st.success("✅ Đã lưu thành công!")
                except Exception as e:
                    st.error(f"Lỗi: {e}")

    # ==========================================
    # 3. GIAO DIỆN HỌC VIÊN
    # ==========================================
    elif st.session_state['role'] == 'student':
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
        
        # --- [QUAN TRỌNG] KẾT THÚC BÀI THI ---
        if idx >= len(questions):
            # 1. Lưu điểm
            luu_diem(db, st.session_state['user'], st.session_state['score'], st.session_state['hoten'])
            
            # 2. [MỚI] KHÓA TÀI KHOẢN NGAY LẬP TỨC
            khoa_tai_khoan(db, st.session_state['user'])
            
            st.balloons()
            st.success(f"🎉 HOÀN THÀNH! Điểm số: {st.session_state['score']}/{len(questions)}")
            st.warning("⚠️ Tài khoản của bạn đã được khóa để tránh thi lại.")
            
            time.sleep(4)
            st.session_state['role'] = None
            st.rerun()
            return

        q_data = questions[idx]
        
        giai_thich = ""
        possible_headers = ["GiaiThich", "Giải Thích", "Explain"]
        for header in possible_headers:
            if header in q_data:
                giai_thich = str(q_data[header])
                break
        if not giai_thich: giai_thich = "Không có giải thích chi tiết."

        st.subheader(f"Câu hỏi {idx + 1}:")
        st.info(f"{q_data['CauHoi']}")

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
        else:
            user_ans = st.session_state['user_choice']
            correct_ans = str(q_data['DapAn_Dung']).strip().upper()
            is_correct = (user_ans == correct_ans)

            if is_correct:
                st.success(f"✅ CHÍNH XÁC!\n\n💡 {giai_thich}")
            elif user_ans is None:
                st.error(f"⌛ HẾT GIỜ!\n\n👉 Đáp án đúng: {correct_ans}\n\n💡 {giai_thich}")
            else:
                st.error(f"❌ SAI RỒI (Bạn chọn {user_ans})\n\n👉 Đáp án đúng: {correct_ans}\n\n💡 {giai_thich}")

            if st.button("Câu tiếp theo ➡️"):
                if is_correct: st.session_state['score'] += 1
                st.session_state['current_index'] += 1
                st.session_state['submitted_answer'] = False
                st.session_state['user_choice'] = None
                st.session_state['end_time_question'] = None
                st.rerun()

if __name__ == "__main__":
    main()