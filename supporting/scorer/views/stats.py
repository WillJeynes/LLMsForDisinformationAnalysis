from collections import Counter
from pathlib import Path
import json
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

THRESH = 0.6

def page_title() -> str:
    return "Statistics"

def render():
    st.header("Statistics")

    word_counter = Counter()
    confidence_counter = Counter()

    # ---- collect stats ----
    for entry in st.session_state.data:
        for c in entry.get("events", []):
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
        thresh = THRESH
        if ("flan" in file_path.name):
            thresh = 0.94

        st.subheader(f"File: {file_path.name}")

        confidence_counter = Counter()
        wrong_counter = Counter()
        overconfident_docs = []
        underconfident_docs = []
        dup_counter = 0

        # ---- Read file line by line ----
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                doc_id = entry.get("documentUrl", "UNKNOWN")
                for event in entry.get("events", []):
                    score = event.get("score", None)
                    extra_lower = (event.get("extra_info", "") or "").strip().lower()
                    # print(extra_lower)
                    if score is not None:
                        if score == -1 or "duplicate" in extra_lower:
                            dup_counter += 1
                        elif "ranked" not in event:
                            "ignore for now"
                        elif score > thresh and extra_lower == "perfect":
                            confidence_counter["Correct-PERFECT"] += 1
                        elif score > thresh and extra_lower == "":
                            confidence_counter["Correct-FINE"] += 1
                        elif score > thresh and extra_lower != "perfect" and extra_lower != "":
                            confidence_counter["Over-confident"] += 1
                            wrong_counter[extra_lower] += 1
                            overconfident_docs.append(doc_id)
                        elif score < thresh and (extra_lower == "perfect" or extra_lower == ""):
                            confidence_counter["Under-confident"] += 1
                            underconfident_docs.append(doc_id)
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
            correct = confidence_counter["Correct-PERFECT"] + confidence_counter["Correct-FINE"] + confidence_counter["Correct-FALSE"]

            goodkept = confidence_counter["Correct-PERFECT"] + confidence_counter["Correct-FINE"]
            allkept = confidence_counter["Correct-PERFECT"] + confidence_counter["Correct-FINE"] + confidence_counter["Over-confident"]

            if (allkept == 0):
                allkept = -1

            corr_percent = (correct / total) * 100
            kept_percent = (goodkept / allkept) * 100
            st.markdown(f"**Correct: {corr_percent:.2f}% ({correct}/{total})**")
            st.markdown(f"**Kept: {kept_percent:.2f}% ({goodkept}/{allkept})**")
            st.markdown(f"Duplicates: {dup_counter}")
            st.pyplot(fig, width=500)

            st.subheader("Over-Confident Document IDs")

            if overconfident_docs:
                st.container(height=200).write(sorted(set(overconfident_docs)))
            else:
                st.info("None")

            st.subheader("Under-Confident Document IDs")

            if underconfident_docs:
                st.container(height=200).write(sorted(set(underconfident_docs)))
            else:
                st.info("None")

            df_words = (
                pd.DataFrame(wrong_counter.items(), columns=["Label", "Count"])
                .sort_values("Count", ascending=False)
            )

            st.dataframe(df_words)
        else:
            st.info("No score data available in this file.")