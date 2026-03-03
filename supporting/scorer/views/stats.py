from collections import Counter
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

THRESH = 0.7

def page_title() -> str:
    return "Statistics"

def render():
    st.header("Statistics")

    word_counter = Counter()
    confidence_counter = Counter()

    # ---- collect stats ----
    for entry in st.session_state.data:
        for o in entry.get("output", []):
            for c in o.get("content_parsed", []):

                # ---- extra_info word counts ----
                extra = c.get("extra_info", "")
                score = c.get("score", None)

                if extra:
                    words = extra.strip().split()
                    word_counter.update(words)

                # ---- confidence classification ----
                if score is not None:
                    extra_lower = extra.strip().lower()

                    if score > THRESH and extra_lower == "perfect":
                        confidence_counter["Correct"] += 1

                    elif score > THRESH and extra_lower != "perfect":
                        confidence_counter["Over-confident"] += 1

                    elif score < THRESH and extra_lower == "perfect":
                        confidence_counter["Under-confident"] += 1

                    else:
                        confidence_counter["Other"] += 1

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

    # --------------------------
    # Confidence vs Label Stats
    # --------------------------
    st.subheader("Confidence vs Label Distribution")

    if confidence_counter:
        df_conf = pd.DataFrame(
            confidence_counter.items(),
            columns=["Category", "Count"]
        )

        fig, ax = plt.subplots()
        ax.pie(
            df_conf["Count"],
            labels=df_conf["Category"],
            autopct="%1.1f%%",
            startangle=90
        )
        ax.axis("equal")

        st.pyplot(fig, width=500)

    else:
        st.info("No score data available yet.")