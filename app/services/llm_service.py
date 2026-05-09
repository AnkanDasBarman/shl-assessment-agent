import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


SYSTEM_PROMPT = """
You are an SHL assessment recommendation assistant.

Rules:
- Use ONLY provided SHL assessment data.
- Never hallucinate assessments.
- Stay within SHL catalog.
- Recommend relevant assessments.
- Be concise and professional.
"""


def generate_response(
    user_query,
    retrieved_assessments
):
    catalog_context = ""

    for item in retrieved_assessments:
        catalog_context += f"""
Name: {item['name']}
URL: {item['url']}
Description: {item['description']}
Categories: {item['categories']}
"""

    prompt = f"""
{SYSTEM_PROMPT}

User Query:
{user_query}

Retrieved SHL Assessments:
{catalog_context}

Task:
Recommend the best assessments.
Explain briefly why they match.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content