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
    # Khử khoảng trắng để so khớp chính xác hơn
    target_clean = target_level.replace(" ", "").lower()
    if target_level in data_dict: return data_dict[target_level]
    for key in data_dict.keys():
        if key.replace(" ", "").lower() == target_clean:
            return data_dict[key]
    return list(data_dict.values())[0] if data_dict else None

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en'); fp = io.BytesIO()
        tts.write_to_fp(fp); st.audio(fp, format='audio/mp3')
    except: st.error("Lỗi âm thanh!")

# --- 2. THUẬT TOÁN SRS ---
def init_srs():
    for s in ['srs_retry_pool', 'srs_spaced_pool', 'srs_fail_streak']:
        if s not in st.session_state: st.session_state[s] = {} if s == 'srs_retry_pool' else []
    if 'srs_total_seen' not in st.session_state: st.session_state.srs_total_seen = 0
    if 'srs_last_retry_at' not in st.session_state: st.session_state.srs_last_retry_at = 0

def pick_next_word(vocab_list):
    init_srs(); total = st.session_state.srs_total_seen
    if len(st.session_state.srs_fail_streak) >= 5: return st.session_state.srs_fail_streak[0]
    if (total - st.session_state.srs_last_retry_at >= 10) and st.session_state.srs_retry_pool:
        word_en = random.choice(list(st.session_state.srs_retry_pool.keys()))
        st.session_state.srs_last_retry_at = total
        return st.session_state.srs_retry_pool[word_en]['data']
    return random.choice(vocab_list)

# --- 3. SESSION STATE ---
states = ['current_task', 'options', 'prev_mode', 'prev_level', 'score_feedback', 
          'prev_module', 'is_correct', 'listen_sub_pool', 'current_listen_idx', 'prev_type']
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
    unique_levels = sorted(list(set(all_keys))) if all_keys else ["Pathways: Life & Work"]
    level = st.selectbox("Trình độ:", unique_levels)

    type_mode = st.selectbox("Kiểu học:", ["Anh -> Việt", "Việt -> Anh"]) if mode == "Từ vựng" else "Anh -> Việt"

    if (st.session_state.prev_mode != mode or st.session_state.prev_level != level or 
        st.session_state.prev_module != module_choice or st.session_state.prev_type != type_mode):
        reset_task()
        st.session_state.listen_sub_pool = None
        st.session_state.prev_mode, st.session_state.prev_level = mode, level
        st.session_state.prev_module, st.session_state.prev_type = module_choice, type_mode
        st.rerun()

# --- 5. LOGIC CHẾ ĐỘ ---

if mode == "Scripts":
    s_data = get_content(bundle.get('scripts'), level)
    if not s_data: st.warning("⚠️ Trống dữ liệu Scripts.")
    else:
        st.subheader("📜 Nội dung Scripts")
        tab_v, tab_a = st.tabs(["🎥 Video", "🎧 Audio"])
        with tab_v:
            for item in s_data.get("video", []):
                with st.expander(f"Unit {item['unit']}: {item['title']}"):
                    st.write(item['transcript'])
                    if st.button(f"🔊 Nghe Video U{item['unit']}", key=f"vs_{item['unit']}"): play_audio(item['transcript'])
        with tab_a:
            for item in s_data.get("audio", []):
                with st.expander(f"Unit {item['unit']}: {item['title']}"):
                    st.write(item['transcript'])
                    if st.button(f"🔊 Nghe Audio U{item['unit']}", key=f"as_{item['unit']}"): play_audio(item['transcript'])

elif mode == "Nghe":
    s_data = get_content(bundle.get('scripts'), level)
    if not s_data: st.warning("⚠️ Trống dữ liệu Nghe.")
    else:
        col_t, col_u = st.columns(2)
        l_type = col_t.selectbox("Loại:", ["video", "audio"])
        l_unit = col_u.selectbox("Unit:", [1, 2])
        segment = next((x for x in s_data.get(l_type, []) if x['unit'] == l_unit), None)
        
        if segment:
            if st.session_state.listen_sub_pool is None:
                st.session_state.listen_sub_pool = random.sample(segment['questions'], 5)
                st.session_state.current_listen_idx = 0
            
            curr_idx = st.session_state.current_listen_idx
            task = st.session_state.listen_sub_pool[curr_idx]
            st.subheader(f"🎧 {segment['title']} ({curr_idx + 1}/5)")
            if st.button("🔊 PHÁT TOÀN BỘ ĐOẠN"): play_audio(segment['transcript'])
            
            with st.form("listen_form"):
                st.info(f"Điền từ: {task['sentence']}")
                u_ans = st.text_input("Đáp án:")
                if st.form_submit_button("Kiểm tra ✅"):
                    if u_ans.strip().lower() == task['answer'].strip().lower():
                        st.session_state.is_correct = True; st.session_state.score_feedback = "Đúng! 🎉"
                    else:
                        st.session_state.is_correct = False; st.session_state.score_feedback = f"Sai. Đáp án: {task['answer']}"
            
            if st.session_state.score_feedback:
                if st.session_state.is_correct: st.success(st.session_state.score_feedback)
                else: st.error(st.session_state.score_feedback)
                if st.button("Câu tiếp theo ⏭️"):
                    if st.session_state.current_listen_idx < 4:
                        st.session_state.current_listen_idx += 1
                        st.session_state.score_feedback = None; st.rerun()
                    else:
                        st.balloons(); st.success("Hoàn thành!"); st.session_state.listen_sub_pool = None; st.rerun()

elif mode == "Từ vựng":
    v_data = get_content(bundle.get('vocab'), level)
    v_list = v_data.get("vocabulary", []) if v_data else []
    if not v_list: st.warning("Trống từ vựng.")
    else:
        if st.session_state.current_task is None: st.session_state.current_task = pick_next_word(v_list)
        w = st.session_state.current_task
        st.subheader(f"Từ vựng: {level}")
        if st.button("🔊 Nghe"): play_audio(w['en'])
        q_text = w['en'] if type_mode == "Anh -> Việt" else w['vn']
        correct = w['vn'] if type_mode == "Anh -> Việt" else w['en']
        with st.form("vocab_form"):
            ans = st.text_input(f"Dịch: {q_text}")
            if st.form_submit_button("Check"):
                if ans.strip().lower() == correct.strip().lower():
                    st.success("Đúng!"); st.session_state.is_correct = True
                else: st.error(f"Sai. Đáp án: {correct}"); st.session_state.is_correct = False
        if st.session_state.is_correct is not None:
            if st.button("Tiếp"): st.session_state.srs_total_seen += 1; reset_task(); st.rerun()

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
            st.info(q['sentence'])
            choice = st.radio("Chọn:", st.session_state.options)
            if st.form_submit_button("Check"):
                if choice == q['answer']: st.success("Đúng!"); st.session_state.is_correct = True
                else: st.error(f"Sai. Đáp án: {q['answer']}"); st.session_state.is_correct = False
        if st.session_state.is_correct is not None:
            if st.button("Tiếp"): reset_task(); st.rerun()

elif mode == "Reading":
    r_list = get_content(bundle.get('read'), level)
    if not r_list: st.warning("Trống bài đọc.")
    else:
        if st.session_state.current_task is None: st.session_state.current_task = random.choice(r_list)
        r = st.session_state.current_task
        col1, col2 = st.columns([2, 1])
        with col1: st.text_area("Passage:", r['passage'], height=350)
        with col2:
            with st.form("reading_form"):
                u_ans = [st.radio(f"{i+1}. {qs['q']}", qs['options'], key=f"rd_{i}") for i, qs in enumerate(r['questions'])]
                if st.form_submit_button("Nộp"):
                    c = sum(1 for i, qs in enumerate(r['questions']) if u_ans[i] == qs['a'])
                    st.info(f"Kết quả: {c}/{len(r['questions'])} đúng.")
            st.button("Bài mới", on_click=reset_task)

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
