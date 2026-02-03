import streamlit as st
import json
import random
from gtts import gTTS
import io
import pandas as pd

# 1. CẤU HÌNH TRANG & CSS CUSTOM (Làm cho app đẹp hơn)
st.set_page_config(page_title="UTH English Pro", layout="centered", page_icon="🎓")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #007bff; color: white; }
    .word-card { background-color: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; margin-bottom: 20px; border-left: 5px solid #007bff; }
    .vn-meaning { color: #1f2937; font-size: 28px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. DỮ LIỆU & ANALYTICS THỦ CÔNG
PASSWORD_ADMIN = "uth2026"

@st.cache_resource
def get_stats():
    return {"views": 0, "correct": 0, "wrong": 0, "history": []}

stats = get_stats()

def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"Lỗi": [{"en": "Error", "vn": "Kiểm tra file data.json"}]}

data = load_data()

# 3. GIAO DIỆN CHÍNH
st.title("🚀 UTH English Pro v2.0")

# --- SIDEBAR QUẢN TRỊ ---
with st.sidebar:
    st.image("https://img.icons8.com/clouds/100/000000/learning.png")
    st.header("Admin Center")
    pw = st.text_input("🔑 Mật mã:", type="password")
    if pw == PASSWORD_ADMIN:
        st.success("Xin chào Kiệt!")
        st.metric("Tổng lượt xem", stats["views"])
        if stats["correct"] + stats["wrong"] > 0:
            acc = (stats["correct"] / (stats["correct"] + stats["wrong"])) * 100
            st.metric("Tỷ lệ đúng", f"{acc:.1f}%")
        
        # Biểu đồ phân tích (AI/Data Science vibe)
        if stats["history"]:
            st.write("Biểu đồ hiệu suất:")
            df_stats = pd.DataFrame(stats["history"], columns=["Kết quả"])
            st.bar_chart(df_stats["Kết quả"].value_counts())
    
# --- LOGIC HỌC TẬP ---
if 'visited' not in st.session_state:
    stats["views"] += 1
    st.session_state.visited = True

col1, col2 = st.columns([3, 1])
with col1:
    category = st.selectbox("Chọn chủ đề học:", list(data.keys()))
with col2:
    if st.button("🔄 Đổi từ"):
        del st.session_state.pool
        st.rerun()

if 'pool' not in st.session_state:
    words = data[category]
    random.shuffle(words)
    st.session_state.pool = words[:10]
    st.session_state.index = 0
    st.session_state.score = 0

# Giao diện học tập chính
if st.session_state.index < len(st.session_state.pool):
    curr = st.session_state.pool[st.session_state.index]
    
    # Progress bar
    progress = (st.session_state.index) / 10
    st.progress(progress)
    st.caption(f"Đang hoàn thành: {st.session_state.index}/10 từ")

    # Hiển thị Card từ vựng
    st.markdown(f"""
        <div class="word-card">
            <div style="color: #6b7280; font-size: 14px;">NGHĨA TIẾNG VIỆT</div>
            <div class="vn-meaning">{curr['vn']}</div>
        </div>
        """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔊 Phát âm"):
            tts = gTTS(text=curr['en'], lang='en')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            st.audio(fp, format='audio/mp3')
    with c2:
        if st.button("💡 Gợi ý"):
            st.warning(f"Từ này bắt đầu bằng chữ: **{curr['en'][0].upper()}**")

    with st.form(key='input_form', clear_on_submit=True):
        ans = st.text_input("Nhập từ tiếng Anh của bạn:").strip().lower()
        if st.form_submit_button("KIỂM TRA"):
            if ans == curr['en'].lower():
                st.balloons()
                st.success(f"Chính xác! ✨ Đáp án: {curr['en']}")
                stats["correct"] += 1
                stats["history"].append("Đúng")
                st.session_state.index += 1
                st.session_state.score += 1
                st.rerun()
            else:
                st.error(f"Sai mất rồi! Đáp án đúng là: {curr['en']}")
                stats["wrong"] += 1
                stats["history"].append("Sai")
else:
    st.snow()
    st.success(f"🎊 Chúc mừng! Bạn đạt {st.session_state.score}/10 điểm.")
    if st.button("Học lượt mới ngay"):
        del st.session_state.pool
        st.rerun()