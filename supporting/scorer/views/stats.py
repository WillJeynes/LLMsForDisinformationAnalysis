from collections import Counter
from pathlib import Path
import json
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
    st.header("Confidence vs Label Distribution per JSONL File")

    path = Path("../../data/reranked")

    if not path.exists() or not path.is_dir():
        st.error("Invalid folder path.")
        return

    jsonl_files = sorted(path.glob("*.jsonl"))
    if not jsonl_files:
        st.info("No .jsonl files found in this folder.")
        return

    for file_path in jsonl_files:
        st.subheader(f"File: {file_path.name}")

        confidence_counter = Counter()

        # ---- Read file line by line ----
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                for event in entry.get("events", []):
                    score = event.get("score", None)
                    extra_lower = (event.get("extra_info", "") or "").strip().lower()
                    print(extra_lower)
                    if score is not None:
                        if score > THRESH and extra_lower == "perfect":
                            confidence_counter["Correct-TRUE"] += 1
                        elif score > THRESH and extra_lower != "perfect":
                            confidence_counter["Over-confident"] += 1
                        elif score < THRESH and extra_lower == "perfect":
                            confidence_counter["Under-confident"] += 1
                        else:
                            confidence_counter["Correct-FALSE"] += 1

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
            ax.set_title(file_path.name)

            total = sum(confidence_counter.values())
            correct = confidence_counter["Correct-TRUE"] + confidence_counter["Correct-FALSE"]

            corr_percent = (correct / total) * 100
            st.markdown(f"**Correct: {corr_percent:.2f}% ({correct}/{total})**")
            st.pyplot(fig, width=500)
        else:
            st.info("No score data available in this file.")