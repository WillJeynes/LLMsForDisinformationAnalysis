import streamlit as st
import json
import random
from pathlib import Path

# Path to your JSONL file
INPUT_FILE = "../../data/results.jsonl"
OUTPUT_FILE = "../../data/ranked.jsonl"

# --------------------------
# Helper functions
# --------------------------

def load_data(file_path):
    """Load JSONL file into a list of dicts with parsed content."""
    data = []

    if Path(file_path).exists():
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                entry = json.loads(line)

                outputs = entry.get("output", [])

                # ---- normalize format ----
                # old format: list
                # new format: single dict
                if isinstance(outputs, dict):
                    outputs = [outputs]

                # ---- parse content ----
                for o in outputs:
                    content = o.get("content")

                    if content:
                        try:
                            o["content_parsed"] = json.loads(content)
                        except json.JSONDecodeError:
                            o["content_parsed"] = []
                            print("parse error")

                # optionally store normalized outputs back
                entry["output"] = outputs

                data.append(entry)

    return data

def save_data_clean(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        for entry in data:
            for o in entry.get("output", []):
                if "content_parsed" in o:
                    entry["events"] = o["content_parsed"] 
            del entry["output"]
            del entry["status"]
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


# --------------------------
# Session State Init
# --------------------------
if "data" not in st.session_state:
    st.session_state.data = load_data(INPUT_FILE)

if "current_claim" not in st.session_state:
    st.session_state.current_claim = None

if "drag_order" not in st.session_state:
    st.session_state.drag_order = None

st.set_page_config(
    page_title="Claim Visualizer",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("Claim Visualizer")

# --------------------------
# Sidebar
# --------------------------
view = st.sidebar.selectbox(
    "Choose View",
    ["All Claims", "Single Claim Random", "View Rules"]
)

# --------------------------
# ALL CLAIMS VIEW
# --------------------------
if view == "All Claims":
    st.header("All Claims")
    for entry in st.session_state.data:
        st.subheader(entry.get("text"))

        for o in entry.get("output", []):
            for c in o.get("content_parsed", []):
                st.markdown(f"**Event:** {c.get('event')}")
                st.markdown(f"**Reasoning:** {c.get('reasoningWhyRelevant')}")
                st.markdown(f"**Score:** {c.get('score')}")
                st.markdown(f"**Human Score:** {c.get('human_score')}")
                st.markdown(f"**Extra Info:** {c.get('extra_info', '')}")
                st.markdown("---")

# --------------------------
# SINGLE CLAIM RANDOM VIEW
# --------------------------

elif view == "Single Claim Random":
    # Select new entry if needed
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
            st.session_state.drag_order = None
        else:
            st.session_state.current_claim = None

    bundle = st.session_state.current_claim

    if bundle is None:
        st.info("No entries remaining without human scores.")
    else:
        entry = bundle["entry"]
        claims = bundle["claims"]

        st.subheader(entry.get("text"))

        # --------------------------
        # Stable Drag IDs (FIX)
        # --------------------------

        claim_ids = [str(i) for i in range(len(claims))]

        # Initialize order only once
        if (
            st.session_state.drag_order is None
            or len(st.session_state.drag_order) != len(claim_ids)
        ):
            st.session_state.drag_order = claim_ids.copy()

        ordered_indices = [
            int(i) for i in st.session_state.drag_order
        ]

        # --------------------------
        # Annotation Section
        # --------------------------

        st.subheader("Annotate Events")

        for pos, idx in enumerate(ordered_indices):
            c = claims[idx]

            with st.container(border=True):

                st.markdown(f"**Event:** {c.get('event')}")
                st.markdown(
                    f"**Reasoning:** {c.get('reasoningWhyRelevant')}"
                )

                cols = st.columns(5)

                temp = ""

                with cols[0]:
                    a = st.checkbox("Rewording", key = "R" + str(idx) + c.get('event') )
                    temp += "REWORDING " if a else ""

                with cols[1]:
                    a = st.checkbox("Not Specific", key = "S" + str(idx) + c.get('event') )
                    temp += "NSPECIFIC " if a else ""

                with cols[2]:
                    a = st.checkbox("Time Incorrect", key = "T" + str(idx) + c.get('event') )
                    temp += "TINCORRECT " if a else ""

                with cols[3]:
                    a = st.checkbox("Story?", key = "Y" + str(idx) + c.get('event') )
                    temp += "STORY " if a else ""
                
                with cols[4]:
                    a = st.checkbox("Perfect", key = "P" + str(idx) + c.get('event') )
                    temp += "PERFECT " if a else ""

                c["extra_info"] = temp

                # ---- MOVE BUTTONS ----
                move_cols = st.columns(2)

                with move_cols[0]:
                    if st.button(
                        "Up",
                        key="UP" + str(idx) + c.get("event")
                    ):
                        if pos > 0:
                            order = st.session_state.drag_order
                            order[pos], order[pos - 1] = order[pos - 1], order[pos]
                            st.session_state.drag_order = order
                            st.rerun()

                with move_cols[1]:
                    if st.button(
                        "Down",
                        key="DOWN" + str(idx) + c.get("event")
                    ):
                        if pos < len(st.session_state.drag_order) - 1:
                            order = st.session_state.drag_order
                            order[pos], order[pos + 1] = order[pos + 1], order[pos]
                            st.session_state.drag_order = order
                            st.rerun()


        # --------------------------
        # Submit Ranking
        # --------------------------

        if st.button("Submit Ranking"):

            n = len(ordered_indices)

            for rank_position, idx in enumerate(ordered_indices):

                claim_obj = claims[idx]
                score = 0
                if n == 1:
                    score = 1.0
                else:
                    score = 1 - (rank_position / (n - 1))

                if (claim_obj["extra_info"] != ""):
                    if (claim_obj["extra_info"].find("PERFECT") != -1):
                        score = 1
                    else:
                        score *= 0.5
                    

                claim_obj["human_score"] = round(score, 3)

            save_data(INPUT_FILE, st.session_state.data)
            save_data_clean(OUTPUT_FILE, st.session_state.data)


            print("Ranking converted to scores and saved!")

            st.session_state.current_claim = None
            st.session_state.drag_order = None

            st.rerun()

elif view == "View Rules":
    with open("rules.txt", "r", encoding="utf-8") as f:
        st.write(f.readlines())
