import streamlit as st
import json
import random
from gtts import gTTS
import io
import os
import pandas as pd
from datetime import datetime

# --- 1. CẤU HÌNH & CSS ---
st.set_page_config(page_title="UTH English Pro v4.0", layout="wide")
st.markdown("<style>button { cursor: pointer !important; } .stTextInput input { font-size: 1.2rem; }</style>", unsafe_allow_html=True)

# --- 2. QUẢN LÝ DỮ LIỆU ---
@st.cache_data
def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Lỗi file data.json: {e}")
        return {}

def log_action(user, task, result, mode):
    try:
        log_file = "learning_logs.csv"
        df = pd.DataFrame([{
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": user, "task": task, "is_correct": result, "mode": mode
        }])
        df.to_csv(log_file, mode='a', header=not os.path.exists(log_file), index=False, encoding="utf-8-sig")
    except PermissionError:
        st.warning("⚠️ Hãy đóng file learning_logs.csv trong Excel để lưu kết quả!")
    except: pass

# --- 3. KHỞI TẠO BIẾN TẠM (SESSION STATE) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = True
    st.session_state.username = "Hi"

if 'word_index' not in st.session_state: st.session_state.word_index = 0
if 'current_word' not in st.session_state: st.session_state.current_word = None

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp)
    except: st.error("Lỗi âm thanh!")

# --- 4. GIAO DIỆN ---
data = load_data()
with st.sidebar:
    st.title("🎓 UTH Pro")
    mode = st.radio("Chế độ:", ["Từ vựng", "Trắc nghiệm", "Reading", "Writing", "Thống kê"])
    level = st.selectbox("Trình độ:", list(data.keys()))
    if mode == "Từ vựng":
        type_mode = st.selectbox("Kiểu học:", ["Anh -> Việt", "Việt -> Anh"])

# --- 5. LOGIC PHẦN TỪ VỰNG (ĐÃ TỐI ƯU 100%) ---
if mode == "Từ vựng":
    st.header(f"Luyện tập: {level}")
    vocab = data[level].get("vocabulary", [])
    
    if not vocab:
        st.warning("Level này trống từ vựng!")
    else:
        # CHỌN TỪ: Nếu chưa có từ hoặc vừa làm xong câu trước
        if st.session_state.current_word is None:
            st.session_state.current_word = random.choice(vocab)
            st.session_state.word_index += 1 # Dùng để đổi Key, tránh trùng
        
        w = st.session_state.current_word
        
        # UI HIỂN THỊ
        col1, col2 = st.columns([1, 3])
        with col1:
            st.write(f"🔉 **IPA:** `{w.get('ipa', 'N/A')}`")
            if st.button("🔊 Nghe"): play_audio(w['en'])
        
        with col2:
            # Tạo Key cực kỳ an toàn bằng cách kết hợp Index và ID từ
            input_key = f"input_{st.session_state.word_index}_{w['en'][:3]}"
            
            if type_mode == "Anh -> Việt":
                st.subheader(f"Dịch từ: :blue[{w['en']}]")
                ans = st.text_input("Nhập nghĩa Việt:", key=input_key)
                correct = w['vn']
            else:
                st.subheader(f"Dịch nghĩa: :green[{w['vn']}]")
                ans = st.text_input("Nhập từ Anh:", key=input_key)
                correct = w['en']

        # NÚT BẤM
        c_btn1, c_btn2 = st.columns(2)
        if c_btn1.button("Kiểm tra", use_container_width=True):
            if ans.strip().lower() == correct.strip().lower():
                st.balloons()
                st.success("Chuẩn cơm mẹ nấu!")
                log_action(st.session_state.username, w['en'], 1, "Vocab")
                st.session_state.current_word = None # Để vòng lặp sau bốc từ mới
                st.rerun()
            else:
                st.error(f"Sai rồi! Đáp án là: **{correct}**")
                log_action(st.session_state.username, w['en'], 0, "Vocab")
        
        if c_btn2.button("Đổi từ khác", use_container_width=True):
            st.session_state.current_word = None
            st.rerun()

# --- CÁC CHẾ ĐỘ KHÁC (GIỮ NGUYÊN HOẶC TỰ ĐỘNG GEN) ---
elif mode == "Trắc nghiệm":
    st.header("Trắc nghiệm")
    vocab = data[level].get("vocabulary", [])
    if vocab:
        if st.session_state.current_word is None: st.session_state.current_word = random.choice(vocab)
        q = st.session_state.current_word
        st.subheader(f"Nghĩa của **{q['en']}** là gì?")
        # Tự tạo distractors từ nghĩa Việt của các từ khác
        others = [v['vn'] for v in vocab if v['vn'] != q['vn']]
        opts = random.sample(others, min(len(others), 3)) + [q['vn']]
        random.shuffle(opts)
        choice = st.radio("Chọn:", opts, key=f"q_{st.session_state.word_index}")
        if st.button("Xác nhận"):
            if choice == q['vn']:
                st.success("Đúng!"); log_action(st.session_state.username, q['en'], 1, "Quiz")
                st.session_state.current_word = None; st.rerun()
            else: st.error("Sai rồi!"); log_action(st.session_state.username, q['en'], 0, "Quiz")

elif mode == "Reading":
    st.info("💡 Bài đọc lấy từ data.json...")
    tasks = data[level].get("reading", [])
    if tasks: st.write(random.choice(tasks)['passage'])
    else: st.warning("Trống dữ liệu Reading.")

elif mode == "Writing":
    st.info("Luyện viết câu...")
    tasks = data[level].get("writing", [])
    if tasks:
        t = random.choice(tasks)
        st.write(f"Dịch: {t['vn_sentence']}")
        if st.button("Xem đáp án"): st.success(t['en_sentence'])
    else: st.warning("Trống dữ liệu Writing.")

elif mode == "Thống kê":
    st.header("Kết quả của bạn")
    if os.path.exists("learning_logs.csv"):
        df = pd.read_csv("learning_logs.csv")
        st.dataframe(df.tail(10))
        st.bar_chart(df['is_correct'].value_counts())
