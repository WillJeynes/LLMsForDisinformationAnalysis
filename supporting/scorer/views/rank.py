import streamlit as st
import copy
import random
from streamlit_sortables import sort_items
from config import INPUT_FILE, OUTPUT_FILE
from data_utils import save_data, save_data_clean


def page_title() -> str:
    return "Rank"

def render():
    st.header("Rank Events")
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
        st.info("No events available.")
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