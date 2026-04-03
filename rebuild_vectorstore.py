import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import VECTOR_DB_PATH

def rebuild():
    print("=== PTIT Chatbot - Rebuild Vectorstore ===\n")
    
    if os.path.exists(VECTOR_DB_PATH):
        shutil.rmtree(VECTOR_DB_PATH)
        print(f"[OK] Removed old vectorstore at: {VECTOR_DB_PATH}")
    else:
        print(f"[INFO] No old vectorstore found at: {VECTOR_DB_PATH}")
    
    print("[INFO] Loading and splitting documents...")
    from src.loader import load_documents
    docs = load_documents()
    print(f"[OK] Loaded {len(docs)} chunks from data/")

    print("[INFO] Creating embeddings and FAISS index (may take a few minutes)...")
    from src.vectorstore import create_vectorstore
    create_vectorstore()
    print(f"[OK] Vectorstore saved at: {VECTOR_DB_PATH}")
    
    print("\n=== Finished! ===")

if __name__ == "__main__":
    rebuild()
