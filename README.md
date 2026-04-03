# PTIT Admission Chatbot

Hệ thống **trợ lý tuyển sinh PTIT** giúp thí sinh tra cứu điểm chuẩn, học phí, TTNV và các thông tin liên quan đến tuyển sinh Học viện Công nghệ Bưu chính Viễn thông (PTIT). Ứng dụng sử dụng mô hình ngôn ngữ lớn (LLM) với cơ chế Retrieval-Augmented Generation (RAG) để chỉ trả lời dựa trên dữ liệu do người dùng cung cấp.

> *Thiết kế ưu tiên độ chính xác: chatbot chỉ trả lời khi thông tin có trong dữ liệu, không dùng kiến thức từ tập huấn hoặc bịa số.*

---

## Tính năng nổi bật

- Trả lời nhanh các câu hỏi cấu trúc: điểm chuẩn, TTNV, so sánh điểm, gợi ý ngành.
- RAG + LLM xử lý câu hỏi tự do như học phí, danh mục ngành, phương thức tuyển sinh.
- Hệ thống dữ liệu Markdown có cấu trúc (điểm chuẩn, học phí, phương thức, v.v.).
- Cấu hình dễ dàng: điều chỉnh mô hình embedding, LLM, các tham số retriever.
- Cơ chế tự bảo vệ chống tạo số ảo giác, ngôn ngữ lạc hướng và ngoại ngữ.
- Hiển thị nguồn tài liệu đã truy xuất để tăng độ tin cậy.

---

## Cấu trúc thư mục chính

```
chatbot/
├── app.py                # API chính, router câu hỏi, gọi RAG/LLM
├── src/
│   ├── config.py         # Tham số cấu hình chung
│   ├── llm.py            # Khởi tạo LLM (Gemma) với nhiệt độ thấp, stop tokens
│   ├── prompt.py         # Bộ template hệ thống và hướng dẫn chatbot
│   ├── query_router.py   # Xử lý trực tiếp câu hỏi kiểu điểm/TTNV/so sánh
│   ├── loader.py         # Load & split Markdown thành chunk có tag
│   ├── vectorstore.py    # Tạo và nạp lại Faiss/BM25, thiết lập hybrid retriever
│   ├── rag_chain.py      # Xây dựng chuỗi RAG với prompt chat
│   └── ...
├── data/                 # Tài liệu Markdown: điểm chuẩn, học phí, v.v.
├── vectorstore/          # Chỉ mục Faiss đã build
├── requirements.txt
└── README.md             # (bạn đang xem)
```

---

## Cài đặt và sử dụng

1. **Môi trường Python**
   ```bash
   python -m venv .venv
   source .venv/Scripts/activate  # Windows
   pip install -r requirements.txt
   ```

2. **Khởi tạo bộ dữ liệu**
   ```bash
   python rebuild_vectorstore.py
   ```
   Lệnh này đọc các tệp Markdown trong `data/`, tạo chỉ mục Faiss, lưu vào `vectorstore/faiss`.

3. **Chạy chatbot**
   Thực thi module hoặc tích hợp giao diện (Flask/Gradio) tuỳ nhu cầu:
   ```bash
   python app.py  
   ./.venv/Scripts/uvicorn.exe app:app --host 127.0.0.1 --port 8000 --reload
   ```

4. **Truy vấn**
   ```python
   from app import ask
   print(ask("Điểm chuẩn CNTT năm 2025 là bao nhiêu?"))
   ```

---

## Cấu hình chính (`src/config.py`)

| Biến | Giá trị mặc định | Ý nghĩa |
|------|------------------|---------|
| `DATA_PATH` | `data/` | Nơi chứa Markdown nguồn |
| `VECTOR_DB_PATH` | `vectorstore/faiss` | Đường dẫn chỉ mục Faiss |
| `EMBEDDING_MODEL` | `intfloat/multilingual-e5-base` | Embedding model |
| `LLM_MODEL` | `gemma3:4b` | Mô hình RAG |
| `CHUNK_SIZE`, `CHUNK_OVERLAP` | `2000`, `400` | Tham số chia văn bản |
| `TOP_K` | `4` | Số chunk lấy từ mỗi retriever |

---

## Ghi chú quan trọng

* **Ngôn ngữ:** chatbot luôn trả lời bằng tiếng Việt, ngắt khi phát hiện ký tự lạ.
* **Chỉ nguồn trong dữ liệu:** nếu RAG không tìm thấy chunk liên quan, chatbot trả:  "Hiện tôi chưa có thông tin về vấn đề này trong cơ sở dữ liệu." (và không gọi LLM thêm).
* **TTNV** chỉ sử dụng để dự đoán khi điểm NV = điểm chuẩn.
* **Không bịa số:** Ràng buộc trong `prompt.py` ngăn model tự tạo số liệu ngoài context.

---


