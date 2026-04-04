from src.rag_chain import create_rag_chain
from src.query_router import route_query, find_major_code, major_display_name, SCORE_DB
from src.query_router_admissions import find_admission_method_code
from src.query_router_scores import is_forecast_score_query


import os
# os.environ['TRANSFORMERS_OFFLINE'] = '1'
# os.environ['HF_DATASETS_OFFLINE'] = '1'

# Khởi tạo RAG chain theo kiểu lazy để tránh treo lúc khởi động server
qa_chain = None

def _get_qa_chain():
    global qa_chain
    if qa_chain is None:
        try:
            qa_chain = create_rag_chain()
        except Exception as e:
            print(f"Lỗi khởi tạo RAG chain: {e}")
            return None
    return qa_chain

# Dictionary lưu trữ lịch sử chat theo session_id (giả lập)
chat_histories = {}
session_context = {}

def _strip_accents(text: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFD", text or "")
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")

def _normalize_for_match(text: str) -> str:
    import re
    s = (text or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s

def _is_short_followup(text: str) -> bool:
    import re
    s = _normalize_for_match(text)
    if not s:
        return False
    if len(s) <= 24:
        return True
    tokens = [t for t in re.split(r"\s+", s) if t]
    return len(tokens) <= 4

def _expand_common_unaccented_phrases(text: str) -> str:
    s = _normalize_for_match(text)
    ascii_s = _strip_accents(s)
    replacements = [
        ("hoc phi", "học phí"),
        ("hoc bong", "học bổng"),
        ("diem chuan", "điểm chuẩn"),
        ("phuong thuc", "phương thức"),
        ("xet tuyen", "xét tuyển"),
        ("nguyen vong", "nguyện vọng"),
        ("thong tin lien he", "thông tin liên hệ"),
        ("dia chi", "địa chỉ"),
        ("so dien thoai", "số điện thoại"),
        ("email", "email"),
        ("website", "website"),
    ]
    out = s
    for raw, viet in replacements:
        if raw in ascii_s and viet not in out:
            out = f"{out} {viet}".strip()
    return out

def _rewrite_short_followup(question: str, last_assistant: str, ctx: dict) -> str:
    q = _expand_common_unaccented_phrases(question)
    q_norm = _normalize_for_match(q)
    q_ascii = _strip_accents(q_norm)
    last_norm = _normalize_for_match(last_assistant)
    last_ascii = _strip_accents(last_norm)

    if not _is_short_followup(q_norm):
        return q

    last_major = ctx.get("last_major")

    # 1. Handle "school info" topics regardless of last_topic, as long as they are general
    school_topics = {
        "cơ sở vật chất": ["cơ sở vật chất", "co so vat chat", "cơ sở", "co so", "phòng lab", "phòng thí nghiệm", "thư viện", "ký túc", "ktx"],
        "học phí": ["học phí", "hoc phi", "học bổng", "hoc bong"],
        "ngành đào tạo": ["ngành đào tạo", "các ngành", "ngành học", "danh mục ngành", "nganh dao tao"],
        "phương thức tuyển sinh": ["phương thức", "xét tuyển", "tuyển sinh", "phuong thuc", "xet tuyen"],
        "thông tin liên hệ": ["địa chỉ", "liên hệ", "số điện thoại", "website", "hotline"],
        "cơ hội nghề nghiệp": ["cơ hội", "việc làm", "nghề nghiệp", "co hoi", "viec lam"],
    }

    for topic, keywords in school_topics.items():
        if any(k in q_norm for k in keywords) or any(_strip_accents(k) in q_ascii for k in keywords):
            if "ptit" not in q_ascii and "hoc vien" not in q_ascii and "trường" not in q_ascii:
                if topic == "thông tin liên hệ":
                    return "Thông tin liên hệ của PTIT"
                if topic == "ngành đào tạo":
                    return "Danh mục ngành đào tạo PTIT"
                if topic == "cơ hội nghề nghiệp":
                    if last_major:
                        return f"Cơ hội nghề nghiệp của ngành {last_major}"
                    return "Cơ hội nghề nghiệp tại PTIT"
                return f"{topic} của PTIT"

    # 2. Handle major-specific followups if we have a last_major
    if last_major and not find_major_code(q):
        score_keywords = ["điểm chuẩn", "điểm xét", "bao nhiêu điểm", "cutoff", "cut-off", "diem"]
        method_keywords = ["phương thức", "xét tuyển", "pt1", "pt2", "pt3", "pt4", "pt5", "phuong thuc", "xet tuyen"]
        job_keywords = ["cơ hội", "việc làm", "nghề nghiệp", "lương", "co hoi", "viec lam"]
        
        is_score = any(k in q_norm for k in score_keywords) or any(k in q_ascii for k in score_keywords)
        is_method = any(k in q_norm for k in method_keywords) or any(k in q_ascii for k in method_keywords)
        is_job = any(k in q_norm for k in job_keywords) or any(k in q_ascii for k in job_keywords)

        if is_score: return f"Điểm chuẩn ngành {last_major} năm 2025 là bao nhiêu?"
        if is_method: return f"Phương thức xét tuyển ngành {last_major} gồm những gì?"
        if is_job: return f"Cơ hội việc làm và định hướng nghề nghiệp của ngành {last_major}"

    # 3. Handle context-sensitive suggestions (e.g., if the bot asked "Bạn muốn hỏi về A, B hay C?")
    if "ban muon" in last_ascii or "goi y" in last_ascii or "?" in last_assistant:
        # If the user just typed a word that was in the last response, assume they are picking that option
        # This is a bit more aggressive but helps with short inputs
        for word in q_norm.split():
            if len(word) > 2 and word in last_norm:
                # But only if it's not a common word
                if word not in ["trường", "ngành", "điểm", "học", "cho"]:
                    # Try to see if it's a topic
                    if any(k in word for k in ["điểm", "diem"]): return f"Điểm chuẩn {last_major or 'PTIT'}"
                    if any(k in word for k in ["ngành", "nganh"]): return f"Các ngành đào tạo của PTIT"

    # 4. If the user input is exactly one of the suggested options from the last message
    # We can detect this by looking for "ngành đào tạo", "cơ sở vật chất", "học phí", "học bổng", "phương thức"
    # and ensuring they are mapped to PTIT context if they are not already.
    # (This is already mostly covered by step 1, but we can be more explicit for specific suggestion phrases)
    suggestion_phrases = ["ngành đào tạo", "cơ sở vật chất", "học phí/học bổng", "phương thức tuyển sinh"]
    for phrase in suggestion_phrases:
        if q_norm in phrase or phrase in q_norm:
            if "ptit" not in q_ascii:
                return f"{q_norm} của PTIT"

    return q

def _infer_topic_from_sources(source_files: list[str]) -> str | None:
    lower = " ".join((f or "").lower() for f in source_files)
    if "hoc_phi" in lower or "hoc_bong" in lower:
        return "tuition"
    if "phuong_thuc" in lower:
        return "admission_methods"
    if "diem_chuan" in lower:
        return "scores"
    if "danh_muc_nganh" in lower:
        return "majors"
    if "gioi_thieu_ptit" in lower:
        return "school_info"
    if "co_hoi_viec_lam" in lower:
        return "career"
    return None

def _has_non_vietnamese_word(text: str) -> bool:
    import re
    lower = (text or "").lower()
    words = re.findall(r"\b[a-z]{2,}\b", lower)
    if not words:
        return False
    allowed = {
        "ptit", "pt", "pt1", "pt2", "pt3", "pt4", "pt5",
        "sat", "act", "hsa", "tsa", "apt", "spt", "ttnv",
        "ielts", "toefl", "ibt", "itp", "gpa", "hsnl",
        "clc", "iot", "aiot", "cntt", "attt", "khmt", "qtkd", "tmdt",
    }
    return any(w not in allowed for w in words)

def ask(question: str, session_id: str = "default", rating: str | None = None) -> str:
    # Lấy lịch sử chat của session
    history = chat_histories.get(session_id, [])
    ctx = session_context.get(session_id, {})
    
    # Xử lý trường hợp đánh giá (retry)
    if rating and history:
        # Kiểm tra xem câu hỏi hiện tại có trùng với câu hỏi cuối cùng trong lịch sử không
        if history[-1][0] == question:
            if rating == "good":
                # Trả lại đúng câu trả lời cũ
                return history[-1][1]
            elif rating == "bad":
                # Xóa câu trả lời cũ khỏi lịch sử để tạo câu trả lời mới
                history.pop()

    last_assistant = history[-1][1] if history else ""
    
    # Prefix cho yêu cầu chi tiết
    llm_prefix = ""
    if rating == "bad":
        llm_prefix = "[YÊU CẦU QUAN TRỌNG: Hãy thay đổi cách chào hỏi và trả lời CHI TIẾT, ĐẦY ĐỦ hơn câu trả lời trước đó của bạn]: "

    # Sử dụng câu hỏi đã rewrite cho logic tiếp theo
    question_rewritten = _rewrite_short_followup(question, last_assistant, ctx)
    
    lower = question.lower().strip()
    has_pronoun = any(k in lower for k in ["nó", "ngành này", "ngành đó", "chương trình này", "mã này"])
    ma_in_question = find_major_code(question)
    method_in_question = find_admission_method_code(question)
    last_major = ctx.get("last_major")
    last_topic = ctx.get("last_topic")
    last_method = ctx.get("last_method")

    routed_question = question_rewritten
    if has_pronoun and not ma_in_question and last_major and last_major in SCORE_DB:
        routed_question = f"{question_rewritten} {last_major}"

    wants_more_detail = any(k in lower for k in ["chi tiết", "cụ thể", "nói rõ", "giải thích", "kỹ hơn", "thêm"])
    if (wants_more_detail or rating == "bad") and not method_in_question and last_method:
        routed_question = f"{routed_question} {last_method}"

    needs_major_context = any(
        k in lower
        for k in [
            "điểm chuẩn",
            "điểm xét",
            "bao nhiêu điểm",
            "cut-off",
            "cutoff",
            "ttnv",
            "thứ tự nguyện vọng",
            "phương thức",
            "xét tuyển",
            "chương trình",
            "định hướng",
            "nghề nghiệp",
            "cơ hội",
            "việc làm",
        ]
    )
    should_attach_major = needs_major_context and not is_forecast_score_query(question)
    if should_attach_major and not find_major_code(routed_question) and last_major and last_major in SCORE_DB:
        routed_question = f"{routed_question} {last_major}"

    # Check if this is a follow-up about the school in general
    has_school_token = any(k in lower for k in ["ptit", "học viện", "trường"])
    school_keywords = [
        "họ", "trường đó", "trường này", "ở đó", "thế mạnh", "nổi bật",
        "cơ sở", "cơ sở vật chất", "phòng lab", "thư viện", "ký túc", "ktx",
        "học phí", "học bổng", "phương thức", "xét tuyển", "tuyển sinh"
    ]
    is_school_followup = (not has_school_token) and any(k in lower for k in school_keywords)
    
    if is_school_followup:
        if not needs_major_context:
            routed_question = f"{routed_question} của PTIT"

    # Áp dụng prefix "bad" vào routed_question trước khi gửi tới LLM hoặc Router
    final_routed_question = f"{llm_prefix}{routed_question}"

    # Kiểm tra trực tiếp qua query_router (stateless)
    direct_answer = route_query(final_routed_question)
    if direct_answer:
        # Cập nhật lịch sử với câu trả lời trực tiếp (dùng question gốc)
        history.append((question, direct_answer))
        ma = find_major_code(final_routed_question) or find_major_code(question)
        method = find_admission_method_code(final_routed_question) or find_admission_method_code(question)
        if ma:
            ctx["last_major"] = ma
        if method:
            ctx["last_method"] = method
        if any(
            k in direct_answer
            for k in [
                "PTIT (Posts and Telecommunications Institute of Technology)",
                "Học viện Công nghệ Bưu chính Viễn thông",
                "Thông tin liên hệ PTIT:",
                "Một số ngành/lĩnh vực được nhắc như thế mạnh",
                "Tóm tắt nhanh:",
                "Cơ sở vật chất của PTIT:",
                "Thông tin học phí và học bổng tại PTIT",
            ]
        ):
            ctx["last_topic"] = "school_info"
        elif "PTIT tuyển sinh" in direct_answer or "tuyển sinh" in direct_answer and "PT1" in direct_answer and "PT5" in direct_answer:
            ctx["last_topic"] = "admission_methods"
        elif method:
            ctx["last_topic"] = "admission_methods"
        elif ma:
            ctx["last_topic"] = "major"
        session_context[session_id] = ctx
        chat_histories[session_id] = history[-30:]
        return direct_answer

    if any(k in lower for k in ["điểm chuẩn", "điểm xét", "bao nhiêu điểm", "cut-off", "cutoff", "ttnv", "thứ tự nguyện vọng"]) and not find_major_code(final_routed_question):
        return "Hiện tại mình chưa có thông tin chính xác về nội dung này. Bạn có thể cho mình biết bạn đang hỏi ngành nào được không?"

    # Nếu không có câu trả lời trực tiếp, dùng RAG chain có hỗ trợ memory
    chain = _get_qa_chain()
    if not chain:
        return "Hiện tại mình chưa có thông tin chính xác về nội dung này. Bạn có thể cung cấp thêm chi tiết được không?"
    
    try:
        result = chain({"question": final_routed_question, "chat_history": history})
    except Exception as e:
        print(f"Lỗi khi chạy RAG chain: {e}")
        return "Hiện tại mình chưa có thông tin chính xác về nội dung này. Bạn có thể cung cấp thêm chi tiết được không?"

    srcs = result.get("source_documents") or []
    answer = result.get("answer", "") # ConversationalRetrievalChain dùng key "answer"

    if not answer or len(srcs) == 0 or "Hiện tại mình chưa có thông tin" in answer:
        return "Hiện tại mình chưa có thông tin chính xác về nội dung này. Bạn có thể cung cấp thêm chi tiết được không?"
    if _has_non_vietnamese_word(answer):
        return "Hiện tại mình chưa có thông tin chính xác về nội dung này. Bạn có thể cung cấp thêm chi tiết được không?"

    # Cập nhật lịch sử (dùng question gốc)
    history.append((question, answer))
    chat_histories[session_id] = history[-30:]
    ma = find_major_code(final_routed_question) or find_major_code(question)
    if ma:
        ctx["last_major"] = ma
    files = sorted({d.metadata.get("source_file", "(nguồn không rõ)") for d in srcs})
    inferred = _infer_topic_from_sources(files)
    if inferred:
        ctx["last_topic"] = inferred
    session_context[session_id] = ctx
    if files:
        answer = f"{answer}\n\nNguồn: {', '.join(files)}"

    return answer


from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Request


app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    rating: str | None = None

@app.post("/chat")
def chat(req: ChatRequest):

    response = ask(req.message, req.session_id, req.rating)

    return {"response": response}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

#uvicorn app:app --reload
