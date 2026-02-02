import streamlit as st
import json
import random

# Thiết lập giao diện di động
st.set_page_config(page_title="Học Tiếng Anh UTH", layout="centered")

def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"Lỗi": [{"en": "No data", "vn": "Chưa có dữ liệu"}]}

data = load_data()

st.title("📚 Học Tiếng Anh v1.0")

# Chọn chủ đề
category = st.selectbox("Chọn chủ đề:", list(data.keys()))

if 'pool' not in st.session_state or st.button("Làm mới lượt học"):
    words = data[category]
    random.shuffle(words)
    st.session_state.pool = words[:10]  # Lấy 10 từ
    st.session_state.index = 0
    st.session_state.score = 0

if st.session_state.index < len(st.session_state.pool):
    current_word = st.session_state.pool[st.session_state.index]
    
    st.subheader(f"Nghĩa: {current_word['vn']}")
    
    # Form nhập liệu
    with st.form(key='my_form', clear_on_submit=True):
        user_input = st.text_input("Nhập từ tiếng Anh:").strip().lower()
        submit_button = st.form_submit_button(label='Kiểm tra')

    if submit_button:
        if user_input == current_word['en'].lower():
            st.success("Chính xác! 🎉")
            st.session_state.index += 1
            st.session_state.score += 1
            st.rerun()
        else:
            st.error(f"Sai rồi! Đáp án đúng là: {current_word['en']}")
            # Bạn có thể thêm logic lưu từ sai vào đây
else:
    st.balloons()
    st.success(f"Hoàn thành! Bạn đúng {st.session_state.score}/10 từ.")