from fastapi import FastAPI
from pydantic import BaseModel

from app.services.chat_service import (
    handle_chat
)


app = FastAPI(
    title="SHL Assessment Recommendation API",
    description=(
        "AI-powered recommendation system "
        "for SHL assessments using "
        "semantic search and RAG."
    ),
    version="1.0.0",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@app.post("/chat")
def chat(request: ChatRequest):
    try:
        response = handle_chat(
            request.query
        )

        return response

    except Exception as e:
        return {
            "error": str(e)
        }