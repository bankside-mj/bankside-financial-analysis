import re
import streamlit as st
from main.constants import c_text


class DataContainer:
    input_ticker__value = ''
    input_ticker__growth = ''
    input_ticker__theme = ''
    input_ticker__watchlist = ''

    value_ticker_ls = []
    growth_ticker_ls = []
    theme_ticker_ls = []
    watchlist_ticker_ls = []
    master_ticker_ls = []

    def __init__(self):
        pass

    def _split_input(self, txt):
        txt = re.split('[;, ]+', txt)
        txt = [t.upper().strip() for t in txt]
        txt = list(filter(lambda x: x != '', txt))

        return txt
    
    def is_empty(self) -> bool:
        return len(self.master_ticker_ls) == 0

    def batch_process_ticker(self):
        self.value_ticker_ls = self._split_input(self.input_ticker__value)
        self.growth_ticker_ls = self._split_input(self.input_ticker__growth)
        self.theme_ticker_ls = self._split_input(self.input_ticker__theme)
        self.watchlist_ticker_ls = self._split_input(self.input_ticker__watchlist)

        self.master_ticker_ls = self.value_ticker_ls + self.growth_ticker_ls + self.theme_ticker_ls + self.watchlist_ticker_ls
        self.master_ticker_ls = list(dict.fromkeys(self.master_ticker_ls))    

    def __repr__(self):
        return f'''
        VALUE_TICKER={self.input_ticker__value},
        GROWTH_TICKER={self.input_ticker__growth},
        THEME_TICKER={self.input_ticker__theme},
        WATCHLIST_TICKER={self.input_ticker__watchlist},

        VALUE_TICKER_LS={self.value_ticker_ls},
        GROWTH_TICKER_LS={self.growth_ticker_ls},
        THEME_TICKER_LS={self.theme_ticker_ls},
        WATCHLIST_TICKER_LS={self.watchlist_ticker_ls},
        '''