import copy
import streamlit as st
import json
import random
from pathlib import Path
from collections import Counter, defaultdict
import pandas as pd
from streamlit_sortables import sort_items

INPUT_FILE = "../../data/results.jsonl"
OUTPUT_FILE = "../../data/ranked.jsonl"

# --------------------------
# Helper functions
# --------------------------
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
    [
        "All Claims",
        "Single Claim Random",
        "Rank Perfect Events",
        "View Rules",
        "Statistics"
    ]
)

# --------------------------
# View/AllClaims
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
# View/Annotate
# --------------------------
elif view == "Single Claim Random":

    if st.session_state.current_claim is None:

        unannotated = []

        for entry in st.session_state.data:
            claims = []

            for o in entry.get("output", []):
                for c in o.get("content_parsed", []):
                    if not c.get("ranked"):
                        claims.append(c)

            if claims:
                unannotated.append({"entry": entry, "claims": claims})

        if unannotated:
            st.session_state.current_claim = random.choice(unannotated)
            st.session_state.drag_order = None

    bundle = st.session_state.current_claim

    if bundle is None:
        st.info("All items annotated.")
    else:
        entry = bundle["entry"]
        claims = bundle["claims"]

        st.subheader(entry.get("text"))
        st.write(entry.get("normalized", ""))

        st.subheader("Annotate Events")

        for idx, c in enumerate(claims):

            with st.container(border=True):

                st.markdown(f"**Event:** {c.get('event')}")
                st.markdown(f"**Reasoning:** {c.get('reasoningWhyRelevant')}")

                cols = st.columns(7)
                temp = ""

                labels = [
                    ("Rewording", "REWORDING"),
                    ("Not Specific", "NSPECIFIC"),
                    ("Time Incorrect", "TINCORRECT"),
                    ("Story?", "STORY"),
                    ("Duplicate?", "DUPLICATE"),
                    ("Bias Shown", "BIAS"),
                    ("Perfect", "PERFECT"),
                ]

                for i, (name, tag) in enumerate(labels):
                    with cols[i]:
                        if st.checkbox(name, key=f"{tag}{idx}{c.get('event')}"):
                            temp += tag + " "

                c["extra_info"] = temp.strip()
                c["ranked"] = True

        if st.button("Save Annotation"):
            save_data(INPUT_FILE, st.session_state.data)
            st.session_state.current_claim = None
            print("Annotation saved")
            st.rerun()

# --------------------------
# View/Rank
# --------------------------

elif view == "Rank Perfect Events":

    st.header("Rank PERFECT Events")
    candidates = []

    for entry in st.session_state.data:
        perfect = []

        for o in entry.get("output", []):
            for c in o.get("content_parsed", []):
                if "PERFECT" in c.get("extra_info", "") and not c.get("rank_position"):
                    perfect.append(c)

        if perfect:
            candidates.append({"entry": entry, "claims": perfect})

    if not candidates:
        st.info("No PERFECT events available.")
        st.stop()

    if "current_bundle" not in st.session_state:
        st.session_state.current_bundle = random.choice(candidates)

    bundle = st.session_state.current_bundle
    entry = bundle["entry"]
    claims = bundle["claims"]

    st.subheader(entry.get("text"))

    # init
    if "perfect_order" not in st.session_state:
        st.session_state.perfect_order = list(range(len(claims)))

    order = st.session_state.perfect_order

    # labels shown in sortable UI
    labels = [
        f"{i+1}. {claims[idx].get('event')}"
        for i, idx in enumerate(order)
    ]

    st.markdown("### Drag to reorder:")

    # -------------------------
    # Drag & drop UI
    # -------------------------
    new_labels = sort_items(labels)

    # Convert reordered labels back → indices
    if new_labels != labels:
        new_order = []
        for lbl in new_labels:
            original_pos = labels.index(lbl)
            new_order.append(order[original_pos])

        st.session_state.perfect_order = new_order
        order = new_order

    st.markdown("---")
    for rank, idx in enumerate(order):
        c = claims[idx]
        st.markdown(f"**Rank {rank+1}: {c.get('event')}**")
        st.markdown(c.get("reasoningWhyRelevant"))
        st.markdown("---")

    if st.button("Submit PERFECT Ranking"):

        n = len(order)

        for rank_position, idx in enumerate(order):
            claim_obj = claims[idx]

            # explicit stored rank
            claim_obj["rank_position"] = rank_position + 1

            claim_obj["human_score"] = 1

        # Auto-scoring
        for entry in st.session_state.data:
            for o in entry.get("output", []):
                for c in o.get("content_parsed", []):

                    if c.get("human_score") is not None:
                        continue

                    extra = c.get("extra_info", "")

                    if "DUPLICATE" in extra:
                        c["human_score"] = 0
                    elif extra:
                        c["human_score"] = round(
                            c.get("score", 0) * 0.5, 3
                        )

        save_data(INPUT_FILE, st.session_state.data)
        save_data_clean(
            OUTPUT_FILE,
            copy.deepcopy(st.session_state.data)
        )

        # reset state for next example
        del st.session_state.current_bundle
        del st.session_state.perfect_order

        print("Ranking saved!")
        st.rerun()

# --------------------------
# View/Rules
# --------------------------
elif view == "View Rules":
    with open("rules.txt", "r", encoding="utf-8") as f:
        st.write(f.read())

# --------------------------
# View/Statistics
# --------------------------
elif view == "Statistics":
    st.header("Statistics")

    word_counter = Counter()
    doc_scores = defaultdict(list)
    diff_scores = defaultdict(list)

    # ---- collect stats ----
    for entry in st.session_state.data:
        doc_url = entry.get("documentUrl")

        for o in entry.get("output", []):
            for c in o.get("content_parsed", []):

                # ---- extra_info word counts ----
                extra = c.get("extra_info", "")
                if extra:
                    words = extra.strip().split()
                    word_counter.update(words)

    # --------------------------
    # Extra Info Word Counts
    # --------------------------
    st.subheader("Extra Info Label Counts")

    if word_counter:
        df_words = (
            pd.DataFrame(word_counter.items(), columns=["Label", "Count"])
            .sort_values("Count", ascending=False)
        )

        st.dataframe(df_words)
        st.bar_chart(df_words.set_index("Label"))
    else:
        st.info("No extra_info data available yet.")