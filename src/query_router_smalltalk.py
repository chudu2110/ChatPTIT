GREETINGS = ["xin chào", "chào bạn", "hello", "bonjour", "chào", "hey", "hi", "alo"]

OUT_OF_SCOPE_KEYWORDS = [
    "người yêu",
    "thời tiết",
    "giải trí",
    "chính trị",
    "đá bóng",
    "ca nhạc",
    "game",
    "phim",
    "cổ phiếu",
    "crypto",
    "tiền ảo",
]


def split_leading_greeting(text: str) -> tuple[bool, str]:
    if not text:
        return False, ""
    s = text.lstrip()
    lower = s.lower()
    for g in sorted(GREETINGS, key=len, reverse=True):
        if lower.startswith(g):
            after = lower[len(g) :]
            if after == "" or after[0] in " ,.!?:;/-–—\t\n":
                rest = s[len(g) :].lstrip(" ,.!?:;/-–—\t\n")
                return True, rest
    return False, text


def is_pure_greeting(text: str) -> bool:
    lower = (text or "").lower().strip()
    if not lower:
        return True
    if lower in GREETINGS:
        return True
    if len(lower.split()) <= 2 and any(g == lower for g in GREETINGS):
        return True
    return False


def answer_greeting() -> str:
    return "Chào bạn! Mình là tư vấn viên tuyển sinh của PTIT. Bạn muốn hỏi về ngành học, điểm chuẩn hay phương thức xét tuyển?"


def is_out_of_scope(text: str) -> bool:
    lower = (text or "").lower()
    return any(k in lower for k in OUT_OF_SCOPE_KEYWORDS)


def answer_out_of_scope() -> str:
    return "Mình chỉ hỗ trợ tư vấn tuyển sinh PTIT (ngành học, điểm chuẩn, phương thức xét tuyển...). Bạn muốn hỏi nội dung nào về tuyển sinh?"
