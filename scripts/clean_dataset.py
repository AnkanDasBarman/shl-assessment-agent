import json
import re

INPUT_FILE = "data/raw/shl_catalog.json"
OUTPUT_FILE = "data/processed/clean_assessments.json"


def _escape_control_chars_inside_strings(raw_text):
    repaired = []
    in_string = False
    escaped = False

    for ch in raw_text:
        if in_string:
            if escaped:
                repaired.append(ch)
                escaped = False
                continue

            if ch == "\\":
                repaired.append(ch)
                escaped = True
                continue

            if ch == "\"":
                repaired.append(ch)
                in_string = False
                continue

            code = ord(ch)
            if code < 0x20:
                if ch == "\n":
                    repaired.append("\\n")
                elif ch == "\r":
                    repaired.append("\\r")
                elif ch == "\t":
                    repaired.append("\\t")
                else:
                    repaired.append(f"\\u{code:04x}")
                continue

            repaired.append(ch)
            continue

        repaired.append(ch)
        if ch == "\"":
            in_string = True

    return "".join(repaired)


def load_json_with_repair(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        raw = f.read()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        repaired = _escape_control_chars_inside_strings(raw)
        return json.loads(repaired)


def extract_duration_minutes(duration_text):
    numbers = re.findall(r"\d+", duration_text)

    if numbers:
        return int(numbers[0])

    return None


def normalize_boolean(value):
    return str(value).lower() == "yes"


def build_search_text(item):
    fields = [
        item.get("name", ""),
        item.get("description", ""),
        " ".join(item.get("job_levels", [])),
        " ".join(item.get("keys", [])),
    ]

    return " ".join(fields)


def clean_item(item):
    return {
        "id": item.get("entity_id"),
        "name": item.get("name"),
        "url": item.get("link"),
        "description": item.get("description"),
        "job_levels": item.get("job_levels", []),
        "languages": item.get("languages", []),
        "duration_minutes": extract_duration_minutes(
            item.get("duration", "")
        ),
        "remote": normalize_boolean(item.get("remote")),
        "adaptive": normalize_boolean(item.get("adaptive")),
        "categories": item.get("keys", []),
        "search_text": build_search_text(item),
    }


def main():
    data = load_json_with_repair(INPUT_FILE)

    cleaned = []

    seen_urls = set()

    for item in data:
        url = item.get("link")

        if not url or url in seen_urls:
            continue

        seen_urls.add(url)

        cleaned.append(clean_item(item))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(cleaned)} cleaned assessments")


if __name__ == "__main__":
    main()
