import streamlit as st
import json
import random
import os
import pandas as pd
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="UTH English Pro v5.3", layout="wide")

# --- 1. QUẢN LÝ DỮ LIỆU ---
@st.cache_data
def load_all_data():
    files = {"vocab": "vocab.json", "quiz": "quiz.json", "read": "reading.json", "write": "writing.json"}
    bundle = {}
    for k, v in files.items():
        if os.path.exists(v):
            with open(v, "r", encoding="utf-8") as f: bundle[k] = json.load(f)
        else: bundle[k] = {}
    return bundle

# --- 2. QUẢN LÝ TRẠNG THÁI (SESSION STATE) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = True
if 'username' not in st.session_state: st.session_state.username = "Kiệt_Admin"

# Khởi tạo các biến điều khiển
states = ['current_task', 'options', 'prev_mode', 'prev_level', 'prev_type', 'score_feedback']
for s in states:
    if s not in st.session_state: st.session_state[s] = None

def reset_task():
    st.session_state.current_task = None
    st.session_state.options = None
    st.session_state.score_feedback = None

# --- 3. SIDEBAR ---
bundle = load_all_data()
with st.sidebar:
    st.title("🎓 UTH Pro v5.3")
    mode = st.radio("Chế độ:", ["Từ vựng", "Trắc nghiệm", "Reading", "Writing", "Thống kê"])
    
    # FIX: Tự động lấy danh sách trình độ từ file JSON để không bị lệch tên
    all_available_levels = list(bundle['vocab'].keys()) if bundle['vocab'] else ["Level_A1"]
    level = st.selectbox("Trình độ:", all_available_levels)
    
    if st.session_state.prev_mode != mode or st.session_state.prev_level != level:
        reset_task()
        st.session_state.prev_mode, st.session_state.prev_level = mode, level
        st.rerun()

# --- 4. LOGIC CHẾ ĐỘ ---

# --- PHẦN 1: TỪ VỰNG ---
if mode == "Từ vựng":
    type_mode = st.selectbox("Kiểu học:", ["Anh -> Việt", "Việt -> Anh"])
    if st.session_state.prev_type != type_mode:
        reset_task(); st.session_state.prev_type = type_mode; st.rerun()

    v_list = bundle['vocab'].get(level, {}).get("vocabulary", [])
    if not v_list: st.warning("Không tìm thấy từ vựng cho trình độ này!")
    else:
        if st.session_state.current_task is None: st.session_state.current_task = random.choice(v_list)
        w = st.session_state.current_task
        
        st.subheader(f"Luyện tập: {level}")
        st.write(f"IPA: `{w.get('ipa', 'N/A')}`")
        q_label = f"Dịch: **{w['en']}**" if type_mode == "Anh -> Việt" else f"Nghĩa là: **{w['vn']}**"
        correct = w['vn'] if type_mode == "Anh -> Việt" else w['en']
        
        with st.form("vocab_form"):
            ans = st.text_input(q_label)
            c1, c2 = st.columns(2)
            submit = c1.form_submit_button("Kiểm tra")
            change = c2.form_submit_button("Đổi từ khác")
            
            if submit:
                if ans.strip().lower() == correct.strip().lower():
                    st.success("Chuẩn cơm mẹ nấu!")
                    reset_task(); st.rerun()
                else: st.error(f"Sai rồi ấy ơi. Đáp án: {correct}")
            if change: reset_task(); st.rerun()

# --- PHẦN 2: TRẮC NGHIỆM ---
elif mode == "Trắc nghiệm":
    q_list = bundle['quiz'].get(level, [])
    if not q_list: st.warning("Chưa có câu hỏi trắc nghiệm trong quiz.json!")
    else:
        if st.session_state.current_task is None:
            q = random.choice(q_list)
            st.session_state.current_task = q
            opts = list(q['options'])
            random.shuffle(opts)
            st.session_state.options = opts
        
        q = st.session_state.current_task
        with st.form("quiz_form"):
            st.info(f"Điền vào chỗ trống: \n\n **{q['sentence']}**")
            choice = st.radio("Chọn đáp án:", st.session_state.options)
            if st.form_submit_button("Xác nhận câu trả lời"):
                if choice == q['answer']:
                    st.success("Tuyệt vời! Đang qua câu mới...")
                    reset_task(); st.rerun()
                else: st.error("Chưa đúng rồi!")

# --- PHẦN 3: READING ---
elif mode == "Reading":
    r_list = bundle['read'].get(level, [])
    if not r_list: st.warning("Trống bài đọc trong reading.json!")
    else:
        if st.session_state.current_task is None: st.session_state.current_task = random.choice(r_list)
        r = st.session_state.current_task
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**Nguồn:** {r['source']}")
            st.text_area("Đoạn văn:", r['passage'], height=300)
        
        with col2:
            with st.form("reading_form"):
                user_ans = []
                for i, quest in enumerate(r['questions']):
                    a = st.radio(f"{i+1}. {quest['q']}", quest['options'], key=f"r_{i}")
                    user_ans.append(a)
                
                if st.form_submit_button("Nộp bài đọc"):
                    correct = sum(1 for i, qs in enumerate(r['questions']) if user_ans[i] == qs['a'])
                    st.session_state.score_feedback = f"Kết quả: {correct}/{len(r['questions'])} câu đúng."
            
            if st.session_state.score_feedback:
                st.write(st.session_state.score_feedback)
                if st.button("Làm bài mới"): reset_task(); st.rerun()

# --- PHẦN 4: WRITING ---
elif mode == "Writing":
    w_list = bundle['write'].get(level, [])
    if not w_list: st.warning("Trống dữ liệu trong writing.json!")
    else:
        if st.session_state.current_task is None: st.session_state.current_task = random.choice(w_list)
        t = st.session_state.current_task
        with st.form("write_form"):
            st.subheader("Hoàn thành câu sau:")
            st.write(f"Đề bài: **{t['prompt']}**")
            user_w = st.text_input("Viết tại đây:")
            if st.form_submit_button("Kiểm tra câu viết"):
                if user_w.strip().lower() == t['answer'].strip().lower():
                    st.balloons(); st.success("Quá chuẩn!")
                else: st.info(f"Đáp án gợi ý: {t['answer']}")
        if st.button("Đổi câu khác"): reset_task(); st.rerun()

# --- PHẦN 5: THỐNG KÊ ---
elif mode == "Thống kê":
    st.header("Kết quả học tập")
    if os.path.exists("learning_logs.csv"):
        df = pd.read_csv("learning_logs.csv")
        st.dataframe(df.tail(10), use_container_width=True)
    else: st.info("Chưa có lịch sử học tập.")
