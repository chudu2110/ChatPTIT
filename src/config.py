import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# LLM Config
LLM_API_KEY = os.getenv("HF_TOKEN", "")  # HuggingFace Inference API
LLM_MODEL = "mistralai/Mistral-7B-Instruct-v0.1"
USE_LOCAL_LLM = False  # Set to True if using Ollama

# RAG Config
CHUNK_SIZE = 400       # Max words per chunk
CHUNK_OVERLAP = 50
TOP_K_RETRIEVAL = 5    # Increased from 3 for better recall
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"  # Multilingual, better for Vietnamese

# All markdown data files to search
DATA_FILES = [
    "danh_muc_nganh_dao_tao.md",
    "diem_chuan_chi_tiet_2025.md",
    "hoc_phi_hoc_bong.md",
    "phuong_thuc.md",
    "gioi_thieu_ptit.md",
    "co_hoi_viec_lam.md",
]

# -------------------------------------------------------------------
# MAJORS — Dữ liệu thực tế từ diem_chuan_chi_tiet_2025.md (PT5/THPT)
# cutoff_score: điểm chuẩn THPT 2025, ttnv: thứ tự nguyện vọng tối đa
# -------------------------------------------------------------------
MAJORS = {
    "CNTT": {
        "name": "Công nghệ Thông tin",
        "code": "7480201",
        "keywords": ["công nghệ thông tin", "cntt", "lập trình", "phần mềm", "software"],
        "cutoff_score": 26.55,
        "ttnv": 5,
        "type": "Đại trà",
        "category": "cong_nghe",
    },
    "ATTT": {
        "name": "An toàn Thông tin",
        "code": "7480202",
        "keywords": ["an toàn thông tin", "attt", "bảo mật", "cyber", "security"],
        "cutoff_score": 26.10,
        "ttnv": 5,
        "type": "Đại trà",
        "category": "cong_nghe",
    },
    "KHMT": {
        "name": "Khoa học Máy tính",
        "code": "7480101",
        "keywords": ["khoa học máy tính", "khmt", "computer science", "machine learning", "data science", "dữ liệu", "ai"],
        "cutoff_score": 26.40,
        "ttnv": 3,
        "type": "Đại trà",
        "category": "cong_nghe",
    },
    "KTDTVT": {
        "name": "Kỹ thuật Điện tử Viễn thông",
        "code": "7520207",
        "keywords": ["điện tử viễn thông", "viễn thông", "vt", "ktdtvt", "electronics", "telecom"],
        "cutoff_score": 25.10,
        "ttnv": 2,
        "type": "Đại trà",
        "category": "cong_nghe",
    },
    "AIOT": {
        "name": "Trí tuệ nhân tạo vạn vật (AIoT)",
        "code": "7520207_AIoT",
        "keywords": ["trí tuệ nhân tạo", "aiot", "iot", "ai", "vạn vật"],
        "cutoff_score": 24.87,
        "ttnv": 2,
        "type": "Đại trà",
        "category": "cong_nghe",
    },
    "KTDKTH": {
        "name": "Kỹ thuật Điều khiển và Tự động hóa",
        "code": "7520216",
        "keywords": ["điều khiển", "tự động hóa", "automation", "robot"],
        "cutoff_score": 25.10,
        "ttnv": 2,
        "type": "Đại trà",
        "category": "cong_nghe",
    },
    "IOT": {
        "name": "Công nghệ Internet vạn vật (IoT)",
        "code": "7520207_IoT",
        "keywords": ["internet vạn vật", "iot", "smart"],
        "cutoff_score": 25.20,
        "ttnv": 3,
        "type": "Đại trà",
        "category": "cong_nghe",
    },
    "KTDDT": {
        "name": "Công nghệ kỹ thuật điện, điện tử",
        "code": "7510301",
        "keywords": ["điện điện tử", "điện tử", "điện", "electrical", "electronics"],
        "cutoff_score": 25.05,
        "ttnv": 4,
        "type": "Đại trà",
        "category": "cong_nghe",
    },
    "CNDPT": {
        "name": "Công nghệ Đa phương tiện",
        "code": "7329001",
        "keywords": ["đa phương tiện", "multimedia", "thiết kế", "đồ họa", "game"],
        "cutoff_score": 25.85,
        "ttnv": 3,
        "type": "Đại trà",
        "category": "truyen_thong",
    },
    "TTDPT": {
        "name": "Truyền thông Đa phương tiện",
        "code": "7320104",
        "keywords": ["truyền thông", "media", "báo chí", "multimedia"],
        "cutoff_score": 26.20,
        "ttnv": 5,
        "type": "Đại trà",
        "category": "truyen_thong",
    },
    "BC": {
        "name": "Báo chí số",
        "code": "7320101",
        "keywords": ["báo chí", "journalism", "news"],
        "cutoff_score": 25.00,
        "ttnv": 2,
        "type": "Đại trà",
        "category": "truyen_thong",
    },
    "QTKD": {
        "name": "Quản trị Kinh doanh",
        "code": "7340101",
        "keywords": ["quản trị kinh doanh", "qtkd", "business", "kinh doanh"],
        "cutoff_score": 25.60,
        "ttnv": 4,
        "type": "Đại trà",
        "category": "kinh_te",
    },
    "MKT": {
        "name": "Marketing",
        "code": "7340115",
        "keywords": ["marketing", "quảng cáo", "thương hiệu"],
        "cutoff_score": 25.90,
        "ttnv": 5,
        "type": "Đại trà",
        "category": "kinh_te",
    },
    "QHC": {
        "name": "Quan hệ Công chúng",
        "code": "7340115_QHC",
        "keywords": ["quan hệ công chúng", "pr", "public relations"],
        "cutoff_score": 23.47,
        "ttnv": 3,
        "type": "Đại trà",
        "category": "truyen_thong",
    },
    "TMDT": {
        "name": "Thương mại Điện tử",
        "code": "7340122",
        "keywords": ["thương mại điện tử", "tmdt", "e-commerce", "ecommerce"],
        "cutoff_score": 26.35,
        "ttnv": 5,
        "type": "Đại trà",
        "category": "kinh_te",
    },
    "FINTECH": {
        "name": "Công nghệ Tài chính (Fintech)",
        "code": "7340205",
        "keywords": ["tài chính", "fintech", "finance", "ngân hàng"],
        "cutoff_score": 25.70,
        "ttnv": 3,
        "type": "Đại trà",
        "category": "kinh_te",
    },
    "KT": {
        "name": "Kế toán",
        "code": "7340301",
        "keywords": ["kế toán", "accounting", "tài khoản"],
        "cutoff_score": 25.35,
        "ttnv": 6,
        "type": "Đại trà",
        "category": "kinh_te",
    },
    "CNTT_CLC": {
        "name": "Công nghệ Thông tin Chất lượng cao",
        "code": "7480201_CLC",
        "keywords": ["công nghệ thông tin clc", "cntt clc", "chất lượng cao cntt"],
        "cutoff_score": 26.15,
        "ttnv": 2,
        "type": "Chất lượng cao",
        "category": "cong_nghe",
    },
    "QTKD_CLC": {
        "name": "Quản trị Kinh doanh Chất lượng cao",
        "code": "7340101_CLC",
        "keywords": ["qtkd clc", "kinh doanh clc", "chất lượng cao kinh doanh"],
        "cutoff_score": 25.00,
        "ttnv": 3,
        "type": "Chất lượng cao",
        "category": "kinh_te",
    },
}
