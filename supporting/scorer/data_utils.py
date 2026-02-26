import json
from pathlib import Path

def load_data(file_path):
    data = []

    if Path(file_path).exists():
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                entry = json.loads(line)
                outputs = entry.get("output", [])

                if isinstance(outputs, dict):
                    outputs = [outputs]

                for o in outputs:
                    content = o.get("content")
                    if content:
                        try:
                            o["content_parsed"] = json.loads(content)
                        except json.JSONDecodeError:
                            o["content_parsed"] = []

                entry["output"] = outputs
                data.append(entry)

    return data


def save_data_clean(file_path, data):
    merged = {}

    for entry in data:
        events = []
        for o in entry.get("output", []):
            if "content_parsed" in o:
                events.extend(o["content_parsed"])

        doc_url = entry.get("documentUrl")
        if not doc_url:
            continue

        if doc_url not in merged:
            new_entry = entry.copy()
            new_entry["events"] = events
            new_entry.pop("output", None)
            new_entry.pop("status", None)
            merged[doc_url] = new_entry
        else:
            merged[doc_url]["events"].extend(events)

    for entry in merged.values():
        entry["events"].sort(
            key=lambda e: e.get("human_score", 0),
            reverse=True
        )

    with open(file_path, "w", encoding="utf-8") as f:
        for entry in merged.values():
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def save_data(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        for entry in data:
            for o in entry.get("output", []):
                if "content_parsed" in o:
                    o["content"] = json.dumps(
                        o["content_parsed"],
                        ensure_ascii=False
                    )
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

