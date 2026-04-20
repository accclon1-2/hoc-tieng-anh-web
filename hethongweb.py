import streamlit as st
import json
import random
from gtts import gTTS
import io

st.set_page_config(page_title="UTH English Pro v3.2", layout="wide")

# --- CSS: CON TRỎ CHUỘT BÀN TAY ---
st.markdown("""
    <style>
    div[data-testid="stSelectbox"], div[data-testid="stRadio"] label, button { cursor: pointer !important; }
    </style>
    """, unsafe_allow_html=True)

# --- QUẢN LÝ DỮ LIỆU ---
@st.cache_data
def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except: return {}

data = load_data()

# --- KHỞI TẠO SESSION STATE (BỘ NHỚ TẠM) ---
if 'retry_list' not in st.session_state:
    st.session_state.retry_list = [] # Chứa các từ bị sai và số bước chờ
if 'current_word' not in st.session_state:
    st.session_state.current_word = None
if 'learn_count' not in st.session_state:
    st.session_state.learn_count = 0

def play_audio(text):
    tts = gTTS(text=text, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    st.audio(fp)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎓 UTH Learning")
    level = st.selectbox("Chọn trình độ:", list(data.keys()))
    mode = st.radio("Chế độ:", ["Học từ vựng (Gõ phím) ⌨️", "Trắc nghiệm", "Reading", "Writing"])
    type_mode = st.selectbox("Kiểu học:", ["Anh -> Việt", "Việt -> Anh"])

# --- CHẾ ĐỘ CHÍNH: HỌC TỪ VỰNG (GÕ PHÍM) ---
if mode == "Học từ vựng (Gõ phím) ⌨️":
    st.header(f"⌨️ Luyện tập: {level}")
    vocab_list = data[level].get("vocabulary", [])
    
    # Logic thuật toán nhắc lại: Sau 2-3 từ, nếu có từ sai thì ưu tiên hiện lại
    if st.session_state.retry_list and st.session_state.learn_count >= 3:
        word = st.session_state.retry_list.pop(0)
        st.session_state.learn_count = 0 # Reset đếm
        st.info("🔄 Nhắc lại từ bạn đã làm sai:")
    else:
        if not st.session_state.current_word:
            st.session_state.current_word = random.choice(vocab_list)
        word = st.session_state.current_word

    # Hiển thị IPA và Phát âm
    st.write(f"🔉 **Phiên âm:** `{word.get('ipa', 'N/A')}`")
    if st.button("🔊 Nghe phát âm"):
        play_audio(word['en'])

    # Giao diện câu hỏi
    if type_mode == "Anh -> Việt":
        st.subheader(f"Từ tiếng Anh: **{word['en']}**")
        answer = st.text_input("Nhập nghĩa tiếng Việt:", key="input_vn")
        correct_ans = word['vn']
    else:
        st.subheader(f"Nghĩa tiếng Việt: **{word['vn']}**")
        answer = st.text_input("Nhập từ tiếng Anh:", key="input_en")
        correct_ans = word['en']

    if st.button("Kiểm tra"):
        if answer.strip().lower() == correct_ans.strip().lower():
            st.success(f"Chính xác! 🎉")
            st.session_state.learn_count += 1
            st.session_state.current_word = None # Đổi từ mới
            st.rerun()
        else:
            st.error(f"Sai rồi! Đáp án đúng: {correct_ans}")
            st.info(f"💡 Ghi nhớ: {word['en']} - {word['vn']} {word.get('ipa', '')}")
            # Thêm vào hàng đợi nhắc lại sau 3 câu
            if word not in st.session_state.retry_list:
                st.session_state.retry_list.append(word)
