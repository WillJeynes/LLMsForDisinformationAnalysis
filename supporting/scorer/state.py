import streamlit as st
from config import INPUT_FILE
from data_utils import load_data

def init_state():
    if "data" not in st.session_state:
        st.session_state.data = load_data(INPUT_FILE)

    if "current_claim" not in st.session_state:
        st.session_state.current_claim = None

    if "drag_order" not in st.session_state:
        st.session_state.drag_order = None