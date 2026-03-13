import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# CONFIG
CSV_PATH = "../../data/classify.csv"
EVENT_COLUMN = "event"
TOP_K = 60

# Load CSV
df = pd.read_csv(CSV_PATH)

events = df[EVENT_COLUMN].astype(str).tolist()

# Load embedding model
model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

print("Embedding events...")
embeddings = model.encode(events, batch_size=32, show_progress_bar=True)

# Compute cosine similarity matrix
sim_matrix = cosine_similarity(embeddings)

# Collect pair similarities
pairs = []

n = len(events)
for i in range(n):
    for j in range(i + 1, n):  # avoid duplicates and self comparisons
        pairs.append((sim_matrix[i][j], i, j))

# Sort by similarity descending
pairs.sort(reverse=True, key=lambda x: x[0])

# Top K pairs
top_pairs = pairs[:TOP_K]

print("\nTop Similar Event Pairs:\n")

for score, i, j in top_pairs:
    print(f"Similarity: {score:.4f}")
    print(f"Event 1: {events[i]}")
    print(f"Event 2: {events[j]}")
    print("-" * 60)