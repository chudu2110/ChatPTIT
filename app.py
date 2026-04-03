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
        qa_chain = create_rag_chain()
    return qa_chain

# Dictionary lưu trữ lịch sử chat theo session_id (giả lập)
chat_histories = {}
session_context = {}

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

def ask(question: str, session_id: str = "default") -> str:
    # Lấy lịch sử chat của session
    history = chat_histories.get(session_id, [])
    ctx = session_context.get(session_id, {})
    
    lower = question.lower().strip()
    has_pronoun = any(k in lower for k in ["nó", "ngành này", "ngành đó", "chương trình này", "mã này"])
    ma_in_question = find_major_code(question)
    method_in_question = find_admission_method_code(question)
    last_major = ctx.get("last_major")
    last_topic = ctx.get("last_topic")
    last_method = ctx.get("last_method")

    routed_question = question
    if has_pronoun and not ma_in_question and last_major and last_major in SCORE_DB:
        routed_question = f"{question} {last_major}"

    wants_more_detail = any(k in lower for k in ["chi tiết", "cụ thể", "nói rõ", "giải thích", "kỹ hơn", "thêm"])
    if wants_more_detail and not method_in_question and last_method:
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
        routed_question = f"{question} {last_major}"

    has_school_token = any(k in lower for k in ["ptit", "học viện", "trường"])
    is_school_followup = (
        (last_topic == "school_info")
        and (not has_school_token)
        and any(k in lower for k in ["họ", "trường đó", "trường này", "ở đó", "thế mạnh", "nổi bật", "ngành"])
    )
    if is_school_followup:
        routed_question = f"{question} của PTIT"

    # Kiểm tra trực tiếp qua query_router (stateless)
    direct_answer = route_query(routed_question)
    if direct_answer:
        # Cập nhật lịch sử với câu trả lời trực tiếp
        history.append((question, direct_answer))
        ma = find_major_code(routed_question) or find_major_code(question)
        method = find_admission_method_code(routed_question) or find_admission_method_code(question)
        if ma:
            ctx["last_major"] = ma
        if method:
            ctx["last_method"] = method
        if any(k in direct_answer for k in ["PTIT (Posts and Telecommunications Institute of Technology)", "Học viện Công nghệ Bưu chính Viễn thông", "Thông tin liên hệ PTIT:", "Một số ngành/lĩnh vực được nhắc như thế mạnh", "Tóm tắt nhanh:"]):
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

    if any(k in lower for k in ["điểm chuẩn", "điểm xét", "bao nhiêu điểm", "cut-off", "cutoff", "ttnv", "thứ tự nguyện vọng"]) and not find_major_code(routed_question):
        return "Hiện tại mình chưa có thông tin chính xác về nội dung này. Bạn có thể cho mình biết bạn đang hỏi ngành nào được không?"

    # Nếu không có câu trả lời trực tiếp, dùng RAG chain có hỗ trợ memory
    chain = _get_qa_chain()
    result = chain({"question": routed_question, "chat_history": history})

    srcs = result.get("source_documents") or []
    answer = result.get("answer", "") # ConversationalRetrievalChain dùng key "answer"

    if not answer or len(srcs) == 0 or "Hiện tại mình chưa có thông tin" in answer:
        return "Hiện tại mình chưa có thông tin chính xác về nội dung này. Bạn có thể cung cấp thêm chi tiết được không?"
    if _has_non_vietnamese_word(answer):
        return "Hiện tại mình chưa có thông tin chính xác về nội dung này. Bạn có thể cung cấp thêm chi tiết được không?"

    # Cập nhật lịch sử
    history.append((question, answer))
    chat_histories[session_id] = history[-30:]
    ma = find_major_code(routed_question) or find_major_code(question)
    if ma:
        ctx["last_major"] = ma
        session_context[session_id] = ctx

    files = sorted({d.metadata.get("source_file", "(nguồn không rõ)") for d in srcs})
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

@app.post("/chat")
def chat(req: ChatRequest):

    response = ask(req.message, req.session_id)

    return {"response": response}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

#uvicorn app:app --reload
