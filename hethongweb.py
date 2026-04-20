import streamlit as st
import json
import random
from gtts import gTTS
import io
import os
import pandas as pd
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="UTH English Pro v3.8", layout="wide")
st.markdown("<style>div[data-testid='stSelectbox'], div[data-testid='stRadio'] label, button { cursor: pointer !important; }</style>", unsafe_allow_html=True)

# --- 1. DATA & LOGGING ---
@st.cache_data
def load_data():
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)

def log_action(username, task, result, mode):
    log_file = "learning_logs.csv"
    new_entry = {"time": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")], "user": [username], "task": [task], "is_correct": [result], "mode": [mode]}
    df = pd.DataFrame(new_entry)
    df.to_csv(log_file, mode='a', header=not os.path.exists(log_file), index=False, encoding="utf-8-sig")

def play_audio(text):
    tts = gTTS(text=text, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    st.audio(fp)

# --- 2. SESSION STATE & TẮT LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = True 
    st.session_state.username = "Hi"

if 'current_word' not in st.session_state: st.session_state.current_word = None

# --- 3. GIAO DIỆN CHÍNH ---
data = load_data()
with st.sidebar:
    st.success(f"👤 Sinh viên: {st.session_state.username}")
    st.divider()
    mode = st.radio("Chế độ:", ["Học từ vựng", "Trắc nghiệm", "Reading", "Writing", "Analytics"])
    level = st.selectbox("Trình độ:", list(data.keys()))

# --- 4. LOGIC CÁC CHẾ ĐỘ ---

# CHẾ ĐỘ TỪ VỰNG
if mode == "Học từ vựng ⌨️":
    st.header(f"⌨️ Luyện tập: {level}")
    vocab_list = data[level].get("vocabulary", [])
    if not st.session_state.current_word: st.session_state.current_word = random.choice(vocab_list)
    word = st.session_state.current_word
    st.write(f"🔉 **IPA:** `{word.get('ipa', 'N/A')}`")
    if st.button("🔊 Nghe"): play_audio(word['en'])
    ans = st.text_input(f"Dịch từ: {word['en']}")
    if st.button("Kiểm tra"):
        if ans.strip().lower() == word['vn'].strip().lower():
            st.success("Đúng! 🎉"); log_action(st.session_state.username, word['en'], 1, "Vocab")
            st.session_state.current_word = None; st.rerun()
        else: st.error(f"Sai! Đáp án: {word['vn']}")

# CHẾ ĐỘ TRẮC NGHIỆM (Hết lỏ - Tự tạo đáp án tiếng Việt)
elif mode == "Trắc nghiệm":
    st.header(f"Trắc nghiệm thông minh: {level}")
    vocab_list = data[level].get("vocabulary", [])
    if not st.session_state.current_word: st.session_state.current_word = random.choice(vocab_list)
    word = st.session_state.current_word

    st.subheader(f"Nghĩa của từ **{word['en']}**?")
    # Tự bốc các nghĩa tiếng Việt khác làm mồi nhử
    others = [v['vn'] for v in vocab_list if v['vn'] != word['vn']]
    distractors = random.sample(others, 3) if len(others) >=3 else others
    options = [word['vn']] + distractors
    random.shuffle(options)
    
    choice = st.radio("Chọn đáp án:", options, key="quiz")
    if st.button("Xác nhận"):
        if choice == word['vn']:
            st.success("Chuẩn cơm mẹ nấu!"); log_action(st.session_state.username, word['en'], 1, "Quiz")
            st.session_state.current_word = None; st.rerun()
        else: st.error(f"Sai! Đáp án: {word['vn']}")

# CHẾ ĐỘ READING (Auto-Gen nếu trống)
elif mode == "Reading":
    st.header(f"Reading: {level}")
    tasks = data[level].get("reading", [])
    if not tasks: # Nếu JSON trống, tự tạo bài từ Vocabulary
        vocab = data[level].get("vocabulary", [])
        sample_words = random.sample(vocab, 3)
        passage = f"Today I learned about {sample_words[0]['en']}, {sample_words[1]['en']} and {sample_words[2]['en']}. It was great!"
        st.info("💡 (Bài đọc tự động tạo từ vựng):")
        st.write(passage)
    else:
        task = random.choice(tasks)
        st.write(task['passage'])

# CHẾ ĐỘ WRITING (Auto-Gen nếu trống)
elif mode == "Writing":
    st.header(f"Writing: {level}")
    tasks = data[level].get("writing", [])
    if not tasks:
        vocab = data[level].get("vocabulary", [])
        word = random.choice(vocab)
        st.subheader(f"Viết lại từ này bằng tiếng Anh: **{word['vn']}**")
        user_text = st.text_input("Gõ câu của bạn:")
        if st.button("Nộp bài"):
            st.write(f"Đáp án: **{word['en']}**")
    else:
        task = random.choice(tasks)
        st.subheader(f"Dịch: {task['vn_sentence']}")
        st.text_area("Viết tại đây...")
        if st.button("Check"): st.write(f"Đáp án: {task['en_sentence']}")

# CHẾ ĐỘ ANALYTICS
elif mode == "Analytics":
    st.header("Thống kê kết quả")
    if os.path.exists("learning_logs.csv"):
        df = pd.read_csv("learning_logs.csv")
        st.line_chart(df['is_correct'].rolling(10).mean())
        st.bar_chart(df['mode'].value_counts())
    else: st.info("Chưa có dữ liệu học tập.")
