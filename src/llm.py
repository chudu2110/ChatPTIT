from langchain_ollama import ChatOllama
from .config import *


def load_llm():
    llm = ChatOllama(
        model=LLM_MODEL,
        temperature=0,          # Loại bỏ sáng tạo — chỉ trả lời dựa trên data
        num_predict=600,        # Giới hạn token output — tránh lan man, ảo giác kéo dài
        repeat_penalty=1.2,     # Phạt lặp từ — giảm language drift
        stop=["Question:", "Context:", "Human:", "User:"],  # Dừng nếu bot cố tự tạo Q&A
    )
    return llm