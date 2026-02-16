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
# Single Claim Random View
# --------------------------
elif view == "Single Claim Random":
    # Rebuild the list of unscored claims only when needed
    if st.session_state.current_claim is None:
        single_claims = []
        for entry in st.session_state.data:
            url = entry.get("documentUrl")
            text = entry.get("text")
            for o in entry.get("output", []):
                for c in o.get("content_parsed", []):
                    if "human_score" not in c or c.get("human_score") is None:
                        single_claims.append({
                            "documentUrl": url,
                            "text": text,
                            "event": c.get("event"),
                            "reasoningWhyRelevant": c.get("reasoningWhyRelevant"),
                            "raw_obj": c  # reference to original object
                        })
        if single_claims:
            st.session_state.current_claim = random.choice(single_claims)
        else:
            st.session_state.current_claim = None

    claim = st.session_state.current_claim

    if claim is None:
        st.info("No claims available without a human score.")
    else:
        st.subheader(f"{claim['text']}")
        st.markdown(f"**Event:** {claim['event']}")
        st.markdown(f"**Reasoning:** {claim['reasoningWhyRelevant']}")

        # Input for new human score
        new_score = st.number_input(
            "Provide a score (0 to 1)",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.01,
            format="%.2f"
        )

        if st.button("Submit Score"):
            # Update the original object
            claim["raw_obj"]["human_score"] = new_score

            # Save immediately
            save_data(DATA_FILE, st.session_state.data)
            st.success("Score saved!")

            # Clear current claim so a new one will be selected next run
            st.session_state.current_claim = None

            # Rerun app to show a new claim
            st.rerun()
