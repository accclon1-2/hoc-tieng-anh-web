import streamlit as st
import json
import random
import os
import pandas as pd
from gtts import gTTS
import io
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="UTH English Pro v6.0", layout="wide")
st.markdown("<style>button { cursor: pointer !important; }</style>", unsafe_allow_html=True)

# --- 1. QUẢN LÝ DỮ LIỆU ---
@st.cache_data
def load_all_data(module_prefix):
    files = {"vocab": f"{module_prefix}_vocab.json", "quiz": f"{module_prefix}_quiz.json", 
             "read": f"{module_prefix}_read.json", "write": f"{module_prefix}_write.json"}
    defaults = {"vocab": "vocab.json", "quiz": "quiz.json", "read": "reading.json", "write": "writing.json"}
    bundle = {}
    for k, v in files.items():
        target = v if os.path.exists(v) else defaults[k]
        if os.path.exists(target):
            try:
                with open(target, "r", encoding="utf-8") as f: bundle[k] = json.load(f)
            except: bundle[k] = {}
        else: bundle[k] = {}
    return bundle

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en'); fp = io.BytesIO()
        tts.write_to_fp(fp); st.audio(fp, format='audio/mp3')
    except: st.error("Lỗi âm thanh!")

# --- 2. THUẬT TOÁN SRS (SPACED REPETITION SYSTEM) ---
def init_srs():
    if 'srs_retry_pool' not in st.session_state:
        st.session_state.srs_retry_pool = {} # {word_en: {'count': 0, 'data': {}}}
    if 'srs_spaced_pool' not in st.session_state:
        st.session_state.srs_spaced_pool = [] # List of {'reappear_at': int, 'data': {}}
    if 'srs_fail_streak' not in st.session_state:
        st.session_state.srs_fail_streak = [] # Danh sách từ bị sai liên tiếp
    if 'srs_total_seen' not in st.session_state:
        st.session_state.srs_total_seen = 0 # Tổng số từ đã làm qua
    if 'srs_last_retry_at' not in st.session_state:
        st.session_state.srs_last_retry_at = 0

def pick_next_word(vocab_list):
    init_srs()
    total = st.session_state.srs_total_seen
    
    # 1. Cơ chế Reset Chuỗi: Sai liên tiếp 5 từ
    if len(st.session_state.srs_fail_streak) >= 5:
        first_fail = st.session_state.srs_fail_streak[0]
        st.session_state.srs_fail_streak = [] # Reset chuỗi
        if first_fail['en'] in st.session_state.srs_retry_pool:
            st.session_state.srs_retry_pool[first_fail['en']]['count'] = 0 # Reset số lần đúng
        return first_fail

    # 2. Cơ chế 1/10: Trong 10 từ phải có ít nhất 1 từ sai quay lại
    if (total - st.session_state.srs_last_retry_at >= 9) and st.session_state.srs_retry_pool:
        word_en = random.choice(list(st.session_state.srs_retry_pool.keys()))
        st.session_state.srs_last_retry_at = total
        return st.session_state.srs_retry_pool[word_en]['data']

    # 3. Cơ chế Spaced Repetition (Sau 20 từ)
    for i, item in enumerate(st.session_state.srs_spaced_pool):
        if total >= item['reappear_at']:
            word_data = st.session_state.srs_spaced_pool.pop(i)
            return word_data['data']

    # 4. Ưu tiên từ trong hàng đợi sai (30% tỉ lệ xuất hiện ngẫu nhiên)
    if st.session_state.srs_retry_pool and random.random() < 0.3:
        word_en = random.choice(list(st.session_state.srs_retry_pool.keys()))
        return st.session_state.srs_retry_pool[word_en]['data']

    # 5. Mặc định: Bốc từ mới
    return random.choice(vocab_list)

# --- 3. SESSION STATE QUẢN LÝ APP ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = True
if 'current_task' not in st.session_state: st.session_state.current_task = None
if 'prev_mode' not in st.session_state: st.session_state.prev_mode = None
if 'prev_level' not in st.session_state: st.session_state.prev_level = None

def reset_task():
    st.session_state.current_task = None
    st.session_state.score_feedback = None

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🎓 UTH Pro v6.0")
    module_choice = st.selectbox("Bộ Sách:", ["Mặc định", "Pathways"])
    module_prefix = "pathways" if module_choice == "Pathways" else "default"
    bundle = load_all_data(module_prefix)
    
    st.divider()
    mode = st.radio("Chế độ:", ["Từ vựng", "Trắc nghiệm", "Reading", "Writing"])
    
    all_keys = []
    for d in bundle.values(): all_keys.extend(list(d.keys()))
    unique_levels = sorted(list(set(all_keys))) if all_keys else ["Level_A1"]
    level = st.selectbox("Trình độ:", unique_levels)
    
    if st.session_state.prev_mode != mode or st.session_state.prev_level != level:
        reset_task(); st.session_state.prev_mode = mode; st.session_state.prev_level = level; st.rerun()

# --- 5. LOGIC CHẾ ĐỘ TỪ VỰNG (THUẬT TOÁN SRS) ---
if mode == "Từ vựng":
    v_data = bundle['vocab'].get(level, {})
    v_list = v_data.get("vocabulary", []) if v_data else []
    
    if not v_list: st.warning("Trống từ vựng.")
    else:
        if st.session_state.current_task is None: 
            st.session_state.current_task = pick_next_word(v_list)
        
        w = st.session_state.current_task
        st.subheader(f"Học thông minh: {level}")
        
        col_info, col_audio = st.columns([3, 1])
        with col_info: st.markdown(f"**IPA:** `{w.get('ipa', 'N/A')}`")
        with col_audio:
            if st.button("🔊 Nghe"): play_audio(w['en'])
        
        with st.form("vocab_form"):
            ans = st.text_input(f"Dịch từ: **{w['en']}**")
            if st.form_submit_button("Kiểm tra"):
                st.session_state.srs_total_seen += 1
                if ans.strip().lower() == w['vn'].strip().lower():
                    st.success("Đúng rồi!")
                    st.session_state.srs_fail_streak = [] # Reset chuỗi sai liên tiếp
                    
                    # Xử lý Logic 2-Hit
                    if w['en'] in st.session_state.srs_retry_pool:
                        st.session_state.srs_retry_pool[w['en']]['count'] += 1
                        if st.session_state.srs_retry_pool[w['en']]['count'] >= 2:
                            # Đã đúng 2 lần -> Cho vào hàng đợi chờ 20 từ
                            st.session_state.srs_spaced_pool.append({
                                'reappear_at': st.session_state.srs_total_seen + 20,
                                'data': w
                            })
                            del st.session_state.srs_retry_pool[w['en']]
                    
                    reset_task(); st.rerun()
                else:
                    st.error(f"Sai rồi! Đáp án: {w['vn']}")
                    # Thêm vào hàng đợi sai và chuỗi sai liên tiếp
                    st.session_state.srs_retry_pool[w['en']] = {'count': 0, 'data': w}
                    st.session_state.srs_fail_streak.append(w)
                    # Không reset_task ngay để người dùng nhìn đáp án

        if st.button("Tiếp tục"): reset_task(); st.rerun()

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
