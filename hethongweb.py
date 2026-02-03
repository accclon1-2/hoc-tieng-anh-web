import streamlit as st
import json
import random
from gtts import gTTS
import io
import streamlit_analytics2 as streamlit_analytics # Dùng bản số 2 ổn định hơn

PASSWORD_ADMIN = "uth2026" 

st.set_page_config(page_title="Học Tiếng Anh UTH", layout="centered")

def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            # Kiểm tra nếu file JSON rỗng
            if not data:
                return {"Lỗi": [{"en": "Data Empty", "vn": "File JSON đang rỗng"}]}
            return data
    except Exception:
        return {"Lỗi": [{"en": "File Error", "vn": "Không đọc được data.json"}]}

data = load_data()

# Bắt đầu theo dõi lượt truy cập
with streamlit_analytics.track():
    st.title("📚 Học Tiếng Anh + Phát Âm")

    # Cổng quản trị nằm gọn trong Sidebar
    with st.sidebar:
        st.header("Cổng Quản Trị")
        pw = st.text_input("Mật khẩu Admin:", type="password")
        if pw == PASSWORD_ADMIN:
            st.success("Chào Kiệt! Đây là thống kê:")
            # Sử dụng cách gọi an toàn hơn
            try:
                streamlit_analytics.show_results()
            except:
                st.warning("Không thể hiển thị biểu đồ lúc này.")

    # Giao diện học tập
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

        with st.form(key='my_form', clear_on_submit=True):
            user_input = st.text_input("Gõ từ tiếng Anh:").strip().lower()
            if st.form_submit_button("Kiểm tra"):
                if user_input == current_word['en'].lower():
                    st.success("Chính xác!")
                    st.session_state.index += 1
                    st.session_state.score += 1
                    st.rerun()
                else:
                    st.error(f"Sai rồi! Đáp án là: {current_word['en']}")
    else:
        st.balloons()
        st.success(f"Xong! Bạn đúng {st.session_state.score}/10")