from app.services.chat_service import (
    handle_chat
)


while True:
    query = input("\nYou: ")

    response = handle_chat(query)

    print("\nAssistant:\n")

    print(response["reply"])

    print("\nRecommendations:\n")

    for item in response["recommendations"]:
        print("-", item["name"])

    print("\n---")