import os
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_classic.retrievers import EnsembleRetriever

from .loader import load_documents
from .embedding import load_embedding
from .config import *

def create_vectorstore():

    docs = load_documents()

    embedding = load_embedding()

    db = FAISS.from_documents(

        docs,

        embedding
    )

    os.makedirs(os.path.dirname(VECTOR_DB_PATH), exist_ok=True)
    db.save_local(VECTOR_DB_PATH)

    return db


def load_vectorstore():

    embedding = load_embedding()

    db = FAISS.load_local(

        VECTOR_DB_PATH,

        embedding,

        allow_dangerous_deserialization=True
    )

    return db

def create_bm25():

    docs = load_documents()

    bm25 = BM25Retriever.from_documents(

        docs

    )

    bm25.k = TOP_K

    return bm25


def create_hybrid_retriever():

    # Nếu chưa có FAISS index thì tạo mới
    if not os.path.exists(VECTOR_DB_PATH):
        create_vectorstore()

    faiss_db = load_vectorstore()

    faiss_retriever = faiss_db.as_retriever(

        search_kwargs={"k": TOP_K}

    )

    bm25 = create_bm25()

    hybrid = EnsembleRetriever(

        retrievers=[

            bm25,

            faiss_retriever

        ],

        # BM25 0.7: ưu tiên khớp từ khóa chính xác ("CNTT", "TTNV", "điểm chuẩn")
        # FAISS 0.3: hỗ trợ ngữ nghĩa khi câu hỏi dùng từ đồng nghĩa
        weights=[

            0.7,

            0.3
        ]
    )

    return hybrid
