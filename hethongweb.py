import streamlit as st
import json
import random
from gtts import gTTS
import io
import os
import pandas as pd
from datetime import datetime

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="UTH English Pro v3.5 - Full Analytics", layout="wide")

# --- CSS: CON TRỎ CHUỘT & GIAO DIỆN ---
st.markdown("<style>div[data-testid='stSelectbox'], div[data-testid='stRadio'] label, button { cursor: pointer !important; }</style>", unsafe_allow_html=True)

# --- 1. QUẢN LÝ DỮ LIỆU & LOGGING ---
@st.cache_data
def load_data():
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)

def log_action(username, word_en, result):
    """Ghi dữ liệu học tập vào file CSV để làm Data Science"""
    log_file = "learning_logs.csv"
    new_entry = {
        "time": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "user": [username],
        "word": [word_en],
        "is_correct": [result] # 1: Đúng, 0: Sai
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
    st.title("🔐 UTH English - Đăng nhập hệ thống")
    try:
        with open("users.json", "r") as f: user_db = json.load(f)
        u = st.text_input("Tên đăng nhập")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("Vào học ngay"):
            if u in user_db and user_db[u] == p:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else: st.error("Sai tài khoản hoặc mật khẩu rồi Kiệt ơi!")
    except: st.error("Lỗi: Kiệt chưa tạo file users.json kìa!")
    st.stop()

# --- 4. GIAO DIỆN CHÍNH ---
data = load_data()
with st.sidebar:
    st.success(f"👤 Sinh viên: {st.session_state.username}")
    if st.button("Đăng xuất"):
        st.session_state.logged_in = False
        st.rerun()
    st.divider()
    st.title("🎓 Menu")
    mode = st.radio("Chế độ:", ["Học từ vựng", "Trắc nghiệm", "Thống kê (Analytics) 📊"])
    
    if mode != "Thống kê (Analytics) 📊":
        level = st.selectbox("Chọn trình độ:", list(data.keys()))
        type_mode = st.selectbox("Kiểu học:", ["Anh -> Việt", "Việt -> Anh"])

# --- 5. LOGIC XỬ LÝ TỪNG CHẾ ĐỘ ---

# CHẾ ĐỘ 1: HỌC TỪ VỰNG (GÕ PHÍM)
if mode == "Học từ vựng ⌨️":
    st.header(f"⌨️ Luyện tập: {level}")
    vocab_list = data[level].get("vocabulary", [])
    
    # Thuật toán nhắc lại từ sai
    if st.session_state.retry_list and st.session_state.learn_count >= 3:
        word = st.session_state.retry_list.pop(0)
        st.session_state.learn_count = 0
        st.info("🔄 Nhắc lại từ bạn đã làm sai trước đó:")
    else:
        if not st.session_state.current_word:
            st.session_state.current_word = random.choice(vocab_list)
        word = st.session_state.current_word

    st.write(f"🔉 **Phiên âm:** `{word.get('ipa', 'N/A')}`")
    if st.button("🔊 Nghe phát âm"): play_audio(word['en'])

    if type_mode == "Anh -> Việt":
        st.subheader(f"Từ tiếng Anh: **{word['en']}**")
        ans = st.text_input("Nhập nghĩa tiếng Việt:", key="v_vn")
        correct = word['vn']
    else:
        st.subheader(f"Nghĩa tiếng Việt: **{word['vn']}**")
        ans = st.text_input("Nhập từ tiếng Anh:", key="v_en")
        correct = word['en']

    if st.button("Kiểm tra"):
        if ans.strip().lower() == correct.strip().lower():
            st.success("Chính xác! 🎉")
            log_action(st.session_state.username, word['en'], 1)
            st.session_state.learn_count += 1
            st.session_state.current_word = None
            st.rerun()
        else:
            st.error(f"Sai rồi! Đáp án: {correct}")
            log_action(st.session_state.username, word['en'], 0)
            if word not in st.session_state.retry_list:
                st.session_state.retry_list.append(word)

# CHẾ ĐỘ 2: TRẮC NGHIỆM
elif mode == "Trắc nghiệm 📝":
    st.header(f"📝 Trắc nghiệm: {level}")
    vocab_list = data[level].get("vocabulary", [])
    
    if not st.session_state.current_word:
        st.session_state.current_word = random.choice(vocab_list)
    word = st.session_state.current_word

    st.subheader(f"Từ: **{word['en']}** có nghĩa là gì?")
    options = [word['vn']] + word.get('distractors', [])[:3]
    random.shuffle(options)
    
    choice = st.radio("Chọn đáp án:", options, key="quiz_choice")
    
    if st.button("Xác nhận"):
        if choice == word['vn']:
            st.success("Quá chuẩn! 🎯")
            log_action(st.session_state.username, word['en'], 1)
            st.session_state.current_word = None
            st.rerun()
        else:
            st.error(f"Sai rồi! Đáp án đúng là: {word['vn']}")
            log_action(st.session_state.username, word['en'], 0)

# CHẾ ĐỘ 3: THỐNG KÊ (ANALYTICS)
elif mode == "Thống kê (Analytics) 📊":
    st.header(f"📊 Dashboard Học Tập - {st.session_state.username}")
    if os.path.exists("learning_logs.csv"):
        df = pd.read_csv("learning_logs.csv")
        user_df = df[df['user'] == st.session_state.username]
        
        if not user_df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Tổng số câu", len(user_df))
            c2.metric("Số câu Đúng", user_df['is_correct'].sum())
            c3.metric("Tỉ lệ Chính xác", f"{(user_df['is_correct'].sum()/len(user_df))*100:.1f}%")

            st.subheader("📈 Tiến độ theo thời gian")
            user_df['time'] = pd.to_datetime(user_df['time'])
            st.line_chart(user_df.set_index('time').resample('min').count()['word'])

            st.subheader("❌ Những từ bạn hay sai nhất")
            st.bar_chart(user_df[user_df['is_correct'] == 0]['word'].value_counts().head(10))
        else: st.info("Bạn chưa có dữ liệu học tập.")
    else: st.warning("Chưa có dữ liệu log.")
