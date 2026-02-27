import requests
import json
import random
from urllib.parse import urlencode

BASE_URL = "https://dbkf.ontotext.com/rest-api/search/documents"

# search parameters 
# Ukraine: http://weverify.eu/resource/Concept/Q212
# COVID: http://weverify.eu/resource/Concept/Q84263196

# "documentTypes": "http://schema.org/Claim",
DEFAULT_PARAMS = [
    ("concept", "http://weverify.eu/resource/Concept/Q212"),
    ("from", "2000-01-01"),
    ("to", "2026-02-19"),
    ("lang", "en"),
    ("limit", 5000),
    ("page", 1),
    ("orderBy", "date"),

    # duplicate keys allowed
    ("organization", "http://weverify.eu/resource/Organization/3727f7b2aa90ec0716693e5464b28d18"), # StopFake
    ("organization", "http://weverify.eu/resource/Organization/c71953fa6cf24ac4178f751c77862070"), # CheckYourFact
]

NUM_RANDOM_CLAIMS = 20

INPUT_FILE = "../../data/input.jsonl"
OUTPUT_FILE = "../../data/claims.json"

def load_existing_urls(input_file):
    existing_urls = set()

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                url = obj.get("documentUrl")
                if url:
                    existing_urls.add(url)

        print(f"Loaded {len(existing_urls)} existing document URLs.")
    except FileNotFoundError:
        print(f"No existing file found at {input_file}")
    except Exception as e:
        print(f"Error reading JSONL file: {e}")

    return existing_urls


def fetch_claims(params=None):
    if params is None:
        params = DEFAULT_PARAMS

    query_string = urlencode(params)
    url = f"{BASE_URL}?{query_string}"
    print(f"Fetching data from: {url}\n")

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        documents = data.get("documents", [])
        print(f"Fetched {len(documents)} documents.")
        return documents
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

def save_random_claims(documents, output_file, excluded_urls=None, num_claims=20):
    if not documents:
        print("No documents to save.")
        return

    excluded_urls = excluded_urls or set()

    # remove already-used documents
    filtered_docs = [
        d for d in documents
        if d.get("documentUrl") not in excluded_urls
    ]

    print(f"{len(filtered_docs)} documents remain after filtering.")

    if not filtered_docs:
        print("No new documents available after filtering.")
        return

    sample_size = min(num_claims, len(documents))
    selected = random.sample(documents, sample_size)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(selected, f, indent=4, ensure_ascii=False)

    print(f"Saved {sample_size} random claims to {output_file}")

if __name__ == "__main__":
    existing_urls = load_existing_urls(INPUT_FILE)

    docs = fetch_claims()

    save_random_claims(
        docs,
        OUTPUT_FILE,
        excluded_urls=existing_urls,
        num_claims=NUM_RANDOM_CLAIMS
    )
