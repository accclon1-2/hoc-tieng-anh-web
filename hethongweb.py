import streamlit as st
import json
import random
from gtts import gTTS
import io
import os
import pandas as pd
from datetime import datetime

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="UTH English Pro v3.4 - Data Analytics", layout="wide")
DEV_MODE = True  # Kiệt để True để tự đăng nhập khi đang code, False khi đưa cho bạn bè dùng

# --- CSS: FIX CON TRỎ CHUỘT ---
st.markdown("<style>div[data-testid='stSelectbox'], div[data-testid='stRadio'] label, button { cursor: pointer !important; }</style>", unsafe_allow_html=True)

# --- QUẢN LÝ DỮ LIỆU ---
@st.cache_data
def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except: return {}

def log_action(username, word_en, result):
    log_file = "learning_logs.csv"
    new_entry = {
        "time": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "user": [username],
        "word": [word_en],
        "is_correct": [result]
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

# --- KHỞI TẠO TRẠNG THÁI ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = DEV_MODE # Tự động đăng nhập nếu ở chế độ Dev
    st.session_state.username = "kiet_admin" if DEV_MODE else ""

if 'current_word' not in st.session_state: st.session_state.current_word = None
if 'learn_count' not in st.session_state: st.session_state.learn_count = 0
if 'retry_list' not in st.session_state: st.session_state.retry_list = []

# --- 1. GIAO DIỆN ĐĂNG NHẬP ---
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
            else: st.error("Sai thông tin!")
    except: st.error("Thiếu file users.json!")
    st.stop()

# --- 2. GIAO DIỆN CHÍNH ---
data = load_data()
with st.sidebar:
    st.success(f"👤: {st.session_state.username}")
    if st.button("Đăng xuất"):
        st.session_state.logged_in = False
        st.rerun()
    st.divider()
    # DANH SÁCH CHẾ ĐỘ (CÓ THÊM ANALYTICS)
    mode = st.radio("Chế độ học:", ["Học từ vựng ⌨️", "Trắc nghiệm 📝", "Thống kê (Analytics) 📊"])
    
    if mode != "Thống kê (Analytics) 📊":
        level = st.selectbox("Chọn trình độ:", list(data.keys()))
        type_mode = st.selectbox("Kiểu học:", ["Anh -> Việt", "Việt -> Anh"])

# --- 3. XỬ LÝ CÁC CHẾ ĐỘ ---
if mode == "Thống kê (Analytics) 📊":
    st.header(f"📊 Dashboard Phân Tích của {st.session_state.username}")
    
    if os.path.exists("learning_logs.csv"):
        df = pd.read_csv("learning_logs.csv")
        user_df = df[df['user'] == st.session_state.username]
        
        if not user_df.empty:
            # Hiển thị chỉ số nhanh
            c1, c2, c3 = st.columns(3)
            total = len(user_df)
            correct = user_df['is_correct'].sum()
            c1.metric("Tổng số câu", total)
            c2.metric("Số câu Đúng ✅", correct)
            c3.metric("Tỉ lệ chính xác", f"{(correct/total)*100:.1f}%")

            # Biểu đồ cột: Top từ hay sai
            st.subheader("❌ Những từ bạn hay bị sai nhất")
            wrong_df = user_df[user_df['is_correct'] == 0]
            if not wrong_df.empty:
                st.bar_chart(wrong_df['word'].value_counts().head(10))
            else:
                st.success("Bạn chưa sai từ nào!")
            
            # Biểu đồ đường: Tiến độ theo thời gian
            st.subheader("📈 Lịch sử học tập")
            user_df['time'] = pd.to_datetime(user_df['time'])
            timeline = user_df.set_index('time').resample('h').count() # Gom nhóm theo giờ
            st.line_chart(timeline['word'])
        else:
            st.info("Chưa có dữ liệu. Hãy vào học để hệ thống thu thập nhé!")
    else:
        st.warning("Chưa có file learning_logs.csv. Hãy làm bài để tạo file!")

elif mode == "Học từ vựng (Gõ phím) ⌨️":
    st.header(f"⌨️ Luyện tập: {level}")
    vocab_list = data[level].get("vocabulary", [])
    
    # Logic nhắc lại từ sai
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

    # Input & Kiểm tra
    if type_mode == "Anh -> Việt":
        st.subheader(f"Từ: **{word['en']}**")
        ans = st.text_input("Nghĩa Việt:", key="in_vn")
        correct = word['vn']
    else:
        st.subheader(f"Nghĩa: **{word['vn']}**")
        ans = st.text_input("Từ Anh:", key="in_en")
        correct = word['en']

    if st.button("Kiểm tra"):
        if ans.strip().lower() == correct.strip().lower():
            st.success("Đúng rồi! 🎉")
            log_action(st.session_state.username, word['en'], 1)
            st.session_state.learn_count += 1
            st.session_state.current_word = None
            st.rerun()
        else:
            st.error(f"Sai! Đáp án: {correct}")
            log_action(st.session_state.username, word['en'], 0)
            if word not in st.session_state.retry_list:
                st.session_state.retry_list.append(word)

elif mode == "Trắc nghiệm 📝":
    st.write("Chế độ này Kiệt tự ráp thêm nhé!")
