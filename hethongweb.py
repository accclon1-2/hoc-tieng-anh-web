### 2. Full Code `hethongweb.py` (v5.2 - Siêu ổn định)
import streamlit as st
import json
import random
import os
import pandas as pd
from datetime import datetime

# --- CẤU HÌNH ---
st.set_page_config(page_title="UTH English Pro v5.2", layout="wide")

# --- 1. NẠP DỮ LIỆU ---
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
# Tự động vào thẳng Kiet_Admin
if 'logged_in' not in st.session_state: st.session_state.logged_in = True
if 'username' not in st.session_state: st.session_state.username = "Kiệt_Admin"

# Khởi tạo các biến điều khiển
states = ['current_task', 'options', 'submitted', 'feedback', 'prev_mode', 'prev_level', 'prev_type']
for s in states:
    if s not in st.session_state: st.session_state[s] = None

def reset_task():
    st.session_state.current_task = None
    st.session_state.submitted = False
    st.session_state.feedback = ""

# --- 3. SIDEBAR ---
bundle = load_all_data()
with st.sidebar:
    st.title("🎓 UTH Pro v5.2")
    mode = st.radio("Chế độ:", ["Từ vựng", "Trắc nghiệm", "Reading", "Writing", "Thống kê"])
    level = st.selectbox("Trình độ:", ["Level_A1", "Level_A2", "Level_B1"])
    
    # Reset nếu đổi Mode hoặc Level
    if st.session_state.prev_mode != mode or st.session_state.prev_level != level:
        reset_task()
        st.session_state.prev_mode, st.session_state.prev_level = mode, level
        st.rerun()

# --- 4. LOGIC CÁC PHẦN ---

# --- PHẦN 1: TỪ VỰNG (FIXED) ---
if mode == "Từ vựng":
    type_mode = st.selectbox("Kiểu học:", ["Anh -> Việt", "Việt -> Anh"])
    if st.session_state.prev_type != type_mode:
        reset_task()
        st.session_state.prev_type = type_mode
        st.rerun()

    v_list = bundle['vocab'].get(level, {}).get("vocabulary", [])
    if not v_list: st.warning("Dữ liệu từ vựng trống!")
    else:
        if st.session_state.current_task is None: 
            st.session_state.current_task = random.choice(v_list)
        
        w = st.session_state.current_task
        st.subheader(f"Luyện từ vựng: {level}")
        st.write(f"IPA: `{w.get('ipa', 'N/A')}`")
        
        q_label = f"Dịch: **{w['en']}**" if type_mode == "Anh -> Việt" else f"Nghĩa là: **{w['vn']}**"
        correct = w['vn'] if type_mode == "Anh -> Việt" else w['en']
        
        ans = st.text_input(q_label, key=f"voc_{w['en']}")
        
        col1, col2 = st.columns(2)
        if col1.button("Kiểm tra"):
            if ans.strip().lower() == correct.strip().lower():
                st.success("Chính xác!")
                reset_task(); st.rerun()
            else: st.error(f"Sai rồi. Đáp án: {correct}")
        if col2.button("Đổi từ khác "): reset_task(); st.rerun()

# --- PHẦN 2: TRẮC NGHIỆM (Sửa lỗi nút bấm & Đáp án đứng yên) ---
elif mode == "Trắc nghiệm":
    q_list = bundle['quiz'].get(level, [])
    if not q_list: st.warning("Chưa có câu hỏi trắc nghiệm!")
    else:
        if st.session_state.current_task is None:
            q = random.choice(q_list)
            st.session_state.current_task = q
            opts = list(q['options'])
            random.shuffle(opts)
            st.session_state.options = opts
        
        q = st.session_state.current_task
        st.info(f"Điền vào chỗ trống: \n\n **{q['sentence']}**")
        
        choice = st.radio("Chọn đáp án:", st.session_state.options, key="quiz_opt")
        
        if st.button("Xác nhận câu trả lời"):
            if choice == q['answer']:
                st.success("Tuyệt vời! Đang chuyển câu...")
                reset_task(); st.rerun()
            else: st.error("Chưa đúng rồi!")

# --- PHẦN 3: READING (Fix lỗi xác nhận không phản hồi) ---
elif mode == "Reading":
    r_list = bundle['read'].get(level, [])
    if not r_list: st.warning("Trống dữ liệu Reading.")
    else:
        if st.session_state.current_task is None: 
            st.session_state.current_task = random.choice(r_list)
        
        r = st.session_state.current_task
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f"**Nguồn:** {r['source']}")
            st.text_area("Đoạn văn:", r['passage'], height=300)
        with c2:
            st.write("Câu hỏi:")
            user_ans = []
            for i, quest in enumerate(r['questions']):
                a = st.radio(f"{i+1}. {quest['q']}", quest['options'], key=f"r_{i}")
                user_ans.append(a)
        
        if st.button("Nộp bài đọc"):
            correct_count = 0
            for i, quest in enumerate(r['questions']):
                if user_ans[i] == quest['a']: correct_count += 1
            st.write(f"Kết quả: {correct_count}/{len(r['questions'])} câu đúng.")
            if st.button("Làm bài mới"): reset_task(); st.rerun()

# --- PHẦN 4: WRITING (Đã mở rộng cho nhiều câu) ---
elif mode == "Writing":
    w_list = bundle['write'].get(level, [])
    if not w_list: st.warning("Trống dữ liệu Writing.")
    else:
        if st.session_state.current_task is None: 
            st.session_state.current_task = random.choice(w_list)
        
        t = st.session_state.current_task
        st.subheader("Hoàn thành câu sau:")
        st.write(f"Đề bài: **{t['prompt']}**")
        
        user_w = st.text_input("Viết tại đây:", key="write_input")
        if st.button("Kiểm tra câu viết"):
            if user_w.strip().lower() == t['answer'].strip().lower():
                st.balloons()
                st.success("Quá chuẩn!")
                if st.button("Tiếp tục"): reset_task(); st.rerun()
            else:
                st.info(f"Đáp án gợi ý: {t['answer']}")
        if st.button("Đổi câu khác"): reset_task(); st.rerun()

# --- PHẦN 5: THỐNG KÊ ---
elif mode == "Thống kê":
    st.info("Chức năng thống kê đang hiển thị dữ liệu lịch sử...")
    if os.path.exists("learning_logs.csv"):
        df = pd.read_csv("learning_logs.csv")
        st.dataframe(df.tail(10), use_container_width=True)
