import streamlit as st
import json
import random
import os
from gtts import gTTS
import io

# --- CONFIG ---
st.set_page_config(page_title="UTH English Pro v6.7", layout="wide")
st.markdown("<style>button { cursor: pointer !important; }</style>", unsafe_allow_html=True)

# --- 1. QUẢN LÝ DỮ LIỆU ---
def load_all_data(module_prefix):
    files = {
        "vocab": f"{module_prefix}_vocab.json", 
        "quiz": f"{module_prefix}_quiz.json", 
        "read": f"{module_prefix}_read.json", 
        "write": f"{module_prefix}_write.json",
        "scripts": f"{module_prefix}_scripts.json" 
    }
    defaults = {"vocab": "vocab.json", "quiz": "quiz.json", "read": "reading.json", "write": "writing.json", "scripts": "scripts.json"}
    bundle = {}
    for k, v in files.items():
        target = v if os.path.exists(v) else defaults.get(k, "")
        if os.path.exists(target):
            try:
                with open(target, "r", encoding="utf-8") as f:
                    bundle[k] = json.load(f)
            except: bundle[k] = {}
        else: bundle[k] = {}
    return bundle

def get_content(data_dict, target_level):
    if not data_dict: return None
    if target_level in data_dict: return data_dict[target_level]
    for key in data_dict.keys():
        if target_level.replace(" ", "") in key.replace(" ", ""):
            return data_dict[key]
    return list(data_dict.values())[0] if data_dict else None

def play_audio(text):
    """Hàm nâng cấp: Đổi giọng (Accent) dựa trên nhân vật trong thoại."""
    try:
        voice_map = {
            "Narrator": "co.uk", "Holly": "com", "Annie": "com", 
            "Ray": "com.au", "Host": "com.au", "Presenter": "com.au",
            "Advisor": "com.au", "Susan": "ie", "Student": "com",
            "Paula": "com.ca", "Ahmed": "co.in", "Interviewer": "com.au"
        }
        lines = text.split('\n')
        combined_audio = io.BytesIO()
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            if ":" in line:
                speaker, content = line.split(":", 1)
                # Lấy accent tương ứng với nhân vật, mặc định là Mỹ (com)
                tld = voice_map.get(speaker.strip(), "com")
                tts = gTTS(text=content.strip(), lang='en', tld=tld)
            else:
                tts = gTTS(text=line, lang='en', tld="com")
            
            tts.write_to_fp(combined_audio)
            
        st.audio(combined_audio.getvalue(), format='audio/mp3')
    except: st.error("Lỗi âm thanh đa giọng!")

# --- 2. THUẬT TOÁN SRS (TỪ VỰNG) ---
def init_srs():
    if 'srs_retry_pool' not in st.session_state: st.session_state.srs_retry_pool = {}
    if 'srs_spaced_pool' not in st.session_state: st.session_state.srs_spaced_pool = []
    if 'srs_fail_streak' not in st.session_state: st.session_state.srs_fail_streak = []
    if 'srs_total_seen' not in st.session_state: st.session_state.srs_total_seen = 0
    if 'srs_last_retry_at' not in st.session_state: st.session_state.srs_last_retry_at = 0

def pick_next_word(vocab_list):
    init_srs()
    total = st.session_state.srs_total_seen
    if len(st.session_state.srs_fail_streak) >= 5: return st.session_state.srs_fail_streak[0]
    if (total - st.session_state.srs_last_retry_at >= 10) and st.session_state.srs_retry_pool:
        word_en = random.choice(list(st.session_state.srs_retry_pool.keys()))
        st.session_state.srs_last_retry_at = total
        return st.session_state.srs_retry_pool[word_en]['data']
    for i, item in enumerate(st.session_state.srs_spaced_pool):
        if total >= item['reappear_at']: return st.session_state.srs_spaced_pool.pop(i)['data']
    return random.choice(vocab_list)

# --- 3. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = True
states = ['current_task', 'options', 'prev_mode', 'prev_level', 'prev_type', 'score_feedback', 
          'prev_module', 'is_correct', 'listen_sub_pool', 'current_listen_idx', 'prev_listen_id']
for s in states:
    if s not in st.session_state: st.session_state[s] = None

def reset_task():
    st.session_state.current_task = None
    st.session_state.score_feedback = None
    st.session_state.is_correct = None

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🎓 UTH Pro v6.7")
    module_choice = st.selectbox("Bộ Sách:", ["Mặc định", "Pathways"])
    module_prefix = "pathways" if module_choice == "Pathways" else "default"
    bundle = load_all_data(module_prefix)
    
    st.divider()
    mode = st.radio("Chế độ:", ["Từ vựng", "Trắc nghiệm", "Nghe", "Scripts", "Reading", "Writing"])
    
    all_keys = []
    for d in bundle.values(): 
        if isinstance(d, dict): all_keys.extend(list(d.keys()))
    unique_levels = sorted(list(set(all_keys))) if all_keys else ["Level_A1"]
    level = st.selectbox("Trình độ:", unique_levels)

    type_mode = "Anh -> Việt"
    if mode == "Từ vựng":
        type_mode = st.selectbox("Kiểu học:", ["Anh -> Việt", "Việt -> Anh"])

    if (st.session_state.prev_mode != mode or st.session_state.prev_level != level or 
        st.session_state.prev_module != module_choice or (mode == "Từ vựng" and st.session_state.prev_type != type_mode)):
        reset_task()
        st.session_state.listen_sub_pool = None
        st.session_state.prev_mode, st.session_state.prev_level = mode, level
        st.session_state.prev_module, st.session_state.prev_type = module_choice, type_mode
        st.rerun()

# --- 5. LOGIC CHẾ ĐỘ ---

# 5.1 SCRIPTS
if mode == "Scripts":
    s_data = get_content(bundle.get('scripts'), level)
    if not s_data: st.warning("Trống dữ liệu Scripts.")
    else:
        st.subheader(f"Audio & Video Scripts: {level}")
        tab_v, tab_a = st.tabs(["Video", "Audio"])
        with tab_v:
            for item in s_data.get("video", []):
                with st.expander(f"Unit {item['unit']}: {item['title']}"):
                    st.write(item['transcript'])
                    if st.button(f"🔊 Nghe Video U{item['unit']}", key=f"vs_{item['unit']}"):
                        play_audio(item['transcript'])
        with tab_a:
            for item in s_data.get("audio", []):
                with st.expander(f"Unit {item['unit']}: {item['title']}"):
                    st.write(item['transcript'])
                    if st.button(f"🔊 Nghe Audio U{item['unit']}", key=f"as_{item['unit']}"):
                        play_audio(item['transcript'])

# 5.2 NGHE (FIX LỖI CHUYỂN ĐỔI AUDIO/VIDEO)
elif mode == "Nghe":
    s_data = get_content(bundle.get('scripts'), level)
    if not s_data: st.warning("Trống dữ liệu Nghe.")
    else:
        col_t, col_u = st.columns(2)
        l_type = col_t.selectbox("Loại học liệu:", ["video", "audio"])
        l_unit = col_u.selectbox("Chọn Unit:", [1, 2])
        
        # Kiểm tra nếu người dùng thay đổi selection thì phải reset bài tập
        current_ctx_id = f"{l_type}_{l_unit}"
        if st.session_state.prev_listen_id != current_ctx_id:
            st.session_state.listen_sub_pool = None
            st.session_state.current_listen_idx = 0
            st.session_state.prev_listen_id = current_ctx_id
            reset_task()
            st.rerun()

        segment = next((x for x in s_data.get(l_type, []) if x['unit'] == l_unit), None)
        
        if segment:
            if st.session_state.listen_sub_pool is None:
                # Bốc 5 câu hỏi ngẫu nhiên từ bộ câu hỏi trong JSON
                q_pool = segment['questions']
                st.session_state.listen_sub_pool = random.sample(q_pool, min(5, len(q_pool)))
                st.session_state.current_listen_idx = 0
            
            curr_idx = st.session_state.current_listen_idx
            task = st.session_state.listen_sub_pool[curr_idx]
            
            st.subheader(f"🎧 Đang luyện: {segment['title']} ({curr_idx + 1}/5)")
            if st.button("🔊 PHÁT TOÀN BỘ ĐOẠN HỘI THOẠI"):
                play_audio(segment['transcript'])
            
            with st.form("listen_form"):
                st.info(f"Nghe và điền từ còn thiếu: \n\n **{task['sentence']}**")
                u_ans = st.text_input("Nhập đáp án của bạn:")
                if st.form_submit_button("Kiểm tra"):
                    if u_ans.strip().lower() == task['answer'].strip().lower():
                        st.session_state.is_correct = True
                        st.session_state.score_feedback = f"Chính xác! Đáp án: **{task['answer']}**"
                    else:
                        st.session_state.is_correct = False
                        st.session_state.score_feedback = f"Chưa đúng. Đáp án là: **{task['answer']}**"
            
            if st.session_state.score_feedback:
                if st.session_state.is_correct: st.success(st.session_state.score_feedback)
                else: st.error(st.session_state.score_feedback)
                if st.button("Câu tiếp theo"):
                    if st.session_state.current_listen_idx < len(st.session_state.listen_sub_pool) - 1:
                        st.session_state.current_listen_idx += 1
                        st.session_state.score_feedback = None; st.rerun()
                    else:
                        st.balloons(); st.success("Hoàn thành bài luyện nghe này!"); st.session_state.listen_sub_pool = None; st.rerun()

# (GIỮ NGUYÊN CÁC CHẾ ĐỘ TỪ VỰNG, TRẮC NGHIỆM, READING, WRITING NHƯ CŨ...)
elif mode == "Từ vựng":
    v_data = get_content(bundle.get('vocab'), level)
    v_list = v_data.get("vocabulary", []) if v_data and isinstance(v_data, dict) else []
    if not v_list: st.warning("Trống từ vựng.")
    else:
        if st.session_state.current_task is None: st.session_state.current_task = pick_next_word(v_list)
        w = st.session_state.current_task
        st.subheader(f"Từ vựng: {level}")
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
                    st.session_state.is_correct = True; st.session_state.score_feedback = "Chính xác!"
                    # SRS logic here...
                else:
                    st.session_state.is_correct = False; st.session_state.score_feedback = f"Sai rồi. Đáp án: {correct}"
        if st.session_state.score_feedback:
            if st.session_state.is_correct: st.success(st.session_state.score_feedback)
            else: st.error(st.session_state.score_feedback)
            if st.button("Tiếp tục"): reset_task(); st.rerun()

elif mode == "Trắc nghiệm":
    q_list = get_content(bundle.get('quiz'), level)
    if not q_list: st.warning("Trống trắc nghiệm.")
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
                if choice == q['answer']: st.success("Quá chuẩn!"); st.session_state.is_correct = True
                else: st.error(f"Sai rồi. Đáp án: {q['answer']}"); st.session_state.is_correct = False
        if st.session_state.is_correct is not None: st.button("Câu tiếp theo", on_click=reset_task)

elif mode == "Reading":
    r_list = get_content(bundle.get('read'), level)
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
                    c_count = sum(1 for i, qs in enumerate(r['questions']) if u_ans[i] == qs['a'])
                    st.info(f"Kết quả: {c_count}/{len(r['questions'])} đúng.")
            st.button("Làm bài mới", on_click=reset_task)

elif mode == "Writing":
    w_list = get_content(bundle.get('write'), level)
    if not w_list: st.warning("Trống writing.")
    else:
        if st.session_state.current_task is None: st.session_state.current_task = random.choice(w_list)
        t = st.session_state.current_task
        with st.form("write_form"):
            st.subheader(t['prompt'])
            u_w = st.text_input("Gõ câu:")
            if st.form_submit_button("Check"):
                if u_w.strip().lower().replace(".", "") == t['answer'].strip().lower().replace(".", ""):
                    st.success("Đúng!"); st.session_state.is_correct = True
                else: st.info(f"Gợi ý: {t['answer']}"); st.session_state.is_correct = False
        if st.session_state.is_correct is not None: st.button("Tiếp", on_click=reset_task)
