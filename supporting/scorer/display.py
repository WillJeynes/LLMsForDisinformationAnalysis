import importlib
import pkgutil
import streamlit as st
from config import PAGE_TITLE
from state import init_state
import views

st.set_page_config(
    page_title=PAGE_TITLE,
    layout="wide",
    initial_sidebar_state="expanded",
)

init_state()
st.title(PAGE_TITLE)

def discover_views():
    routes = {}

    for module_info in pkgutil.iter_modules(views.__path__):
        module_name = module_info.name

        module = importlib.import_module(f"views.{module_name}")

        if hasattr(module, "render") and hasattr(module, "page_title"):
            title = module.page_title()
            routes[title] = module.render

    return routes


ROUTES = discover_views()

# optional: stable ordering
ROUTES = dict(sorted(ROUTES.items()))

view = st.sidebar.selectbox(
    "Choose View",
    list(ROUTES.keys()),
)

ROUTES[view]()