import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .config import *

# Bảng mapping: từ khóa trong tên file → [prefix nội dung, metadata category]
_FILE_TAGS = {
    "diem_chuan": (
        "[DỮ LIỆU ĐIỂM CHUẨN VÀ TTNV — Chứa bảng điểm thi THPT và thứ tự nguyện vọng]\n",
        "diem_chuan"
    ),
    "hoc_phi": (
        "[DỮ LIỆU HỌC PHÍ VÀ HỌC BỔNG — Đây là thông tin tài chính, KHÔNG phải điểm thi hay TTNV]\n",
        "hoc_phi"
    ),
    "phuong_thuc": (
        "[PHƯƠNG THỨC TUYỂN SINH PTIT — Mô tả các phương thức PT1, PT2, PT4, PT5, TTNV]\n",
        "phuong_thuc"
    ),
    "danh_muc": (
        "[DANH MỤC NGÀNH ĐÀO TẠO PTIT — Tên ngành, mã xét tuyển, tổ hợp môn, loại chương trình]\n",
        "danh_muc_nganh"
    ),
    "co_hoi": (
        "[CƠ HỘI VIỆC LÀM VÀ HỢP TÁC DOANH NGHIỆP — Không chứa điểm chuẩn hay học phí]\n",
        "viec_lam"
    ),
}

_DEFAULT_TAG = (
    "[THÔNG TIN CHUNG VỀ PTIT — Giới thiệu học viện, định hướng đào tạo]\n",
    "gioi_thieu"
)


def _get_file_tag(filename: str):
    """Trả về (prefix_text, category_name) dựa trên tên file."""
    name_lower = filename.lower()
    for keyword, tag in _FILE_TAGS.items():
        if keyword in name_lower:
            return tag
    return _DEFAULT_TAG


def load_documents():
    if not os.path.isdir(DATA_PATH):
        return []

    documents = []
    md_files = []
    for root, _, files in os.walk(DATA_PATH):
        for filename in files:
            if filename.lower().endswith(".md"):
                md_files.append(os.path.join(root, filename))

    for file_path in sorted(md_files):
        source_file = os.path.relpath(file_path, DATA_PATH).replace("\\", "/")
        loader = TextLoader(file_path, encoding="utf-8")
        raw_docs = loader.load()

        prefix_text, category = _get_file_tag(source_file)
        for doc in raw_docs:
            doc.metadata["category"] = category
            doc.metadata["source_file"] = source_file
            doc.page_content = prefix_text + doc.page_content

        documents.extend(raw_docs)

    # Cấu hình tối ưu cho bảng biểu — kích thước lớn hơn để giữ nguyên vẹn bảng
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", "|", " ", ""],
        keep_separator=True,
    )

    docs = splitter.split_documents(documents)

    # Đảm bảo prefix category được giữ lại trên mỗi chunk sau khi split
    for doc in docs:
        category = doc.metadata.get("category", "")
        prefix_text, _ = _get_file_tag(doc.metadata.get("source_file", ""))
        # Nếu chunk bị mất prefix (do split cắt bỏ), thêm lại vào đầu
        if not doc.page_content.startswith("["):
            doc.page_content = prefix_text + doc.page_content

    return docs
