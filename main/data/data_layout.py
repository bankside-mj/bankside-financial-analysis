from main.constants import c_text


class DataLayout:
    input_ticker__value = ''
    input_ticker__growth = ''
    input_ticker__theme = ''
    input_ticker__watchlist = ''

    value_ticker_ls = []
    growth_ticker_ls = []
    theme_ticker_ls = []
    watchlist_ticker_ls = []

    def __init__(self):
        pass

    def __repr__(self):
        return f'''
        VALUE_TICKER={self.input_ticker__value},
        GROWTH_TICKER={self.growth_ticker_ls},
        THEME_TICKER={self.theme_ticker_ls},
        WATCHLIST_TICKER={self.watchlist_ticker_ls},
        '''