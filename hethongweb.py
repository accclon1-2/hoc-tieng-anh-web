import streamlit as st
import json
import random

st.set_page_config(page_title="UTH English Pro v3.0", layout="wide")

# --- QUẢN LÝ DỮ LIỆU ---
@st.cache_data
def load_data():
    # Kiệt chú ý sửa tên file ở đây cho khớp với GitHub nhé
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Không tìm thấy file dữ liệu data.json!")
        return {}

data = load_data()

# --- GIAO DIỆN MENU ---
with st.sidebar:
    st.title("🎓 UTH Learning")
    if data:
        level = st.selectbox("Chọn trình độ:", list(data.keys()))
        mode = st.radio("Chế độ học:", ["Trắc nghiệm từ vựng", "Đọc hiểu (Reading)", "Luyện viết (Writing)"])
    else:
        st.warning("Dữ liệu đang trống!")

# --- LOGIC XỬ LÝ CHẾ ĐỘ ---
if data:
    # CHẾ ĐỘ 1: TRẮC NGHIỆM
    if mode == "Trắc nghiệm từ vựng":
        vocab_list = data[level].get("vocabulary", [])
        if vocab_list:
            word = random.choice(vocab_list)
            st.header(f"📝 Level: {level}")
            st.subheader(f"Nghĩa: {word['vn']}")
            
            # Trộn đáp án (Lấy từ vựng thật đã cào)
            options = word.get('distractors', []) + [word['en']]
            random.shuffle(options)
            
            ans = st.radio("Chọn đáp án đúng:", options)
            if st.button("Nộp bài"):
                if ans == word['en']:
                    st.success("Chính xác! 🎉")
                    st.balloons()
                else:
                    st.error(f"Sai rồi. Đáp án đúng là: {word['en']}")
        else:
            st.info("Level này chưa có từ vựng.")

    # CHẾ ĐỘ 2: ĐỌC HIỂU
    elif mode == "Đọc hiểu (Reading)":
        reading_list = data[level].get("reading", [])
        if reading_list:
            reading_data = reading_list[0]
            st.header(f"📖 {reading_data['title']}")
            st.info(reading_data['content'])
            # ... (Tiếp tục logic câu hỏi) ...
        else:
            st.warning("⚠️ Chế độ Reading cho trình độ này đang được cập nhật!")

    # CHẾ ĐỘ 3: LUYỆN VIẾT
    elif mode == "Luyện viết (Writing)":
        writing_list = data[level].get("writing", [])
        if writing_list:
            task = random.choice(writing_list)
            # ... (Tiếp tục logic trộn từ) ...
        else:
            st.warning("⚠️ Chế độ Writing cho trình độ này đang được cập nhật!")
