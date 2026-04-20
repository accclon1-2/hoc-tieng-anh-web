import streamlit as st
import json
import random
from gtts import gTTS
import io
import os
import pandas as pd
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="UTH English Pro v3.7", layout="wide")

st.markdown("<style>div[data-testid='stSelectbox'], div[data-testid='stRadio'] label, button { cursor: pointer !important; }</style>", unsafe_allow_html=True)

# --- 1. DATA & LOGGING ---
@st.cache_data
def load_data():
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)

def log_action(username, task, result, mode):
    log_file = "learning_logs.csv"
    new_entry = {
        "time": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "user": [username],
        "task": [task],
        "is_correct": [result],
        "mode": [mode]
    }
    df = pd.DataFrame(new_entry)
    df.to_csv(log_file, mode='a', header=not os.path.exists(log_file), index=False, encoding="utf-8-sig")

def play_audio(text):
    tts = gTTS(text=text, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    st.audio(fp)

# --- 2. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_word' not in st.session_state: st.session_state.current_word = None
if 'learn_count' not in st.session_state: st.session_state.learn_count = 0
if 'retry_list' not in st.session_state: st.session_state.retry_list = []

# --- 3. LOGIN ---
if not st.session_state.logged_in:
    st.title("🔐 UTH English - Đăng nhập")
    try:
        with open("users.json", "r") as f: db = json.load(f)
        u = st.text_input("Tên đăng nhập")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("Vào hệ thống"):
            if u in db and db[u] == p:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else: st.error("Sai tài khoản!")
    except: st.error("Thiếu file users.json!")
    st.stop()

# --- 4. MAIN UI ---
data = load_data()
with st.sidebar:
    st.success(f"👤: {st.session_state.username}")
    if st.button("Đăng xuất"):
        st.session_state.logged_in = False
        st.rerun()
    st.divider()
    mode = st.radio("Chế độ:", ["Học từ vựng", "Trắc nghiệm", "Reading", "Writing", "Analytics"])
    level = st.selectbox("Trình độ:", list(data.keys()))
    if mode == "Học từ vựng":
        type_mode = st.selectbox("Kiểu học:", ["Anh -> Việt", "Việt -> Anh"])

# --- 5. LOGIC MODES ---

# --- MODE: TỪ VỰNG ---
if mode == "Học từ vựng":
    st.header(f"Luyện tập: {level}")
    vocab_list = data[level].get("vocabulary", [])
    if not st.session_state.current_word: st.session_state.current_word = random.choice(vocab_list)
    word = st.session_state.current_word
    
    st.write(f"🔉 **IPA:** `{word.get('ipa', 'N/A')}`")
    if st.button("🔊 Nghe"): play_audio(word['en'])
    
    label = f"Dịch từ: {word['en']}" if type_mode == "Anh -> Việt" else f"Dịch nghĩa: {word['vn']}"
    ans = st.text_input(label, key="vocab_in")
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

# --- MODE: TRẮC NGHIỆM (FIXED LOGIC) ---
elif mode == "Trắc nghiệm":
    st.header(f"Trắc nghiệm thông minh: {level}")
    vocab_list = data[level].get("vocabulary", [])
    if not st.session_state.current_word: st.session_state.current_word = random.choice(vocab_list)
    word = st.session_state.current_word

    st.subheader(f"Nghĩa của từ **{word['en']}** là gì?")
    
    # THUẬT TOÁN MỚI: Tự tạo mồi nhử bằng tiếng Việt
    all_vn_meanings = [v['vn'] for v in vocab_list if v['vn'] != word['vn']]
    distractors = random.sample(all_vn_meanings, 3) # Lấy 3 nghĩa tiếng Việt ngẫu nhiên khác
    options = [word['vn']] + distractors
    random.shuffle(options)
    
    choice = st.radio("Chọn đáp án chính xác:", options, key="quiz_choice")
    if st.button("Xác nhận"):
        if choice == word['vn']:
            st.success("Chuẩn cơm mẹ nấu!")
            log_action(st.session_state.username, word['en'], 1, "Quiz")
            st.session_state.current_word = None
            st.rerun()
        else:
            st.error(f"Sai rồi! Đáp án đúng là: {word['vn']}")
            log_action(st.session_state.username, word['en'], 0, "Quiz")

# --- MODE: READING ---
elif mode == "Reading 📖":
    st.header(f"📖 Reading: {level}")
    tasks = data[level].get("reading", [])
    if tasks:
        task = random.choice(tasks)
        st.info(task['passage'])
    else:
        st.warning("Level này chưa có bài đọc. Kiệt hãy nạp thêm vào data.json nhé!")

# --- MODE: WRITING ---
elif mode == "Writing":
    st.header(f"Writing: {level}")
    tasks = data[level].get("writing", [])
    if tasks:
        task = random.choice(tasks)
        st.subheader(f"Dịch sang tiếng Anh: {task['vn_sentence']}")
        user_text = st.text_area("Viết câu của bạn:")
        if st.button("Check"):
            st.write(f"Đáp án mẫu: **{task['en_sentence']}**")
    else:
        st.warning("Level này chưa có bài viết.")

# --- MODE: ANALYTICS ---
elif mode == "Analytics":
    st.header(f"Dashboard: {st.session_state.username}")
    if os.path.exists("learning_logs.csv"):
        df = pd.read_csv("learning_logs.csv")
        user_df = df[df['user'] == st.session_state.username]
        if not user_df.empty:
            col1, col2 = st.columns(2)
            col1.metric("Tổng số câu", len(user_df))
            col2.metric("Tỉ lệ đúng", f"{(user_df['is_correct'].sum()/len(user_df))*100:.1f}%")
            st.subheader("Tiến độ học tập")
            st.line_chart(user_df['is_correct'].rolling(window=5).mean())
        else: st.info("Chưa có dữ liệu.")
    else: st.warning("Chưa có file log.")
