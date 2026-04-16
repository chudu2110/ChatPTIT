"""Recommendation engine — Improved intent detection and major suggestions"""

import re
from typing import List, Dict, Any, Optional
from config import MAJORS


class RecommendationEngine:
    def __init__(self):
        self.majors = MAJORS
        self.keywords_mapping = self._build_keyword_mapping()
        self.category_keywords = {
            "kinh_te": ["kinh tế", "kinh doanh", "marketing", "tài chính", "fintech", "kế toán", "thương mại"],
            "cong_nghe": ["công nghệ", "kỹ thuật", "cntt", "an toàn thông tin", "lập trình", "ai", "iot"],
            "truyen_thong": ["truyền thông", "báo chí", "media", "pr", "đa phương tiện"],
        }

    def _build_keyword_mapping(self) -> Dict[str, List[str]]:
        """Build mapping from keywords to major IDs"""
        mapping = {}
        for major_id, info in self.majors.items():
            for kw in info["keywords"]:
                mapping.setdefault(kw, []).append(major_id)
        return mapping

    # ------------------------------------------------------------------
    # Intent Detection
    # ------------------------------------------------------------------
    def detect_intent(self, text: str) -> str:
        """
        Detect user intent from query.

        Intents:
        - score_recommendation : User states THEIR score and wants ngành advice
        - cutoff_query          : User asks "điểm chuẩn ngành X là bao nhiêu?"
        - ttnv_query            : User asks about TTNV (thứ tự nguyện vọng)
        - tuition               : Questions about học phí / tiền / học bổng
        - career                : Questions about việc làm / lương / cơ hội nghề nghiệp
        - admission_method      : Questions about phương thức tuyển sinh / SAT / IELTS
        - comparison            : Comparing majors
        - general_qa            : Everything else
        """
        text_lower = text.lower()

        # 1. TTNV — must check before score_recommendation to avoid misclassification
        if any(w in text_lower for w in ["ttnv", "thứ tự nguyện vọng", "nguyện vọng tối đa", "nguyện vọng mấy"]):
            return "ttnv_query"

        # 2. Admission-method queries should win over generic score recommendation
        if any(w in text_lower for w in ["phương thức", "xét tuyển", "sat", "act", "ielts", "toefl", "hsa", "tsa", "apt", "spt", "pt1", "pt2", "pt3", "pt4", "pt5", "học bạ", "học ba"]):
            return "admission_method"

        # 3. User gives their OWN score → recommendation
        #    Pattern: "tôi được X điểm", "đạt X điểm", "điểm của tôi là X", "X điểm thi được"
        own_score_patterns = [
            r'tôi\s+(?:được|đạt|có|thi)\s+\d+',
            r'(?:được|đạt|có)\s+\d+\s+điểm',
            r'\d+\s+điểm\s+(?:thi|được|đạt|có)',
            r'điểm\s+(?:của\s+tôi|mình)\s+(?:là|được|đạt)\s+\d+',
        ]
        for pat in own_score_patterns:
            if re.search(pat, text_lower):
                return "score_recommendation"

        # 4. Asking about cutoff score of a specific major
        cutoff_query_words = ["điểm chuẩn", "điểm đầu vào", "cần bao nhiêu điểm", "lấy bao nhiêu", "bao nhiêu điểm để vào"]
        if any(w in text_lower for w in cutoff_query_words):
            return "cutoff_query"

        # 5. Tuition / Scholarship
        if any(w in text_lower for w in ["học phí", "tiền học", "học bổng", "bao nhiêu tiền", "tài chính"]):
            return "tuition"

        # 6. Career / Job
        if any(w in text_lower for w in ["lương", "việc làm", "cơ hội việc làm", "nghề nghiệp", "job", "tuyển dụng", "ra trường"]):
            return "career"

        # 7. Comparison
        if any(w in text_lower for w in ["so sánh", "tốt hơn", "khác biệt", "hay là"]):
            return "comparison"

        return "general_qa"

    # ------------------------------------------------------------------
    # Score extraction
    # ------------------------------------------------------------------
    def extract_score(self, text: str) -> Optional[float]:
        """Extract user's score from input (valid range: 15–30)"""
        # Match patterns like "24 điểm", "được 24", "đạt 26.5"
        patterns = [
            r'(?:được|đạt|có|điểm\s+(?:là)?)\s*([\d]{1,2}(?:[.,]\d+)?)',
            r'([\d]{1,2}(?:[.,]\d+)?)\s*điểm',
        ]
        for pat in patterns:
            matches = re.findall(pat, text.lower())
            for m in matches:
                try:
                    score = float(m.replace(',', '.'))
                    if 15.0 <= score <= 30.0:
                        return score
                except ValueError:
                    continue
        return None

    # ------------------------------------------------------------------
    # Score-based recommendation
    # ------------------------------------------------------------------
    def recommend_by_score(self, score: float) -> Dict[str, Any]:
        """Recommend majors based on user's score vs real 2025 cutoff_score"""
        result = {"safe": [], "match": [], "stretch": []}

        for major_id, info in self.majors.items():
            cutoff = info["cutoff_score"]
            gap = score - cutoff

            if gap >= 0:
                result["safe"].append({
                    "id": major_id,
                    "name": info["name"],
                    "cutoff": cutoff,
                    "ttnv": info.get("ttnv", "-"),
                    "gap": gap,
                    "type": info.get("type", "Đại trà"),
                })
            elif gap >= -1.0:
                result["match"].append({
                    "id": major_id,
                    "name": info["name"],
                    "cutoff": cutoff,
                    "ttnv": info.get("ttnv", "-"),
                    "gap": abs(gap),
                    "type": info.get("type", "Đại trà"),
                })
            elif gap >= -3.0:
                result["stretch"].append({
                    "id": major_id,
                    "name": info["name"],
                    "cutoff": cutoff,
                    "ttnv": info.get("ttnv", "-"),
                    "gap": abs(gap),
                    "type": info.get("type", "Đại trà"),
                })

        # Sort safe by gap descending (closest win first), others by gap ascending
        result["safe"].sort(key=lambda x: x["gap"], reverse=False)
        result["match"].sort(key=lambda x: x["gap"])
        result["stretch"].sort(key=lambda x: x["gap"])

        return result

    def detect_category_filter(self, text: str) -> Optional[str]:
        """Detect if the user only wants a specific major group."""
        text_lower = text.lower()
        for category, keywords in self.category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        return None

    def filter_recommendations(self, recommendations: Dict[str, Any], category: Optional[str]) -> Dict[str, Any]:
        """Filter recommendation buckets by category when requested."""
        if not category:
            return recommendations

        filtered = {"safe": [], "match": [], "stretch": []}
        for bucket, items in recommendations.items():
            filtered[bucket] = [
                item for item in items
                if self.majors[item["id"]].get("category") == category
            ]
        return filtered

    def recommend_by_interest(self, text: str) -> List[Dict[str, Any]]:
        """Recommend majors based on interest keywords"""
        text_lower = text.lower()
        matched = set()
        for kw, ids in self.keywords_mapping.items():
            if len(kw) < 3:
                continue
            if re.search(rf"(?<!\w){re.escape(kw)}(?!\w)", text_lower):
                matched.update(ids)
            elif " " in kw and kw in text_lower:
                matched.update(ids)

        return [
            {"id": mid, "name": self.majors[mid]["name"],
             "reason": "Phù hợp với sở thích của bạn"}
            for mid in matched
        ]

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------
    def format_recommendation(self, score: float, recommendations: Dict[str, Any]) -> str:
        """Format score-based recommendation for display"""
        total = sum(len(v) for v in recommendations.values())
        if total == 0:
            return (
                f"🎯 **Dựa trên {score} điểm THPT của bạn (điểm chuẩn 2025):**\n\n"
                "Hiện mình chưa thấy ngành phù hợp trong nhóm bạn hỏi. Bạn có thể thử mở rộng sang nhóm ngành khác hoặc hỏi cụ thể một ngành để mình tra chính xác hơn."
            )

        lines = [f"🎯 **Dựa trên {score} điểm THPT của bạn (điểm chuẩn 2025):**\n"]

        lines.append(self._format_bucket_table(
            "✅ An toàn",
            "Điểm của bạn >= điểm chuẩn",
            recommendations["safe"][:6],
            status="Đủ điểm",
        ))

        lines.append(self._format_bucket_table(
            "⚠️ Sát điểm chuẩn",
            "Thiếu dưới 1 điểm",
            recommendations["match"][:4],
            status="Cân nhắc",
        ))

        lines.append(self._format_bucket_table(
            "💪 Thử sức",
            "Thiếu từ 1 đến 3 điểm",
            recommendations["stretch"][:4],
            status="Khá khó",
        ))

        return "\n\n".join(part for part in lines if part)

    def _format_bucket_table(self, title: str, note: str, items: List[Dict[str, Any]], status: str) -> str:
        """Render a markdown table for one recommendation bucket."""
        if not items:
            return ""

        lines = [f"{title} ({note})", "", "| Ngành | Điểm chuẩn | Chênh lệch | TTNV | Loại | Đánh giá |", "|---|---:|---:|---:|---|---|"]
        for item in items:
            gap_text = f"+{item['gap']:.2f}" if title.startswith("✅") else f"-{item['gap']:.2f}"
            lines.append(
                f"| {item['name']} | {item['cutoff']:.2f} | {gap_text} | <={int(item['ttnv'])} | {item['type']} | {status} |"
            )
        return "\n".join(lines)

    def format_interest_recommendation(self, recommendations: List[Dict[str, Any]]) -> str:
        """Format interest-based recommendation"""
        if not recommendations:
            return "Không tìm thấy ngành phù hợp. Hãy thử mô tả rõ hơn sở thích của bạn."
        lines = ["💡 **Các ngành phù hợp với sở thích của bạn:**\n"]
        for m in recommendations:
            info = self.majors[m["id"]]
            lines.append(f"  • **{m['name']}** — Điểm chuẩn 2025: {info['cutoff_score']} | TTNV: ≤{info['ttnv']}")
        return "\n".join(lines)
