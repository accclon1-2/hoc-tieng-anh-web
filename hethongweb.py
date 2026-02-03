import streamlit as st
import json
import random
from gtts import gTTS
import io
import streamlit_analytics

# 1. Cấu hình
PASSWORD_ADMIN = "uth2026" 

st.set_page_config(page_title="Học Tiếng Anh UTH", layout="centered")

def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Nếu data.json lỗi, trả về dữ liệu mẫu để app không sập
        return {"Lỗi": [{"en": "Check data.json", "vn": "Kiệt ơi, kiểm tra lại file data.json trên GitHub nhé!"}]}

data = load_data()

# 2. Theo dõi lượt truy cập
with streamlit_analytics.track():
    st.title("📚 Học Tiếng Anh + Phát Âm")

    # --- CỔNG QUẢN TRỊ (SIDEBAR) ---
    with st.sidebar:
        st.header("Admin Panel")
        pw = st.text_input("Mật khẩu xem thống kê:", type="password")
        
        if pw == PASSWORD_ADMIN:
            st.success("Xác thực thành công!")
            try:
                # Cách gọi an toàn: Kiểm tra xem hàm có tồn tại không trước khi gọi
                if hasattr(streamlit_analytics, 'show_results'):
                    streamlit_analytics.show_results()
                else:
                    st.warning("Thư viện thống kê đang bảo trì, Kiệt thử lại sau nhé!")
            except Exception as e:
                st.error(f"Lỗi hiển thị biểu đồ: {e}")
        elif pw != "":
            st.error("Sai mật khẩu!")

    # --- PHẦN HỌC TẬP ---
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
        
        # Nút phát âm
        if st.button("🔊 Nghe phát âm"):
            tts = gTTS(text=current_word['en'], lang='en')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            st.audio(fp, format='audio/mp3')

        with st.form(key='my_form', clear_on_submit=True):
            user_input = st.text_input("Gõ từ tiếng Anh:").strip().lower()
            if st.form_submit_button("Kiểm tra"):
                if user_input == current_word['en'].lower():
                    st.success("Chính xác! 🎉")
                    st.session_state.index += 1
                    st.session_state.score += 1
                    st.rerun()
                else:
                    st.error(f"Sai rồi! Đáp án: {current_word['en']}")
    else:
        st.balloons()
        st.success(f"Hoàn thành! Bạn đúng {st.session_state.score}/10 từ.")
        if st.button("Học tiếp lượt mới"):
            del st.session_state.pool
            st.rerun()