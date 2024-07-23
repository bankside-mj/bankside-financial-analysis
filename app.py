import streamlit as st

# Title and Header
st.title("Bankside Capital Ptd. Ltd. - Financial Analysis")
st.header("Welcome to my Streamlit app!")

# Sidebar
st.sidebar.header("Company List")
user_input = st.sidebar.text_input("Enter some text")

# Main Content
st.write("You entered:", user_input)

# Adding a chart
import numpy as np
import pandas as pd

data = pd.DataFrame(
    np.random.randn(100, 2),
    columns=['x', 'y']
)
st.line_chart(data)

# Adding an interactive widget
if st.button('Click me'):
    st.write("Button clicked!")