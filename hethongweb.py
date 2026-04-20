import streamlit as st
import json
import random
from gtts import gTTS
import io
import os
import pandas as pd
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="UTH English Pro v3.9", layout="wide")
st.markdown("<style>div[data-testid='stSelectbox'], div[data-testid='stRadio'] label, button { cursor: pointer !important; }</style>", unsafe_allow_html=True)

# --- 1. DATA & LOGGING ---
@st.cache_data
def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Lỗi nạp file data.json: {e}")
        return {}

def log_action(username, task, result, mode):
    try:
        log_file = "learning_logs.csv"
        new_entry = {"time": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")], "user": [username], "task": [task], "is_correct": [result], "mode": [mode]}
        df = pd.DataFrame(new_entry)
        df.to_csv(log_file, mode='a', header=not os.path.exists(log_file), index=False, encoding="utf-8-sig")
    except: pass

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp)
    except: st.warning("Không thể phát âm thanh lúc này.")

# --- 2. TẮT ĐĂNG NHẬP ĐỂ DEV ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = True 
    st.session_state.username = "Hi"

if 'current_word' not in st.session_state: st.session_state.current_word = None
if 'learn_count' not in st.session_state: st.session_state.learn_count = 0
if 'retry_list' not in st.session_state: st.session_state.retry_list = []

# --- 3. GIAO DIỆN CHÍNH ---
data = load_data()
if not data:
    st.error("Dữ liệu trống! Kiệt kiểm tra lại file data.json nhé.")
    st.stop()

with st.sidebar:
    st.success(f"👤 Sinh viên: {st.session_state.username}")
    st.divider()
    mode = st.radio("Chế độ:", ["Học từ vựng", "Trắc nghiệm", "Reading", "Writing", "Analytics"])
    level = st.selectbox("Trình độ:", list(data.keys()))
    if mode == "Học từ vựng ⌨️":
        type_mode = st.selectbox("Kiểu học:", ["Anh -> Việt", "Việt -> Anh"])

# --- 4. LOGIC CÁC CHẾ ĐỘ ---

# --- CHẾ ĐỘ TỪ VỰNG (ĐÃ FIX LỖI TRẮNG MÀN HÌNH) ---
if mode == "Học từ vựng ⌨️":
    st.header(f"⌨️ Luyện tập: {level}")
    vocab_list = data[level].get("vocabulary", [])
    
    if not vocab_list:
        st.error("Cảnh báo: Trình độ này không có từ vựng nào trong file JSON!")
    else:
        # Chọn từ mới nếu chưa có
        if st.session_state.current_word is None:
            st.session_state.current_word = random.choice(vocab_list)
        
        word = st.session_state.current_word
        
        # Hiển thị
        st.write(f"🔉 **IPA:** `{word.get('ipa', 'N/A')}`")
        if st.button("🔊 Nghe", key="btn_speak"): play_audio(word['en'])
        
        # Logic câu hỏi
        if type_mode == "Anh -> Việt":
            st.subheader(f"Từ tiếng Anh: **{word['en']}**")
            ans = st.text_input("Nhập nghĩa tiếng Việt:", key=f"input_{word['en']}")
            correct = word['vn']
        else:
            st.subheader(f"Nghĩa tiếng Việt: **{word['vn']}**")
            ans = st.text_input("Nhập từ tiếng Anh:", key=f"input_{word['vn']}")
            correct = word['en']

        if st.button("Kiểm tra", key="btn_check"):
            if ans.strip().lower() == correct.strip().lower():
                st.success("Chính xác! 🎉")
                log_action(st.session_state.username, word['en'], 1, "Vocab")
                st.session_state.current_word = None # Reset để qua từ mới
                st.rerun()
            else:
                st.error(f"Sai rồi! Đáp án đúng: {correct}")
                log_action(st.session_state.username, word['en'], 0, "Vocab")

# --- CHẾ ĐỘ TRẮC NGHIỆM ---
elif mode == "Trắc nghiệm":
    st.header(f"Trắc nghiệm: {level}")
    vocab_list = data[level].get("vocabulary", [])
    if not vocab_list:
        st.error("Không có dữ liệu trắc nghiệm.")
    else:
        if st.session_state.current_word is None:
            st.session_state.current_word = random.choice(vocab_list)
        word = st.session_state.current_word

        st.subheader(f"Nghĩa của từ **{word['en']}** là gì?")
        others = [v['vn'] for v in vocab_list if v['vn'] != word['vn']]
        distractors = random.sample(others, min(len(others), 3))
        options = list(set([word['vn']] + distractors))
        random.shuffle(options)
        
        choice = st.radio("Chọn đáp án:", options, key=f"quiz_{word['en']}")
        if st.button("Xác nhận câu trả lời"):
            if choice == word['vn']:
                st.success("Chuẩn cơm mẹ nấu!")
                log_action(st.session_state.username, word['en'], 1, "Quiz")
                st.session_state.current_word = None
                st.rerun()
            else:
                st.error(f"Sai! Đáp án: {word['vn']}")
                log_action(st.session_state.username, word['en'], 0, "Quiz")

# --- CHẾ ĐỘ READING & WRITING (GIỮ NGUYÊN AUTO-GEN) ---
elif mode == "Reading":
    st.header(f"Reading: {level}")
    tasks = data[level].get("reading", [])
    if not tasks:
        vocab = data[level].get("vocabulary", [])
        if len(vocab) >= 3:
            s = random.sample(vocab, 3)
            st.info(f"💡 Bài đọc tự động: Today, I learned {s[0]['en']}, {s[1]['en']} and {s[2]['en']}.")
        else: st.warning("Cần thêm từ vựng để tạo bài đọc.")
    else:
        st.write(random.choice(tasks)['passage'])

elif mode == "Writing":
    st.header(f"Writing: {level}")
    tasks = data[level].get("writing", [])
    if not tasks:
        vocab = data[level].get("vocabulary", [])
        if vocab:
            w = random.choice(vocab)
            st.subheader(f"Dịch từ: **{w['vn']}**")
            u = st.text_input("Kết quả:", key=f"write_{w['en']}")
            if st.button("Check"): st.write(f"Đáp án: {w['en']}")
        else: st.warning("Trống dữ liệu Writing.")
    else:
        t = random.choice(tasks)
        st.subheader(f"Dịch: {t['vn_sentence']}")
        if st.button("Xem đáp án"): st.write(t['en_sentence'])

# --- CHẾ ĐỘ ANALYTICS ---
elif mode == "Analytics":
    st.header("Thống kê")
    if os.path.exists("learning_logs.csv"):
        df = pd.read_csv("learning_logs.csv")
        st.bar_chart(df['mode'].value_counts())
        st.line_chart(df['is_correct'])
    else: st.info("Chưa có dữ liệu.")
