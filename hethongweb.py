import streamlit as st
import json
import random
from gtts import gTTS
import io
import os
import pandas as pd
from datetime import datetime

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="UTH English Pro v3.6 - Full Suite", layout="wide")

# --- CSS: TÙY CHỈNH GIAO DIỆN ---
st.markdown("""
    <style>
    div[data-testid="stSelectbox"], div[data-testid="stRadio"] label, button { cursor: pointer !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. QUẢN LÝ DỮ LIỆU & LOGGING ---
@st.cache_data
def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except: return {}

def log_action(username, task_name, result, mode_name):
    """Lưu dữ liệu học tập để phục vụ phân tích Data Science"""
    log_file = "learning_logs.csv"
    new_entry = {
        "time": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "user": [username],
        "task": [task_name],
        "is_correct": [result], # 1: Đúng, 0: Sai
        "mode": [mode_name]
    }
    df_new = pd.DataFrame(new_entry)
    if not os.path.isfile(log_file):
        df_new.to_csv(log_file, index=False, encoding="utf-8-sig")
    else:
        df_new.to_csv(log_file, mode='a', header=False, index=False, encoding="utf-8-sig")

def play_audio(text):
    tts = gTTS(text=text, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    st.audio(fp)

# --- 2. KHỞI TẠO SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_word' not in st.session_state: st.session_state.current_word = None
if 'learn_count' not in st.session_state: st.session_state.learn_count = 0
if 'retry_list' not in st.session_state: st.session_state.retry_list = []

# --- 3. HỆ THỐNG ĐĂNG NHẬP ---
if not st.session_state.logged_in:
    st.title("🔐 UTH English - Đăng nhập")
    try:
        with open("users.json", "r") as f: user_db = json.load(f)
        u = st.text_input("Tên đăng nhập")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("Vào hệ thống"):
            if u in user_db and user_db[u] == p:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else: st.error("Sai tài khoản hoặc mật khẩu rồi Kiệt ơi!")
    except: st.error("Lỗi: Kiệt chưa tạo file users.json trên máy!")
    st.stop()

# --- 4. GIAO DIỆN CHÍNH ---
data = load_data()
with st.sidebar:
    st.success(f"👤 Sinh viên: {st.session_state.username}")
    if st.button("Đăng xuất"):
        st.session_state.logged_in = False
        st.rerun()
    st.divider()
    # ĐÃ CẬP NHẬT ĐỦ 5 CHẾ ĐỘ
    mode = st.radio("Chế độ:", ["Học từ vựng", "Trắc nghiệm", "Reading", "Writing", "Thống kê (Analytics)"])
    
    if mode != "Thống kê (Analytics)":
        level = st.selectbox("Chọn trình độ:", list(data.keys()))
        type_mode = st.selectbox("Kiểu học:", ["Anh -> Việt", "Việt -> Anh"])

# --- 5. LOGIC XỬ LÝ CÁC CHẾ ĐỘ ---

# CHẾ ĐỘ: HỌC TỪ VỰNG
if mode == "Học từ vựng":
    st.header(f"Luyện tập: {level}")
    vocab_list = data[level].get("vocabulary", [])
    
    if st.session_state.retry_list and st.session_state.learn_count >= 3:
        word = st.session_state.retry_list.pop(0)
        st.session_state.learn_count = 0
        st.info("🔄 Nhắc lại từ bạn đã làm sai:")
    else:
        if not st.session_state.current_word:
            st.session_state.current_word = random.choice(vocab_list)
        word = st.session_state.current_word

    st.write(f"🔉 **Phiên âm:** `{word.get('ipa', 'N/A')}`")
    if st.button("🔊 Nghe"): play_audio(word['en'])

    label = f"Từ: {word['en']}" if type_mode == "Anh -> Việt" else f"Nghĩa: {word['vn']}"
    ans = st.text_input(label, key="vocab_input")
    correct = word['vn'] if type_mode == "Anh -> Việt" else word['en']

    if st.button("Kiểm tra"):
        if ans.strip().lower() == correct.strip().lower():
            st.success("Chính xác! 🎉")
            log_action(st.session_state.username, word['en'], 1, "Vocabulary")
            st.session_state.learn_count += 1
            st.session_state.current_word = None
            st.rerun()
        else:
            st.error(f"Sai rồi! Đáp án: {correct}")
            log_action(st.session_state.username, word['en'], 0, "Vocabulary")
            if word not in st.session_state.retry_list:
                st.session_state.retry_list.append(word)

# CHẾ ĐỘ: TRẮC NGHIỆM
elif mode == "Trắc nghiệm":
    st.header(f"Trắc nghiệm: {level}")
    vocab_list = data[level].get("vocabulary", [])
    if not st.session_state.current_word:
        st.session_state.current_word = random.choice(vocab_list)
    word = st.session_state.current_word

    st.subheader(f"Từ **{word['en']}** có nghĩa là gì?")
    options = [word['vn']] + word.get('distractors', [])[:3]
    random.shuffle(options)
    
    choice = st.radio("Chọn đáp án:", options, key="quiz_radio")
    if st.button("Xác nhận"):
        if choice == word['vn']:
            st.success("Quá chuẩn!")
            log_action(st.session_state.username, word['en'], 1, "Quiz")
            st.session_state.current_word = None
            st.rerun()
        else:
            st.error(f"Sai rồi! Đáp án đúng: {word['vn']}")
            log_action(st.session_state.username, word['en'], 0, "Quiz")

# CHẾ ĐỘ: READING
elif mode == "Reading":
    st.header(f"Luyện kỹ năng Đọc: {level}")
    reading_tasks = data[level].get("reading", [])
    if reading_tasks:
        task = random.choice(reading_tasks)
        st.info("💡 Đọc đoạn văn dưới đây:")
        st.markdown(f"> {task['passage']}")
        # Kiệt có thể bổ sung thêm câu hỏi từ task['questions'] ở đây
    else:
        st.warning("Hiện tại trình độ này chưa có bài đọc trong data.json.")

# CHẾ ĐỘ: WRITING
elif mode == "Writing":
    st.header(f"Luyện kỹ năng Viết: {level}")
    writing_tasks = data[level].get("writing", [])
    if writing_tasks:
        task = random.choice(writing_tasks)
        st.subheader(f"Dịch sang tiếng Anh: **{task['vn_sentence']}**")
        user_write = st.text_area("Câu trả lời của bạn:", placeholder="Gõ câu tiếng Anh vào đây...")
        if st.button("Gửi bài"):
            st.write(f"Đáp án mẫu: **{task['en_sentence']}**")
            # Bạn có thể dùng logic so sánh chuỗi để chấm điểm ở đây
    else:
        st.warning("Hiện tại trình độ này chưa có bài viết trong data.json.")

# CHẾ ĐỘ: THỐNG KÊ (ANALYTICS)
elif mode == "Thống kê (Analytics)":
    st.header(f"Dashboard Phân Tích của {st.session_state.username}")
    if os.path.exists("learning_logs.csv"):
        df = pd.read_csv("learning_logs.csv")
        user_df = df[df['user'] == st.session_state.username]
        if not user_df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Tổng lượt làm bài", len(user_df))
            c2.metric("Số câu Đúng ✅", user_df['is_correct'].sum())
            c3.metric("Tỉ lệ Chính xác", f"{(user_df['is_correct'].sum()/len(user_df))*100:.1f}%")
            
            st.subheader("❌ Top từ hay bị sai nhất")
            wrong_words = user_df[user_df['is_correct'] == 0]['task'].value_counts().head(5)
            if not wrong_words.empty:
                st.bar_chart(wrong_words)
            else: st.success("Bạn chưa sai từ nào cả!")
        else: st.info("Bạn chưa có lịch sử học tập.")
    else: st.warning("Chưa có dữ liệu log.")
