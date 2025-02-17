import re
import streamlit as st
from main.constants import c_text


class DataContainer:
    input_ticker__us = ''
    input_ticker__cn = ''
    input_ticker__jp = ''

    us_ticker_ls = []
    cn_ticker_ls = []
    jp_ticker_ls = []
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
        self.cn_ticker_ls = self._split_input(self.input_ticker__cn)
        self.us_ticker_ls = self._split_input(self.input_ticker__us)
        self.jp_ticker_ls = self._split_input(self.input_ticker__jp)

        self.master_ticker_ls = self.cn_ticker_ls + self.us_ticker_ls + self.jp_ticker_ls
        self.master_ticker_ls = list(dict.fromkeys(self.master_ticker_ls))

    def __repr__(self):
        return f'''
        CN_TICKER={self.input_ticker__cn},
        US_TICKER={self.input_ticker__us},
        JP_TICKER={self.input_ticker__jp},

        CN_TICKER_LS={self.cn_ticker_ls},
        US_TICKER_LS={self.us_ticker_ls},
        JP_TICKER_LS={self.jp_ticker_ls},
        '''