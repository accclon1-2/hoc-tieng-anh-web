import streamlit as st
import json
import random
from gtts import gTTS
import io

st.set_page_config(page_title="UTH English Pro v3.0", layout="wide")

# --- QUẢN LÝ DỮ LIỆU ---
@st.cache_data
def load_data():
    with open("data.json", "r", encoding="utf-8") as f:
        return json.load(f)

data = load_data()

# --- GIAO DIỆN MENU ---
with st.sidebar:
    st.title("🎓 UTH Learning")
    level = st.selectbox("Chọn trình độ:", list(data.keys()))
    mode = st.radio("Chế độ học:", ["Trắc nghiệm từ vựng", "Đọc hiểu (Reading)", "Luyện viết (Writing)"])

# --- CHẾ ĐỘ 1: TRẮC NGHIỆM (Giống Section I của đề) ---
if mode == "Trắc nghiệm từ vựng":
    st.header("📝 Section I: Vocabulary")
    vocab_list = data[level]["vocabulary"]
    word = random.choice(vocab_list)
    
    st.subheader(f"Nghĩa: {word['vn']}")
    options = word['distractors'] + [word['en']]
    random.shuffle(options)
    
    ans = st.radio("Chọn đáp án đúng:", options)
    if st.button("Nộp bài"):
        if ans == word['en']:
            st.success("Chính xác! 🎉")
        else:
            st.error(f"Sai rồi. Đáp án đúng là: {word['en']}")

# --- CHẾ ĐỘ 2: ĐỌC HIỂU (Giống Section II của đề) ---
elif mode == "Đọc hiểu (Reading)":
    reading_data = data[level]["reading"][0]
    st.header(f"📖 Section II: {reading_data['title']}")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info(reading_data['content']) # Hiển thị bài đọc
    
    with col2:
        for q in reading_data['questions']:
            st.write(q['q'])
            st.radio("Chọn:", q['options'], key=q['q'])

# --- CHẾ ĐỘ 3: LUYỆN VIẾT (Giống Section III của đề) ---
elif mode == "Luyện viết (Writing)":
    st.header("✍️ Section III: Unscramble the words")
    task = random.choice(data[level]["writing"])
    
    # Tự động trộn từ (Auto-Shuffle)
    shuffled_parts = random.sample(task['parts'], len(task['parts']))
    st.write("Sắp xếp các cụm từ sau: ", " / ".join(shuffled_parts))
    
    user_input = st.text_input("Gõ lại câu hoàn chỉnh:")
    if st.button("Kiểm tra"):
        if user_input.strip().lower() == task['original'].lower():
            st.success("Tuyệt vời! Bạn đã viết đúng cấu trúc.")
        else:
            st.error(f"Chưa đúng. Câu chuẩn là: {task['original']}")
