import streamlit as st
import json
import random
import os
import pandas as pd
from gtts import gTTS
import io
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="UTH English Pro v5.8", layout="wide")
st.markdown("<style>button { cursor: pointer !important; }</style>", unsafe_allow_html=True)

# --- 1. QUẢN LÝ ĐA MODULE (TÁCH FILE RIÊNG BIỆT) ---
@st.cache_data
def load_module_data(module_prefix):
    """
    Load 4 file riêng: {prefix}_vocab.json, {prefix}_quiz.json...
    Nếu không có file prefix, sẽ dùng file mặc định.
    """
    files = {
        "vocab": f"{module_prefix}_vocab.json",
        "quiz": f"{module_prefix}_quiz.json",
        "read": f"{module_prefix}_read.json",
        "write": f"{module_prefix}_write.json"
    }
    defaults = {"vocab": "vocab.json", "quiz": "quiz.json", "read": "reading.json", "write": "writing.json"}
    
    bundle = {}
    for k, v in files.items():
        # Ưu tiên file module riêng, nếu không có thì lấy file gốc
        target = v if os.path.exists(v) else defaults[k]
        if os.path.exists(target):
            try:
                with open(target, "r", encoding="utf-8") as f:
                    bundle[k] = json.load(f)
            except: bundle[k] = {}
        else: bundle[k] = {}
    return bundle

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp, format='audio/mp3')
    except: st.error("Lỗi âm thanh!")

def get_content(data_dict, target_level):
    if not data_dict: return None
    if target_level in data_dict: return data_dict[target_level]
    for key in data_dict.keys():
        if target_level.split('(')[0].strip() in key or key in target_level:
            return data_dict[key]
    return None

# --- 2. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = True
if 'username' not in st.session_state: st.session_state.username = "Kiệt_Admin"

# Khởi tạo các biến điều khiển
states = ['current_task', 'options', 'prev_mode', 'prev_level', 'prev_type', 'score_feedback', 'prev_module']
for s in states:
    if s not in st.session_state: st.session_state[s] = None

def reset_task():
    st.session_state.current_task = None
    st.session_state.options = None
    st.session_state.score_feedback = None

# --- 3. SIDEBAR (BỘ CHỌN MODULE) ---
with st.sidebar:
    st.title("🎓 UTH Pro v5.8")
    
    # Kiệt chọn "Pathways" để web gọi các file pathways_vocab.json...
    module_choice = st.selectbox("Bộ Sách:", ["Mặc định", "Pathways"])
    module_prefix = "pathways" if module_choice == "Pathways" else "default"
    
    bundle = load_module_data(module_prefix)
    
    st.divider()
    mode = st.radio("Chế độ:", ["Từ vựng", "Trắc nghiệm", "Reading", "Writing", "Thống kê"])
    
    # Lấy danh sách Level từ dữ liệu đã load
    all_keys = []
    for d in bundle.values(): all_keys.extend(list(d.keys()))
    unique_levels = sorted(list(set(all_keys))) if all_keys else ["Level_A1"]
    level = st.selectbox("Trình độ:", unique_levels)
    
    if (st.session_state.prev_mode != mode or 
        st.session_state.prev_level != level or 
        st.session_state.prev_module != module_choice):
        reset_task()
        st.session_state.prev_mode = mode
        st.session_state.prev_level = level
        st.session_state.prev_module = module_choice
        st.rerun()

# --- 4. LOGIC CHÍNH ---

# 4.1 TỪ VỰNG (ĐÃ FIX LỖI NHẢY TỪ)
if mode == "Từ vựng":
    type_mode = st.selectbox("Kiểu học:", ["Anh -> Việt", "Việt -> Anh"])
    if st.session_state.prev_type != type_mode:
        reset_task(); st.session_state.prev_type = type_mode; st.rerun()

    v_data = get_content(bundle['vocab'], level)
    v_list = v_data.get("vocabulary", []) if v_data else []
    
    if not v_list: st.warning("Không thấy dữ liệu từ vựng.")
    else:
        # SỬA LỖI: Sử dụng duy nhất current_task để cố định từ
        if st.session_state.current_task is None: 
            st.session_state.current_task = random.choice(v_list)
        
        w = st.session_state.current_task
        
        st.subheader(f"Từ vựng: {level}")
        col_info, col_audio = st.columns([3, 1])
        with col_info:
            st.markdown(f"**IPA:** `{w.get('ipa', 'N/A')}`")
        with col_audio:
            if st.button("🔊 Nghe"): play_audio(w['en'])
        
        q_label = f"Dịch: **{w['en']}**" if type_mode == "Anh -> Việt" else f"Nghĩa là: **{w['vn']}**"
        correct = w['vn'] if type_mode == "Anh -> Việt" else w['en']
        
        with st.form("vocab_form"):
            ans = st.text_input(q_label)
            if st.form_submit_button("Kiểm tra ✅"):
                if ans.strip().lower() == correct.strip().lower():
                    st.success("Chính xác!")
                    reset_task(); st.rerun()
                else: st.error(f"Sai rồi. Đáp án: {correct}")
        
        if st.button("Đổi từ khác"): reset_task(); st.rerun()

# 4.2 TRẮC NGHIỆM
elif mode == "Trắc nghiệm":
    q_list = get_content(bundle['quiz'], level)
    if not q_list: st.warning("Trống dữ liệu trắc nghiệm.")
    else:
        if st.session_state.current_task is None:
            st.session_state.current_task = random.choice(q_list)
            q = st.session_state.current_task
            opts = list(q['options'])
            random.shuffle(opts)
            st.session_state.options = opts
        
        q = st.session_state.current_task
        with st.form("quiz_form"):
            st.info(f"Điền vào chỗ trống: \n\n **{q['sentence']}**")
            choice = st.radio("Chọn đáp án:", st.session_state.options)
            if st.form_submit_button("Xác nhận"):
                if choice == q['answer']:
                    st.success("Đúng rồi!"); reset_task(); st.rerun()
                else: st.error("Thử lại nhé!")

# 4.3 READING
elif mode == "Reading":
    r_list = get_content(bundle['read'], level)
    if not r_list: st.warning("Trống bài đọc.")
    else:
        if st.session_state.current_task is None: st.session_state.current_task = random.choice(r_list)
        r = st.session_state.current_task
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**Nguồn:** {r.get('source', 'Pathways')}")
            st.text_area("Văn bản:", r['passage'], height=350)
        with col2:
            with st.form("reading_form"):
                u_ans = []
                for i, q_item in enumerate(r['questions']):
                    u_ans.append(st.radio(f"{i+1}. {q_item['q']}", q_item['options'], key=f"rd_{i}"))
                if st.form_submit_button("Nộp bài"):
                    correct = sum(1 for i, q_item in enumerate(r['questions']) if u_ans[i] == q_item['a'])
                    st.session_state.score_feedback = f"Kết quả: {correct}/{len(r['questions'])} câu đúng."
            if st.session_state.score_feedback:
                st.write(st.session_state.score_feedback)
                if st.button("Làm bài mới"): reset_task(); st.rerun()

# 4.4 WRITING
elif mode == "Writing":
    w_list = get_content(bundle['write'], level)
    if not w_list: st.warning("Trống dữ liệu viết.")
    else:
        if st.session_state.current_task is None: st.session_state.current_task = random.choice(w_list)
        t = st.session_state.current_task
        with st.form("write_form"):
            st.subheader(f"Đề bài: {t['prompt']}")
            user_w = st.text_input("Gõ câu hoàn chỉnh:")
            if st.form_submit_button("Kiểm tra"):
                if user_w.strip().lower().replace(".", "") == t['answer'].strip().lower().replace(".", ""):
                    st.success("Viết rất tốt!"); reset_task(); st.rerun()
                else: st.info(f"Gợi ý: {t['answer']}")
        if st.button("Đổi câu khác"): reset_task(); st.rerun()
