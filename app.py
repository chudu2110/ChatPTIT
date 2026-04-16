"""Main FastAPI backend for PTIT Admission Chatbot — Improved RAG Pipeline"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import re

from config import TOP_K_RETRIEVAL, DATA_FILES
from data_loader import (
    DocumentLoader,
    init_knowledge_base,
    load_markdown_content,
    lookup_score,
    get_knowledge_base,
)
from recommendation_engine import RecommendationEngine
from llm_service import LLMService
from cutoffs import find_major_by_query, get_cutoffs as get_cutoff_data

# Embedding service — real FAISS-based
from embedding_service import EmbeddingService

# Initialize FastAPI
app = FastAPI(title="PTIT Admission Chatbot", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services
doc_loader: Optional[DocumentLoader] = None
embedding_service: Optional[EmbeddingService] = None
recommendation_engine: Optional[RecommendationEngine] = None
llm_service: Optional[LLMService] = None
initialized = False

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


# Pydantic models
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    rating: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    source: str
    intent: str = ""
    mode: str = "chat"


class HealthResponse(BaseModel):
    status: str
    initialized: bool


# -----------------------------------------------------------------------
# Initialization
# -----------------------------------------------------------------------
def initialize_services():
    """Initialize all services on startup"""
    global doc_loader, embedding_service, recommendation_engine, llm_service, initialized

    if initialized:
        return

    print("\n[INIT] Initializing PTIT Chatbot System v2.0...")

    # 1. Knowledge base (structured, fast lookup)
    print("[INIT] Loading knowledge base...")
    init_knowledge_base()

    # 2. Load and chunk all documents
    print("[INIT] Loading & chunking documents...")
    doc_loader = DocumentLoader()
    documents = doc_loader.load_all_documents()

    # 3. Build FAISS vector index (cached to disk)
    print("[INIT] Building vector index...")
    embedding_service = EmbeddingService()
    embedding_service.create_index(documents)

    # 4. Recommendation engine
    print("[INIT] Initializing recommendation engine...")
    recommendation_engine = RecommendationEngine()

    # 5. LLM service
    print("[INIT] Initializing LLM service...")
    llm_service = LLMService()

    initialized = True
    print("\n[OK] System ready!\n")


# -----------------------------------------------------------------------
# Helper — Fallback full-text keyword search across ALL data files
# -----------------------------------------------------------------------
def _keyword_fallback_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Improved fallback: searches ALL data files, returns FULL sections (not 300 chars).
    Uses keyword scoring to rank results.
    """
    keywords = [w for w in re.findall(r'\w{3,}', query.lower()) if len(w) >= 3]
    if not keywords:
        return []

    results = []
    kb = get_knowledge_base()
    section_map = kb.get("sections", {})

    for filename in DATA_FILES:
        for section in section_map.get(filename, []):
            section_lower = section.lower()
            score = sum(1 for kw in keywords if kw in section_lower)
            if score > 0:
                results.append({
                    "text": section[:1200],
                    "source": filename,
                    "type": "fallback",
                    "score": score,
                })

    # Sort by score, take top_k
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_relevant_section(filename: str, query: str) -> Optional[str]:
    kb = get_knowledge_base()
    sections = kb.get("sections", {}).get(filename, [])
    if not sections:
        return None

    keywords = [w for w in re.findall(r"\w{3,}", query.lower()) if len(w) >= 3]
    best_section = None
    best_score = 0

    for section in sections:
        section_lower = section.lower()
        score = sum(2 if kw in section_lower else 0 for kw in keywords)
        if query.lower() in section_lower:
            score += 3
        if score > best_score:
            best_score = score
            best_section = section

    return best_section if best_score > 0 else sections[0]


def _format_section_answer(title: str, body: str, limit: int = 900) -> str:
    body = _normalize_text(body)
    if len(body) > limit:
        body = body[:limit].rsplit(" ", 1)[0] + "..."
    return f"📌 **{title}**\n\n{body}"


def _clean_section_text(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == "---":
            continue
        if stripped.startswith(("**Tags:**", "**Keywords:**", "**Category:**")):
            continue
        lines.append(stripped)
    return "\n".join(lines)


def _is_broad_admission_query(query: str) -> bool:
    query_lower = query.lower()
    broad_keywords = [
        "phương thức tuyển sinh",
        "các phương thức",
        "bao nhiêu phương thức",
        "tất cả phương thức",
        "toàn bộ phương thức",
        "xét tuyển như thế nào",
        "các hình thức xét tuyển",
    ]
    specific_keywords = ["ielts", "toefl", "sat", "act", "hsa", "tsa", "apt", "spt", "pt1", "pt2", "pt3", "pt4", "pt5"]
    return any(keyword in query_lower for keyword in broad_keywords) and not any(
        keyword in query_lower for keyword in specific_keywords
    )


def _is_method_cutoff_lookup(query: str) -> bool:
    q = query.lower()
    method_tokens = ["pt1", "pt4", "sat", "act", "hsa", "tsa", "spt", "apt", "ielts", "toefl"]
    amount_tokens = ["bao nhiêu", "bao nhieu", "mốc", "điểm chuẩn", "lấy bao nhiêu", "bao nhiêu điểm"]
    return any(token in q for token in method_tokens) and any(token in q for token in amount_tokens)


def _format_all_admission_methods() -> str:
    return """📌 **Các phương thức tuyển sinh PTIT 2026**

| Phương thức | Nội dung chính | Điều kiện/Ngưỡng cơ bản |
|---|---|---|
| PT1 | Xét tuyển tài năng | Xét tuyển thẳng hoặc hồ sơ năng lực; học lực lớp 10-12 từ 7.5 trở lên, hạnh kiểm Khá trở lên cho diện hồ sơ năng lực |
| PT2 | Chứng chỉ quốc tế SAT/ACT | SAT từ 1130/1600 hoặc ACT từ 25/36 trở lên |
| PT3 | Đánh giá năng lực/tư duy | HSA từ 75/150, TSA từ 50/100, SPT từ 15/30, APT từ 600/1200 trở lên |
| PT4 | Chứng chỉ tiếng Anh + học bạ | IELTS 5.5 hoặc TOEFL iBT 65 hoặc TOEFL ITP 513; học lực lớp 10-12 từ 7.5 trở lên, hạnh kiểm Khá trở lên |
| PT5 | Điểm thi tốt nghiệp THPT | Xét theo tổng điểm 3 môn trong tổ hợp + điểm ưu tiên nếu có |

**Lưu ý thêm:**
- PT5 là phương thức chính và phổ biến nhất.
- Một số ngành có quy định **TTNV**: nếu bằng đúng điểm chuẩn, bạn cần đặt ngành ở thứ tự nguyện vọng không vượt quá mức TTNV.
- Nếu bạn muốn, mình có thể giải thích chi tiết riêng từng phương thức như `PT1`, `PT4`, `SAT/ACT`, `IELTS`, hoặc cách tính điểm xét tuyển."""


def _format_identity_answer() -> str:
    return (
        "Mình là chatbot tư vấn tuyển sinh PTIT. "
        "Mình có thể hỗ trợ tra cứu điểm chuẩn, TTNV, phương thức tuyển sinh, học phí, học bổng, "
        "giới thiệu ngành và gợi ý ngành phù hợp theo điểm hoặc sở thích của bạn."
    )


def _is_forecast_query(query: str) -> bool:
    q = query.lower()
    return any(token in q for token in ["2026", "2027", "năm sau", "sẽ tăng", "sẽ giảm", "liệu có tăng", "dự đoán điểm", "đoán điểm"]) and any(
        token in q for token in ["điểm chuẩn", "cutoff", "đỗ", "tăng điểm", "giảm điểm"]
    )


def _format_forecast_answer(query: str) -> str:
    major = find_major_by_query(query)
    if major:
        return (
            f"Mình chưa có dữ liệu chính thức để dự đoán **điểm chuẩn {major.name}** cho năm tới.\n\n"
            f"Hiện mình chỉ có mốc tham chiếu chắc chắn là **điểm chuẩn 2025 của ngành này: {major.cutoff_pt5} điểm**.\n\n"
            "Vì điểm chuẩn năm sau còn phụ thuộc vào số lượng hồ sơ, độ khó đề thi và mặt bằng điểm chung, "
            "nên mình không nên đoán một con số cụ thể. Cách an toàn hơn là bạn:\n"
            f"- lấy mốc {major.cutoff_pt5} làm tham chiếu\n"
            "- cố gắng tạo khoảng dư điểm nếu có thể\n"
            "- chuẩn bị thêm phương án ở các ngành gần hoặc phương thức khác\n\n"
            "Bạn cứ tập trung học thật tốt và tối ưu hồ sơ; nếu muốn, mình có thể gợi ý cho bạn một danh sách ngành an toàn, vừa sức và thử sức."
        )
    return (
        "Mình chưa có dữ liệu chính thức để dự đoán điểm chuẩn năm tới một cách đáng tin cậy.\n\n"
        "Điểm chuẩn các năm sau có thể thay đổi theo số lượng thí sinh, mức độ cạnh tranh và mặt bằng điểm chung, "
        "nên mình không nên đoán trước một con số cụ thể.\n\n"
        "Cách an toàn nhất là bạn dùng dữ liệu 2025 làm mốc tham chiếu, học tập thật tốt và chuẩn bị thêm vài phương án phù hợp theo điểm cũng như phương thức xét tuyển."
    )


def _format_method_conditions_answer(query: str) -> Optional[str]:
    q = query.lower()
    if any(keyword in q for keyword in ["hồ sơ năng lực", "hsnl", "pt1", "tài năng", "xét tuyển tài năng"]):
        return """📌 **Điều kiện chính của PT1 (xét tuyển tài năng/hồ sơ năng lực)**  

- PT1 gồm diện **xét tuyển thẳng** và **xét tuyển dựa vào hồ sơ năng lực**.
- Với diện **hồ sơ năng lực**, thí sinh cần có **một trong các điều kiện thành tích phù hợp** theo thông báo của PTIT.
- Đồng thời cần có:
- **Kết quả trung bình chung học tập lớp 10, 11, 12 từ 7.5 trở lên**
- **Hạnh kiểm Khá trở lên**

Nếu bạn muốn, mình có thể giải thích kỹ hơn PT1 theo hướng `điều kiện`, `cách tính điểm`, hoặc xem hồ sơ của bạn có phù hợp không."""

    if any(keyword in q for keyword in ["pt4", "học bạ", "học ba", "ielts", "toefl"]):
        return """📌 **Điều kiện chính của PT4 (chứng chỉ tiếng Anh + học bạ)**  

- Cần có một trong các chứng chỉ còn hạn:
- **IELTS từ 5.5 trở lên**
- **TOEFL iBT từ 65 trở lên**
- **TOEFL ITP từ 513 trở lên**
- Đồng thời cần có:
- **Kết quả trung bình chung học tập lớp 10, 11, 12 từ 7.5 trở lên**
- **Hạnh kiểm Khá trở lên**

Sau khi đủ điều kiện, điểm xét tuyển PT4 sẽ được đối chiếu với mốc điểm của từng ngành."""

    if any(keyword in q for keyword in ["sat", "act", "pt2"]):
        return """📌 **Điều kiện chính của PT2 (SAT/ACT)**  

- **SAT từ 1130/1600 trở lên**, hoặc
- **ACT từ 25/36 trở lên**
- Chứng chỉ cần còn hạn theo quy định của PTIT.

Sau khi đủ điều kiện, bạn sẽ được so với mốc điểm tham chiếu SAT/ACT của từng ngành."""

    if any(keyword in q for keyword in ["hsa", "tsa", "apt", "spt", "đánh giá năng lực", "đánh giá tư duy", "pt3"]):
        return """📌 **Điều kiện chính của PT3 (ĐGNL/ĐGTD)**  

- **HSA từ 75/150 trở lên**
- **TSA từ 50/100 trở lên**
- **SPT từ 15/30 trở lên**
- **APT từ 600/1200 trở lên**

Sau khi đủ điều kiện, điểm của bạn sẽ được đối chiếu với mốc tham chiếu của từng ngành theo đúng loại bài thi."""

    if any(keyword in q for keyword in ["pt5", "thpt", "điểm thi"]):
        return """📌 **PT5 (điểm thi tốt nghiệp THPT)**  

- Đây là phương thức xét tuyển bằng **điểm thi tốt nghiệp THPT**.
- Điểm xét tuyển = **tổng điểm 3 môn trong tổ hợp xét tuyển + điểm ưu tiên (nếu có)**.
- Sau đó đối chiếu với **điểm chuẩn PT5** của từng ngành."""

    return None


def _parse_english_bonus(query: str) -> Optional[Dict[str, Any]]:
    query_lower = query.lower()
    ielts_match = re.search(r"ielts\s*([4-9](?:[.,]\d)?)", query_lower)
    if ielts_match:
        score = float(ielts_match.group(1).replace(",", "."))
        if score >= 7.0:
            bonus = 1.5
        elif score >= 6.5:
            bonus = 1.0
        elif score >= 6.0:
            bonus = 0.75
        elif score >= 5.5:
            bonus = 0.5
        else:
            bonus = 0.0
        return {"exam": "IELTS", "score": score, "bonus": bonus}

    ibt_match = re.search(r"toefl\s*ibt\s*([0-9]{2,3})", query_lower)
    if ibt_match:
        score = int(ibt_match.group(1))
        if score >= 94:
            bonus = 1.5
        elif score >= 86:
            bonus = 1.0
        elif score >= 72:
            bonus = 0.75
        elif score >= 46:
            bonus = 0.5
        else:
            bonus = 0.0
        return {"exam": "TOEFL iBT", "score": score, "bonus": bonus}

    itp_match = re.search(r"toefl\s*itp\s*([0-9]{3})", query_lower)
    if itp_match:
        score = int(itp_match.group(1))
        if score >= 627:
            bonus = 1.5
        elif score >= 591:
            bonus = 1.0
        elif score >= 546:
            bonus = 0.75
        elif score >= 500:
            bonus = 0.5
        else:
            bonus = 0.0
        return {"exam": "TOEFL ITP", "score": score, "bonus": bonus}

    return None


def _parse_method_score(query: str) -> Optional[Dict[str, Any]]:
    q = query.lower()
    method_configs = [
        ("sat", ["sat"], r"sat[^\d]{0,10}(\d{3,4}(?:[.,]\d+)?)", "cutoff_sat"),
        ("act", ["act"], r"act[^\d]{0,10}(\d{1,2}(?:[.,]\d+)?)", "cutoff_act"),
        ("hsa", ["hsa", "đánh giá năng lực", "đhqg hà nội"], r"(?:hsa|đánh giá năng lực)[^\d]{0,15}(\d{1,3}(?:[.,]\d+)?)", "cutoff_hsa"),
        ("tsa", ["tsa", "đánh giá tư duy"], r"(?:tsa|đánh giá tư duy)[^\d]{0,15}(\d{1,3}(?:[.,]\d+)?)", "cutoff_tsa"),
        ("spt", ["spt"], r"spt[^\d]{0,10}(\d{1,2}(?:[.,]\d+)?)", "cutoff_spt"),
        ("apt", ["apt", "đhqg tp"], r"(?:apt|đhqg tp)[^\d]{0,15}(\d{2,4}(?:[.,]\d+)?)", "cutoff_apt"),
    ]

    if any(keyword in q for keyword in ["học bạ", "học ba", "ielts", "toefl", "pt4"]):
        score_match = re.search(r"(\d{1,2}(?:[.,]\d+)?)\s*điểm\s*học\s*bạ|(\d{1,2}(?:[.,]\d+)?)\s*học\s*bạ", q)
        if score_match:
            raw = next(group for group in score_match.groups() if group)
            base_score = float(raw.replace(",", "."))
            english = _parse_english_bonus(query)
            if english:
                return {
                    "method": "pt4",
                    "field": "cutoff_pt4",
                    "label": "PT4 (chứng chỉ tiếng Anh + học bạ)",
                    "score": round(base_score + english["bonus"], 2),
                    "base_score": base_score,
                    "english_exam": english["exam"],
                    "english_score": english["score"],
                    "bonus": english["bonus"],
                }

    if any(keyword in q for keyword in ["thpt", "điểm thi", "pt5"]):
        score_match = re.search(r"(\d{1,2}(?:[.,]\d+)?)\s*điểm", q)
        if score_match:
            return {
                "method": "pt5",
                "field": "cutoff_pt5",
                "label": "PT5 (điểm thi THPT)",
                "score": float(score_match.group(1).replace(",", ".")),
            }

    for method, keywords, pattern, field in method_configs:
        if any(keyword in q for keyword in keywords):
            match = re.search(pattern, q)
            if match:
                return {
                    "method": method,
                    "field": field,
                    "label": method.upper(),
                    "score": float(match.group(1).replace(",", ".")),
                }

    return None


def _check_method_eligibility(score_info: Dict[str, Any]) -> Dict[str, Any]:
    """Check minimum method conditions before comparing with cutoff references."""
    field = score_info["field"]

    if field == "cutoff_pt4":
        english_score = score_info.get("english_score", 0)
        exam = score_info.get("english_exam", "")
        minimums = {
            "IELTS": 5.5,
            "TOEFL iBT": 65,
            "TOEFL ITP": 513,
        }
        min_required = minimums.get(exam, 0)
        ok = english_score >= min_required
        reason = (
            f"Bạn **chưa đủ điều kiện PT4** vì {exam} hiện là **{english_score}**, trong khi mức tối thiểu là **{min_required}**."
            if not ok else
            f"Bạn **đủ điều kiện chứng chỉ tiếng Anh của PT4** vì {exam} đạt **{english_score}** (tối thiểu {min_required})."
        )
        extra = "Lưu ý: PT4 còn yêu cầu **kết quả trung bình chung lớp 10-12 từ 7.5 trở lên** và **hạnh kiểm Khá trở lên**."
        return {"eligible": ok, "reason": reason, "extra": extra}

    thresholds = {
        "cutoff_sat": 1130,
        "cutoff_act": 25,
        "cutoff_hsa": 75,
        "cutoff_tsa": 50,
        "cutoff_spt": 15,
        "cutoff_apt": 600,
    }
    labels = {
        "cutoff_sat": "SAT",
        "cutoff_act": "ACT",
        "cutoff_hsa": "HSA",
        "cutoff_tsa": "TSA",
        "cutoff_spt": "SPT",
        "cutoff_apt": "APT",
    }
    if field in thresholds:
        min_required = thresholds[field]
        label = labels[field]
        ok = score_info["score"] >= min_required
        reason = (
            f"Bạn **chưa đủ điều kiện {label}** vì hiện mới đạt **{score_info['score']}**, trong khi tối thiểu cần **{min_required}**."
            if not ok else
            f"Bạn **đã đủ điều kiện sơ bộ theo {label}** vì đạt **{score_info['score']}** (tối thiểu {min_required})."
        )
        return {"eligible": ok, "reason": reason, "extra": ""}

    return {"eligible": True, "reason": "", "extra": ""}


def _recommend_by_method_score(score_info: Dict[str, Any], category: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    thresholds = {
        "cutoff_pt5": (1.0, 3.0),
        "cutoff_pt4": (1.0, 3.0),
        "cutoff_sat": (30.0, 100.0),
        "cutoff_act": (1.0, 3.0),
        "cutoff_hsa": (3.0, 10.0),
        "cutoff_tsa": (3.0, 10.0),
        "cutoff_spt": (1.0, 3.0),
        "cutoff_apt": (30.0, 100.0),
    }
    near, stretch = thresholds.get(score_info["field"], (1.0, 3.0))
    results = {"safe": [], "match": [], "stretch": []}

    for info in recommendation_engine.majors.values():
        if category and info.get("category") != category:
            continue
        cutoff_major = next((m for m in get_cutoff_data() if m.code == info["code"]), None)
        if not cutoff_major:
            continue
        cutoff_value = getattr(cutoff_major, score_info["field"], None)
        if cutoff_value is None:
            continue
        gap = score_info["score"] - float(cutoff_value)
        item = {
            "id": info["code"],
            "name": cutoff_major.name,
            "cutoff": float(cutoff_value),
            "ttnv": cutoff_major.ttnv,
            "gap": abs(gap),
            "type": cutoff_major.program_type,
        }
        if gap >= 0:
            results["safe"].append(item)
        elif gap >= -near:
            results["match"].append(item)
        elif gap >= -stretch:
            results["stretch"].append(item)

    for bucket in results.values():
        bucket.sort(key=lambda x: x["gap"])
    return results


def _format_method_recommendation(score_info: Dict[str, Any], recommendations: Dict[str, List[Dict[str, Any]]], category: Optional[str]) -> str:
    total = sum(len(v) for v in recommendations.values())
    category_labels = {
        "cong_nghe": "nhóm ngành Công nghệ",
        "kinh_te": "nhóm ngành Kinh tế",
        "truyen_thong": "nhóm ngành Truyền thông",
    }
    category_text = f" cho {category_labels.get(category, 'PTIT')}" if category else ""

    intro = f"🎯 **Đánh giá theo {score_info['label']}{category_text}:**"
    details = []
    if score_info["method"] == "pt4":
        details.append(
            f"Bạn có **{score_info['base_score']:.2f} điểm học bạ** và **{score_info['english_exam']} {score_info['english_score']:.1f}**, "
            f"được cộng **{score_info['bonus']:.2f} điểm**, nên điểm xét tuyển tạm tính theo PT4 là **{score_info['score']:.2f}**."
        )
    else:
        details.append(f"Mình đang đối chiếu mức **{score_info['score']:.2f}** của bạn theo phương thức **{score_info['label']}**.")

    if total == 0:
        details.append("Hiện mình chưa thấy ngành phù hợp trong nhóm bạn hỏi ở phương thức này.")
        return "\n\n".join([intro] + details)

    parts = [intro, *details]
    bucket_titles = [
        ("safe", "✅ Có khả năng cạnh tranh tốt", "Bạn đang đạt hoặc vượt mức tham chiếu"),
        ("match", "⚠️ Cần cân nhắc", "Bạn đang sát mức tham chiếu"),
        ("stretch", "💪 Thử sức", "Bạn còn thiếu một khoảng nhất định"),
    ]
    for key, title, note in bucket_titles:
        items = recommendations[key]
        if not items:
            continue
        parts.append(title)
        parts.append(note)
        parts.append("")
        parts.append("| Ngành | Mốc tham chiếu | Chênh lệch | TTNV |")
        parts.append("|---|---:|---:|---:|")
        for item in items[:5]:
            sign = "+" if key == "safe" else "-"
            parts.append(f"| {item['name']} | {item['cutoff']:.2f} | {sign}{item['gap']:.2f} | <={item['ttnv']} |")
        parts.append("")

    if not recommendations["safe"] and recommendations["match"]:
        parts.append("Nhìn chung, ở phương thức này bạn đang ở mức **sát ngưỡng** với một số ngành, nên vẫn có thể cân nhắc nhưng cần đặt kỳ vọng thực tế.")
    elif not recommendations["safe"] and not recommendations["match"] and recommendations["stretch"]:
        parts.append("Nhìn nhanh thì hiện chưa có ngành nào thật sự an toàn trong nhóm bạn hỏi; các ngành trên phù hợp theo hướng **thử sức** hơn.")
    elif recommendations["safe"]:
        parts.append("Tổng thể, bạn đang có một vài lựa chọn khá ổn theo phương thức này.")

    parts.append("Nếu bạn muốn, mình có thể tiếp tục so sánh giữa **PT4, PT5, SAT, HSA...** để xem phương thức nào lợi hơn cho bạn.")
    return "\n".join(parts).strip()


def _format_method_ineligible_answer(score_info: Dict[str, Any], eligibility: Dict[str, Any], category: Optional[str]) -> str:
    category_labels = {
        "cong_nghe": "nhóm ngành Công nghệ",
        "kinh_te": "nhóm ngành Kinh tế",
        "truyen_thong": "nhóm ngành Truyền thông",
    }
    category_text = category_labels.get(category, "nhóm ngành bạn đang hỏi")

    lines = [f"📌 **Đánh giá điều kiện theo {score_info['label']}**", ""]
    if score_info["method"] == "pt4":
        lines.append(
            f"Bạn đang có **{score_info['base_score']} điểm học bạ** và **{score_info['english_exam']} {score_info['english_score']}**."
        )
        lines.append("")
    lines.append(eligibility["reason"])
    if eligibility.get("extra"):
        lines.append(eligibility["extra"])
    lines.extend([
        "",
        f"Vì vậy, với dữ liệu hiện có thì bạn **chưa thể xét vào {category_text} bằng phương thức này**.",
        "Nếu bạn muốn, mình có thể kiểm tra giúp bạn theo phương thức khác như **PT5, SAT, HSA, TSA...** để xem còn lựa chọn nào phù hợp hơn.",
    ])
    return "\n".join(lines)


def _extract_bullets(section: str, limit: int = 5) -> List[str]:
    bullets = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
        if len(bullets) >= limit:
            break
    return bullets


def _extract_section_by_heading(content: str, heading: str) -> str:
    pattern = re.compile(
        rf"##\s+{re.escape(heading)}\s*\n(.*?)(?=\n##\s+|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(content)
    return match.group(1).strip() if match else ""


def _find_mentioned_majors(query: str) -> List[Any]:
    query_lower = query.lower()
    found = []
    seen_codes = set()
    cutoff_by_code = {major.code: major for major in get_cutoff_data()}
    for info in recommendation_engine.majors.values():
        names = {
            info["name"].lower(),
            info["code"].lower(),
            *[kw.lower() for kw in info.get("keywords", [])],
        }
        matched = any(name and name in query_lower for name in names)
        if matched and info["code"] in cutoff_by_code and info["code"] not in seen_codes:
            found.append(cutoff_by_code[info["code"]])
            seen_codes.add(info["code"])
    return found


def _is_major_list_query(query: str) -> bool:
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in [
        "có những ngành nào",
        "danh sách ngành",
        "các ngành",
        "ngành đào tạo",
        "khối ngành",
    ]) and "điểm" not in query_lower


def _format_major_list_answer(query: str) -> str:
    category = recommendation_engine.detect_category_filter(query)
    category_titles = {
        "cong_nghe": "Nhóm Công nghệ",
        "kinh_te": "Nhóm Kinh tế",
        "truyen_thong": "Nhóm Truyền thông",
    }
    grouped = {"cong_nghe": [], "kinh_te": [], "truyen_thong": []}
    for info in recommendation_engine.majors.values():
        grouped.setdefault(info.get("category", "cong_nghe"), []).append(info)
    for items in grouped.values():
        items.sort(key=lambda x: x["cutoff_score"], reverse=True)

    lines = ["📌 **Danh sách ngành đào tạo PTIT**", "", "Mình đã gom các ngành theo từng nhóm để bạn dễ theo dõi hơn:", ""]
    targets = [category] if category else ["cong_nghe", "kinh_te", "truyen_thong"]
    for key in targets:
        items = grouped.get(key, [])
        if not items:
            continue
        lines.append(f"**{category_titles.get(key, key)}**")
        lines.append("")
        lines.append("| Ngành | Mã | Điểm chuẩn 2025 | TTNV |")
        lines.append("|---|---|---:|---:|")
        for item in items:
            lines.append(f"| {item['name']} | {item['code']} | {item['cutoff_score']:.2f} | <={item['ttnv']} |")
        lines.append("")
    lines.append("Nếu bạn muốn, mình có thể lọc tiếp theo nhóm ngành, mức điểm hoặc giới thiệu kỹ một ngành cụ thể.")
    return "\n".join(lines)


def _format_intro_answer(query: str) -> str:
    intro_content = get_knowledge_base().get("intro", "")
    q1 = _extract_section_by_heading(intro_content, "Q1: PTIT là gì? PTIT là trường gì?")
    q2 = _extract_section_by_heading(intro_content, "Q2: PTIT có những đặc điểm gì nổi bật?")
    q3 = _extract_section_by_heading(intro_content, "Q3: PTIT có những khối ngành nào?")
    q5 = _extract_section_by_heading(intro_content, "Q5: PTIT ở đâu? Cơ sở vật chất ra sao?")

    school_type = _extract_bullets(q1, limit=4)
    strengths = _extract_bullets(q2, limit=4)
    fields = _extract_bullets(q3, limit=4)
    facilities = _extract_bullets(q5, limit=3)

    lines = [
        "📌 **Giới thiệu về PTIT**",
        "",
        "PTIT (Học viện Công nghệ Bưu chính Viễn thông) là trường đại học công lập, nổi bật ở các lĩnh vực công nghệ, kinh tế và truyền thông.",
        "",
        "**Thông tin chính:**",
    ]

    for item in school_type:
        lines.append(f"- {item}")

    if strengths:
        lines.extend(["", "**Điểm nổi bật:**"])
        for item in strengths:
            lines.append(f"- {item}")

    if fields:
        lines.extend(["", "**Nhóm ngành đào tạo:**"])
        for item in fields:
            lines.append(f"- {item}")

    if facilities:
        lines.extend(["", "**Cơ sở vật chất và liên hệ:**"])
        for item in facilities:
            lines.append(f"- {item}")

    lines.extend([
        "",
        "Nếu bạn muốn, mình có thể giới thiệu tiếp về `ngành đào tạo`, `học phí`, `phương thức tuyển sinh` hoặc `cơ hội việc làm` của PTIT.",
    ])
    return "\n".join(lines)


def _extract_field(block: str, label: str) -> Optional[str]:
    pattern = re.compile(rf"-\s+\*\*{re.escape(label)}:\*\*\s*(.+)", re.IGNORECASE)
    match = pattern.search(block)
    return match.group(1).strip() if match else None


def _extract_major_block(query: str) -> Optional[str]:
    major = find_major_by_query(query)
    if not major:
        return None

    majors = get_knowledge_base().get("majors", {})
    normalized_names = [
        major.name,
        major.name.replace(" (CNTT)", ""),
        major.name.replace(" (ATTT)", ""),
        major.name.replace(" (QTKD)", ""),
        major.name.replace(" (CNTT CLC)", ""),
        major.name.replace(" (QTKD CLC)", ""),
    ]

    for name in normalized_names:
        for key, value in majors.items():
            if name.lower() in key.lower() or key.lower() in name.lower():
                return value
    return None


def _detect_known_major_without_cutoff(query: str) -> Optional[Dict[str, str]]:
    query_lower = query.lower()
    known = [

        {
            "match": ["việt nhật", "vnh"],
            "name": "Công nghệ Thông tin Việt-Nhật",
            "code": "7480201_VNH",
        },
        {
            "match": ["định hướng ứng dụng", "udu"],
            "name": "Công nghệ Thông tin Định hướng Ứng dụng",
            "code": "7480201_UDU",
        },
        {
            "match": ["an toàn thông tin clc", "attt clc"],
            "name": "An toàn Thông tin CLC",
            "code": "7480202_CLC",
        },
        {
            "match": ["marketing clc"],
            "name": "Marketing CLC",
            "code": "7340115_CLC",
        },
        {
            "match": ["kế toán clc", "acca"],
            "name": "Kế toán CLC (Tiêu chuẩn ACCA)",
            "code": "7340301_CLC",
        },
    ]
    for item in known:
        if any(token in query_lower for token in item["match"]):
            return item
    return None


def _is_major_info_query(query: str) -> bool:
    query_lower = query.lower()
    info_keywords = [
        "giới thiệu ngành",
        "ngành này",
        "thông tin ngành",
        "mô tả ngành",
        "học gì",
        "ra làm gì",
        "tổ hợp",
        "mã ngành",
    ]
    return find_major_by_query(query) is not None and (
        "ngành" in query_lower or any(keyword in query_lower for keyword in info_keywords)
    )


def _format_major_intro_answer(query: str) -> Optional[str]:
    major = find_major_by_query(query)
    block = _extract_major_block(query)
    if not major or not block:
        return None

    title = block.splitlines()[0].strip("# ").strip()
    code = _extract_field(block, "Mã xét tuyển") or _extract_field(block, "Mã")
    combos = _extract_field(block, "Tổ hợp xét tuyển") or _extract_field(block, "Tổ hợp")
    description = _extract_field(block, "Mô tả") or _extract_field(block, "Đặc điểm")
    skills = _extract_field(block, "Kỹ năng chính")
    careers = _extract_field(block, "Cơ hội việc làm")
    salary = _extract_field(block, "Mức lương dự kiến")
    tuition = _extract_field(block, "Học phí")

    lines = [
        f"📌 **Giới thiệu ngành {title}**",
        "",
        f"Nếu bạn đang quan tâm tới **{title}**, đây là những thông tin quan trọng nhất:",
        "",
        "| Mục | Thông tin |",
        "|---|---|",
        f"| Mã ngành/Mã xét tuyển | {code or major.code} |",
        f"| Nhóm chương trình | {major.program_type} |",
        f"| Điểm chuẩn THPT 2025 | {major.cutoff_pt5} |",
    ]

    if combos:
        lines.append(f"| Tổ hợp xét tuyển | {combos} |")
    if description:
        lines.append(f"| Mô tả ngắn | {description} |")
    if skills:
        lines.append(f"| Kỹ năng chính | {skills} |")
    if careers:
        lines.append(f"| Cơ hội việc làm | {careers} |")
    if salary:
        lines.append(f"| Mức lương dự kiến | {salary} |")
    if tuition:
        lines.append(f"| Học phí tham khảo | {tuition} |")

    lines.extend([
        "",
        "Nếu bạn muốn, mình có thể nói tiếp về `điểm chuẩn`, `TTNV`, `học phí` hoặc so sánh ngành này với ngành khác tại PTIT.",
    ])
    return "\n".join(lines)


def _format_major_comparison_answer(query: str) -> Optional[str]:
    majors = _find_mentioned_majors(query)
    if len(majors) < 2:
        return None

    selected = majors[:2]
    lines = ["📌 **So sánh ngành tại PTIT**", "", "Mình đặt hai ngành cạnh nhau để bạn nhìn khác biệt rõ hơn:", "", "| Tiêu chí | Ngành 1 | Ngành 2 |", "|---|---|---|"]

    blocks = [_extract_major_block(major.name) or "" for major in selected]
    descriptions = [_extract_field(block, "Mô tả") or _extract_field(block, "Đặc điểm") or "-" for block in blocks]
    skills = [_extract_field(block, "Kỹ năng chính") or "-" for block in blocks]
    careers = [_extract_field(block, "Cơ hội việc làm") or "-" for block in blocks]
    combos = [_extract_field(block, "Tổ hợp xét tuyển") or _extract_field(block, "Tổ hợp") or "-" for block in blocks]

    rows = [
        ("Tên ngành", selected[0].name, selected[1].name),
        ("Mã ngành", selected[0].code, selected[1].code),
        ("Điểm chuẩn THPT 2025", f"{selected[0].cutoff_pt5}", f"{selected[1].cutoff_pt5}"),
        ("TTNV", f"<={selected[0].ttnv}", f"<={selected[1].ttnv}"),
        ("Tổ hợp xét tuyển", combos[0], combos[1]),
        ("Mô tả", descriptions[0], descriptions[1]),
        ("Kỹ năng chính", skills[0], skills[1]),
        ("Cơ hội việc làm", careers[0], careers[1]),
    ]
    for label, left, right in rows:
        lines.append(f"| {label} | {left} | {right} |")
    lines.extend(["", "Nếu bạn muốn, mình có thể gợi ý thêm ngành nào hợp hơn với điểm số hoặc sở thích của bạn."])
    return "\n".join(lines)


def _format_tuition_answer(query: str) -> str:
    q = query.lower()
    if any(keyword in q for keyword in ["học bổng", "scholarship"]):
        return """📌 **Học bổng PTIT**

Nếu bạn đang quan tâm tới hỗ trợ tài chính, đây là các nhóm học bổng nổi bật của PTIT:

| Loại học bổng | Số lượng/Giá trị | Điều kiện nổi bật |
|---|---|---|
| Học bổng đặc biệt | 30 suất, tới 500 triệu đồng/suất | Giải quốc gia/quốc tế hoặc điểm THPT từ 29.0 trở lên |
| Học bổng toàn phần | 50 suất, tới 250 triệu đồng/suất | Giải học sinh giỏi phù hợp hoặc điểm THPT từ 28.5 trở lên |
| Học bổng bán phần | 50 suất, tới 100 triệu đồng/suất | Giải học sinh giỏi phù hợp hoặc điểm THPT từ 28.0 trở lên |
| Miễn 100% học phí năm 1 | Tối đa 100 suất | Thành tích học sinh giỏi/quốc gia/quốc tế hoặc kết quả THPT cao |

PTIT cũng có thêm nhiều học bổng doanh nghiệp như Samsung, Cowell Asia, Yokogawa, Bosch..."""

    if any(keyword in q for keyword in ["clc", "chất lượng cao"]):
        return "📌 **Học phí PTIT cho chương trình chất lượng cao (CLC)** hiện ở mức khoảng **35–45 triệu đồng/năm**."

    if any(keyword in q for keyword in ["kinh tế", "truyền thông"]):
        return "📌 **Học phí PTIT cho nhóm ngành Kinh tế và Truyền thông** khoảng **25–30 triệu đồng/năm**."

    if any(keyword in q for keyword in ["kỹ thuật", "công nghệ", "cntt", "attt"]):
        return "📌 **Học phí PTIT cho nhóm ngành Kỹ thuật/Công nghệ hệ đại trà** khoảng **25–35 triệu đồng/năm**."

    return """📌 **Học phí PTIT 2025**

Bạn có thể tham khảo nhanh theo từng nhóm chương trình như sau:

| Nhóm chương trình | Học phí tham khảo |
|---|---:|
| Kỹ thuật/Công nghệ đại trà | 25–35 triệu đồng/năm |
| Kinh tế, Truyền thông | 25–30 triệu đồng/năm |
| Chất lượng cao (CLC) | 35–45 triệu đồng/năm |

Nếu bạn muốn, mình có thể tra tiếp phần `học bổng` hoặc `học phí` theo từng nhóm ngành."""


def _get_major_category_info(query: str) -> Optional[Dict[str, str]]:
    major = find_major_by_query(query)
    if not major:
        return None

    for info in recommendation_engine.majors.values():
        if info["code"] == major.code:
            category = info.get("category")
            labels = {
                "cong_nghe": ("Công nghệ", "Khoảng 20–40 triệu/tháng"),
                "kinh_te": ("Kinh tế", "Khoảng 15–25 triệu/tháng"),
                "truyen_thong": ("Truyền thông", "Khoảng 12–20 triệu/tháng"),
            }
            label, salary = labels.get(category, ("Ngành liên quan", "Chưa có dữ liệu mức lương riêng"))
            return {"category": category or "", "label": label, "salary": salary}
    return None


def _format_career_answer(query: str) -> str:
    if find_major_by_query(query):
        major = find_major_by_query(query)
        block = _extract_major_block(query) or ""
        description = _extract_field(block, "Mô tả") or _extract_field(block, "Đặc điểm")
        careers = _extract_field(block, "Cơ hội việc làm")
        salary = _extract_field(block, "Mức lương dự kiến")
        skills = _extract_field(block, "Kỹ năng chính")
        category_info = _get_major_category_info(query)
        lines = [f"📌 **Cơ hội việc làm ngành {major.name}**", ""]

        if description:
            lines.append(f"{major.name} là ngành thiên về: {description}")
            lines.append("")
        lines.extend([
            "| Mục | Thông tin |",
            "|---|---|",
            f"| Điểm chuẩn THPT 2025 | {major.cutoff_pt5} |",
        ])
        if category_info:
            lines.append(f"| Nhóm ngành | {category_info['label']} |")
        if careers:
            lines.append(f"| Cơ hội việc làm | {careers} |")
        elif category_info:
            lines.append(f"| Mặt bằng cơ hội việc làm | Khá tốt trong nhóm {category_info['label'].lower()} của PTIT |")
        if salary:
            lines.append(f"| Mức lương dự kiến | {salary} |")
        elif category_info:
            lines.append(f"| Mức lương tham khảo theo nhóm ngành | {category_info['salary']} |")
        if skills:
            lines.append(f"| Kỹ năng cần chú trọng | {skills} |")
        lines.extend([
            "",
            "Nếu bạn muốn, mình có thể so sánh thêm triển vọng của ngành này với một ngành khác tại PTIT hoặc gợi ý xem ngành này có hợp với mức điểm của bạn không.",
        ])
        return "\n".join(lines)

    return """📌 **Cơ hội việc làm tại PTIT**

Nhìn chung, PTIT có lợi thế khá tốt về kết nối doanh nghiệp và đầu ra việc làm:

| Nội dung | Thông tin |
|---|---|
| Đối tác doanh nghiệp | Google, Microsoft, Intel, Samsung, Viettel, VNPT, FPT, Bosch, Cowell Asia... |
| Cơ hội thực tập | 500+ offer internship mỗi năm ở nhiều doanh nghiệp |
| Mức lương tham khảo ngành Công nghệ | Khoảng 20–40 triệu/tháng |
| Mức lương tham khảo ngành Kinh tế | Khoảng 15–25 triệu/tháng |
| Mức lương tham khảo ngành Truyền thông | Khoảng 12–20 triệu/tháng |

PTIT cũng có ngày hội tuyển dụng, hội thảo doanh nghiệp và hỗ trợ chuẩn bị hồ sơ/phỏng vấn cho sinh viên."""


def _format_interest_answer(query: str) -> Optional[str]:
    recommendations = recommendation_engine.recommend_by_interest(query)
    if not recommendations:
        return None
    lines = ["💡 **Gợi ý ngành theo sở thích của bạn**", "", "Dựa trên mô tả của bạn, mình thấy các ngành sau là gần nhất:", ""]
    lines.append("| Ngành | Điểm chuẩn 2025 | TTNV | Gợi ý |")
    lines.append("|---|---:|---:|---|")
    for rec in recommendations[:6]:
        info = recommendation_engine.majors[rec["id"]]
        lines.append(
            f"| {info['name']} | {info['cutoff_score']:.2f} | <={info['ttnv']} | {rec['reason']} |"
        )
    lines.extend(["", "Nếu bạn muốn, mình có thể phân tích tiếp ngành nào hợp hơn với mức điểm của bạn."])
    return "\n".join(lines)


def _build_targeted_context(query: str, intent: str) -> str:
    sections = []
    kb = get_knowledge_base()

    if intent == "comparison":
        for major in _find_mentioned_majors(query)[:2]:
            major_block = _extract_major_block(major.name)
            if major_block:
                sections.append(f"[danh_muc_nganh_dao_tao.md]\n{_clean_section_text(major_block)}")
        if sections:
            return "\n\n---\n\n".join(dict.fromkeys(sections))

    if _is_major_info_query(query):
        major_block = _extract_major_block(query)
        if major_block:
            sections.append(f"[danh_muc_nganh_dao_tao.md]\n{_clean_section_text(major_block)}")

    if intent == "admission_method":
        section = _extract_relevant_section("phuong_thuc.md", query)
        if section:
            sections.append(f"[phuong_thuc.md]\n{_clean_section_text(section)}")
    elif intent == "tuition":
        sections.append(f"[hoc_phi_hoc_bong.md]\n{_clean_section_text(kb.get('tuition', '')[:1600])}")
    elif intent == "career":
        sections.append(f"[co_hoi_viec_lam.md]\n{_clean_section_text(kb.get('careers', '')[:1600])}")
    elif intent == "general_qa":
        if any(keyword in query.lower() for keyword in ["ptit", "trường", "học viện", "ở đâu", "địa chỉ"]):
            sections.append(f"[gioi_thieu_ptit.md]\n{_clean_section_text(kb.get('intro', '')[:1600])}")
        interest_answer = _format_interest_answer(query)
        if interest_answer:
            sections.append(f"[danh_muc_nganh_dao_tao.md]\n{interest_answer}")
        if any(keyword in query.lower() for keyword in ["ngành", "chuyên ngành"]):
            major_section = _extract_relevant_section("danh_muc_nganh_dao_tao.md", query)
            if major_section:
                sections.append(f"[danh_muc_nganh_dao_tao.md]\n{_clean_section_text(major_section)}")

    if not sections:
        retrieved_docs = embedding_service.search(query, top_k=TOP_K_RETRIEVAL) if embedding_service else []
        if not retrieved_docs:
            retrieved_docs = _keyword_fallback_search(query, top_k=TOP_K_RETRIEVAL)
        for doc in retrieved_docs:
            sections.append(f"[{doc.get('source', 'KB')}]\n{_clean_section_text(doc.get('text', ''))}")

    return "\n\n---\n\n".join(dict.fromkeys(section for section in sections if section))


def _route_direct_answer(message: str, intent: str) -> Optional[Dict[str, str]]:
    query_lower = message.lower()

    if _is_forecast_query(message):
        return {
            "reply": _format_forecast_answer(message),
            "source": "diem_chuan_chi_tiet_2025.md",
            "intent": "forecast",
            "mode": "query",
        }

    if any(keyword in query_lower for keyword in ["bạn là ai", "cậu là ai", "mày là ai", "ai cơ mà", "ai vậy"]):
        return {
            "reply": _format_identity_answer(),
            "source": "System",
            "intent": "identity",
            "mode": "query",
        }

    if _is_major_list_query(message):
        return {
            "reply": _format_major_list_answer(message),
            "source": "danh_muc_nganh_dao_tao.md, diem_chuan_chi_tiet_2025.md",
            "intent": "major_list",
            "mode": "query",
        }

    comparison_triggers = ["so sánh", "khác nhau", "khác biệt", "hay", "với"]
    comparison_answer = _format_major_comparison_answer(message)
    if comparison_answer and (intent == "comparison" or any(trigger in query_lower for trigger in comparison_triggers)):
        return {
            "reply": comparison_answer,
            "source": "danh_muc_nganh_dao_tao.md, diem_chuan_chi_tiet_2025.md",
            "intent": "comparison",
            "mode": "query",
        }

    interest_answer = _format_interest_answer(message)
    if interest_answer and any(keyword in query_lower for keyword in ["thích", "sở thích", "đam mê", "muốn học"]):
        return {
            "reply": interest_answer,
            "source": "danh_muc_nganh_dao_tao.md, diem_chuan_chi_tiet_2025.md",
            "intent": "interest_recommendation",
            "mode": "query",
        }

    if intent == "admission_method":
        if find_major_by_query(message) and _is_method_cutoff_lookup(message):
            direct_answer = _format_direct_cutoff_answer(message)
            if direct_answer:
                return {
                    "reply": direct_answer,
                    "source": "diem_chuan_chi_tiet_2025.md",
                    "intent": "admission_method",
                    "mode": "query",
                }

        conditions_answer = _format_method_conditions_answer(message)
        score_info = _parse_method_score(message)
        if conditions_answer and score_info is None:
            return {
                "reply": conditions_answer,
                "source": "phuong_thuc.md",
                "intent": "admission_method_conditions",
                "mode": "query",
            }

        if score_info:
            category = recommendation_engine.detect_category_filter(message)
            eligibility = _check_method_eligibility(score_info)
            if not eligibility["eligible"]:
                return {
                    "reply": _format_method_ineligible_answer(score_info, eligibility, category),
                    "source": "phuong_thuc.md",
                    "intent": "admission_method_ineligible",
                    "mode": "query",
                }
            recommendations = _recommend_by_method_score(score_info, category)
            reply = _format_method_recommendation(score_info, recommendations, category)
            if eligibility["reason"]:
                reply = f"{reply}\n\n{eligibility['reason']}"
                if eligibility.get("extra"):
                    reply = f"{reply}\n{eligibility['extra']}"
            return {
                "reply": reply,
                "source": "phuong_thuc.md, diem_chuan_chi_tiet_2025.md",
                "intent": "admission_method_recommendation",
                "mode": "query",
            }

    if intent in ("cutoff_query", "ttnv_query"):
        direct_answer = _format_direct_cutoff_answer(message)
        if direct_answer:
            return {
                "reply": direct_answer,
                "source": "diem_chuan_chi_tiet_2025.md",
                "intent": intent,
                "mode": "query",
            }

    if intent == "score_recommendation":
        score = recommendation_engine.extract_score(message)
        if score is not None:
            recs = recommendation_engine.recommend_by_score(score)
            category = recommendation_engine.detect_category_filter(message)
            recs = recommendation_engine.filter_recommendations(recs, category)
            reply = recommendation_engine.format_recommendation(score, recs)
            if category == "kinh_te":
                reply = reply.replace(
                    f"🎯 **Dựa trên {score} điểm THPT của bạn (điểm chuẩn 2025):**",
                    f"🎯 **Dựa trên {score} điểm THPT của bạn cho nhóm ngành Kinh tế (điểm chuẩn 2025):**",
                    1,
                )
            elif category == "cong_nghe":
                reply = reply.replace(
                    f"🎯 **Dựa trên {score} điểm THPT của bạn (điểm chuẩn 2025):**",
                    f"🎯 **Dựa trên {score} điểm THPT của bạn cho nhóm ngành Công nghệ (điểm chuẩn 2025):**",
                    1,
                )
            elif category == "truyen_thong":
                reply = reply.replace(
                    f"🎯 **Dựa trên {score} điểm THPT của bạn (điểm chuẩn 2025):**",
                    f"🎯 **Dựa trên {score} điểm THPT của bạn cho nhóm ngành Truyền thông (điểm chuẩn 2025):**",
                    1,
                )
            return {
                "reply": reply,
                "source": "diem_chuan_chi_tiet_2025.md",
                "intent": intent,
                "mode": "query",
            }

    if intent == "tuition":
        return {
            "reply": _format_tuition_answer(message),
            "source": "hoc_phi_hoc_bong.md",
            "intent": intent,
            "mode": "query",
        }

    if intent == "admission_method":
        if _is_broad_admission_query(message):
            return {
                "reply": _format_all_admission_methods(),
                "source": "phuong_thuc.md",
                "intent": intent,
                "mode": "query",
            }
        section = _extract_relevant_section("phuong_thuc.md", message)
        if section:
            return {
                "reply": _format_section_answer("Phương thức tuyển sinh PTIT", _clean_section_text(section)),
                "source": "phuong_thuc.md",
                "intent": intent,
                "mode": "query",
            }

    if intent == "career":
        return {
            "reply": _format_career_answer(message),
            "source": "co_hoi_viec_lam.md, danh_muc_nganh_dao_tao.md",
            "intent": intent,
            "mode": "query",
        }

    if _is_major_info_query(message):
        major_reply = _format_major_intro_answer(message)
        if major_reply:
            return {
                "reply": major_reply,
                "source": "danh_muc_nganh_dao_tao.md, diem_chuan_chi_tiet_2025.md",
                "intent": "major_info",
                "mode": "query",
            }

    intro_keywords = ["ptit là gì", "ptit là trường gì", "giới thiệu", "ở đâu", "địa chỉ", "trường công hay tư"]
    if any(keyword in query_lower for keyword in intro_keywords):
        return {
            "reply": _format_intro_answer(message),
            "source": "gioi_thieu_ptit.md",
            "intent": "general_qa",
            "mode": "query",
        }

    return None


def _build_query_response(message: str) -> Optional[ChatResponse]:
    intent = recommendation_engine.detect_intent(message)
    direct_result = _route_direct_answer(message, intent)
    if direct_result:
        return ChatResponse(**direct_result)
    return None


# -----------------------------------------------------------------------
# Direct KB answer for cutoff / TTNV queries (no LLM needed)
# -----------------------------------------------------------------------
def _format_direct_cutoff_answer(query: str) -> Optional[str]:
    """
    If query is asking about a specific major's cutoff/TTNV,
    return a structured answer directly from CUTOFF_DATA.
    Returns None if major not identified or value not found.
    """
    major = find_major_by_query(query)
    if not major:
        special_major = _detect_known_major_without_cutoff(query)
        if special_major:
            return (
                f"📌 **{special_major['name']}** (Mã: {special_major['code']})\n\n"
                "Hiện trong bộ dữ liệu điểm chuẩn mình đang dùng **chưa có điểm chuẩn chính thức** cho ngành/chương trình này, "
                "nên mình chưa thể trả một con số chính xác.\n\n"
                "Nếu bạn muốn, mình vẫn có thể:\n"
                "- giới thiệu chi tiết ngành này\n"
                "- kiểm tra tổ hợp xét tuyển và đặc điểm chương trình\n"
                "- gợi ý ngành gần nhất có dữ liệu điểm chuẩn để bạn tham khảo"
            )
        return None

    query_lower = query.lower()

    if any(w in query_lower for w in ["ttnv", "nguyện vọng"]):
        return (
            f"📌 **TTNV ngành {major.name}**\n\n"
            "| Mục | Thông tin |\n"
            "|---|---|\n"
            f"| Mã ngành | {major.code} |\n"
            f"| TTNV tối đa | <={major.ttnv} |\n"
            f"| Điểm chuẩn THPT 2025 | {major.cutoff_pt5} |\n\n"
            f"Nếu bạn có điểm đúng bằng mức chuẩn {major.cutoff_pt5}, bạn cần đặt ngành này từ **NV1 đến NV{major.ttnv}** để có cơ hội trúng tuyển."
        )

    if any(w in query_lower for w in ["sat"]):
        return (
            f"📌 **{major.name}** — Điểm chuẩn SAT 2025: **{major.cutoff_sat}/1600**\n"
            f"  (Điều kiện tối thiểu: SAT ≥ 1130)"
        )
    if any(w in query_lower for w in ["pt1", "hồ sơ năng lực", "tài năng"]):
        return (
            f"📌 **{major.name}** — Mốc tham chiếu PT1 2025: **{major.cutoff_pt1}/100**\n"
            "  (Đây là mốc theo phương thức tài năng/hồ sơ năng lực; hồ sơ thực tế vẫn cần đáp ứng điều kiện riêng của PTIT)"
        )
    if any(w in query_lower for w in ["pt4", "ielts", "toefl", "học bạ", "học ba"]):
        return (
            f"📌 **{major.name}** — Mốc tham chiếu PT4 2025: **{major.cutoff_pt4}/30**\n"
            "  (PT4 yêu cầu chứng chỉ tiếng Anh hợp lệ và điều kiện học lực/hạnh kiểm theo quy định)"
        )
    if any(w in query_lower for w in ["act"]):
        return (
            f"📌 **{major.name}** — Điểm chuẩn ACT 2025: **{major.cutoff_act}/36**\n"
            f"  (Điều kiện tối thiểu: ACT ≥ 25)"
        )
    if any(w in query_lower for w in ["hsa", "đánh giá năng lực", "đhqg hà nội"]):
        return (
            f"📌 **{major.name}** — Điểm chuẩn HSA 2025: **{major.cutoff_hsa}/150**\n"
            f"  (Điều kiện tối thiểu: HSA ≥ 75)"
        )
    if any(w in query_lower for w in ["tsa", "bách khoa", "đánh giá tư duy"]):
        return (
            f"📌 **{major.name}** — Điểm chuẩn TSA 2025: **{major.cutoff_tsa}/100**\n"
            f"  (Điều kiện tối thiểu: TSA ≥ 50)"
        )
    if any(w in query_lower for w in ["spt", "sư phạm"]):
        return (
            f"📌 **{major.name}** — Điểm chuẩn SPT 2025: **{major.cutoff_spt}/30**\n"
            f"  (Điều kiện tối thiểu: SPT ≥ 15)"
        )
    if any(w in query_lower for w in ["apt", "hcm", "đhqg tp"]):
        return (
            f"📌 **{major.name}** — Điểm chuẩn APT 2025: **{major.cutoff_apt}/1200**\n"
            f"  (Điều kiện tối thiểu: APT ≥ 600)"
        )

    # Default: PT5 cutoff
    return (
        f"📌 **Điểm chuẩn ngành {major.name}**\n\n"
        "| Phương thức | Điểm chuẩn/Mốc tham chiếu | Ghi chú |\n"
        "|---|---:|---|\n"
        f"| THPT (PT5) | {major.cutoff_pt5} | TTNV <= {major.ttnv} |\n"
        f"| Kết hợp (PT4) | {major.cutoff_pt4} | Thang 30 |\n"
        f"| Tài năng (PT1) | {major.cutoff_pt1} | Thang 100 |\n"
        f"| SAT | {major.cutoff_sat} | Thang 1600 |\n"
        f"| ACT | {major.cutoff_act} | Thang 36 |\n"
        f"| HSA | {major.cutoff_hsa} | Thang 150 |\n"
        f"| TSA | {major.cutoff_tsa} | Thang 100 |\n"
        f"| SPT | {major.cutoff_spt} | Thang 30 |\n"
        f"| APT | {major.cutoff_apt} | Thang 1200 |\n\n"
        f"Mã ngành: **{major.code}**. Loại chương trình: **{major.program_type}**."
    )


# -----------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
async def health():
    return {"status": "OK", "initialized": initialized}


@app.get("/")
async def root():
    html_path = Path(__file__).parent / "templates" / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    return {"message": "PTIT Admission Chatbot v2.0 — Backend Running"}


@app.post("/chat")
async def chat(request: ChatRequest):
    """Main chat endpoint — Improved RAG pipeline"""

    if not initialized:
        initialize_services()

    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        # ── Step 1: Detect intent ──────────────────────────────────────
        intent = recommendation_engine.detect_intent(message)
        print(f"\n[CHAT] User: {message}")
        print(f"[CHAT] Intent: {intent}")
        context = ""

        quick_response = _route_direct_answer(message, intent)
        if quick_response:
            print(f"[FAST] Direct query route hit: {quick_response['source']}")
            return {"response": quick_response["reply"]}

        # ── Step 2: Fast-path — direct KB answers (no LLM needed) ─────
        direct_answer = ""

        if intent in ("cutoff_query", "ttnv_query"):
            direct_answer = _format_direct_cutoff_answer(message)

        # ── Step 3: Score-based recommendation ────────────────────────
        recommendation_text = ""
        score = None
        if intent == "score_recommendation":
            score = recommendation_engine.extract_score(message)
            if score:
                recs = recommendation_engine.recommend_by_score(score)
                recommendation_text = recommendation_engine.format_recommendation(score, recs)
                print(f"[CHAT] Score detected: {score}")
        elif any(w in message.lower() for w in ["sở thích", "thích", "yêu thích"]):
            interest_recs = recommendation_engine.recommend_by_interest(message)
            if interest_recs:
                recommendation_text = recommendation_engine.format_interest_recommendation(interest_recs)

        # ── Step 4: Vector search (semantic RAG) ──────────────────────
        retrieved_docs = []
        if not direct_answer:
            context = _build_targeted_context(message, intent)
            print(f"[RAG] Targeted context ready: {bool(context)}")

        # ── Step 5: Build context from retrieved docs ──────────────────
        if retrieved_docs and not direct_answer and not context:
            # Pass FULL text (not cut to 200 chars)
            context_parts = []
            for doc in retrieved_docs:
                source = doc.get("source", "KB")
                text = doc.get("text", "")
                context_parts.append(f"[{source}]\n{text}")
            context = "\n\n---\n\n".join(context_parts)

        # ── Step 6: Generate response ──────────────────────────────────
        response = llm_service.generate_response(
            query=message,
            context=context,
            recommendation=recommendation_text,
            direct_answer=direct_answer,
        )

        # ── Step 7: Source attribution ─────────────────────────────────
        if direct_answer:
            source_str = "diem_chuan_chi_tiet_2025.md"
        elif context:
            source_matches = re.findall(r"\[([^\]]+)\]", context)
            source_str = ", ".join(dict.fromkeys(source_matches[:3])) or "Knowledge Base"
        elif retrieved_docs:
            sources = list(dict.fromkeys(doc["source"] for doc in retrieved_docs))
            source_str = ", ".join(sources[:3])
        else:
            source_str = "Knowledge Base"

        final_response = response
        if recommendation_text and not direct_answer:
            if not response.startswith("🎯") and not response.startswith("✅"):
                final_response = f"{recommendation_text}\n\n{response}" if context else recommendation_text

        print(f"[OK] Response ({intent}): {final_response[:120]}...\n")

        return {"response": final_response}

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback; traceback.print_exc()
        return {"response": "Xin lỗi, có lỗi xảy ra. Vui lòng thử lại hoặc liên hệ PTIT: ☎️ 1800.599.980"}


@app.get("/query", response_model=ChatResponse)
async def query(message: str):
    """Fast query route for low-latency direct answers without LLM."""
    if not initialized:
        initialize_services()

    normalized = message.strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    response = _build_query_response(normalized)
    if response is None:
        raise HTTPException(status_code=404, detail="No direct route matched")
    return response


@app.get("/majors")
async def get_majors():
    from config import MAJORS
    return {"majors": MAJORS}


@app.get("/cutoffs")
async def get_cutoffs_endpoint():
    """Get all cutoff scores — useful for frontend display"""
    data = [
        {
            "code": m.code,
            "name": m.name,
            "pt5": m.cutoff_pt5,
            "ttnv": m.ttnv,
            "type": m.program_type,
        }
        for m in get_cutoff_data()
    ]
    return {"cutoffs": data}


@app.get("/test")
async def test_endpoint():
    """Test endpoint — runs 5 representative queries"""
    if not initialized:
        initialize_services()

    test_cases = [
        "Điểm chuẩn ngành CNTT là bao nhiêu?",
        "Tôi được 25 điểm, nên học ngành nào?",
        "TTNV ngành An toàn thông tin là bao nhiêu?",
        "Học phí PTIT bao nhiêu?",
        "Cần bao nhiêu điểm IELTS để xét tuyển PT4?",
    ]

    results = []
    for q in test_cases:
        req = ChatRequest(message=q)
        resp = await chat(req)
        results.append({
            "question": q,
            "intent": resp.intent,
            "answer_preview": resp.reply[:200],
            "source": resp.source,
        })

    return {"test_results": results, "status": "OK"}


# Serve static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.on_event("startup")
async def startup_event():
    initialize_services()


if __name__ == "__main__":
    import uvicorn
    print("""
    =======================================================
      PTIT Admission Chatbot v2.0 - Improved RAG
      Starting on http://localhost:8080
      API Docs: http://localhost:8080/docs
      Test: http://localhost:8080/test
    =======================================================
    """)
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info",
    )
