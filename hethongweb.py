import streamlit as st
import json
import random
from gtts import gTTS
import io

st.set_page_config(page_title="UTH English Pro v3.1", layout="wide")

# --- CSS INJECTION: FIX CON TRỎ CHUỘT ---
# Đoạn này giúp biến con trỏ thành hình bàn tay khi lia vào các mục tương tác
st.markdown("""
    <style>
    /* Biến con trỏ thành bàn tay cho Selectbox, Radio, Button và các mục click được */
    div[data-testid="stSelectbox"], 
    div[data-testid="stRadio"] label, 
    button, 
    .stDownloadButton,
    div[role="button"] {
        cursor: pointer !important;
    }
    /* Hiệu ứng khi di chuột qua các lựa chọn trắc nghiệm */
    div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
        background-color: #f0f2f6;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- QUẢN LÝ DỮ LIỆU ---
@st.cache_data
def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

data = load_data()

# --- GIAO DIỆN MENU ---
with st.sidebar:
    st.title("🎓 UTH Learning")
    if data:
        level = st.selectbox("Chọn trình độ:", list(data.keys()))
        # THÊM CHẾ ĐỘ "HỌC TỪ MỚI" VÀO ĐẦU DANH SÁCH
        mode = st.radio("Chế độ học:", ["Học từ mới 📖", "Trắc nghiệm từ vựng", "Đọc hiểu (Reading)", "Luyện viết (Writing)"])
    else:
        st.warning("Dữ liệu đang trống!")

if data:
    vocab_list = data[level].get("vocabulary", [])

    # --- CHẾ ĐỘ 0: HỌC TỪ MỚI (FLASHCARDS) ---
    if mode == "Học từ mới 📖":
        st.header(f"📖 Danh sách từ vựng: {level}")
        if vocab_list:
            # Dùng session_state để lưu vị trí từ đang học
            if 'vocab_idx' not in st.session_state:
                st.session_state.vocab_idx = 0
            
            idx = st.session_state.vocab_idx
            word = vocab_list[idx]

            # Hiển thị Card từ vựng
            st.markdown(f"""
                <div style="background-color: white; padding: 30px; border-radius: 15px; border-left: 10px solid #FF4B4B; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
                    <h1 style="color: #1E1E1E; margin-bottom: 0;">{word['en']}</h1>
                    <p style="color: #666; font-size: 20px;">{word['vn']}</p>
                </div>
            """, unsafe_allow_html=True)

            # Nút điều hướng
            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                if st.button("⬅️ Trước"):
                    st.session_state.vocab_idx = max(0, idx - 1)
                    st.rerun()
            with col2:
                if st.button("Sau ➡️"):
                    st.session_state.vocab_idx = min(len(vocab_list) - 1, idx + 1)
                    st.rerun()
            
            st.write(f"Tiến độ: {idx + 1} / {len(vocab_list)}")
        else:
            st.info("Chưa có từ vựng để học.")

    # --- CHẾ ĐỘ 1: TRẮC NGHIỆM ---
    elif mode == "Trắc nghiệm từ vựng":
        st.header("📝 Trắc nghiệm nhanh")
        if vocab_list:
            # Chọn ngẫu nhiên một từ để kiểm tra
            word = random.choice(vocab_list)
            st.subheader(f"Nghĩa của từ là: {word['vn']}")
            
            options = word.get('distractors', []) + [word['en']]
            random.shuffle(options)
            
            ans = st.radio("Chọn đáp án tiếng Anh đúng:", options)
            if st.button("Nộp bài"):
                if ans == word['en']:
                    st.success("Chính xác! 🎉")
                    st.balloons()
                else:
                    st.error(f"Sai rồi. Đáp án đúng là: {word['en']}")
    
    # ... (Các chế độ khác giữ nguyên) ...
