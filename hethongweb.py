import streamlit as st
import json
import random
from gtts import gTTS
import io
import streamlit_analytics

# 1. Cấu hình bảo mật (Kiệt có thể đổi mật khẩu ở đây)
PASSWORD_ADMIN = "uth2026" 

st.set_page_config(page_title="Học Tiếng Anh UTH - Admin Mode", layout="centered")

def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"Lỗi": [{"en": "No data", "vn": "Chưa có dữ liệu"}]}

data = load_data()

# 2. Bọc toàn bộ ứng dụng bằng bộ theo dõi thống kê
with streamlit_analytics.track():
    st.title("📚 Học Tiếng Anh + Phát Âm")

    # --- THANH BÊN (SIDEBAR) CHO ADMIN ---
    st.sidebar.title("Cổng Quản Trị")
    pw = st.sidebar.text_input("Nhập mật khẩu để xem thống kê:", type="password")
    
    if pw == PASSWORD_ADMIN:
        st.sidebar.success("Xác thực thành công!")
        st.header("📊 Thống kê lượt truy cập")
        # Hiển thị bảng điều khiển thống kê ngay tại đây
        streamlit_analytics.show_results()
        st.markdown("---") # Đường kẻ ngăn cách phần quản trị và phần học
    elif pw != "":
        st.sidebar.error("Sai mật khẩu rồi Kiệt ơi!")

    # --- PHẦN HỌC TIẾNG ANH CHÍNH ---
    category = st.selectbox("Chọn chủ đề để bắt đầu:", list(data.keys()))

    if 'pool' not in st.session_state or st.button("Làm mới lượt học 🔄"):
        words = data[category]
        random.shuffle(words)
        st.session_state.pool = words[:10]
        st.session_state.index = 0
        st.session_state.score = 0

    if st.session_state.index < len(st.session_state.pool):
        current_word = st.session_state.pool[st.session_state.index]
        
        st.info(f"Từ số {st.session_state.index + 1}/10")
        st.subheader(f"Nghĩa: {current_word['vn']}")
        
        # Nút phát âm
        if st.button("🔊 Nghe phát âm"):
            tts = gTTS(text=current_word['en'], lang='en')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            st.audio(fp, format='audio/mp3')

        with st.form(key='study_form', clear_on_submit=True):
            user_input = st.text_input("Gõ từ tiếng Anh vào đây:").strip().lower()
            submit = st.form_submit_button(label='Kiểm tra đáp án')

        if submit:
            if user_input == current_word['en'].lower():
                st.success(f"Quá chuẩn! 🎉 Đáp án: {current_word['en']}")
                st.session_state.index += 1
                st.session_state.score += 1
                # Tự động chuyển từ sau 1 giây (Streamlit sẽ rerun)
                st.rerun()
            else:
                st.error(f"Tiếc quá! Đáp án đúng phải là: **{current_word['en']}**")
    else:
        st.balloons()
        st.success(f"Chúc mừng Nguyễn Võ Tuấn Kiệt! Bạn đã hoàn thành lượt học với số điểm: {st.session_state.score}/10")
        if st.button("Học tiếp lượt mới"):
            del st.session_state.pool
            st.rerun()