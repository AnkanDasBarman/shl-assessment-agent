from app.retrieval.retriever import (
    search_assessments
)

from app.services.llm_service import (
    generate_response
)


query = input("Enter query: ")

results = search_assessments(
    query,
    top_k=5
)

response = generate_response(
    query,
    results
)

print("\nAI RESPONSE:\n")

print(response)