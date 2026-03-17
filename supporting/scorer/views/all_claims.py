import streamlit as st

def page_title() -> str:
    return "All Claims"

def render():
    st.header("All Claims")
    for entry in st.session_state.data:
        st.subheader(entry.get("text"))
        st.markdown(f"\"{entry.get('documentUrl')}\"")
        for c in entry.get("events", []):
            st.markdown(f"**Event:** {c.get('Event')}")
            st.markdown(f"**Reasoning:** {c.get('ReasoningWhyRelevant')}")
            st.markdown(f"**Score:** {c.get('score')}")
            st.markdown(f"**Extra Info:** {c.get('extra_info', '')}")
            st.markdown("---")