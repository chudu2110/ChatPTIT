import re

from .query_router_constants import SCORE_DB
from .query_router_majors import IT_MAJORS, find_major_code


def _find_score_in_question(text: str) -> float | None:
    matches = re.findall(r"\b(\d{1,2}(?:[.,]\d{1,2})?)\s*điểm?\b", text)
    for m in matches:
        try:
            val = float(m.replace(",", "."))
            if 10.0 <= val <= 30.0:
                return val
        except ValueError:
            pass
    matches2 = re.findall(r"\bđược\s+(\d{1,2}(?:[.,]\d{1,2})?)\b", text)
    for m in matches2:
        try:
            val = float(m.replace(",", "."))
            if 10.0 <= val <= 30.0:
                return val
        except ValueError:
            pass
    return None


def _find_score_type_and_value(text: str) -> dict | None:
    lower = (text or "").lower()
    result: dict[str, float] = {}

    if "học bạ" in lower or "gpa" in lower:
        matches = re.findall(r"\b(\d{1,2}(?:[.,]\d{1,2})?)\s*(?:điểm)?\s*(?:học bạ|gpa)", lower)
        if not matches:
            matches = re.findall(r"(?:học bạ|gpa)\s+(\d{1,2}(?:[.,]\d{1,2})?)", lower)
        if matches:
            try:
                result["hoc_ba"] = float(matches[0].replace(",", "."))
            except ValueError:
                pass

    if "thpt" in lower or "thi tốt nghiệp" in lower or "thi thpt" in lower:
        matches = re.findall(r"\b(\d{1,2}(?:[.,]\d{1,2})?)\s*(?:điểm)?\s*(?:thpt|tốt nghiệp)", lower)
        if not matches:
            matches = re.findall(r"(?:thpt|tốt nghiệp)\s+(\d{1,2}(?:[.,]\d{1,2})?)", lower)
        if matches:
            try:
                result["thpt"] = float(matches[0].replace(",", "."))
            except ValueError:
                pass

    if result:
        return result

    matches = re.findall(r"\b(\d{1,2}(?:[.,]\d{1,2})?)\s*điểm?\b", text)
    for m in matches:
        try:
            val = float(m.replace(",", "."))
            if 20.0 <= val <= 30.0:
                return {"thpt": val}
            if 10.0 <= val < 20.0:
                return {"hoc_ba": val}
        except ValueError:
            pass

    return None


def _find_english_score(text: str) -> tuple[str, float] | None:
    lower = (text or "").lower()

    ielts_matches = re.findall(r"ielts\s+(\d{1,2}(?:[.,]\d{1,2})?)", lower)
    if ielts_matches:
        try:
            score = float(ielts_matches[0].replace(",", "."))
            if 0 <= score <= 9:
                return ("ielts", score)
        except ValueError:
            pass

    toefl_ibt_matches = re.findall(r"toefl\s+ibt\s+(\d{1,3})", lower)
    if toefl_ibt_matches:
        try:
            score = float(toefl_ibt_matches[0])
            if 0 <= score <= 120:
                return ("toefl_ibt", score)
        except ValueError:
            pass

    toefl_itp_matches = re.findall(r"toefl\s+itp\s+(\d{1,3})", lower)
    if toefl_itp_matches:
        try:
            score = float(toefl_itp_matches[0])
            if 0 <= score <= 677:
                return ("toefl_itp", score)
        except ValueError:
            pass

    return None


def _check_pt4_eligibility(english_cert: tuple[str, float] | None) -> bool:
    if not english_cert:
        return False
    cert_type, score = english_cert
    if cert_type == "ielts":
        return score >= 5.5
    if cert_type == "toefl_ibt":
        return score >= 65
    if cert_type == "toefl_itp":
        return score >= 513
    return False


def is_score_query(text: str) -> bool:
    lower = (text or "").lower()
    keywords = ["điểm chuẩn", "điểm xét", "bao nhiêu điểm", "cut-off", "cutoff"]
    return any(k in lower for k in keywords)


def is_forecast_score_query(text: str) -> bool:
    lower = (text or "").lower()
    time_markers = ["năm sau", "năm tới", "sang năm", "năm tiếp theo", "tương lai"]
    compare_markers = [
        "cao hơn",
        "thấp hơn",
        "tăng",
        "giảm",
        "nhích",
        "tụt",
        "dự đoán",
        "liệu",
        "có tăng",
        "có giảm",
        "có cao",
        "có thấp",
    ]
    score_markers = ["điểm chuẩn", "điểm xét", "cut-off", "cutoff", "điểm"]
    if not any(k in lower for k in score_markers):
        return False
    return any(k in lower for k in time_markers) and any(k in lower for k in compare_markers)


def answer_forecast_score_query(question: str) -> str:
    ma = find_major_code(question)
    ng = SCORE_DB.get(ma) if ma else None
    if not ng:
        return (
            "Mình không thể dự đoán chính xác điểm chuẩn **năm sau** sẽ cao hay thấp.\n\n"
            "Điểm chuẩn phụ thuộc vào nhiều yếu tố như số lượng thí sinh đăng ký, mặt bằng điểm thi, chỉ tiêu và độ “hot” của từng ngành.\n\n"
            "Mình có thể giúp bạn tham khảo **điểm chuẩn năm 2025** của ngành bạn quan tâm và cách ước lượng mức điểm mục tiêu để đăng ký an toàn."
        )

    return (
        f"Mình không thể khẳng định **năm sau** điểm chuẩn của **{ng['ten']}** sẽ cao hay thấp, vì còn phụ thuộc vào số lượng đăng ký, mặt bằng điểm thi và chỉ tiêu.\n\n"
        f"Để bạn tham khảo, **điểm chuẩn THPT (PT5) năm 2025** của ngành **{ng['ten']}** (mã {ng['ma']}) là **{ng['pt5']} điểm**.\n\n"
        "Gợi ý nhỏ: bạn cứ đặt mục tiêu cao hơn mốc tham khảo một chút và chuẩn bị hồ sơ/nguyện vọng kỹ để tăng cơ hội trúng tuyển."
    )


def is_ttnv_query(text: str) -> bool:
    lower = (text or "").lower()
    return "ttnv" in lower or "thứ tự nguyện vọng" in lower or "nguyện vọng tối đa" in lower


def is_comparison_query(text: str) -> bool:
    lower = (text or "").lower()
    has_number = _find_score_in_question(text) is not None
    has_intent = any(
        k in lower
        for k in [
            "có đỗ",
            "có đậu",
            "đỗ không",
            "đậu không",
            "trúng tuyển không",
            "vào được không",
            "có vào",
            "đủ điểm",
            "có đủ",
            "có thể đỗ",
            "có thể vào",
        ]
    )
    suggest_intent = any(
        k in lower
        for k in [
            "nên học",
            "nên đăng ký",
            "nên chọn",
            "học ngành nào",
            "đăng ký ngành nào",
            "chọn ngành nào",
            "phù hợp với em",
        ]
    )
    return has_number and (has_intent or suggest_intent)


def answer_score_query(question: str) -> str | None:
    ma = find_major_code(question)
    if not ma or ma not in SCORE_DB:
        return None
    ng = SCORE_DB[ma]
    lower = (question or "").lower()

    if "sat" in lower:
        return (
            f"Điểm chuẩn SAT của ngành **{ng['ten']}** (mã {ng['ma']}) năm 2025 là **{ng['sat']}/1600**.\n\n"
            f"*Dựa trên điểm chuẩn 2025, năm sau có thể thay đổi.*"
        )
    if "act" in lower:
        return (
            f"Điểm chuẩn ACT của ngành **{ng['ten']}** (mã {ng['ma']}) năm 2025 là **{ng['act']}/36**.\n\n"
            f"*Dựa trên điểm chuẩn 2025, năm sau có thể thay đổi.*"
        )
    if "hsa" in lower or ("đánh giá năng lực" in lower and "hà nội" in lower):
        return (
            f"Điểm chuẩn HSA (Đánh giá năng lực ĐH Quốc gia HN - thang 150) của ngành **{ng['ten']}** "
            f"(mã {ng['ma']}) năm 2025 là **{ng['hsa']}/150**.\n\n"
            f"*Dựa trên điểm chuẩn 2025, năm sau có thể thay đổi.*"
        )
    if "tsa" in lower or "đánh giá tư duy" in lower:
        return (
            f"Điểm chuẩn TSA (Đánh giá tư duy ĐH Bách Khoa HN - thang 100) của ngành **{ng['ten']}** "
            f"(mã {ng['ma']}) năm 2025 là **{ng['tsa']}/100**.\n\n"
            f"*Dựa trên điểm chuẩn 2025, năm sau có thể thay đổi.*"
        )
    if "apt" in lower or ("đánh giá năng lực" in lower and "hồ chí minh" in lower):
        return (
            f"Điểm chuẩn APT (Đánh giá năng lực ĐH Quốc gia TP.HCM - thang 1200) của ngành **{ng['ten']}** "
            f"(mã {ng['ma']}) năm 2025 là **{ng['apt']}/1200**.\n\n"
            f"*Dựa trên điểm chuẩn 2025, năm sau có thể thay đổi.*"
        )
    if "kết hợp" in lower or "pt4" in lower:
        return (
            f"Điểm chuẩn Kết hợp (PT4) của ngành **{ng['ten']}** (mã {ng['ma']}) năm 2025 là **{ng['pt4']}/30**.\n\n"
            f"*Dựa trên điểm chuẩn 2025, năm sau có thể thay đổi.*"
        )
    if "tài năng" in lower or "pt1" in lower:
        return (
            f"Điểm chuẩn Tài năng (PT1, thang 100) của ngành **{ng['ten']}** (mã {ng['ma']}) năm 2025 là **{ng['pt1']}/100**.\n\n"
            f"*Dựa trên điểm chuẩn 2025, năm sau có thể thay đổi.*"
        )

    return (
        f"Điểm chuẩn ngành **{ng['ten']}** (mã {ng['ma']}, {ng['loai']}) năm 2025:\n\n"
        f"- **THPT (PT5)**: **{ng['pt5']} điểm**\n"
        f"- Tài năng (PT1): {ng['pt1']}/100\n"
        f"- SAT: {ng['sat']}/1600 | ACT: {ng['act']}/36\n"
        f"- HSA: {ng['hsa']}/150 | TSA: {ng['tsa']}/100 | APT: {ng['apt']}/1200\n"
        f"- Kết hợp (PT4): {ng['pt4']}/30\n"
        f"- **TTNV (Thứ tự nguyện vọng tối đa)**: ≤{ng['ttnv']}\n\n"
        f"*Dựa trên điểm chuẩn 2025, năm sau có thể thay đổi.*"
    )


def answer_ttnv_query(question: str) -> str | None:
    ma = find_major_code(question)
    if not ma or ma not in SCORE_DB:
        return None
    ng = SCORE_DB[ma]
    ttnv = ng["ttnv"]
    dc = ng["pt5"]
    return (
        f"**TTNV (Thứ tự Nguyện vọng tối đa)** của ngành **{ng['ten']}** (mã {ng['ma']}) là **≤{ttnv}**.\n\n"
        f"Điều này có nghĩa là:\n"
        f"- Nếu điểm của bạn bằng đúng điểm chuẩn (**{dc} điểm THPT**), bạn chỉ **ĐỖ** khi đặt ngành này ở **nguyện vọng 1 đến {ttnv}**.\n"
        f"- Nếu đặt từ nguyện vọng {ttnv + 1} trở đi: **TRƯỢT**.\n\n"
        f"*TTNV chỉ áp dụng khi điểm bằng đúng điểm chuẩn. Nếu điểm cao hơn: ĐỖ bất kể thứ tự NV.*"
    )


def answer_comparison_query(question: str) -> str | None:
    score_info = _find_score_type_and_value(question)
    if score_info is None:
        return None

    hoc_ba = score_info.get("hoc_ba")
    thpt = score_info.get("thpt")
    lower = (question or "").lower()

    english_cert = _find_english_score(question)
    has_english_cert = english_cert is not None
    is_pt4_eligible = _check_pt4_eligibility(english_cert) if has_english_cert else False

    is_suggestion = any(
        k in lower
        for k in [
            "nên học",
            "nên đăng ký",
            "nên chọn",
            "học ngành nào",
            "đăng ký ngành nào",
            "chọn ngành nào",
            "phù hợp với em",
        ]
    )
    wants_it = any(k in lower for k in ["công nghệ thông tin", "cntt", "it", "kỹ thuật", "phần mềm", "máy tính", "an toàn thông tin"])

    if hoc_ba is not None and thpt is None:
        ma = find_major_code(question)
        lines = [f"Bạn cho biết **học bạ của bạn là {hoc_ba:.1f}/10**.\n"]

        if has_english_cert:
            cert_type, eng_score = english_cert
            if cert_type == "ielts":
                lines.append(f"\n**Chứng chỉ tiếng Anh:** IELTS {eng_score}/9")
            elif cert_type == "toefl_ibt":
                lines.append(f"\n**Chứng chỉ tiếng Anh:** TOEFL iBT {eng_score}/120")
            elif cert_type == "toefl_itp":
                lines.append(f"\n**Chứng chỉ tiếng Anh:** TOEFL ITP {eng_score}/677")

            if is_pt4_eligible and hoc_ba >= 7.5:
                lines.append("\n✓ **PT4 (Tiếng Anh + THPT) - ĐỦ ĐIỀU KIỆN**")
                lines.append("- Chứng chỉ tiếng Anh: Đạt")
                lines.append(f"- Học bạ: {hoc_ba:.1f}/10 ≥ 7.5")
                if ma and ma in SCORE_DB:
                    ng = SCORE_DB[ma]
                    lines.append("\nBạn cần cung cấp **điểm thi THPT (3 môn)** để hoàn tất xét tuyển PT4.")
                    lines.append(f"Điểm chuẩn PT4 của **{ng['ten']}** năm 2025: **{ng['pt4']}/30** (điểm xét theo tổ hợp quy đổi của PTIT)")
                else:
                    lines.append("\nBạn cần cung cấp **điểm thi THPT (3 môn)** để hoàn tất xét tuyển PT4.")
            else:
                lines.append("\n✗ **PT4 (Tiếng Anh + THPT) - KHÔNG ĐỦ ĐIỀU KIỆN**")
                if not is_pt4_eligible:
                    cert_name = "IELTS" if cert_type == "ielts" else "TOEFL"
                    min_score = "5.5" if cert_type == "ielts" else ("65" if cert_type == "toefl_ibt" else "513")
                    lines.append(f"- Chứng chỉ tiếng Anh: {cert_name} {eng_score} < {min_score} (yêu cầu)")
                if hoc_ba < 7.5:
                    lines.append(f"- Học bạ: {hoc_ba:.1f}/10 < 7.5 (yêu cầu)")
        else:
            lines.append("\nBạn chưa cung cấp chứng chỉ tiếng Anh.")
            lines.append("- Để xét PT4: cần IELTS ≥5.5 (hoặc TOEFL tương đương)")

        lines.append("\n**PT5 (Xét tuyển THPT):** bạn chưa có điểm thi THPT.")
        lines.append("\nĐể mình tư vấn tiếp, bạn cho mình:")
        lines.append("- Điểm thi THPT (3 môn trong tổ hợp xét tuyển)")
        lines.append("- Ngành bạn muốn hỏi (ví dụ: CNTT / Marketing / Thương mại điện tử / Điện tử viễn thông)")
        return "\n".join(lines)

    diem_nv = thpt if thpt is not None else hoc_ba
    if diem_nv is None:
        return None

    if is_suggestion:
        eligible = [(ma, ng) for ma, ng in SCORE_DB.items() if ng["pt5"] <= diem_nv]
        eligible.sort(key=lambda x: x[1]["pt5"], reverse=True)

        if not eligible:
            return (
                f"Bạn cho biết điểm của bạn là **{diem_nv} điểm THPT**.\n\n"
                f"Hiện theo dữ liệu điểm chuẩn 2025, bạn chưa đủ điểm cho ngành nào (điểm thấp nhất là 23.47).\n\n"
                f"*Dựa trên điểm chuẩn 2025, năm sau có thể thay đổi.*"
            )

        it_eligible = [(ma, ng) for ma, ng in eligible if ma in IT_MAJORS]
        other_eligible = [(ma, ng) for ma, ng in eligible if ma not in IT_MAJORS]

        lines = [f"Bạn cho biết điểm của bạn là **{diem_nv} điểm THPT**.\n"]

        if wants_it and it_eligible:
            lines.append("Gợi ý một số ngành **IT/Kỹ thuật** bạn có thể đăng ký:\n")
            for ma, ng in it_eligible[:6]:
                du = round(diem_nv - ng["pt5"], 2)
                lines.append(f"- **{ng['ten']}** (mã {ng['ma']}) — điểm chuẩn {ng['pt5']}, dư **{du} điểm**")
            if other_eligible:
                lines.append(f"\nNgoài ra còn có {len(other_eligible)} ngành kinh tế/truyền thông khác.")
        else:
            lines.append("Gợi ý một số ngành bạn có thể đăng ký (từ điểm chuẩn cao xuống thấp):\n")
            for _, ng in eligible[:8]:
                du = round(diem_nv - ng["pt5"], 2)
                lines.append(f"- **{ng['ten']}** (mã {ng['ma']}) — điểm chuẩn {ng['pt5']}, dư **{du} điểm**")

        lines.append("\n*Kết quả dựa trên điểm chuẩn 2025, năm sau có thể thay đổi.*")
        return "\n".join(lines)

    ma = find_major_code(question)
    if ma is None or ma not in SCORE_DB:
        return None

    ng = SCORE_DB[ma]
    dc_pt5 = ng["pt5"]
    dc_pt4 = ng["pt4"]
    ten = ng["ten"]
    ma_code = ng["ma"]
    ttnv = ng["ttnv"]

    lines = [f"Bạn cho biết điểm của bạn là **{diem_nv} điểm THPT**."]

    if has_english_cert:
        cert_type, score = english_cert
        if cert_type == "ielts":
            lines.append(f"\n**Chứng chỉ tiếng Anh:** IELTS {score}/9")
        elif cert_type == "toefl_ibt":
            lines.append(f"\n**Chứng chỉ tiếng Anh:** TOEFL iBT {score}/120")
        elif cert_type == "toefl_itp":
            lines.append(f"\n**Chứng chỉ tiếng Anh:** TOEFL ITP {score}/677")

        if is_pt4_eligible:
            lines.append("\n✓ **PT4 (Kết hợp tiếng Anh + THPT) - ĐỦ ĐIỀU KIỆN TIẾNG ANH**")
            lines.append(f"- Điểm chuẩn PT4 của {ten} năm 2025: **{dc_pt4}/30**")
        else:
            cert_name = "IELTS" if cert_type == "ielts" else "TOEFL"
            min_score = "5.5" if cert_type == "ielts" else ("65" if cert_type == "toefl_ibt" else "513")
            lines.append("\n✗ **PT4 (Kết hợp tiếng Anh + THPT) - KHÔNG ĐỦ ĐIỀU KIỆN TIẾNG ANH**")
            lines.append(f"- {cert_name} {score} < {min_score} (yêu cầu)")

    if diem_nv > dc_pt5:
        du = round(diem_nv - dc_pt5, 2)
        lines.append(
            f"\n**Có khả năng ĐỖ** ngành **{ten}** (mã {ma_code}).\n"
            f"- Điểm chuẩn THPT 2025: **{dc_pt5} điểm**\n"
            f"- Điểm của bạn cao hơn: **+{du} điểm**"
        )
    elif diem_nv < dc_pt5:
        thieu = round(dc_pt5 - diem_nv, 2)
        lines.append(
            f"\n**Khả năng TRƯỢT** ngành **{ten}** (mã {ma_code}).\n"
            f"- Điểm chuẩn THPT 2025: **{dc_pt5} điểm**\n"
            f"- Điểm của bạn: **{diem_nv} điểm** (thiếu **{thieu} điểm**)"
        )
    else:
        lines.append(
            f"\n**Phụ thuộc TTNV** (vì điểm bằng đúng điểm chuẩn).\n"
            f"- Điểm chuẩn THPT 2025: **{dc_pt5} điểm**\n"
            f"- TTNV của ngành {ten}: **≤{ttnv}**\n"
            f"- Đặt nguyện vọng 1 đến {ttnv}: **ĐỖ** | từ {ttnv + 1} trở đi: **TRƯỢT**"
        )

    lines.append("\n*Kết quả dựa trên điểm chuẩn 2025, năm sau có thể thay đổi.*")
    return "\n".join(lines)
