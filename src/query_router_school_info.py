import os
import re

from .config import DATA_PATH

_SCHOOL_INFO_DOC: str | None = None


def _load_school_info_doc() -> str:
    global _SCHOOL_INFO_DOC
    if _SCHOOL_INFO_DOC is not None:
        return _SCHOOL_INFO_DOC
    md_files: list[str] = []
    for root, _, files in os.walk(DATA_PATH):
        for fn in files:
            if fn.lower().endswith(".md"):
                md_files.append(os.path.join(root, fn))
    md_files = sorted(md_files)
    preferred = None
    for p in md_files:
        name = os.path.basename(p).lower()
        if "gioi_thieu" in name:
            preferred = p
            break
    if not preferred and md_files:
        preferred = md_files[0]
    if not preferred:
        _SCHOOL_INFO_DOC = ""
        return _SCHOOL_INFO_DOC
    with open(preferred, "r", encoding="utf-8") as f:
        _SCHOOL_INFO_DOC = f.read()
    return _SCHOOL_INFO_DOC


def _extract_section(md: str, header_prefix: str) -> str | None:
    if not md:
        return None
    m = re.search(rf"(?m)^##\s+{re.escape(header_prefix)}.*$", md)
    if not m:
        return None
    start = m.start()
    m2 = re.search(r"(?m)^##\s+", md[m.end() :])
    end = (m.end() + m2.start()) if m2 else len(md)
    section = md[start:end].strip()
    return section


def _extract_between(md: str, start_marker: str, end_marker: str | None) -> str | None:
    if not md:
        return None
    start = md.find(start_marker)
    if start == -1:
        return None
    start += len(start_marker)
    tail = md[start:]
    if end_marker:
        end = tail.find(end_marker)
        if end != -1:
            tail = tail[:end]
    text = tail.strip()
    return text or None


def _extract_bullets_after(md: str, marker: str, max_items: int) -> list[str]:
    if not md:
        return []
    idx = md.find(marker)
    if idx == -1:
        return []
    after = md[idx + len(marker) :].splitlines()
    items: list[str] = []
    for line in after:
        s = line.strip()
        if not s:
            continue
        if s.startswith("## "):
            break
        if s == "---":
            break
        if s.startswith("**") and not s.startswith("-"):
            break
        if s.startswith("-"):
            items.append(s)
            if len(items) >= max_items:
                break
    return items


def _format_school_intro(md: str) -> str | None:
    sec1 = _extract_section(md, "Q1:")
    sec2 = _extract_section(md, "Q2:")
    if not sec1 and not sec2:
        return None

    intro = None
    if sec1:
        intro_raw = _extract_between(sec1, "**Câu trả lời:**", "**Thông tin cơ bản:**")
        if intro_raw:
            intro_lines = intro_raw.splitlines()
            intro = "\n".join(
                [ln.strip() for ln in intro_lines if ln.strip() and ln.strip() != "---"]
            ).strip()

    basic = _extract_bullets_after(sec1 or "", "**Thông tin cơ bản:**", max_items=6)
    strengths = _extract_bullets_after(sec2 or "", "**Thế mạnh:**", max_items=7)
    env = _extract_bullets_after(sec2 or "", "**Môi trường học tập:**", max_items=5)

    def _strip_bullet(s: str) -> str:
        return s.lstrip("-").strip()

    lines: list[str] = []
    if intro:
        lines.append(intro)

    if basic:
        basics = [_strip_bullet(x) for x in basic[:4]]
        lines.append("\nTóm tắt nhanh:")
        lines.extend([f"- {x}" for x in basics])

    if strengths:
        hi = [_strip_bullet(x) for x in strengths[:6]]
        lines.append("\nMột vài điểm mạnh nổi bật:")
        lines.extend([f"- {x}" for x in hi])

    if env:
        env_items = [_strip_bullet(x) for x in env[:4]]
        lines.append("\nMôi trường học tập:")
        lines.extend([f"- {x}" for x in env_items])

    lines.append(
        "\nBạn muốn mình giới thiệu sâu theo hướng nào: ngành đào tạo, cơ sở vật chất, học phí/học bổng hay phương thức tuyển sinh?"
    )
    return "\n".join(lines).strip()


def _format_school_location(md: str) -> str | None:
    sec = _extract_section(md, "Q5:")
    if not sec:
        return None
    addr = _extract_between(sec, "**Địa chỉ:**", "**Trang web:**")
    web = _extract_between(sec, "**Trang web:**", "**Hotline tư vấn:**")
    hotline = _extract_between(sec, "**Hotline tư vấn:**", "**Cơ sở vật chất:**")
    facilities = _extract_bullets_after(sec, "**Cơ sở vật chất:**", max_items=6)

    lines: list[str] = []
    lines.append("Thông tin liên hệ PTIT:")
    if addr:
        lines.append(f"- Địa chỉ: {addr.strip()}")
    if web:
        lines.append(f"- Website: {web.strip()}")
    if hotline:
        lines.append(f"- Hotline tư vấn: {hotline.strip()}")
    if facilities:
        lines.append("\nCơ sở vật chất:")
        lines.extend(facilities)
    return "\n".join(lines).strip()


def _format_school_majors(md: str) -> str | None:
    sec = _extract_section(md, "Q3:")
    if not sec:
        return None
    body = _extract_between(sec, "**Câu trả lời:**", None) or sec
    out_lines: list[str] = []
    for ln in body.splitlines():
        s = ln.strip()
        if not s or s in ("---", "**Câu trả lời:**"):
            continue
        if s.startswith("## "):
            continue
        out_lines.append(s)
    out = "\n".join(out_lines).strip()
    if out:
        out += "\n\nBạn muốn mình gợi ý ngành theo sở thích/điểm của bạn không?"
    return out or None


def _format_school_strength_majors(md: str) -> str | None:
    sec2 = _extract_section(md, "Q2:")
    if not sec2:
        return None

    strengths = _extract_bullets_after(sec2, "**Thế mạnh:**", max_items=10)
    majors: list[str] = []
    for bullet in strengths:
        m = re.search(r"\(([^)]+)\)", bullet)
        if not m:
            continue
        raw = m.group(1)
        if "," not in raw:
            continue
        for part in raw.split(","):
            name = part.strip().strip(".")
            if not name:
                continue
            low = name.lower()
            if low in {"etc", "etc.", "vv", "vv."}:
                continue
            majors.append(name)

    sec2_lower = sec2.lower()
    if "an toàn thông tin" in sec2_lower and not any("an toàn thông tin" in m.lower() for m in majors):
        majors.append("An toàn thông tin")
    if ("vi mạch" in sec2_lower or "bán dẫn" in sec2_lower) and not any(
        ("vi mạch" in m.lower() or "bán dẫn" in m.lower()) for m in majors
    ):
        majors.append("Vi mạch bán dẫn")

    seen = set()
    uniq: list[str] = []
    for m in majors:
        key = m.lower()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(m)

    if not uniq:
        return None

    lines = ["Một số ngành/lĩnh vực được nhắc như thế mạnh nổi bật của PTIT:"]
    lines.extend([f"- {m}" for m in uniq[:10]])
    lines.append(
        "\nBạn đang quan tâm khối nào (Công nghệ / Kinh tế / Truyền thông), hoặc bạn có điểm THPT khoảng bao nhiêu để mình gợi ý ngành phù hợp?"
    )
    return "\n".join(lines).strip()


def _is_school_info_query(text: str) -> bool:
    lower = (text or "").lower()
    if "ptit" not in lower and "học viện" not in lower and "trường" not in lower:
        return False
    if any(
        k in lower
        for k in ["điểm chuẩn", "ttnv", "mã ngành", "tổ hợp", "pt1", "pt2", "pt3", "pt4", "pt5"]
    ):
        return False
    if any(
        k in lower
        for k in [
            "học phí",
            "học phi",
            "hoc phi",
            "học bổng",
            "hoc bong",
            "phương thức",
            "xét tuyển",
            "tuyển sinh",
            "hồ sơ",
            "đăng ký",
            "chỉ tiêu",
            "lệ phí",
            "việc làm",
            "nghề nghiệp",
            "cơ hội",
            "mức lương",
        ]
    ):
        return False
    if lower.strip() in {
        "ptit",
        "học viện ptit",
        "hoc vien ptit",
        "học viện công nghệ bưu chính viễn thông",
        "hoc vien cong nghe buu chinh vien thong",
    }:
        return True
    base = ["giới thiệu", "thông tin", "là gì", "trường gì", "về trường", "tổng quan", "đặc điểm", "ở đâu", "địa chỉ"]
    if any(k in lower for k in base):
        return True
    if ("thế mạnh" in lower or "nổi bật" in lower) and "ngành" in lower:
        return True
    return False


def answer_school_info_query(question: str) -> str | None:
    if not _is_school_info_query(question):
        return None
    md = _load_school_info_doc()
    if not md:
        return None
    lower = (question or "").lower()
    majors_intent_phrases = [
        "ngành đào tạo",
        "các ngành đào tạo",
        "ngành học",
        "các ngành học",
        "khối ngành",
        "các khối ngành",
        "khối công nghệ",
        "khối kinh tế",
        "khối truyền thông",
        "chương trình chất lượng cao",
        "chất lượng cao",
        "clc",
    ]
    if any(k in lower for k in ["ở đâu", "địa chỉ", "cơ sở", "hotline", "website"]):
        return _format_school_location(md)
    if ("thế mạnh" in lower or "nổi bật" in lower) and "ngành" in lower:
        result = _format_school_strength_majors(md)
        if result:
            return result
    if any(k in lower for k in majors_intent_phrases) or ("ngành" in lower and "đào tạo" in lower):
        return _format_school_majors(md)
    if any(k in lower for k in ["đặc điểm", "nổi bật", "thế mạnh"]):
        return _format_school_intro(md)
    if any(k in lower for k in ["khối ngành", "ngành nào", "ngành gì", "đào tạo gì"]):
        return _format_school_majors(md)
    return _format_school_intro(md)
