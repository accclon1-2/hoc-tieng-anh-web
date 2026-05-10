import streamlit as st
import json
import random
import os
import pandas as pd
from gtts import gTTS
import io
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="UTH English Pro v6.3", layout="wide")
st.markdown("<style>button { cursor: pointer !important; }</style>", unsafe_allow_html=True)

# --- 1. QUẢN LÝ DỮ LIỆU (ĐÃ BỎ CACHE ĐỂ CẬP NHẬT TỨC THÌ) ---
def load_all_data(module_prefix):
    """Đọc trực tiếp từ ổ cứng, không lưu cache để Kiệt sửa file là nhận ngay"""
    files = {"vocab": f"{module_prefix}_vocab.json", "quiz": f"{module_prefix}_quiz.json", 
             "read": f"{module_prefix}_read.json", "write": f"{module_prefix}_write.json"}
    defaults = {"vocab": "vocab.json", "quiz": "quiz.json", "read": "reading.json", "write": "writing.json"}
    bundle = {}
    for k, v in files.items():
        target = v if os.path.exists(v) else defaults[k]
        if os.path.exists(target):
            try:
                with open(target, "r", encoding="utf-8") as f:
                    bundle[k] = json.load(f)
            except: bundle[k] = {}
        else: bundle[k] = {}
    return bundle

def get_content(data_dict, target_level):
    """Hàm thông minh: Nếu không tìm thấy tên chính xác, sẽ lấy ngăn đầu tiên có dữ liệu"""
    if not data_dict: return None
    # 1. Thử tìm tên khớp hoàn toàn
    if target_level in data_dict: return data_dict[target_level]
    # 2. Thử tìm tên khớp tương đối (bỏ qua khoảng trắng)
    for key in data_dict.keys():
        if target_level.replace(" ", "") in key.replace(" ", "") or key.replace(" ", "") in target_level.replace(" ", ""):
            return data_dict[key]
    # 3. Chống cháy: Lấy ngăn đầu tiên trong file JSON
    return list(data_dict.values())[0] if data_dict else None

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en'); fp = io.BytesIO()
        tts.write_to_fp(fp); st.audio(fp, format='audio/mp3')
    except: st.error("Lỗi âm thanh!")

# --- 2. THUẬT TOÁN SRS (SPACED REPETITION) ---
def init_srs():
    if 'srs_retry_pool' not in st.session_state: st.session_state.srs_retry_pool = {}
    if 'srs_spaced_pool' not in st.session_state: st.session_state.srs_spaced_pool = []
    if 'srs_fail_streak' not in st.session_state: st.session_state.srs_fail_streak = []
    if 'srs_total_seen' not in st.session_state: st.session_state.srs_total_seen = 0
    if 'srs_last_retry_at' not in st.session_state: st.session_state.srs_last_retry_at = 0

def pick_next_word(vocab_list):
    init_srs()
    total = st.session_state.srs_total_seen
    # Ưu tiên chuỗi sai
    if len(st.session_state.srs_fail_streak) >= 5: return st.session_state.srs_fail_streak[0]
    # Ưu tiên từ cũ cần ôn (1/10)
    if (total - st.session_state.srs_last_retry_at >= 10) and st.session_state.srs_retry_pool:
        word_en = random.choice(list(st.session_state.srs_retry_pool.keys()))
        st.session_state.srs_last_retry_at = total
        return st.session_state.srs_retry_pool[word_en]['data']
    # Ưu tiên từ trong hàng đợi Spaced
    for i, item in enumerate(st.session_state.srs_spaced_pool):
        if total >= item['reappear_at']: return st.session_state.srs_spaced_pool.pop(i)['data']
    return random.choice(vocab_list)

# --- 3. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = True
states = ['current_task', 'options', 'prev_mode', 'prev_level', 'prev_type', 'score_feedback', 'prev_module', 'is_correct']
for s in states:
    if s not in st.session_state: st.session_state[s] = None

def reset_task():
    st.session_state.current_task = None
    st.session_state.options = None
    st.session_state.score_feedback = None
    st.session_state.is_correct = None

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🎓 UTH Pro v6.3")
    module_choice = st.selectbox("Bộ Sách:", ["Mặc định", "Pathways"])
    module_prefix = "pathways" if module_choice == "Pathways" else "default"
    
    # Đọc dữ liệu mới nhất
    bundle = load_all_data(module_prefix)
    
    st.divider()
    mode = st.radio("Chế độ:", ["Từ vựng", "Trắc nghiệm", "Nghe", "Reading", "Writing"])
    
    all_keys = []
    for d in bundle.values(): all_keys.extend(list(d.keys()))
    unique_levels = sorted(list(set(all_keys))) if all_keys else ["Level_A1"]
    level = st.selectbox("Trình độ:", unique_levels)

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

# 5.1 TỪ VỰNG
if mode == "Từ vựng":
    v_data = get_content(bundle['vocab'], level)
    v_list = v_data.get("vocabulary", []) if v_data and isinstance(v_data, dict) else []
    
    if not v_list: st.warning("Không tìm thấy dữ liệu Từ vựng.")
    else:
        if st.session_state.current_task is None: st.session_state.current_task = pick_next_word(v_list)
        w = st.session_state.current_task
        st.subheader(f"Luyện tập: {level}")
        
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
                    st.session_state.is_correct = True
                    st.session_state.score_feedback = "Chính xác!"
                    # Logic SRS
                    if w['en'] in st.session_state.srs_retry_pool:
                        st.session_state.srs_retry_pool[w['en']]['count'] += 1
                        if st.session_state.srs_retry_pool[w['en']]['count'] >= 2:
                            st.session_state.srs_spaced_pool.append({'reappear_at': st.session_state.srs_total_seen + 20, 'data': w})
                            del st.session_state.srs_retry_pool[w['en']]
                    st.session_state.srs_fail_streak = []
                else:
                    st.session_state.is_correct = False
                    st.session_state.score_feedback = f"Sai rồi. Đáp án: **{correct}**"
                    st.session_state.srs_retry_pool[w['en']] = {'count': 0, 'data': w}
                    st.session_state.srs_fail_streak.append(w)
        
        if st.session_state.score_feedback:
            if st.session_state.is_correct: st.success(st.session_state.score_feedback)
            else: st.error(st.session_state.score_feedback)
            if st.button("Tiếp tục"):
                st.session_state.srs_total_seen += 1
                reset_task(); st.rerun()

# 5.2 TRẮC NGHIỆM
elif mode == "Trắc nghiệm":
    q_list = get_content(bundle['quiz'], level)
    if not q_list or not isinstance(q_list, list): st.warning("Không tìm thấy dữ liệu Trắc nghiệm.")
    else:
        if st.session_state.current_task is None:
            st.session_state.current_task = random.choice(q_list)
            opts = list(st.session_state.current_task['options']); random.shuffle(opts)
            st.session_state.options = opts
        
        q = st.session_state.current_task
        with st.form("quiz_form"):
            st.info(f"Điền vào chỗ trống: \n\n **{q['sentence']}**")
            choice = st.radio("Chọn đáp án:", st.session_state.options)
            if st.form_submit_button("Xác nhận"):
                if choice == q['answer']:
                    st.session_state.is_correct = True
                    st.session_state.score_feedback = "Quá chuẩn!"
                else:
                    st.session_state.is_correct = False
                    st.session_state.score_feedback = f"Sai rồi. Đáp án: **{q['answer']}**"

        if st.session_state.score_feedback:
            if st.session_state.is_correct: st.success(st.session_state.score_feedback)
            else: st.error(st.session_state.score_feedback)
            if st.button("Câu tiếp theo"): reset_task(); st.rerun()

# 5.3 READING
elif mode == "Reading":
    r_list = get_content(bundle['read'], level)
    if not r_list or not isinstance(r_list, list): st.warning("Không tìm thấy bài đọc.")
    else:
        if st.session_state.current_task is None: st.session_state.current_task = random.choice(r_list)
        r = st.session_state.current_task
        col1, col2 = st.columns([2, 1])
        with col1: st.text_area("Văn bản:", r['passage'], height=350)
        with col2:
            with st.form("reading_form"):
                u_ans = [st.radio(f"{i+1}. {qs['q']}", qs['options'], key=f"rd_{i}") for i, qs in enumerate(r['questions'])]
                if st.form_submit_button("Nộp bài"):
                    c_count = sum(1 for i, qs in enumerate(r['questions']) if u_ans[i] == qs['a'])
                    st.session_state.is_correct = (c_count == len(r['questions']))
                    st.session_state.score_feedback = f"Kết quả: {c_count}/{len(r['questions'])} câu đúng."

            if st.session_state.score_feedback:
                if st.session_state.is_correct: st.success(st.session_state.score_feedback)
                else: st.warning(st.session_state.score_feedback)
                if st.button("Làm bài mới"): reset_task(); st.rerun()

# 5.4 WRITING
elif mode == "Writing":
    w_list = get_content(bundle['write'], level)
    if not w_list or not isinstance(w_list, list): st.warning("Không tìm thấy dữ liệu Viết.")
    else:
        if st.session_state.current_task is None: st.session_state.current_task = random.choice(w_list)
        t = st.session_state.current_task
        with st.form("write_form"):
            st.subheader(f"Đề bài: {t['prompt']}")
            user_w = st.text_input("Gõ câu hoàn chỉnh:")
            if st.form_submit_button("Kiểm tra"):
                if user_w.strip().lower().replace(".", "") == t['answer'].strip().lower().replace(".", ""):
                    st.session_state.is_correct = True
                    st.session_state.score_feedback = "Viết rất tốt!"
                else:
                    st.session_state.is_correct = False
                    st.session_state.score_feedback = f"Đáp án gợi ý: **{t['answer']}**"

        if st.session_state.score_feedback:
            if st.session_state.is_correct: st.success(st.session_state.score_feedback)
            else: st.info(st.session_state.score_feedback)
            if st.button("Câu tiếp theo"): reset_task(); st.rerun()
# 5.5 NGHE (DICTATION/GAP-FILL)
elif mode == "Nghe":
    l_list = get_content(bundle['listen'], level)
    if not l_list: st.warning("Trống dữ liệu nghe.")
    else:
        if st.session_state.current_task is None:
            # Chọn ngẫu nhiên 1 câu đục lỗ từ danh sách 80 câu
            st.session_state.current_task = random.choice(l_list)
        
        t = st.session_state.current_task
        st.subheader(f"Luyện nghe: {level}")
        
        if st.button("🔊 Phát đoạn âm thanh"):
            play_audio(t['transcript'])
            
        with st.form("listen_form"):
            st.info(f"Nghe và điền từ còn thiếu: \n\n **{t['sentence']}**")
            user_ans = st.text_input("Nhập từ bạn nghe được:")
            if st.form_submit_button("Kiểm tra"):
                if user_ans.strip().lower() == t['answer'].strip().lower():
                    st.session_state.is_correct = True
                    st.session_state.score_feedback = f"Chính xác! Từ đó là: **{t['answer']}**"
                else:
                    st.session_state.is_correct = False
                    st.session_state.score_feedback = f"Chưa đúng. Đáp án là: **{t['answer']}**"

        if st.session_state.score_feedback:
            if st.session_state.is_correct: st.success(st.session_state.score_feedback)
            else: st.error(st.session_state.score_feedback)
            if st.button("Câu tiếp theo"): reset_task(); st.rerun()
