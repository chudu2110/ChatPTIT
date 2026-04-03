from fastapi import FastAPI

from app import ask


app = FastAPI()


@app.get("/chat")

def chat(q: str):

    answer = ask(q)

    return {

        "question": q,

        "answer": answer

    }