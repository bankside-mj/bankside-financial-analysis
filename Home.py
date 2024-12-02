import streamlit as st
# from main.page import pg_earnings_calendar, pg_constituents, pg_financial
import importlib

# Function to dynamically load and execute a page
def load_page(module_name):
    try:
        module = importlib.import_module(module_name)
        if hasattr(module, "run"):
            module.run()
        else:
            st.error(f"The module {module_name} does not have a `run()` function.")
    except ModuleNotFoundError:
        st.error(f"Module {module_name} not found.")

# Page config
st.set_page_config(page_title='Bankside Capital', page_icon='💰', layout='wide')

# Side bar
st.sidebar.success('📍Select a page above.')

# Home page
st.write('# Welcome! 👋')

st.markdown(
    """
    Please select the page that you are interested!
    """
)