import streamlit as st
import json
import random
from pathlib import Path

# Path to your JSONL file
DATA_FILE = "../../data/results.jsonl"

# --------------------------
# Helper functions
# --------------------------

def load_data(file_path):
    """Load JSONL file into a list of dicts with parsed content."""
    data = []
    if Path(file_path).exists():
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    for o in entry.get("output", []):
                        if "content" in o:
                            try:
                                o["content_parsed"] = json.loads(o["content"])
                            except json.JSONDecodeError:
                                o["content_parsed"] = []
                                print("parse error")
                    data.append(entry)
    return data

def save_data(file_path, data):
    """Save the updated data back to JSONL file."""
    with open(file_path, "w", encoding="utf-8") as f:
        for entry in data:
            for o in entry.get("output", []):
                if "content_parsed" in o:
                    o["content"] = json.dumps(o["content_parsed"], ensure_ascii=False)
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# --------------------------
# Initialize session state
# --------------------------
if "data" not in st.session_state:
    st.session_state.data = load_data(DATA_FILE)

if "current_claim" not in st.session_state:
    st.session_state.current_claim = None

st.title("Claim Visualizer")

# --------------------------
# Sidebar
# --------------------------
view = st.sidebar.selectbox("Choose View", ["All Claims", "Single Claim Random"])

# --------------------------
# All Claims View
# --------------------------
if view == "All Claims":
    st.header("All Claims")
    for entry in st.session_state.data:
        st.subheader(f"{entry.get('text')}")
        for o in entry.get("output", []):
            for c in o.get("content_parsed", []):
                st.markdown(f"**Event:** {c.get('event')}")
                st.markdown(f"**Reasoning:** {c.get('reasoningWhyRelevant')}")
                st.markdown(f"**Score:** {c.get('score')}")
                st.markdown(f"**Human Score:** {c.get('human_score')}")
                st.markdown("---")

# --------------------------
# Single Claim Random View (Ranking Based)
# --------------------------
elif view == "Single Claim Random":

    # Select an entry that still has unscored items
    if st.session_state.current_claim is None:
        unscored_entries = []

        for entry in st.session_state.data:
            unscored = []

            for o in entry.get("output", []):
                for c in o.get("content_parsed", []):
                    if c.get("human_score") is None:
                        unscored.append(c)

            if unscored:
                unscored_entries.append({
                    "entry": entry,
                    "claims": unscored
                })

        if unscored_entries:
            st.session_state.current_claim = random.choice(unscored_entries)
        else:
            st.session_state.current_claim = None

    bundle = st.session_state.current_claim

    if bundle is None:
        st.info("No entries remaining without human scores.")
    else:
        entry = bundle["entry"]
        claims = bundle["claims"]

        st.subheader(entry.get("text"))

        st.write("Rank events (1 = best / most relevant)")

        rankings = []

        # Collect rankings
        for i, c in enumerate(claims):
            st.markdown(f"### Event {i+1}")
            st.markdown(f"**Event:** {c.get('event')}")
            st.markdown(f"**Reasoning:** {c.get('reasoningWhyRelevant')}")

            rank = st.number_input(
                f"Rank for event {i+1}",
                min_value=1,
                max_value=len(claims),
                key=f"rank_{i}"
            )

            rankings.append((c, rank))

        if st.button("Submit Ranking"):

            # Sort by rank (ascending = best)
            rankings.sort(key=lambda x: x[1])

            n = len(rankings)

            # Convert ranking -> normalized score
            for idx, (claim_obj, _) in enumerate(rankings):
                if n == 1:
                    score = 1.0
                else:
                    score = 1 - (idx / (n - 1))

                claim_obj["human_score"] = round(score, 3)

            save_data(DATA_FILE, st.session_state.data)
            st.success("Ranking converted to scores and saved!")

            st.session_state.current_claim = None
            st.rerun()