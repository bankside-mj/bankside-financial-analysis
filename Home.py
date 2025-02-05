import streamlit as st
from main.common.common_layout import CommonLayout


CommonLayout.load()

# Home page
st.write('# Welcome! 👋')

st.markdown(
    """
    Please select the page that you are interested!
    """
)