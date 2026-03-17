import random
import streamlit as st
from config import INPUT_FILE
from data_utils import save_data_clean


def page_title() -> str:
    return "Label"

def render():
    if st.session_state.current_claim is None:

        unannotated = []

        for entry in st.session_state.data:
            claims = []


            for c in entry.get("events", []):
                if not c.get("ranked") and c.get("score") != -1:
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

                st.markdown(f"**Event:** {c.get('Event')}")
                st.markdown(f"**Reasoning:** {c.get('ReasoningWhyRelevant')}")

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
                        if st.checkbox(name, key=f"{tag}{idx}{c.get('Event')}"):
                            temp += tag + " "

                c["extra_info"] = temp.strip()
                c["ranked"] = True

        if st.button("Save Annotation"):
            save_data_clean(INPUT_FILE, st.session_state.data)
            st.session_state.current_claim = None
            print("Annotation saved")
            st.rerun()