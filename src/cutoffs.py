"""Score cutoff data — Dữ liệu thực tế từ diem_chuan_chi_tiet_2025.md (PTIT 2025 - Cơ sở phía Bắc)"""

from dataclasses import dataclass
from typing import Optional, List
import re


@dataclass
class MajorCutoff:
    code: str
    name: str
    cutoff_pt5: float    # Điểm chuẩn THPT (PT5), thang /30
    cutoff_pt1: float    # Điểm Tài năng (PT1), thang /100
    cutoff_sat: float    # SAT, thang /1600
    cutoff_act: float    # ACT, thang /36
    cutoff_hsa: float    # HSA (ĐHQGHN), thang /150
    cutoff_tsa: float    # TSA (Bách Khoa), thang /100
    cutoff_spt: float    # SPT (ĐHSP HN), thang /30
    cutoff_apt: float    # APT (ĐHQG HCM), thang /1200
    cutoff_pt4: float    # Kết hợp (PT4), thang /30
    ttnv: int            # Thứ tự nguyện vọng tối đa
    program_type: str    # "Đại trà" hoặc "Chất lượng cao"


# Dữ liệu thực tế từ file diem_chuan_chi_tiet_2025.md
CUTOFF_DATA: List[MajorCutoff] = [
    MajorCutoff("7520207",      "Kỹ thuật Điện tử Viễn thông",               25.10, 76.79, 1341.43, 29.83, 96.49,  68.96, 22.56, 880.91, 27.64, 2, "Đại trà"),
    MajorCutoff("7520207_AIoT", "Trí tuệ nhân tạo vạn vật (AIoT)",           24.87, 71.86, 1324.29, 29.31, 94.13,  67.29, 21.93, 864.86, 27.24, 2, "Đại trà"),
    MajorCutoff("7480201",      "Công nghệ Thông tin (CNTT)",                 26.55, 86.64, 1374.29, 30.83, 101.20, 72.30, 23.82, 913.03, 28.44, 5, "Đại trà"),
    MajorCutoff("7480202",      "An toàn Thông tin (ATTT)",                   26.10, 81.71, 1358.57, 30.31, 98.84,  70.63, 23.18, 896.91, 28.04, 5, "Đại trà"),
    MajorCutoff("7480101",      "Khoa học Máy tính",                          26.40, 84.18, 1369.29, 30.63, 100.41, 71.74, 23.60, 907.66, 28.30, 3, "Đại trà"),
    MajorCutoff("7520216",      "Kỹ thuật Điều khiển và Tự động hóa",         25.10, 76.79, 1341.43, 29.83, 96.49,  68.96, 22.56, 880.91, 27.64, 2, "Đại trà"),
    MajorCutoff("7520207_IoT",  "Công nghệ Internet vạn vật (IoT)",           25.20, 77.00, 1342.00, 29.90, 96.50,  69.00, 22.60, 881.00, 27.70, 3, "Đại trà"),
    MajorCutoff("7510301",      "Công nghệ kỹ thuật điện, điện tử",           25.05, 76.00, 1340.00, 29.80, 96.00,  68.50, 22.50, 880.00, 27.60, 4, "Đại trà"),
    MajorCutoff("7329001",      "Công nghệ Đa phương tiện",                   25.85, 79.25, 1350.00, 30.06, 97.66,  69.79, 22.87, 888.86, 27.84, 3, "Đại trà"),
    MajorCutoff("7320104",      "Truyền thông Đa phương tiện",                26.20, 81.71, 1358.57, 30.31, 98.84,  70.63, 23.18, 896.91, 28.04, 5, "Đại trà"),
    MajorCutoff("7320101",      "Báo chí số",                                 25.00, 70.00, 1300.00, 29.00, 92.00,  65.00, 21.50, 850.00, 26.50, 2, "Đại trà"),
    MajorCutoff("7340101",      "Quản trị Kinh doanh (QTKD)",                 25.60, 70.00, 1300.00, 29.00, 92.00,  65.00, 21.50, 850.00, 26.50, 4, "Đại trà"),
    MajorCutoff("7340115",      "Marketing",                                  25.90, 73.00, 1320.00, 29.50, 94.00,  67.00, 22.00, 870.00, 27.00, 5, "Đại trà"),
    MajorCutoff("7340115_QHC",  "Quan hệ Công chúng",                         23.47, 42.50, 1248.80, 27.97, 90.91,  65.36, 20.48, 814.86, 26.48, 3, "Đại trà"),
    MajorCutoff("7340122",      "Thương mại Điện tử",                         26.35, 80.00, 1355.00, 30.20, 98.00,  70.00, 23.00, 890.00, 28.00, 5, "Đại trà"),
    MajorCutoff("7340205",      "Công nghệ Tài chính (Fintech)",              25.70, 72.00, 1315.00, 29.20, 93.00,  66.00, 21.80, 860.00, 26.80, 3, "Đại trà"),
    MajorCutoff("7340301",      "Kế toán",                                    25.35, 68.00, 1290.00, 28.80, 91.00,  64.00, 21.20, 840.00, 26.20, 6, "Đại trà"),
    MajorCutoff("7480201_CLC",  "Công nghệ Thông tin Chất lượng cao (CNTT CLC)", 26.15, 80.00, 1350.00, 30.00, 98.00, 70.00, 23.00, 890.00, 28.00, 2, "Chất lượng cao"),
    MajorCutoff("7340101_CLC",  "Quản trị Kinh doanh Chất lượng cao (QTKD CLC)", 25.00, 65.00, 1280.00, 28.50, 90.00, 63.00, 21.00, 830.00, 26.00, 3, "Chất lượng cao"),
    MajorCutoff("7329001_GAM",  "Thiết kế & Phát triển Game",                 25.50, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 28.00, 3, "Chất lượng cao"),
]

# Index by code for fast lookup
CUTOFF_BY_CODE = {m.code: m for m in CUTOFF_DATA}

MAJOR_ALIASES = {
    "cntt": "7480201",
    "công nghệ thông tin": "7480201",
    "it": "7480201",
    "attt": "7480202",
    "an toàn thông tin": "7480202",
    "khmt": "7480101",
    "khoa học máy tính": "7480101",
    "computer science": "7480101",
    "aiot": "7520207_AIoT",
    "trí tuệ nhân tạo vạn vật": "7520207_AIoT",
    "internet vạn vật": "7520207_IoT",
    "iot": "7520207_IoT",
    "điện tử viễn thông": "7520207",
    "viễn thông": "7520207",
    "vt": "7520207",
    "ktdtvt": "7520207",
    "cntt clc": "7480201_CLC",
    "công nghệ thông tin clc": "7480201_CLC",
    "qtkd": "7340101",
    "quản trị kinh doanh": "7340101",
    "marketing": "7340115",
    "mkt": "7340115",
    "thương mại điện tử": "7340122",
    "tmdt": "7340122",
    "fintech": "7340205",
    "công nghệ tài chính": "7340205",
    "tài chính": "7340205",
    "kế toán": "7340301",
    "kt": "7340301",
    "quan hệ công chúng": "7340115_QHC",
    "qhc": "7340115_QHC",
    "pr": "7340115_QHC",
    "truyền thông đa phương tiện": "7320104",
    "ttdpt": "7320104",
    "công nghệ đa phương tiện": "7329001",
    "cndpt": "7329001",
    "báo chí": "7320101",
    "bc": "7320101",
    "tự động hóa": "7520216",
    "điều khiển": "7520216",
    "điện điện tử": "7510301",
    "qtkd clc": "7340101_CLC",
    "game": "7329001_GAM",
    "thiết kế game": "7329001_GAM",
    "phát triển game": "7329001_GAM",
}


def _contains_alias(query_lower: str, alias: str) -> bool:
    if " " in alias:
        return alias in query_lower
    return re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", query_lower) is not None


def get_cutoffs() -> List[MajorCutoff]:
    return CUTOFF_DATA


def find_major_by_query(query: str) -> Optional[MajorCutoff]:
    """Find major by name or code mentioned in query"""
    query_lower = query.lower()

    for alias, code in sorted(MAJOR_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        if _contains_alias(query_lower, alias):
            return CUTOFF_BY_CODE.get(code)

    # Fallback: check against full names
    for major in CUTOFF_DATA:
        if major.name.lower() in query_lower:
            return major

    return None
