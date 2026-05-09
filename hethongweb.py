import streamlit as st
import json
import random
import os
import pandas as pd
from gtts import gTTS
import io
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="UTH English Pro v6.1", layout="wide")
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

def get_content(data_dict, target_level):
    if not data_dict: return None
    if target_level in data_dict: return data_dict[target_level]
    for key in data_dict.keys():
        if target_level.split('(')[0].strip() in key or key in target_level:
            return data_dict[key]
    return None

# --- 2. THUẬT TOÁN SRS (SPACED REPETITION SYSTEM) ---
def init_srs():
    if 'srs_retry_pool' not in st.session_state: st.session_state.srs_retry_pool = {}
    if 'srs_spaced_pool' not in st.session_state: st.session_state.srs_spaced_pool = []
    if 'srs_fail_streak' not in st.session_state: st.session_state.srs_fail_streak = []
    if 'srs_total_seen' not in st.session_state: st.session_state.srs_total_seen = 0
    if 'srs_last_retry_at' not in st.session_state: st.session_state.srs_last_retry_at = 0

def pick_next_word(vocab_list):
    init_srs()
    total = st.session_state.srs_total_seen
    
    # 1. Nếu sai 5 câu liên tiếp -> Quay lại từ đầu tiên trong chuỗi sai
    if len(st.session_state.srs_fail_streak) >= 5:
        return st.session_state.srs_fail_streak[0]

    # 2. Quy tắc 1/10: Cứ 10 câu phải có 1 từ cũ quay lại
    if (total - st.session_state.srs_last_retry_at >= 10) and st.session_state.srs_retry_pool:
        word_en = random.choice(list(st.session_state.srs_retry_pool.keys()))
        st.session_state.srs_last_retry_at = total
        return st.session_state.srs_retry_pool[word_en]['data']

    # 3. Spaced Repetition: Sau 20 từ (Spaced Pool)
    for i, item in enumerate(st.session_state.srs_spaced_pool):
        if total >= item['reappear_at']:
            return st.session_state.srs_spaced_pool.pop(i)['data']

    # 4. Mặc định: Lấy ngẫu nhiên
    return random.choice(vocab_list)

# --- 3. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = True
states = ['current_task', 'options', 'prev_mode', 'prev_level', 'prev_type', 'score_feedback', 'prev_module', 'submitted_correctly']
for s in states:
    if s not in st.session_state: st.session_state[s] = None

def reset_task():
    st.session_state.current_task = None
    st.session_state.options = None
    st.session_state.score_feedback = None
    st.session_state.submitted_correctly = False

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🎓 UTH Pro v6.1")
    module_choice = st.selectbox("Bộ Sách:", ["Mặc định", "Pathways"])
    module_prefix = "pathways" if module_choice == "Pathways" else "default"
    bundle = load_all_data(module_prefix)
    
    st.divider()
    mode = st.radio("Chế độ:", ["Từ vựng", "Trắc nghiệm", "Reading", "Writing"])
    
    all_keys = []
    for d in bundle.values(): all_keys.extend(list(d.keys()))
    unique_levels = sorted(list(set(all_keys))) if all_keys else ["Level_A1"]
    level = st.selectbox("Trình độ:", unique_levels)

    # THÊM PHẦN CHUYỂN ĐỔI ANH-VIỆT
    type_mode = "Anh -> Việt"
    if mode == "Từ vựng":
        type_mode = st.selectbox("Kiểu học:", ["Anh -> Việt", "Việt -> Anh"])

    if (st.session_state.prev_mode != mode or st.session_state.prev_level != level or 
        st.session_state.prev_module != module_choice or st.session_state.prev_type != type_mode):
        reset_task()
        st.session_state.prev_mode, st.session_state.prev_level = mode, level
        st.session_state.prev_module, st.session_state.prev_type = module_choice, type_mode
        st.rerun()

# --- 5. LOGIC CHẾ ĐỘ ---

# 5.1 TỪ VỰNG (THUẬT TOÁN SRS)
if mode == "Từ vựng":
    v_data = get_content(bundle['vocab'], level)
    v_list = v_data.get("vocabulary", []) if v_data else []
    
    if not v_list: st.warning("Trống từ vựng.")
    else:
        if st.session_state.current_task is None: 
            st.session_state.current_task = pick_next_word(v_list)
        
        w = st.session_state.current_task
        st.subheader(f"Học thông minh (SRS): {level}")
        
        col_info, col_audio = st.columns([3, 1])
        with col_info: st.markdown(f"**IPA:** `{w.get('ipa', 'N/A')}`")
        with col_audio:
            if st.button("🔊 Nghe"): play_audio(w['en'])
        
        q_text = w['en'] if type_mode == "Anh -> Việt" else w['vn']
        correct = w['vn'] if type_mode == "Anh -> Việt" else w['en']
        
        with st.form("vocab_form"):
            ans = st.text_input(f"Dịch từ: **{q_text}**")
            if st.form_submit_button("Kiểm tra"):
                if ans.strip().lower() == correct.strip().lower():
                    st.session_state.submitted_correctly = True
                    st.success("Chính xác!")
                    st.session_state.srs_fail_streak = []
                    
                    # Logic 2-Hit: Phải đúng 2 lần nếu đã từng sai
                    if w['en'] in st.session_state.srs_retry_pool:
                        st.session_state.srs_retry_pool[w['en']]['count'] += 1
                        if st.session_state.srs_retry_pool[w['en']]['count'] >= 2:
                            st.session_state.srs_spaced_pool.append({
                                'reappear_at': st.session_state.srs_total_seen + 20,
                                'data': w
                            })
                            del st.session_state.srs_retry_pool[w['en']]
                else:
                    st.session_state.submitted_correctly = False
                    st.error(f"Sai rồi! Đáp án: {correct}")
                    st.session_state.srs_retry_pool[w['en']] = {'count': 0, 'data': w}
                    st.session_state.srs_fail_streak.append(w)

        if st.button("Tiếp tục") or (st.session_state.submitted_correctly and st.session_state.get('auto_next', False)):
            st.session_state.srs_total_seen += 1
            reset_task(); st.rerun()

# 5.2 TRẮC NGHIỆM (FIXED OPTIONS)
elif mode == "Trắc nghiệm":
    q_list = get_content(bundle['quiz'], level)
    if not q_list: st.warning("Trống trắc nghiệm.")
    else:
        if st.session_state.current_task is None:
            st.session_state.current_task = random.choice(q_list)
            opts = list(st.session_state.current_task['options'])
            random.shuffle(opts)
            st.session_state.options = opts
        
        q = st.session_state.current_task
        with st.form("quiz_form"):
            st.info(f"Điền vào chỗ trống: \n\n **{q['sentence']}**")
            choice = st.radio("Chọn đáp án:", st.session_state.options)
            if st.form_submit_button("Xác nhận"):
                if choice == q['answer']:
                    st.success("Quá chuẩn! Đang đổi câu..."); reset_task(); st.rerun()
                else: st.error("Thử lại nhé!")

# 5.3 READING & WRITING (FIXED FEEDBACK)
elif mode == "Reading":
    r_list = get_content(bundle['read'], level)
    if not r_list: st.warning("Trống bài đọc.")
    else:
        if st.session_state.current_task is None: st.session_state.current_task = random.choice(r_list)
        r = st.session_state.current_task
        col1, col2 = st.columns([2, 1])
        with col1: st.text_area("Văn bản:", r['passage'], height=350)
        with col2:
            with st.form("reading_form"):
                u_ans = [st.radio(f"{i+1}. {qs['q']}", qs['options'], key=f"rd_{i}") for i, qs in enumerate(r['questions'])]
                if st.form_submit_button("Nộp bài"):
                    correct = sum(1 for i, qs in enumerate(r['questions']) if u_ans[i] == qs['a'])
                    st.session_state.score_feedback = f"Kết quả: {correct}/{len(r['questions'])} câu đúng."
            if st.session_state.score_feedback:
                st.write(st.session_state.score_feedback)
                if st.button("Làm bài mới"): reset_task(); st.rerun()

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
                    st.balloons(); st.success("Viết rất tốt!"); st.session_state.submitted_correctly = True
                else: st.info(f"Gợi ý: {t['answer']}")
        if st.button("Đổi câu khác"): reset_task(); st.rerun()
