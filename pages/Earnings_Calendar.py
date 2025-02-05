import streamlit as st
from main.common.common_layout import CommonLayout


def run():
    CommonLayout.load()
    st.title("Page 1")
    st.write("Welcome to Page 1! This is some example content.")

run()