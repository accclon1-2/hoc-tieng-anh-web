import streamlit as st
import json
import random
from gtts import gTTS
import io

# 1. Cấu hình bảo mật
PASSWORD_ADMIN = "uth2026" 

st.set_page_config(page_title="Học Tiếng Anh UTH", layout="centered")

# 2. Bộ theo dõi lượt truy cập thủ công (Dành cho dân Data Science)
@st.cache_resource
def get_analytics_data():
    # Tạo một kho lưu trữ dữ liệu ảo trên server
    return {"views": 0, "correct_ans": 0, "wrong_ans": 0}

stats = get_analytics_data()

def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"Lỗi": [{"en": "Error", "vn": "Kiệt ơi, kiểm tra file data.json nhé!"}]}

data = load_data()

# Tăng lượt xem mỗi khi có người load trang
if 'visited' not in st.session_state:
    stats["views"] += 1
    st.session_state.visited = True

st.title("📚 Học Tiếng Anh + Phát Âm")

# --- THANH BÊN ADMIN (SIDEBAR) ---
with st.sidebar:
    st.header("Cổng Quản Trị")
    pw = st.text_input("Nhập mật khẩu Admin:", type="password")
    
    if pw == PASSWORD_ADMIN:
        st.success("Xác thực thành công!")
        st.metric("Tổng lượt truy cập", stats["views"])
        st.metric("Số câu đúng", stats["correct_ans"])
        st.metric("Số câu sai", stats["wrong_ans"])
        
        if st.button("Xóa lịch sử đếm"):
            stats["views"] = 0
            stats["correct_ans"] = 0
            stats["wrong_ans"] = 0
            st.rerun()
    elif pw != "":
        st.error("Sai mật khẩu!")

# --- PHẦN HỌC TẬP CHÍNH ---
category = st.selectbox("Chọn chủ đề:", list(data.keys()))

if 'pool' not in st.session_state or st.button("Làm mới lượt học 🔄"):
    words = data[category]
    random.shuffle(words)
    st.session_state.pool = words[:10]
    st.session_state.index = 0
    st.session_state.score = 0

if st.session_state.index < len(st.session_state.pool):
    current_word = st.session_state.pool[st.session_state.index]
    st.write(f"Tiến độ: {st.session_state.index + 1}/10")
    st.subheader(f"Nghĩa: {current_word['vn']}")
    
    if st.button("🔊 Nghe phát âm"):
        tts = gTTS(text=current_word['en'], lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp, format='audio/mp3')

    with st.form(key='study_form', clear_on_submit=True):
        user_input = st.text_input("Gõ từ tiếng Anh:").strip().lower()
        if st.form_submit_button("Kiểm tra"):
            if user_input == current_word['en'].lower():
                st.success("Chính xác! 🎉")
                stats["correct_ans"] += 1 # Ghi nhận vào server
                st.session_state.index += 1
                st.session_state.score += 1
                st.rerun()
            else:
                st.error(f"Sai rồi! Đáp án: {current_word['en']}")
                stats["wrong_ans"] += 1 # Ghi nhận vào server
else:
    st.balloons()
    st.success(f"Xong! Bạn đúng {st.session_state.score}/10")