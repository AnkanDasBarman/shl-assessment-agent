from app.retrieval.retriever import (
    search_assessments
)

from app.services.llm_service import (
    generate_response
)


conversation_memory = {
    "last_query": None,
    "last_results": [],
}


def needs_clarification(user_query):
    user_query = user_query.lower()

    role_keywords = [
        "developer",
        "engineer",
        "manager",
        "analyst",
        "sales",
        "java",
        "python",
        "frontend",
        "backend",
        "data",
        "cloud",
        "devops",
        "leadership",
        "personality",
        "cognitive",
    ]

    has_role = any(
        word in user_query
        for word in role_keywords
    )

    vague_phrases = [
        "need assessment",
        "need a test",
        "hiring",
        "assessment",
        "test",
    ]

    is_vague = any(
        phrase in user_query
        for phrase in vague_phrases
    )

    if is_vague and not has_role:
        return True

    return False


def is_refinement_query(user_query):
    refinement_words = [
        "also",
        "add",
        "include",
    ]

    return any(
        word in user_query.lower()
        for word in refinement_words
    )


def build_refined_query(user_query):
    previous_query = conversation_memory[
        "last_query"
    ]

    if previous_query:
        return (
            previous_query
            + " "
            + user_query
        )

    return user_query


def merge_results(primary, secondary):
    seen = set()

    merged = []

    for item in primary + secondary:
        url = item["url"]

        if url not in seen:
            seen.add(url)
            merged.append(item)

    return merged


def refinement_search(user_query):
    combined_query = build_refined_query(
        user_query
    )

    primary_results = search_assessments(
        combined_query,
        top_k=5
    )

    extra_results = []

    lower_query = user_query.lower()

    if "personality" in lower_query:
        extra_results += search_assessments(
            "personality behavioral OPQ",
            top_k=3
        )

    if "cognitive" in lower_query:
        extra_results += search_assessments(
            "cognitive aptitude reasoning",
            top_k=3
        )

    return merge_results(
        primary_results,
        extra_results
    )


def handle_chat(user_query):
    if needs_clarification(user_query):
        return {
            "reply": (
                "Could you specify the role, "
                "seniority level, or skills "
                "you are hiring for?"
            ),
            "recommendations": [],
            "end_of_conversation": False,
        }

    if is_refinement_query(user_query):
        results = refinement_search(
            user_query
        )

        refined_query = build_refined_query(
            user_query
        )

        llm_reply = generate_response(
            refined_query,
            results
        )

        conversation_memory[
            "last_query"
        ] = refined_query

    else:
        results = search_assessments(
            user_query,
            top_k=5
        )

        llm_reply = generate_response(
            user_query,
            results
        )

        conversation_memory[
            "last_query"
        ] = user_query

    conversation_memory[
        "last_results"
    ] = results

    recommendations = []

    for item in results:
        recommendations.append({
            "name": item["name"],
            "url": item["url"],
            "test_type": (
                item["categories"][0]
                if item["categories"]
                else "Unknown"
            )
        })

    return {
        "reply": llm_reply,
        "recommendations": recommendations,
        "end_of_conversation": True,
    }