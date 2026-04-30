import streamlit as st
import json
import random
from gtts import gTTS
import io
import os
import pandas as pd
from datetime import datetime

# --- CONFIG & CSS ---
st.set_page_config(page_title="UTH English Pro v5.1", layout="wide")
st.markdown("<style>button { cursor: pointer !important; }</style>", unsafe_allow_html=True)

# --- 1. QUẢN LÝ DỮ LIỆU (TÁCH 4 FILE) ---
@st.cache_data
def load_all_data():
    files = {
        "vocab": "vocab.json",
        "quiz": "quiz.json",
        "read": "reading.json",
        "write": "writing.json"
    }
    data_bundle = {}
    for key, filename in files.items():
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data_bundle[key] = json.load(f)
        except:
            data_bundle[key] = {} # Trả về trống nếu file lỗi/không tồn tại
    return data_bundle

def log_action(user, task, result, mode):
    log_file = "learning_logs.csv"
    df = pd.DataFrame([{"time": datetime.now(), "user": user, "task": task, "is_correct": result, "mode": mode}])
    df.to_csv(log_file, mode='a', header=not os.path.exists(log_file), index=False, encoding="utf-8-sig")

# --- 2. KHỞI TẠO SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = True
    st.session_state.username = "Kiệt_Admin"

# Các biến quan trọng để giữ trạng thái câu hỏi
initial_states = {
    'current_task': None,       # Lưu đối tượng câu hỏi hiện tại
    'fixed_options': [],        # Giữ nguyên 4 đáp án cho tới khi xong câu
    'fixed_sentence': "",       # Giữ câu đục lỗ cố định
    'prev_type_mode': None,     # Theo dõi để đổi từ khi đổi Anh-Việt
    'prev_mode': None,          # Theo dõi để đổi từ khi đổi Chế độ
    'prev_level': None          # Theo dõi để đổi từ khi đổi Trình độ
}
for key, val in initial_states.items():
    if key not in st.session_state: st.session_state[key] = val

# --- 3. SIDEBAR ---
bundle = load_all_data()
with st.sidebar:
    st.title("🎓 UTH Pro v5.1")
    mode = st.radio("Chế độ:", ["Từ vựng", "Trắc nghiệm", "Reading", "Writing", "Thống kê"])
    
    # Lấy danh sách Level từ file vocab (làm chuẩn)
    levels = list(bundle['vocab'].keys()) if bundle['vocab'] else ["Level_A1"]
    level = st.selectbox("Trình độ:", levels)
    
    # RESET KHI ĐỔI MODE HOẶC LEVEL
    if st.session_state.prev_mode != mode or st.session_state.prev_level != level:
        st.session_state.current_task = None
        st.session_state.prev_mode = mode
        st.session_state.prev_level = level
        st.rerun()

# --- 4. LOGIC CHẾ ĐỘ ---

# 4.1 TỪ VỰNG: Fix lỗi "Đổi kiểu học không đổi từ"
if mode == "Từ vựng":
    type_mode = st.selectbox("Kiểu học:", ["Anh -> Việt", "Việt -> Anh"])
    if st.session_state.prev_type_mode != type_mode:
        st.session_state.current_task = None # Buộc đổi từ khi đổi kiểu học
        st.session_state.prev_type_mode = type_mode
        st.rerun()

    vocab_list = bundle['vocab'].get(level, {}).get("vocabulary", [])
    if vocab_list:
        if st.session_state.current_task is None:
            st.session_state.current_task = random.choice(vocab_list)
        
        w = st.session_state.current_task
        st.subheader(f"Luyện tập từ vựng: {level}")
        st.write(f"IPA: `{w.get('ipa', 'N/A')}`")
        
        if type_mode == "Anh -> Việt":
            st.info(f"Dịch từ: **{w['en']}**")
            ans = st.text_input("Nhập nghĩa tiếng Việt:", key=f"v_{w['en']}")
            correct = w['vn']
        else:
            st.info(f"Nghĩa là: **{w['vn']}**")
            ans = st.text_input("Nhập từ tiếng Anh:", key=f"v_{w['vn']}")
            correct = w['en']

        if st.button("Kiểm tra"):
            if ans.strip().lower() == correct.strip().lower():
                st.success("Tày vậy!"); log_action(st.session_state.username, w['en'], 1, "Vocab")
                st.session_state.current_task = None; st.rerun()
            else: st.error(f"Chưa Tày đâu. Đáp án: {correct}")

# 4.2 TRẮC NGHIỆM: Fix lỗi "Nhảy đáp án" & Đục lỗ theo 3 dạng
elif mode == "Trắc nghiệm":
    st.subheader("Trắc nghiệm ngữ cảnh (Cloze Test)")
    quiz_list = bundle['quiz'].get(level, [])
    
    if quiz_list:
        if st.session_state.current_task is None:
            q = random.choice(quiz_list)
            st.session_state.current_task = q
            st.session_state.fixed_sentence = q['sentence']
            # Trộn đáp án 1 lần duy nhất và lưu vào session
            opts = q['options']
            random.shuffle(opts)
            st.session_state.fixed_options = opts
        
        q = st.session_state.current_task
        st.info(f"Điền vào chỗ trống: \n\n **{st.session_state.fixed_sentence}**")
        
        # Đáp án luôn cố định nhờ session_state
        user_choice = st.radio("Chọn từ đúng:", st.session_state.fixed_options, key="q_radio")
        
        if st.button("Xác nhận"):
            if user_choice == q['answer']:
                st.success("Chuẩn Cơm Mẹ Nấu!"); log_action(st.session_state.username, q['answer'], 1, "Quiz")
                st.session_state.current_task = None; st.rerun()
            else: st.error("Thử lại nhó!")

# 4.3 READING: Cấu trúc bài đọc chuyên nghiệp
elif mode == "Reading":
    st.subheader("Đọc hiểu văn bản")
    read_list = bundle['read'].get(level, [])
    if read_list:
        if st.session_state.current_task is None:
            st.session_state.current_task = random.choice(read_list)
        
        r = st.session_state.current_task
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Nguồn:** {r.get('source', 'UTH Exam')}")
            st.text_area("Văn bản:", r['passage'], height=350)
        with col2:
            st.write("Câu hỏi:")
            for i, quest in enumerate(r['questions']):
                st.radio(f"{i+1}. {quest['q']}", quest['options'], key=f"r_q_{i}")
        if st.button("Nộp bài đọc"):
            st.session_state.current_task = None; st.rerun()

# 4.4 WRITING: Sắp xếp câu/Dịch thuật
elif mode == "Writing":
    st.subheader("Luyện kỹ năng viết")
    write_list = bundle['write'].get(level, [])
    if write_list:
        if st.session_state.current_task is None:
            st.session_state.current_task = random.choice(write_list)
        
        task = st.session_state.current_task
        st.write(f"Đề bài: **{task['prompt']}**")
        if 'scrambled' in task: st.warning(f"Từ gợi ý: {task['scrambled']}")
        
        user_write = st.text_input("Viết câu hoàn chỉnh tại đây:", key="w_input")
        if st.button("Kiểm tra câu viết"):
            if user_write.strip().lower() == task['answer'].strip().lower():
                st.success("Viết rất tốt!"); st.session_state.current_task = None
            else: st.info(f"Gợi ý đáp án: {task['answer']}")

# 4.5 THỐNG KÊ
elif mode == "Thống kê":
    st.subheader("Kết quả học tập")
    if os.path.exists("learning_logs.csv"):
        df = pd.read_csv("learning_logs.csv")
        st.line_chart(df['is_correct'].tail(20))
        st.dataframe(df.tail(10), use_container_width=True)
