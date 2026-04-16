"""LLM service — Improved prompt engineering with anti-hallucination guardrails"""

from typing import Optional
import requests
from config import LLM_API_KEY, LLM_MODEL, USE_LOCAL_LLM


SYSTEM_PROMPT = """\
Bạn là chatbot tư vấn tuyển sinh PTIT (Học viện Công nghệ Bưu chính Viễn thông).
Vai trò của bạn là một tư vấn viên tuyển sinh thân thiện, rõ ràng và đáng tin cậy.
Nhiệm vụ của bạn là trả lời chính xác các câu hỏi về tuyển sinh dựa HOÀN TOÀN vào thông tin được cung cấp trong phần [NGỮ CẢNH].

## QUY TẮC BẮT BUỘC:
1. **Chỉ sử dụng thông tin từ [NGỮ CẢNH]** — Tuyệt đối không bịa hoặc dùng kiến thức ngoài.
2. **Phân biệt rõ TTNV và Điểm chuẩn:**
   - **Điểm chuẩn (PT5)**: là điểm thi THPT /30, ví dụ: 26.55, 25.10 — đây là ngưỡng điểm để đỗ.
   - **TTNV (Thứ tự nguyện vọng)**: là số từ 1–6, ví dụ: ≤5 — cho biết thứ tự NV tối đa khi có điểm bằng điểm chuẩn.
   - KHÔNG bao giờ nhầm lẫn hai giá trị này với nhau.
3. Nếu ngữ cảnh không đủ thông tin, hãy nói thẳng: "Tôi không có thông tin chính xác về vấn đề này, vui lòng liên hệ phòng tuyển sinh PTIT: 1800.599.980."
4. Trả lời bằng tiếng Việt, rõ ràng, thân thiện, có cấu trúc (dùng bullet points nếu phù hợp).
5. Không thêm disclaimer thừa hay lặp lại câu hỏi của người dùng.
6. Nếu câu hỏi nói về một ngành cụ thể, hãy ưu tiên thông tin của đúng ngành đó; không trả lời sang thông tin giới thiệu trường nếu ngữ cảnh có ngành.
7. Ưu tiên trả lời tự nhiên như tư vấn viên, nhưng vẫn bám sát số liệu/dữ kiện trong ngữ cảnh.
8. Nếu người dùng đang hỏi khả năng đỗ, hãy trả lời theo hướng cân nhắc/xác suất hợp lý, không khẳng định chắc chắn đỗ hoặc trượt khi dữ liệu chỉ là mốc tham chiếu.
9. Ưu tiên câu mở đầu ngắn gọn, sau đó trình bày 2-5 ý chính thật dễ hiểu.
10. Nếu người dùng chưa đủ điều kiện tối thiểu của một phương thức, hãy nói rõ là chưa đủ điều kiện trước khi bàn tới khả năng đỗ.
"""


class LLMService:
    def __init__(self):
        self.model = LLM_MODEL
        self.api_key = LLM_API_KEY
        self.use_local = USE_LOCAL_LLM

    def generate_response(
        self,
        query: str,
        context: str = "",
        recommendation: str = "",
        direct_answer: str = "",
        max_tokens: int = 600,
    ) -> str:
        """
        Generate response.
        If direct_answer is provided (from KB lookup), return it immediately
        without calling LLM to save latency and avoid hallucination.
        """
        if direct_answer:
            return direct_answer

        if not self.api_key and not self.use_local:
            return self._generate_fallback(query, context, recommendation)

        prompt = self._build_prompt(query, context, recommendation)

        try:
            if self.use_local:
                result = self._generate_local(prompt, max_tokens)
            else:
                result = self._generate_api(prompt, max_tokens)
            if result:
                return result
            return self._generate_fallback(query, context, recommendation)
        except Exception as e:
            print(f"LLM error: {e}")
            return self._generate_fallback(query, context, recommendation)

    def _build_prompt(self, query: str, context: str, recommendation: str) -> str:
        """Build structured prompt: System → Context → Recommendation → Question"""
        parts = [SYSTEM_PROMPT]

        if context:
            parts.append(f"\n[NGỮ CẢNH]\n{context}")
        else:
            parts.append("\n[NGỮ CẢNH]\n(Không có ngữ cảnh đáng tin cậy. Nếu thiếu dữ liệu, hãy từ chối trả lời suy đoán.)")

        if recommendation:
            parts.append(f"\n[KẾT QUẢ TRA CỨU]\n{recommendation}")

        parts.append(f"\n[CÂU HỎI]\n{query}")
        parts.append("\n[TRẢ LỜI]")
        return "\n".join(parts)

    def _generate_api(self, prompt: str, max_tokens: int) -> str:
        """Generate using HuggingFace Inference API"""
        try:
            url = f"https://api-inference.huggingface.co/models/{self.model}"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": 0.3,      # Lower temperature = less hallucination
                    "top_p": 0.90,
                    "repetition_penalty": 1.1,
                    "return_full_text": False,
                },
            }
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and result:
                    text = result[0].get("generated_text", "").strip()
                    # Strip any prompt echo
                    if "[TRẢ LỜI]" in text:
                        text = text.split("[TRẢ LỜI]")[-1].strip()
                    return text
        except Exception as e:
            print(f"API error: {e}")

        return ""

    def _generate_local(self, prompt: str, max_tokens: int) -> str:
        """Generate using local Ollama"""
        try:
            import ollama
            response = ollama.generate(
                model="mistral",
                prompt=prompt,
                options={"temperature": 0.3, "num_predict": max_tokens},
                stream=False,
            )
            return response.get("response", "").strip()
        except Exception as e:
            print(f"Local LLM error: {e}")
            return ""

    def _generate_fallback(self, query: str, context: str, recommendation: str) -> str:
        """Structured fallback when LLM unavailable"""
        if recommendation:
            if context:
                return f"{recommendation}\n\n{self._summarize_context(context, 800)}"
            return recommendation
        if context:
            return self._summarize_context(context, 1000)
        return self._generate_fallback_simple(query)

    def _summarize_context(self, context: str, limit: int) -> str:
        """Return a cleaner, grounded context-only answer when no LLM is available."""
        lines = []
        for line in context.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("[") and stripped.endswith("]"):
                continue
            if stripped in {"---"}:
                continue
            if stripped.startswith(("**Tags:**", "**Keywords:**", "**Category:**")):
                continue
            lines.append(stripped)
        text = "\n".join(lines)
        if len(text) > limit:
            text = text[:limit].rsplit(" ", 1)[0] + "..."
        return f"Trong dữ liệu mình tra được, thông tin phù hợp nhất là:\n\n{text}"

    def _generate_fallback_simple(self, query: str) -> str:
        """Minimal fallback when no context or LLM"""
        q = query.lower()
        if any(w in q for w in ["học phí", "tiền học", "học bổng"]):
            return ("Học phí PTIT 2025:\n"
                    "• Ngành kỹ thuật đại trà: 25–35 triệu đồng/năm\n"
                    "• Ngành kinh tế, truyền thông: 25–30 triệu đồng/năm\n"
                    "• Chương trình chất lượng cao (CLC): 35–45 triệu đồng/năm\n"
                    "Chi tiết về học bổng, vui lòng hỏi thêm!")
        if any(w in q for w in ["điểm chuẩn", "cần bao nhiêu điểm"]):
            return "Để biết điểm chuẩn cụ thể, hãy hỏi đúng tên ngành, ví dụ: 'Điểm chuẩn ngành CNTT là bao nhiêu?'"
        if any(w in q for w in ["ngành", "chuyên ngành"]):
            return ("PTIT có nhiều ngành đào tạo:\n"
                    "• Công nghệ Thông tin (CNTT) — Điểm chuẩn 2025: 26.55\n"
                    "• An toàn Thông tin (ATTT) — 26.10\n"
                    "• Khoa học Máy tính — 26.40\n"
                    "• Truyền thông Đa phương tiện — 26.20\n"
                    "• Và nhiều ngành khác. Bạn muốn biết thêm ngành nào?")
        return "Cảm ơn câu hỏi của bạn! Để được tư vấn chính xác, vui lòng liên hệ phòng tuyển sinh PTIT: ☎️ 1800.599.980 (miễn phí)."
