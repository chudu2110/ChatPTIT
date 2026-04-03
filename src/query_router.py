from .query_router_admissions import (
    answer_admission_method_query,
    answer_admission_methods_overview_query,
    is_admission_method_query,
)
from .query_router_constants import SCORE_DB
from .query_router_majors import (
    find_major_candidates,
    find_major_code,
    looks_like_major_only,
    major_display_name,
)
from .query_router_school_info import answer_school_info_query
from .query_router_scores import (
    answer_comparison_query,
    answer_forecast_score_query,
    answer_score_query,
    answer_ttnv_query,
    is_comparison_query,
    is_forecast_score_query,
    is_score_query,
    is_ttnv_query,
)
from .query_router_smalltalk import (
    answer_greeting,
    answer_out_of_scope,
    is_out_of_scope,
    is_pure_greeting,
    split_leading_greeting,
)

NO_INFO_FALLBACK = "Hiện tại mình chưa có thông tin chính xác về nội dung này. Bạn có thể cung cấp thêm chi tiết được không?"


def _maybe_prefix_greeting(greeted: bool, text: str) -> str:
    if not greeted:
        return text
    if not text:
        return "Xin chào!"
    if text.lower().startswith("xin chào"):
        return text
    return f"Xin chào! {text}"


def _ask_choose_major(codes: list[str]) -> str:
    items: list[str] = []
    for ma in codes[:4]:
        ng = SCORE_DB.get(ma)
        if not ng:
            continue
        items.append(f"- **{ng['ten']}** (mã {ng['ma']})")
    if not items:
        return "Bạn muốn hỏi về ngành nào của PTIT (ví dụ: CNTT, Marketing, Thương mại điện tử, Điện tử viễn thông...)?"
    return "Mình cần bạn làm rõ bạn đang hỏi ngành nào:\n" + "\n".join(items)


def route_query(question: str) -> str | None:
    greeted, cleaned = split_leading_greeting(question)
    lower = (cleaned or "").lower().strip()

    if is_pure_greeting(lower):
        return answer_greeting()

    if is_out_of_scope(lower):
        return answer_out_of_scope()

    major_candidates = find_major_candidates(lower)

    if is_forecast_score_query(lower):
        return _maybe_prefix_greeting(greeted, answer_forecast_score_query(cleaned))

    if not major_candidates:
        result = answer_school_info_query(cleaned)
        if result:
            return _maybe_prefix_greeting(greeted, result)

    if looks_like_major_only(lower):
        if not major_candidates:
            return _maybe_prefix_greeting(
                greeted,
                "Bạn đang quan tâm ngành/chương trình nào của PTIT? Ví dụ: CNTT, Marketing, Thương mại điện tử, Điện tử viễn thông.",
            )
        if len(major_candidates) > 1:
            return _maybe_prefix_greeting(greeted, _ask_choose_major(major_candidates))
        ma = major_candidates[0]
        ng = SCORE_DB.get(ma)
        if not ng:
            return _maybe_prefix_greeting(greeted, NO_INFO_FALLBACK)
        return _maybe_prefix_greeting(
            greeted,
            f"Bạn đang quan tâm đến ngành **{ng['ten']}** (mã {ng['ma']}) đúng không? Bạn muốn hỏi về điểm chuẩn, phương thức xét tuyển hay cơ hội nghề nghiệp?",
        )

    if major_candidates and any(k in lower for k in ["phương thức", "xét tuyển"]):
        if is_admission_method_query(cleaned):
            result = answer_admission_method_query(cleaned)
            if result:
                return _maybe_prefix_greeting(greeted, result)
        result = answer_admission_methods_overview_query(cleaned)
        if result:
            return _maybe_prefix_greeting(greeted, result)

    if major_candidates and is_admission_method_query(cleaned):
        result = answer_admission_method_query(cleaned)
        if result:
            return _maybe_prefix_greeting(greeted, result)

    if major_candidates and any(k in lower for k in ["chương trình", "định hướng", "nghề nghiệp", "cơ hội", "việc làm"]):
        return None

    if major_candidates and (is_score_query(lower) or is_ttnv_query(lower) or is_comparison_query(lower)):
        if len(major_candidates) > 1:
            return _maybe_prefix_greeting(greeted, _ask_choose_major(major_candidates))
    elif major_candidates:
        if len(major_candidates) > 1:
            return _maybe_prefix_greeting(greeted, _ask_choose_major(major_candidates))
        ma = major_candidates[0]
        ng = SCORE_DB.get(ma)
        if not ng:
            return _maybe_prefix_greeting(greeted, NO_INFO_FALLBACK)
        return _maybe_prefix_greeting(
            greeted,
            f"Mình hiểu bạn đang nói đến ngành **{ng['ten']}** (mã {ng['ma']}). Bạn muốn hỏi thông tin nào: điểm chuẩn, phương thức xét tuyển hay chương trình/định hướng nghề nghiệp?",
        )

    result = answer_admission_methods_overview_query(cleaned)
    if result:
        return _maybe_prefix_greeting(greeted, result)

    if is_admission_method_query(cleaned):
        result = answer_admission_method_query(cleaned)
        if result:
            return _maybe_prefix_greeting(greeted, result)

    if is_comparison_query(cleaned):
        result = answer_comparison_query(cleaned)
        if result:
            return _maybe_prefix_greeting(greeted, result)

    if is_ttnv_query(cleaned):
        result = answer_ttnv_query(cleaned)
        if result:
            return _maybe_prefix_greeting(greeted, result)
        if len(major_candidates) == 0:
            return "Hiện tại mình chưa có thông tin chính xác về nội dung này. Bạn có thể cho mình biết bạn đang hỏi ngành nào được không?"

    if is_score_query(cleaned):
        result = answer_score_query(cleaned)
        if result:
            return _maybe_prefix_greeting(greeted, result)
        if len(major_candidates) == 0:
            return "Hiện tại mình chưa có thông tin chính xác về nội dung này. Bạn có thể cho mình biết bạn đang hỏi ngành nào được không?"

    return None
