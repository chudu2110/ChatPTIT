import re

from .query_router_constants import SCORE_DB

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

    if "viễn thông" in text_lower or "đtvt" in text_lower:
        if "7520207" in SCORE_DB:
            return ["7520207"]

    special = _SHORT_QUERY_TO_CANDIDATES.get(text_lower.strip())
    if special:
        return [ma for ma in special if ma in SCORE_DB]

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
        matched = False
        if re.fullmatch(r"[a-z0-9_]+", alias_lower) and len(alias_lower) <= 4:
            matched = re.search(rf"\b{re.escape(alias_lower)}\b", text_lower) is not None
        else:
            matched = alias_lower in text_lower
        if matched and ma in SCORE_DB and ma not in seen:
            seen.add(ma)
            candidates.append(ma)
    return candidates


def find_major_code(text: str) -> str | None:
    candidates = find_major_candidates(text)
    return candidates[0] if candidates else None
