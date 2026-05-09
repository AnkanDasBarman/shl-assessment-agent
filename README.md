---
title: SHL Assessment Agent
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# SHL Assessment Recommendation System

AI-powered recommendation system for SHL assessments using:

- Semantic Search
- FAISS Vector Database
- RAG (Retrieval-Augmented Generation)
- Groq LLM
- FastAPI

---

# Features

- Conversational assessment recommendations
- Clarification questions
- Refinement-aware retrieval
- Personality + technical assessment matching
- Multi-turn conversation memory
- Semantic vector search

---

# Tech Stack

- Python
- FastAPI
- Sentence Transformers
- FAISS
- Groq API
- Llama 3

---

# Installation

## Clone Repository

```bash
git clone <repo_url>
cd shl-assessment-agent
```

## Create Virtual Environment

```bash
python -m venv venv
```

## Activate Virtual Environment

### Windows

```bash
venv\Scripts\activate
```

### Linux/Mac

```bash
source venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create `.env`

```env
GROQ_API_KEY=your_api_key
```

---

# Build Embeddings

```bash
python scripts/build_embeddings.py
```

---

# Run API

```bash
uvicorn app.main:app --reload
```

---

# API Documentation

Open:

```text
http://127.0.0.1:8000/docs
```

---

# Example Request

POST `/chat`

```json
{
  "query": "Need backend Java developer assessments"
}
```

---

# Example Response

```json
{
  "reply": "...",
  "recommendations": [],
  "end_of_conversation": true
}
```
## Live Demo

API:
https://ankan03282002-shl-assessment-agent.hf.space

Swagger Docs:
https://ankan03282002-shl-assessment-agent.hf.space/docs
