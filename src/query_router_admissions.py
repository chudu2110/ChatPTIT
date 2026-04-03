from .query_router_constants import ADMISSION_METHODS


def _find_admission_method(text: str) -> str | None:
    import re

    lower = (text or "").lower()

    m = re.search(r"\b(phương thức|phuong thuc)\b[\s:/\-]*((xét tuyển|xet tuyen|tuyển sinh|tuyen sinh)\b[\s:/\-]*)?(số\s*)?([1-5])\b", lower)
    if m:
        return f"pt{m.group(5)}"

    if "pt1" in lower or "tài năng" in lower or "xét tuyển tài năng" in lower or "phương thức 1" in lower:
        return "pt1"
    if "pt2" in lower or "phương thức 2" in lower:
        return "pt2"
    if "sat" in lower and any(k in lower for k in ["phương thức", "tuyển", "yêu cầu", "điều kiện"]):
        return "pt2"
    if "act" in lower and any(k in lower for k in ["phương thức", "tuyển", "yêu cầu", "điều kiện"]):
        return "pt2"
    if "pt3" in lower or "phương thức 3" in lower or "đgnl" in lower or "đgtd" in lower:
        return "pt3"
    if any(k in lower for k in ["hsa", "tsa", "apt", "spt"]) and any(
        k in lower for k in ["phương thức", "tuyển", "yêu cầu", "điều kiện"]
    ):
        return "pt3"
    if "pt4" in lower or "phương thức 4" in lower:
        return "pt4"
    if "tiếng anh" in lower and "kết hợp" in lower and "thpt" in lower:
        return "pt4"
    if "pt5" in lower or "phương thức 5" in lower:
        return "pt5"
    if "thpt" in lower and "tốt nghiệp" in lower:
        return "pt5"

    return None


def find_admission_method_code(text: str) -> str | None:
    return _find_admission_method(text)


def is_admission_method_query(text: str) -> bool:
    return _find_admission_method(text) is not None


def _is_admission_methods_overview_query(text: str) -> bool:
    lower = (text or "").lower()
    if _find_admission_method(lower) is not None:
        return False
    if "phương thức" not in lower and "cách tuyển" not in lower and "hình thức" not in lower:
        return False
    if "tuyển sinh" not in lower and "xét tuyển" not in lower:
        return False
    stripped = " ".join(lower.split())
    if stripped.startswith("phương thức xét tuyển") or stripped.startswith("phương thức tuyển sinh"):
        return True
    return any(k in lower for k in ["các", "gồm", "bao gồm", "liệt kê", "tổng hợp", "những"])


def answer_admission_methods_overview_query(question: str) -> str | None:
    if not _is_admission_methods_overview_query(question):
        return None

    pt1 = ADMISSION_METHODS["pt1"]
    pt2 = ADMISSION_METHODS["pt2"]
    pt3 = ADMISSION_METHODS["pt3"]
    pt4 = ADMISSION_METHODS["pt4"]
    pt5 = ADMISSION_METHODS["pt5"]

    lines = [
        "Năm 2026, PTIT tuyển sinh đại học chính quy theo **5 phương thức**:",
        f"- **{pt1['name']}**: xét tuyển thẳng và xét hồ sơ năng lực.",
        f"- **{pt2['name']}**: xét bằng chứng chỉ SAT/ACT (có thời hạn).",
        f"- **{pt3['name']}**: xét bằng điểm các bài thi ĐGNL/ĐGTD (HSA/TSA/SPT/APT).",
        f"- **{pt4['name']}**: chứng chỉ tiếng Anh quốc tế + kết quả học tập THPT.",
        f"- **{pt5['name']}**: xét theo điểm thi tốt nghiệp THPT 2026 theo tổ hợp môn.",
        "\nBạn muốn mình giải thích chi tiết điều kiện của phương thức nào (PT1–PT5)?",
    ]
    return "\n".join(lines)


def answer_admission_method_query(question: str) -> str | None:
    method = _find_admission_method(question)
    if not method:
        return None
    lower = (question or "").lower()
    wants_more_detail = any(k in lower for k in ["chi tiết", "cụ thể", "nói rõ", "giải thích", "kỹ hơn", "thêm"])

    if method == "pt1":
        info = ADMISSION_METHODS["pt1"]
        lines = [f"**{info['name']}**\n"]
        lines.append("Xét tuyển thẳng:")
        lines.append(f"- {info['straight_admission']}\n")
        lines.append("Xét tuyển dựa vào hồ sơ năng lực:")
        for req in info["capability_requirements"]:
            lines.append(f"- {req}")
        lines.append(f"\n{info['note']}")
        return "\n".join(lines)

    if method == "pt2":
        info = ADMISSION_METHODS["pt2"]
        lines = [f"**{info['name']}**\n"]
        lines.append(f"{info['description']}\n")
        lines.append(f"- {info['sat_requirement']}")
        lines.append(f"- {info['act_requirement']}")
        lines.append(f"- {info['validity']}\n")
        lines.append(info["note"])
        return "\n".join(lines)

    if method == "pt3":
        info = ADMISSION_METHODS["pt3"]
        lines = [f"**{info['name']}**\n"]
        lines.append(f"{info['description']}\n")
        lines.append("Các kỳ thi chấp nhận:")
        for _, test_info in info["tests"].items():
            lines.append(f"- {test_info}")
        return "\n".join(lines)

    if method == "pt4":
        info = ADMISSION_METHODS["pt4"]
        lines = [f"**{info['name']}**\n"]
        lines.append(f"{info['description']}\n")
        lines.append(f"- {info['english_requirement']}")
        lines.append(f"- {info['gpa_requirement']}")
        lines.append(f"- {info['conduct']}\n")
        lines.append(info["note"])
        return "\n".join(lines)

    if method == "pt5":
        info = ADMISSION_METHODS["pt5"]
        if not wants_more_detail:
            lines = [f"**{info['name']}**\n"]
            lines.append(f"{info['description']}\n")
            lines.append(f"- {info['requirement']}")
            lines.append(f"- {info['score_calc']}")
            return "\n".join(lines)

        lines = [f"**{info['name']}**\n"]
        lines.append("Giải thích chi tiết hơn về PT5:\n")
        lines.append("- Bạn tham gia kỳ thi tốt nghiệp THPT và đăng ký xét tuyển theo tổ hợp 3 môn phù hợp với ngành.")
        lines.append(f"- {info['score_calc']}.")
        lines.append("- Điểm ưu tiên gồm ưu tiên khu vực và ưu tiên đối tượng (nếu có).")
        lines.append("- Khi xét tuyển, bạn cần đăng ký nguyện vọng trên hệ thống theo đúng quy định của Bộ GD&ĐT/nhà trường.")
        lines.append("- Điểm chuẩn từng ngành có thể thay đổi theo năm; nên dùng điểm chuẩn năm gần nhất để tham khảo.")
        lines.append("\nNếu bạn cho mình biết bạn định đăng ký ngành nào và tổ hợp môn (ví dụ A00/A01/D01), mình sẽ hướng dẫn cụ thể hơn cách chuẩn bị và cách ước lượng cơ hội trúng tuyển.")
        return "\n".join(lines)

    return None
