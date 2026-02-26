import streamlit as st


def page_title() -> str:
    return "View Rules"

def render():
    with open("rules.txt", "r", encoding="utf-8") as f:
        st.write(f.read())