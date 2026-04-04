import os
import re

from .config import DATA_PATH

_SCHOOL_INFO_DOC: str | None = None
_MAJORS_DOC: str | None = None
_TUITION_DOC: str | None = None


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


def _load_majors_doc() -> str:
    global _MAJORS_DOC
    if _MAJORS_DOC is not None:
        return _MAJORS_DOC
    md_files: list[str] = []
    for root, _, files in os.walk(DATA_PATH):
        for fn in files:
            if fn.lower().endswith(".md"):
                md_files.append(os.path.join(root, fn))
    md_files = sorted(md_files)
    preferred = None
    for p in md_files:
        name = os.path.basename(p).lower()
        if "danh_muc_nganh" in name or "nganh_dao_tao" in name:
            preferred = p
            break
    if not preferred:
        _MAJORS_DOC = ""
        return _MAJORS_DOC
    with open(preferred, "r", encoding="utf-8") as f:
        _MAJORS_DOC = f.read()
    return _MAJORS_DOC


def _load_tuition_doc() -> str:
    global _TUITION_DOC
    if _TUITION_DOC is not None:
        return _TUITION_DOC
    md_files: list[str] = []
    for root, _, files in os.walk(DATA_PATH):
        for fn in files:
            if fn.lower().endswith(".md"):
                md_files.append(os.path.join(root, fn))
    md_files = sorted(md_files)
    preferred = None
    for p in md_files:
        name = os.path.basename(p).lower()
        if "hoc_phi" in name or "hoc_bong" in name:
            preferred = p
            break
    if not preferred:
        _TUITION_DOC = ""
        return _TUITION_DOC
    with open(preferred, "r", encoding="utf-8") as f:
        _TUITION_DOC = f.read()
    return _TUITION_DOC


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
    
    lines: list[str] = []
    lines.append("Thông tin liên hệ PTIT:")
    if addr:
        lines.append(f"- Địa chỉ: {addr.strip()}")
    if web:
        lines.append(f"- Website: {web.strip()}")
    if hotline:
        lines.append(f"- Hotline tư vấn: {hotline.strip()}")
    return "\n".join(lines).strip()


def _format_school_facilities(md: str) -> str | None:
    sec = _extract_section(md, "Q5:")
    if not sec:
        return None
    facilities = _extract_bullets_after(sec, "**Cơ sở vật chất:**", max_items=10)
    if not facilities:
        return None
    
    lines: list[str] = []
    lines.append("Cơ sở vật chất của PTIT:")
    lines.extend(facilities)
    lines.append("\nBạn có muốn tìm hiểu thêm về các ngành đào tạo, học phí/học bổng hay phương thức tuyển sinh của trường không?")
    return "\n".join(lines).strip()


def _format_school_tuition(md: str) -> str | None:
    if not md:
        return None
    
    lines: list[str] = []
    lines.append("Thông tin học phí và học bổng tại PTIT năm 2025:")
    
    # Extract tuition
    tuition_sec = _extract_between(md, "## 1. Học phí hàng năm (đơn vị: triệu đồng/năm)", "## 2. Cơ hội học bổng")
    if tuition_sec:
        lines.append("\n**Học phí hàng năm:**")
        lines.append(tuition_sec.strip())
        
    # Extract scholarships
    scholarship_sec = _extract_between(md, "## 2. Cơ hội học bổng", None)
    if scholarship_sec:
        lines.append("\n**Cơ hội học bổng:**")
        # Just take the first few bullets or summarized text
        bullets = scholarship_sec.split("\n- ")
        if len(bullets) > 1:
            lines.append("- " + "\n- ".join([b.strip() for b in bullets[1:4]]))
            if len(bullets) > 4:
                lines.append("- Và nhiều cơ hội học bổng khác từ doanh nghiệp...")
        else:
            lines.append(scholarship_sec.strip())
            
    lines.append("\nBạn muốn mình tư vấn thêm về ngành đào tạo, cơ sở vật chất hay phương thức tuyển sinh của PTIT không?")
    return "\n".join(lines).strip()


def _format_school_majors(md: str) -> str | None:
    sec = _extract_section(md, "Q3:")
    if not sec:
        majors_md = _load_majors_doc()
        return _format_major_catalog(majors_md)
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
        out += "\n\nBạn muốn mình tư vấn thêm về cơ sở vật chất, học phí/học bổng hay phương thức tuyển sinh của PTIT không?"
    return out or None


def _format_major_catalog(md: str) -> str | None:
    if not md:
        return None
    groups: dict[str, list[str]] = {}
    current_group: str | None = None

    def _clean_title(s: str) -> str:
        s = re.sub(r"\([^)]*\)", "", s).strip()
        s = re.sub(r"\s{2,}", " ", s).strip()
        return s

    for raw in md.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("## "):
            title = _clean_title(line[3:].strip())
            if not title:
                current_group = None
                continue
            if title.lower().startswith("bảng tóm tắt"):
                break
            current_group = title
            groups.setdefault(current_group, [])
            continue
        if current_group and line.startswith("### "):
            major = _clean_title(line[4:].strip())
            if major:
                groups[current_group].append(major)

    if not groups:
        return None

    ordered = list(groups.items())
    lines: list[str] = ["Danh mục ngành đào tạo PTIT (tóm tắt):"]
    for group, majors in ordered:
        uniq: list[str] = []
        seen = set()
        for m in majors:
            key = m.lower()
            if key in seen:
                continue
            seen.add(key)
            uniq.append(m)
        shown = uniq[:8]
        tail = "" if len(uniq) <= len(shown) else f", ... (tổng {len(uniq)} ngành/chương trình)"
        lines.append(f"\n- **{group}**: " + ", ".join(shown) + tail)

    lines.append(
        "\nBạn muốn xem chi tiết ngành nào (hoặc khối nào) để mình nói rõ về mã xét tuyển, tổ hợp môn và mô tả ngành?"
    )
    return "\n".join(lines).strip()


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
    # If the text is very short and matches a school info topic, we allow it even without "ptit/trường"
    # because the context is handled by app.py rewriting or by the nature of the suggestions.
    school_topics = [
        "cơ sở vật chất", "co so vat chat", "cơ sở", "co so",
        "phòng lab", "phòng thí nghiệm", "thư viện", "ký túc xá", "ktx",
        "học phí", "hoc phi", "học bổng", "hoc bong",
        "địa chỉ", "dia chi", "ở đâu", "o dau",
        "cơ hội nghề nghiệp", "việc làm", "co hoi nghe nghiep", "viec lam",
    ]
    
    is_topic = any(k == lower.strip() or f" {k} " in f" {lower} " for k in school_topics)
    
    if not is_topic and "ptit" not in lower and "học viện" not in lower and "trường" not in lower:
        return False

    if any(
        k in lower
        for k in ["điểm chuẩn", "ttnv", "mã ngành", "tổ hợp", "pt1", "pt2", "pt3", "pt4", "pt5"]
    ):
        return False
    
    # We now allow học phí and học bổng here if they are about PTIT
    # (previously they were excluded to fall through to RAG, but we want a better formatter)
    
    if lower.strip() in {
        "ptit",
        "học viện ptit",
        "hoc vien ptit",
        "học viện công nghệ bưu chính viễn thông",
        "hoc vien cong nghe buu chinh vien thong",
    }:
        return True
    
    majors_intent = [
        "ngành đào tạo",
        "các ngành đào tạo",
        "danh mục ngành",
        "danh muc nganh",
        "ngành học",
        "các ngành học",
        "khối ngành",
        "các khối ngành",
        "đào tạo gì",
        "ngành nào",
        "chương trình chất lượng cao",
        "chất lượng cao",
        "clc",
    ]
    if any(k in lower for k in majors_intent):
        return True
    
    base = ["giới thiệu", "thông tin", "là gì", "trường gì", "về trường", "tổng quan", "đặc điểm", "ở đâu", "địa chỉ", "cơ sở", "học phí", "học bổng", "cơ hội", "việc làm", "nghề nghiệp"]
    if any(k in lower for k in base):
        return True
        
    if ("thế mạnh" in lower or "nổi bật" in lower) and "ngành" in lower:
        return True
    return False


def _format_school_career(md: str) -> str | None:
    sec = _extract_section(md, "Q2:")
    if not sec:
        return None
    
    career_info = _extract_between(sec, "### Cơ hội Việc Làm", "### Chương trình hỗ trợ sự nghiệp:")
    if not career_info:
        return None
        
    lines: list[str] = []
    lines.append("Cơ hội nghề nghiệp của sinh viên PTIT:")
    lines.append(career_info.strip())
    lines.append("\nBạn muốn tìm hiểu chi tiết về cơ hội nghề nghiệp của một ngành cụ thể nào không? (Ví dụ: CNTT, Marketing, ATTT...)")
    return "\n".join(lines).strip()


def answer_school_info_query(question: str) -> str | None:
    if not _is_school_info_query(question):
        return None
    
    lower = (question or "").lower()
    
    # Check for career in general
    if any(k in lower for k in ["cơ hội", "việc làm", "nghề nghiệp"]):
        # But we need to make sure we load the right file
        md_career = None
        md_files: list[str] = []
        for root, _, files in os.walk(DATA_PATH):
            for fn in files:
                if fn.lower().endswith(".md") and ("co_hoi_viec_lam" in fn.lower() or "career" in fn.lower()):
                    with open(os.path.join(root, fn), "r", encoding="utf-8") as f:
                        md_career = f.read()
                    break
        if md_career:
            return _format_school_career(md_career)

    # Check for tuition first since it's in a different file
    if any(k in lower for k in ["học phí", "học phi", "hoc phi", "học bổng", "hoc bong"]):
        tuition_md = _load_tuition_doc()
        if tuition_md:
            return _format_school_tuition(tuition_md)

    md = _load_school_info_doc()
    if not md:
        return None

    if any(k in lower for k in ["cơ sở vật chất", "phòng lab", "thư viện", "ký túc xá", "ktx"]):
        return _format_school_facilities(md)

    if any(k in lower for k in ["ở đâu", "địa chỉ", "cơ sở", "hotline", "website"]):
        return _format_school_location(md)

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
