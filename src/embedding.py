import os

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")

from langchain_huggingface import HuggingFaceEmbeddings
from .config import *


def load_embedding():
    embedding = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
    )
    return embedding

