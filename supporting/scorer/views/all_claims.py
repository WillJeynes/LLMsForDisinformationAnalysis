import streamlit as st

def page_title() -> str:
    return "All Claims"

def render():
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