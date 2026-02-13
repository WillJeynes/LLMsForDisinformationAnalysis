import requests
import json
import random
from urllib.parse import urlencode

BASE_URL = "https://dbkf.ontotext.com/rest-api/search/documents"

# search parameters 
# Ukraine: http://weverify.eu/resource/Concept/Q212
# COVID: http://weverify.eu/resource/Concept/Q84263196

DEFAULT_PARAMS = {
    "concept": "http://weverify.eu/resource/Concept/Q212",
    "documentTypes": "http://schema.org/Claim",
    "from": "2000-01-01",
    "to": "2023-10-17",
    "lang": "en",
    "limit": 50,  # Max per page
    "page": 1,
    "orderBy": "date"
}

NUM_RANDOM_CLAIMS = 10

OUTPUT_FILE = "../Wrapper/claims.json"

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

def save_random_claims(documents, output_file, num_claims=20):
    if not documents:
        print("No documents to save.")
        return

    sample_size = min(num_claims, len(documents))
    selected = random.sample(documents, sample_size)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(selected, f, indent=4, ensure_ascii=False)

    print(f"Saved {sample_size} random claims to {output_file}")

if __name__ == "__main__":
    docs = fetch_claims()
    save_random_claims(docs, OUTPUT_FILE, NUM_RANDOM_CLAIMS)
