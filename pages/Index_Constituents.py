import streamlit as st
from main.common.common_layout import CommonLayout


def run():
    CommonLayout.load()
    st.title("Page 3")
    st.write("Welcome to Page 3! This is some example content.")

run()