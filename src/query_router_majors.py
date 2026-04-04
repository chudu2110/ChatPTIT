import os
import re

from .config import DATA_PATH
from .query_router_constants import SCORE_DB

_CAREER_DOC: str | None = None

MAJOR_ALIASES: dict[str, list[str]] = {
    "7480201": [
        "công nghệ thông tin",
        "cntt",
        "it",
        "7480201",
        "computer science",
        "khoa học máy tính và ứng dụng",
    ],
    "7480202": ["an toàn thông tin", "attt", "7480202", "bảo mật thông tin"],
    "7480101": ["khoa học máy tính", "khmt", "7480101", "computer science"],
    "7520207": ["kỹ thuật điện tử viễn thông", "điện tử viễn thông", "viễn thông", "đtvt", "7520207"],
    "7520207_aiot": ["aiot", "trí tuệ nhân tạo vạn vật", "7520207_aiot"],
    "7520207_iot": ["iot", "internet vạn vật", "7520207_iot"],
    "7520216": ["điều khiển tự động", "tự động hóa", "7520216"],
    "7510301": [
        "công nghệ kỹ thuật điện, điện tử",
        "kỹ thuật điện điện tử",
        "điện điện tử",
        "điện tử",
        "điện từ",
        "kỹ thuật điện",
        "7510301",
    ],
    "7329001": ["đa phương tiện", "7329001", "công nghệ đa phương tiện"],
    "7320104": ["truyền thông đa phương tiện", "7320104"],
    "7320101": ["báo chí", "7320101"],
    "7340101": ["quản trị kinh doanh", "qtkd", "7340101"],
    "7340115": ["marketing", "7340115"],
    "7340115_qhc": ["quan hệ công chúng", "qhc", "7340115_qhc"],
    "7340122": ["thương mại điện tử", "tmđt", "tmdt", "7340122"],
    "7340205": ["fintech", "công nghệ tài chính", "7340205"],
    "7340301": ["kế toán", "7340301"],
    "7480201_clc": ["cntt clc", "cntt chất lượng cao", "7480201_clc"],
    "7340101_clc": ["qtkd clc", "qtkd chất lượng cao", "7340101_clc"],
}

IT_MAJORS = {
    "7480201",
    "7480202",
    "7480101",
    "7520207",
    "7520207_aiot",
    "7520207_iot",
    "7520216",
    "7510301",
    "7340122",
    "7340205",
    "7480201_clc",
}

_SHORT_QUERY_TO_CANDIDATES: dict[str, list[str]] = {
    "điện tử": ["7510301"],
    "viễn thông": ["7520207"],
    "truyền thông": ["7320104", "7329001"],
    "đa phương tiện": ["7320104", "7329001"],
}

def _strip_accents(text: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFD", text or "")
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


def major_display_name(ma: str) -> str | None:
    ng = SCORE_DB.get(ma)
    if not ng:
        return None
    return ng.get("ten")


def looks_like_major_only(text: str) -> bool:
    lower = (text or "").lower().strip()
    if not lower:
        return False
    if any(ch.isdigit() for ch in lower):
        return False
    intent_markers = [
        "giới thiệu",
        "thông tin",
        "về trường",
        "tổng quan",
        "đặc điểm",
        "ptit",
        "học viện",
        "trường",
        "điểm",
        "điểm chuẩn",
        "ttnv",
        "nguyện vọng",
        "phương thức",
        "pt1",
        "pt2",
        "pt3",
        "pt4",
        "pt5",
        "sat",
        "act",
        "hsa",
        "tsa",
        "apt",
        "spt",
        "học phí",
        "học bổng",
        "hồ sơ",
        "đăng ký",
        "tổ hợp",
        "môn",
        "bao nhiêu",
        "là gì",
        "cơ hội",
        "việc làm",
        "nghề nghiệp",
        "?",
    ]
    if any(k in lower for k in intent_markers):
        return False
    tokens = [t for t in re.split(r"\s+", lower) if t]
    return 1 <= len(tokens) <= 6


def find_major_candidates(text: str) -> list[str]:
    text_lower = (text or "").lower()
    if not text_lower.strip():
        return []
    text_ascii = _strip_accents(text_lower)

    if "viễn thông" in text_lower or "đtvt" in text_lower:
        if "7520207" in SCORE_DB:
            return ["7520207"]
    if "vien thong" in text_ascii or "dtvt" in text_ascii:
        if "7520207" in SCORE_DB:
            return ["7520207"]

    special = _SHORT_QUERY_TO_CANDIDATES.get(text_lower.strip())
    if special:
        return [ma for ma in special if ma in SCORE_DB]
    special_ascii = _SHORT_QUERY_TO_CANDIDATES.get(text_ascii.strip())
    if special_ascii:
        return [ma for ma in special_ascii if ma in SCORE_DB]

    all_aliases: list[tuple[str, str]] = []
    for ma, aliases in MAJOR_ALIASES.items():
        for alias in aliases:
            all_aliases.append((alias.lower(), ma))
    all_aliases.sort(key=lambda x: len(x[0]), reverse=True)

    candidates: list[str] = []
    seen: set[str] = set()
    for alias_lower, ma in all_aliases:
        if not alias_lower:
            continue
        alias_ascii = _strip_accents(alias_lower)
        matched = False
        if re.fullmatch(r"[a-z0-9_]+", alias_lower) and len(alias_lower) <= 4:
            matched = re.search(rf"\b{re.escape(alias_lower)}\b", text_lower) is not None
        else:
            matched = alias_lower in text_lower
        if not matched:
            if re.fullmatch(r"[a-z0-9_]+", alias_ascii) and len(alias_ascii) <= 4:
                matched = re.search(rf"\b{re.escape(alias_ascii)}\b", text_ascii) is not None
            else:
                matched = alias_ascii in text_ascii
        if matched and ma in SCORE_DB and ma not in seen:
            seen.add(ma)
            candidates.append(ma)
    return candidates


def find_major_code(text: str) -> str | None:
    candidates = find_major_candidates(text)
    return candidates[0] if candidates else None


def _load_career_doc() -> str:
    global _CAREER_DOC
    if _CAREER_DOC is not None:
        return _CAREER_DOC
    md_files: list[str] = []
    for root, _, files in os.walk(DATA_PATH):
        for fn in files:
            if fn.lower().endswith(".md"):
                md_files.append(os.path.join(root, fn))
    md_files = sorted(md_files)
    preferred = None
    for p in md_files:
        name = os.path.basename(p).lower()
        if "co_hoi_viec_lam" in name or "career" in name:
            preferred = p
            break
    if not preferred:
        _CAREER_DOC = ""
        return _CAREER_DOC
    with open(preferred, "r", encoding="utf-8") as f:
        _CAREER_DOC = f.read()
    return _CAREER_DOC


def answer_major_career_query(major_code: str) -> str | None:
    major_name = major_display_name(major_code)
    if not major_name:
        return None

    md = _load_career_doc()
    if not md:
        return None

    # Determine group based on major
    # Group names in MD: "Cho ngành Công nghệ:", "Cho ngành Kinh tế:", "Cho ngành An toàn Thông tin:"
    group_name = "Kinh tế"
    if major_code in IT_MAJORS:
        group_name = "Công nghệ"
    if "an toàn thông tin" in major_name.lower():
        group_name = "An toàn Thông tin"

    # Extract relevant info from Q3 (Kỹ năng) and Q2 (Lương)
    lines = [f"Cơ hội nghề nghiệp ngành **{major_name}** tại PTIT:\n"]

    # Salary info from Q2
    if group_name == "Công nghệ":
        lines.append("- **Mức lương khởi điểm:** 20 - 40 triệu đồng/tháng (thuộc nhóm cao nhất).")
    elif group_name == "Kinh tế":
        lines.append("- **Mức lương khởi điểm:** 15 - 25 triệu đồng/tháng.")
    else:
        lines.append("- **Mức lương khởi điểm:** 18 - 35 triệu đồng/tháng.")

    # Skills/Job roles from Q3
    pattern = rf"\*\*Cho ngành {re.escape(group_name)}.*?\*\*(.*?)(?=\n\n|\n\*\*Cho ngành|\n###|\Z)"
    m = re.search(pattern, md, re.S | re.I)
    if m:
        content = m.group(1).strip()
        lines.append("\n**Kỹ năng và kiến thức trọng tâm:**")
        lines.append(content)

    # General benefits
    lines.append("\n**Lợi thế khi học tại PTIT:**")
    lines.append("- Thực tập tại các đối tác lớn như Samsung, Viettel, VNPT, FPT...")
    lines.append("- Tham gia các ngày hội tuyển dụng thường niên (2-3 lần/năm).")
    lines.append("- Được hỗ trợ xây dựng hồ sơ LinkedIn và luyện kỹ năng phỏng vấn.")

    lines.append(
        f"\nBạn muốn tìm hiểu thêm về điểm chuẩn hay phương thức xét tuyển của ngành {major_name} không?"
    )
    return "\n".join(lines)
