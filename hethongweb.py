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

# --- CSS: FIX GIAO DIỆN ---
st.markdown("<style>div[data-testid='stSelectbox'], div[data-testid='stRadio'] label, button { cursor: pointer !important; }</style>", unsafe_allow_html=True)

# --- 1. QUẢN LÝ DỮ LIỆU & LOGGING ---
@st.cache_data
def load_data():
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)

def log_action(username, word_en, result, mode):
    """Lưu log học tập để phân tích sau này"""
    log_file = "learning_logs.csv"
    new_entry = {
        "time": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "user": [username],
        "word_or_task": [word_en],
        "is_correct": [result],
        "mode": [mode]
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

# --- 3. ĐĂNG NHẬP ---
if not st.session_state.logged_in:
    st.title("🔐 UTH English - Đăng nhập")
    try:
        with open("users.json", "r") as f: user_db = json.load(f)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Vào học"):
            if u in user_db and user_db[u] == p:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else: st.error("Sai tài khoản!")
    except: st.error("Thiếu file users.json!")
    st.stop()

# --- 4. GIAO DIỆN CHÍNH ---
data = load_data()
with st.sidebar:
    st.success(f"👤: {st.session_state.username}")
    if st.button("Đăng xuất"):
        st.session_state.logged_in = False
        st.rerun()
    st.divider()
    # DANH SÁCH 5 CHẾ ĐỘ ĐẦY ĐỦ
    mode = st.radio("Chế độ học:", [
        "Học từ vựng", 
        "Trắc nghiệm", 
        "Reading", 
        "Writing", 
        "Thống kê (Analytics)"
    ])
    
    if mode != "Thống kê (Analytics)":
        level = st.selectbox("Chọn trình độ:", list(data.keys()))
        type_mode = st.selectbox("Kiểu học:", ["Anh -> Việt", "Việt -> Anh"])

# --- 5. XỬ LÝ LOGIC TỪNG CHẾ ĐỘ ---

# --- CHẾ ĐỘ: HỌC TỪ VỰNG ---
if mode == "Học từ vựng":
    st.header(f"Luyện tập: {level}")
    vocab_list = data[level].get("vocabulary", [])
    if not st.session_state.current_word: st.session_state.current_word = random.choice(vocab_list)
    word = st.session_state.current_word
    
    st.write(f"🔉 **Phiên âm:** `{word.get('ipa', 'N/A')}`")
    if st.button("🔊 Nghe"): play_audio(word['en'])
    
    label = f"Dịch: {word['en']}" if type_mode == "Anh -> Việt" else f"Dịch: {word['vn']}"
    ans = st.text_input(label)
    correct = word['vn'] if type_mode == "Anh -> Việt" else word['en']
    
    if st.button("Kiểm tra"):
        if ans.strip().lower() == correct.strip().lower():
            st.success("Đúng! 🎉")
            log_action(st.session_state.username, word['en'], 1, "Vocabulary")
            st.session_state.current_word = None
            st.rerun()
        else:
            st.error(f"Sai! Đáp án: {correct}")
            log_action(st.session_state.username, word['en'], 0, "Vocabulary")

# --- CHẾ ĐỘ: TRẮC NGHIỆM ---
elif mode == "Trắc nghiệm":
    st.header(f"Trắc nghiệm: {level}")
    vocab_list = data[level].get("vocabulary", [])
    if not st.session_state.current_word: st.session_state.current_word = random.choice(vocab_list)
    word = st.session_state.current_word

    st.subheader(f"Nghĩa của từ **{word['en']}** là gì?")
    options = [word['vn']] + word.get('distractors', [])[:3]
    random.shuffle(options)
    choice = st.radio("Chọn đáp án đúng:", options)
    
    if st.button("Xác nhận"):
        if choice == word['vn']:
            st.success("Chính xác! 🎯")
            log_action(st.session_state.username, word['en'], 1, "Quiz")
            st.session_state.current_word = None
            st.rerun()
        else:
            st.error(f"Sai rồi! Đáp án: {word['vn']}")
            log_action(st.session_state.username, word['en'], 0, "Quiz")

# --- CHẾ ĐỘ: READING (BẢN MẪU) ---
elif mode == "Reading":
    st.header("Luyện kỹ năng Đọc: {level}")
    reading_tasks = data[level].get("reading", [])
    if reading_tasks:
        task = random.choice(reading_tasks)
        st.markdown("---")
        st.subheader("Đoạn văn:")
        st.write(task['passage']) # Hiển thị đoạn văn
        st.markdown("---")
    else:
        st.warning("Hiện tại trình độ này chưa có bài đọc.")

# --- CHẾ ĐỘ: WRITING (BẢN MẪU) ---
elif mode == "Writing":
    st.header("Luyện kỹ năng Viết")
    st.write("Dịch cả câu sau sang tiếng Anh:")
    writing_tasks = data[level].get("writing", [])
    if writing_tasks:
        task = random.choice(writing_tasks)
        st.subheader(task['vn_sentence'])
        user_write = st.text_area("Viết câu của bạn:")
        if st.button("Nộp bài"):
            # Logic so khớp câu (String similarity)
            st.write(f"Đáp án mẫu: {task['en_sentence']}")
    else:
        st.info("Chế độ Writing: Bạn có thể cho người dùng viết lại cả câu dài để luyện ngữ pháp.")

# --- CHẾ ĐỘ: THỐNG KÊ (ANALYTICS) ---
elif mode == "Thống kê (Analytics)":
    st.header(f"Dashboard của {st.session_state.username}")
    if os.path.exists("learning_logs.csv"):
        df = pd.read_csv("learning_logs.csv")
        user_df = df[df['user'] == st.session_state.username]
        if not user_df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Tổng lượt làm bài", len(user_df))
            c2.metric("Số câu Đúng", user_df['is_correct'].sum())
            c3.metric("Tỉ lệ %", f"{(user_df['is_correct'].sum()/len(user_df))*100:.1f}%")
            
            st.subheader("❌ Các từ/kỹ năng bạn cần cải thiện")
            st.bar_chart(user_df[user_df['is_correct'] == 0]['word_or_task'].value_counts().head(5))
        else: st.info("Làm bài đi Kiệt ơi, chưa có dữ liệu gì cả!")
