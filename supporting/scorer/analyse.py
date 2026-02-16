import json
from statistics import mean

# ------------------------------------------------------------
# Load JSONL file
# ------------------------------------------------------------
DATA_FILE = "../Wrapper/results.jsonl"

data = []
with open(DATA_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            data.append(json.loads(line))

# ------------------------------------------------------------
# Extract events
# ------------------------------------------------------------
all_events = []
claims = []

for item in data:
    if item.get("status") != "success":
        continue

    claim_text = item.get("text", "")
    outputs = item.get("output", [])

    for out in outputs:
        if "content_parsed" in out:
            events = out["content_parsed"]

            claims.append({
                "claim": claim_text,
                "events": events
            })

            for ev in events:
                score = ev["score"]
                human = ev["human_score"]

                all_events.append({
                    "claim": claim_text,
                    "event": ev["event"],
                    "reason": ev["reasoningWhyRelevant"],
                    "score": score,
                    "human_score": human,
                    "gap": abs(score - human),
                })

# ------------------------------------------------------------
# Compute metrics
# ------------------------------------------------------------
if not all_events:
    raise ValueError("No events found in file.")

avg_score = mean(e["score"] for e in all_events)
avg_diff = mean(e["gap"] for e in all_events)

largest_gap_event = max(all_events, key=lambda x: x["gap"])
worst_event = largest_gap_event

worst_claim_data = next(
    c for c in claims if c["claim"] == worst_event["claim"]
)

# ------------------------------------------------------------
# Output results
# ------------------------------------------------------------
print(f"Average score: {avg_score:.4f}")
print(f"Average |human_score - score|: {avg_diff:.4f}")

print("\nLargest gap event:")
print(f"Event: {largest_gap_event['event']}")
print(f"Score: {largest_gap_event['score']}")
print(f"Human score: {largest_gap_event['human_score']}")
print(f"Gap: {largest_gap_event['gap']:.4f}")

print("\nWorst performing event and its claims:")
print(f"Claim: {worst_event['claim']}")
print(f"Worst Event: {worst_event['event']}")
