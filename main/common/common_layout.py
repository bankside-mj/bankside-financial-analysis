import streamlit as st

class CommonLayout:
    @classmethod
    def load(self):
        # Page config
        st.set_page_config(page_title='Bankside Capital', page_icon='💰', layout='wide')

        # Side bar
        st.sidebar.success('📍Select a page above.')