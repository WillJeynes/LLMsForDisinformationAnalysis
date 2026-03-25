from collections import Counter
from pathlib import Path
import json
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

THRESH = 0.4

def page_title() -> str:
    return "Statistics 2"

def render():
    st.header("Statistics 2")

    path = Path("../../data/refinement")

    if not path.exists() or not path.is_dir():
        st.error("Invalid folder path.")
        return

    jsonl_files = sorted(path.glob("*.jsonl"))
    if not jsonl_files:
        st.info("No .jsonl files found in this folder.")
        return

    for file_path in jsonl_files:
        thresh = THRESH
        st.subheader(f"File: {file_path.name}")

        confidence_counter = Counter()
        
        # ---- Read file line by line ----
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if (entry.get("status") != "success"):
                    confidence_counter["Crash"] += 1
                for event in entry.get("events", []):
                    score = event.get("score", None)
                    
                    if score is not None:
                        if score == -1:
                            confidence_counter["BAD-1"] += 1
                        elif score > thresh:
                            confidence_counter["PERFECT"] += 1
                        else:
                            confidence_counter["BAD"] += 1
                        
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
            correct = confidence_counter["PERFECT"]

            corr_percent = (correct / total) * 100
            
            st.markdown(f"**Correct: {corr_percent:.2f}% ({correct}/{total})**")
            st.markdown(f"**Crash: {confidence_counter["Crash"]}**")
            st.pyplot(fig, width=500)
        else:
            st.info("No score data available in this file.")