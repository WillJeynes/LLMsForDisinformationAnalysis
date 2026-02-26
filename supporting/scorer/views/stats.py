from collections import Counter, defaultdict
import streamlit as st
import pandas as pd

def page_title() -> str:
    return "Statistics"

def render():
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