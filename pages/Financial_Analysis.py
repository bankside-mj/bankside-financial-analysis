from collections import defaultdict
import datetime as dt
from dotenv import load_dotenv
import os
import re
import streamlit as st
from urllib.parse import urlparse, parse_qs, quote, unquote

import pandas as pd
from main.util.fetch import fetch_data
from main.common.common_layout import CommonLayout

from joblib import Parallel, delayed
import base64

import time

from main.util.formatter import Formatter
from main.util.writer import Writer

BASIC_INFO = 'basic_info'
ANN_INCOME = 'ann_income'
QUAR_INCOME = 'quar_income'
ANN_BALANCE = 'ann_balance'
QUAR_BALANCE = 'quar_balance'
ANN_CF = 'ann_cf'
QUAR_CF = 'quar_cf'
RATIO = 'ratio'
RATIO_TTM = 'ratio_ttm'
DIV_CAL = 'div_cal'

class FinancialAnalysis:
    
    def __init__(self):
        self.ticker_ls = []
        self.data_basic_info = defaultdict(list)
        self.data_invest_metrics = defaultdict(list)
        self.data_invest_risks = defaultdict(list)
        self.data_valuation = defaultdict(list)
        self.data_fin = defaultdict(list)
        self.data_raw_financials = defaultdict(dict)

        self.pct_col_ls = [
            'Gross Margin (Last Quarter)', 'Gross Margin (TTM)', 'Gross Margin (FY -1)', 
            'Gross Margin (FY -3)', 'Gross Margin (FY -5)', 'Gross Margin (FY -10)',
            'EPS CAGR (TTM)', 'EPS CAGR (1Y)', 'EPS CAGR (3Y)', 'EPS CAGR (5Y)', 'EPS CAGR (10Y)',
            'Revenue CAGR (1Y)', 'Revenue CAGR (3Y)', 'Revenue CAGR (5Y)', 'Revenue CAGR (10Y)',
            'ROE (TTM)', 'ROE (FY -1)', 'ROE (FY -3)', 'ROE (FY -5)', 'ROE (FY -10)',
            'Dividend Yield', 'CAPEX / Net Income', 'Payout Ratio',
        ]
        self.num_col_ls = [
            'Current Price', 'Beta', 'Net Debt to Equity (Last Quarter)', 
            'Receivable / Revenue (Last FY)', 'Inventory / Revenue (Last FY)',
            'Trailing PE (TTM)', 'PEG Ratio (TTM)', 'PEG Ratio (FY -1)', 'PEG Ratio (FY -3)',
            'EPS (TTM)', 'Last Dividend Value',
        ]
        self.txt_col_ls = [
            'Market Cap', 'Total Revenue (Last Quarter)', 'Gross Profit (Last Quarter)',
            'Capital Expenditure (Last Year)', 'Net Income (Last Quarter)',
            'Net Income (Last Year)', 'Net Income (TTM)',
        ]

    def _get_query_parameter(self, param_name):
        if param_name not in st.query_params.keys():
            return None
        
        query_params = st.query_params[param_name]
        return query_params

    def _is_valid_input(self, txt):
        if txt is None or txt.strip(' ') == '':
            st.error('Please enter at least one ticker.')
            return False

        return True

    def _split_input(self, txt):
        try:
            txt = re.split('[;, ]+', txt)
            txt = [t.upper().strip() for t in txt]
            txt = list(filter(lambda x: x != '', txt))
        except:
            st.error('Please use comma as delimiter.')

        return txt

    def _get_basic_info(self, batch_size=10):
        with st.spinner('Calculating (1/5) - Basic Info'):
            not_found_ticker_ls = []
            for ticker in self.ticker_ls:
                url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={os.getenv('FMP_KEY')}"
                result_ls = fetch_data(url)

                if len(result_ls) == 0:
                    not_found_ticker_ls.append(ticker)
                    continue

                for result in result_ls:

                    cur_ticker = result.get('symbol')
                    reported_ccy = self._get_latest_value(cur_ticker, ANN_INCOME, 'reportedCurrency', idx=0)

                    self.data_basic_info['Company Name'].append(result.get('companyName'))
                    self.data_basic_info['Ticker'].append(cur_ticker)
                    self.data_basic_info['Sector'].append(result.get('sector'))
                    # self.data_basic_info['Industry'].append(result.get('industry'))
                    self.data_basic_info['Currency'].append(result.get('currency'))
                    self.data_basic_info['Current Price'].append(result.get('price'))
                    self.data_basic_info['Market Cap'].append(result.get('mktCap'))
                    self.data_basic_info['Beta'].append(result.get('beta'))
                    # self.data_basic_info['Exchange'].append(result.get('exchange'))
                    # self.data_basic_info['Reported Currency'].append(reported_ccy)


            # batch_ticker_ls = [
            #     self.ticker_ls[i:i+batch_size] for i in range(0, len(self.ticker_ls), batch_size)
            # ]

            
            # for ticker_ls in batch_ticker_ls:
            #     url_ticker_ls = ','.join(ticker_ls)

            #     url = f"https://financialmodelingprep.com/api/v3/profile/{url_ticker_ls}?apikey={os.getenv('FMP_KEY')}"
            #     result_ls = fetch_data(url)

            #     if result_ls is not None:
            #         for result in result_ls:

            #             cur_ticker = result.get('symbol')
            #             reported_ccy = self._get_latest_value(cur_ticker, ANN_INCOME, 'reportedCurrency', idx=0)

            #             self.data_basic_info['Company Name'].append(result.get('companyName'))
            #             self.data_basic_info['Ticker'].append(cur_ticker)
            #             self.data_basic_info['Sector'].append(result.get('sector'))
            #             # self.data_basic_info['Industry'].append(result.get('industry'))
            #             self.data_basic_info['Currency'].append(result.get('currency'))
            #             self.data_basic_info['Current Price'].append(result.get('price'))
            #             self.data_basic_info['Market Cap'].append(result.get('mktCap'))
            #             self.data_basic_info['Beta'].append(result.get('beta'))
            #             # self.data_basic_info['Exchange'].append(result.get('exchange'))
            #             # self.data_basic_info['Reported Currency'].append(reported_ccy)

            #             ticker_ls.remove(cur_ticker)

                
            #     # Add non found ticker to 
            #     not_found_ticker_ls.extend(ticker_ls)

            # Remove non found ticker
            if len(not_found_ticker_ls) > 0:
                st.warning(f'The following ticker are not found: {not_found_ticker_ls}')
                self.ticker_ls = list(filter(lambda x: x not in not_found_ticker_ls, self.ticker_ls))

    def _fetch_multi_financials(self, ticker, limit=10):
        result = defaultdict(dict)
        
        api_key = os.getenv('FMP_KEY')
        endpoints = [
            (ANN_INCOME, f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?period=annual&limit={limit}&apikey={api_key}"),
            (QUAR_INCOME, f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?period=quarterly&limit={limit}&apikey={api_key}"),
            (ANN_BALANCE, f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?period=annual&limit={limit}&apikey={api_key}"),
            (QUAR_BALANCE, f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?period=quarterly&limit={limit}&apikey={api_key}"),
            (ANN_CF, f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?period=annual&limit={limit}&apikey={api_key}"),
            (QUAR_CF, f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?period=quarterly&limit={limit}&apikey={api_key}"),
            (RATIO, f"https://financialmodelingprep.com/api/v3/ratios/{ticker}?period=annual&apikey={api_key}"),
            (RATIO_TTM, f"https://financialmodelingprep.com/api/v3/ratios-ttm/{ticker}?apikey={api_key}"),
            (DIV_CAL, f"https://financialmodelingprep.com/api/v3/historical-price-full/stock_dividend/{ticker}?apikey={api_key}"),
        ]

        for key, url in endpoints:
            res = fetch_data(url)
            result[ticker][key] = res

        return result

    def _get_raw_financials_statement(self):

        with st.spinner('Fetching financial statements ...'):
            results = Parallel(n_jobs=-1)(
                delayed(self._fetch_multi_financials)(ticker) for ticker in list(dict.fromkeys(self.ticker_ls))
            )
            
            for d in results:
                self.data_raw_financials.update(d)

    def _get_latest_value(self, ticker, fin_key, metrics, idx=0, default_value=0.0):
        # Ticker does not exists
        if self.data_raw_financials.get(ticker) is None:
            return default_value

        # Financials does not exists
        if self.data_raw_financials[ticker].get(fin_key) is None:
            return default_value
        
        # Financials record not long enough
        if len(self.data_raw_financials[ticker][fin_key]) - 1 < idx:
            return default_value

        if fin_key == DIV_CAL:
            if len(self.data_raw_financials[ticker][fin_key]['historical']) == 0:
                return None

            val = self.data_raw_financials[ticker][fin_key]['historical'][idx].get(metrics, default_value)
        
        else:
            val = self.data_raw_financials[ticker][fin_key][idx].get(metrics, default_value)

        return val

    def _calc_cagr(self, latest_val, ori_val, period):
        if latest_val is None or ori_val is None:
            return None

        if latest_val == 0 or ori_val == 0:
            return None
        
        result = (latest_val / ori_val) ** (1 / period) - 1.0

        return float(result.real) if isinstance(result, complex) else float(result)

    def _safe_div(self, n1, n2):
        if n1 is None or n2 is None:
            return None
        
        if n2 == 0:
            return None
        
        return n1 / n2

    def _calc_gross_margin_sec(self, ticker):
        '''
        gm = gross margin
        gp = gross profit
        rev = revenue
        '''
        # Gross margin previous quarter
        gm_prev_1q = self._get_latest_value(ticker, QUAR_INCOME, 'grossProfitRatio', idx=0)

        # Gross margin previous year
        gm_prev_1y = self._get_latest_value(ticker, ANN_INCOME, 'grossProfitRatio', idx=0, default_value=None)
        gm_prev_3y = self._get_latest_value(ticker, ANN_INCOME, 'grossProfitRatio', idx=2, default_value=None)
        gm_prev_5y = self._get_latest_value(ticker, ANN_INCOME, 'grossProfitRatio', idx=4, default_value=None)
        gm_prev_10y = self._get_latest_value(ticker, ANN_INCOME, 'grossProfitRatio', idx=9, default_value=None)

        # Gross margin TTM
        gp_prev_1q = self._get_latest_value(ticker, QUAR_INCOME, 'grossProfit', idx=0)
        gp_prev_2q = self._get_latest_value(ticker, QUAR_INCOME, 'grossProfit', idx=1)
        gp_prev_3q = self._get_latest_value(ticker, QUAR_INCOME, 'grossProfit', idx=2)
        gp_prev_4q = self._get_latest_value(ticker, QUAR_INCOME, 'grossProfit', idx=3)

        rev_prev_1q = self._get_latest_value(ticker, QUAR_INCOME, 'revenue', idx=0)
        rev_prev_2q = self._get_latest_value(ticker, QUAR_INCOME, 'revenue', idx=1)
        rev_prev_3q = self._get_latest_value(ticker, QUAR_INCOME, 'revenue', idx=2)
        rev_prev_4q = self._get_latest_value(ticker, QUAR_INCOME, 'revenue', idx=3)

        gm_ttm = self._safe_div(gp_prev_1q + gp_prev_2q + gp_prev_3q + gp_prev_4q, rev_prev_1q + rev_prev_2q + rev_prev_3q + rev_prev_4q)


        metrics = {
            'Gross Margin (Last Quarter)': gm_prev_1q,
            'Gross Margin (TTM)': gm_ttm,
            'Gross Margin (FY -1)': gm_prev_1y,
            'Gross Margin (FY -3)': gm_prev_3y,
            'Gross Margin (FY -5)': gm_prev_5y,
            'Gross Margin (FY -10)': gm_prev_10y,
        }

        return metrics
    
    def _calc_eps_sec(self, ticker):
        '''
        eps = earnings per share
        '''
        eps_prev_1y = self._get_latest_value(ticker, ANN_INCOME, 'eps', idx=0)
        eps_prev_2y = self._get_latest_value(ticker, ANN_INCOME, 'eps', idx=1)
        eps_prev_3y = self._get_latest_value(ticker, ANN_INCOME, 'eps', idx=2)
        eps_prev_5y = self._get_latest_value(ticker, ANN_INCOME, 'eps', idx=4)
        eps_prev_10y = self._get_latest_value(ticker, ANN_INCOME, 'eps', idx=9)

        eps_cagr_1y = self._calc_cagr(eps_prev_1y, eps_prev_2y, 1)
        eps_cagr_3y = self._calc_cagr(eps_prev_1y, eps_prev_3y, 3)
        eps_cagr_5y = self._calc_cagr(eps_prev_1y, eps_prev_5y, 5)
        eps_cagr_10y = self._calc_cagr(eps_prev_1y, eps_prev_10y, 10)
        
        # EPS TTM
        eps_prev_1q = self._get_latest_value(ticker, QUAR_INCOME, 'eps', idx=0)
        eps_prev_2q = self._get_latest_value(ticker, QUAR_INCOME, 'eps', idx=1)
        eps_prev_3q = self._get_latest_value(ticker, QUAR_INCOME, 'eps', idx=2)
        eps_prev_4q = self._get_latest_value(ticker, QUAR_INCOME, 'eps', idx=3)
        eps_prev_5q = self._get_latest_value(ticker, QUAR_INCOME, 'eps', idx=4)
        eps_prev_6q = self._get_latest_value(ticker, QUAR_INCOME, 'eps', idx=5)
        eps_prev_7q = self._get_latest_value(ticker, QUAR_INCOME, 'eps', idx=6)
        eps_prev_8q = self._get_latest_value(ticker, QUAR_INCOME, 'eps', idx=7)
        eps_ttm = self._safe_div(eps_prev_1q + eps_prev_2q + eps_prev_3q + eps_prev_4q,
                                 eps_prev_5q + eps_prev_6q + eps_prev_7q + eps_prev_8q)

        metrics = {
            'EPS CAGR (TTM)': eps_ttm,
            'EPS CAGR (1Y)': eps_cagr_1y,
            'EPS CAGR (3Y)': eps_cagr_3y,
            'EPS CAGR (5Y)': eps_cagr_5y,
            'EPS CAGR (10Y)': eps_cagr_10y,
        }

        return metrics
    
    def _calc_revenue_sec(self, ticker):
        '''
        rev = revenue
        '''
        rev_prev_1y = self._get_latest_value(ticker, ANN_INCOME, 'revenue', idx=0)
        rev_prev_2y = self._get_latest_value(ticker, ANN_INCOME, 'revenue', idx=1)
        rev_prev_3y = self._get_latest_value(ticker, ANN_INCOME, 'revenue', idx=2)
        rev_prev_5y = self._get_latest_value(ticker, ANN_INCOME, 'revenue', idx=4)
        rev_prev_10y = self._get_latest_value(ticker, ANN_INCOME, 'revenue', idx=9)

        rev_cagr_1y = self._calc_cagr(rev_prev_1y, rev_prev_2y, 1)
        rev_cagr_3y = self._calc_cagr(rev_prev_1y, rev_prev_3y, 3)
        rev_cagr_5y = self._calc_cagr(rev_prev_1y, rev_prev_5y, 5)
        rev_cagr_10y = self._calc_cagr(rev_prev_1y, rev_prev_10y, 10)

        metrics = {
            'Revenue CAGR (1Y)': rev_cagr_1y,
            'Revenue CAGR (3Y)': rev_cagr_3y,
            'Revenue CAGR (5Y)': rev_cagr_5y,
            'Revenue CAGR (10Y)': rev_cagr_10y,
        }

        return metrics

    def _calc_roe_sec(self, ticker):
        '''
        roe = return on equity
        se = shareholder equity
        ni = net income
        '''
        # Net Income prev FY
        ni_prev_1y = self._get_latest_value(ticker, ANN_INCOME, 'netIncome', idx=0)
        ni_prev_3y = self._get_latest_value(ticker, ANN_INCOME, 'netIncome', idx=2)
        ni_prev_5y = self._get_latest_value(ticker, ANN_INCOME, 'netIncome', idx=4)
        ni_prev_10y = self._get_latest_value(ticker, ANN_INCOME, 'netIncome', idx=9)

        # Sharesholder prev FY
        se_prev_1y = self._get_latest_value(ticker, ANN_BALANCE, 'totalEquity', idx=0)
        se_prev_3y = self._get_latest_value(ticker, ANN_BALANCE, 'totalEquity', idx=2)
        se_prev_5y = self._get_latest_value(ticker, ANN_BALANCE, 'totalEquity', idx=4)
        se_prev_10y = self._get_latest_value(ticker, ANN_BALANCE, 'totalEquity', idx=9)

        # ROE TTM
        ni_prev_1q = self._get_latest_value(ticker, QUAR_INCOME, 'netIncome', idx=0)
        ni_prev_2q = self._get_latest_value(ticker, QUAR_INCOME, 'netIncome', idx=1)
        ni_prev_3q = self._get_latest_value(ticker, QUAR_INCOME, 'netIncome', idx=2)
        ni_prev_4q = self._get_latest_value(ticker, QUAR_INCOME, 'netIncome', idx=3)
        
        se_prev_4q = self._get_latest_value(ticker, QUAR_BALANCE, 'totalEquity', idx=3)

        # Calculation
        roe_ttm = self._safe_div(ni_prev_1q + ni_prev_2q + ni_prev_3q + ni_prev_4q, se_prev_4q)
        roe_prev_1y = self._safe_div(ni_prev_1y, se_prev_1y)
        roe_prev_3y = self._safe_div(ni_prev_3y, se_prev_3y)
        roe_prev_5y = self._safe_div(ni_prev_5y, se_prev_5y)
        roe_prev_10y = self._safe_div(ni_prev_10y, se_prev_10y)

        metrics = {
            'ROE (TTM)': roe_ttm,
            'ROE (FY -1)': roe_prev_1y,
            'ROE (FY -3)': roe_prev_3y,
            'ROE (FY -5)': roe_prev_5y,
            'ROE (FY -10)': roe_prev_10y,
        }

        return metrics


    def _get_investment_metrics(self):
        with st.spinner('Calculating (2/5) - Investment Metrics'):
            for ticker in self.ticker_ls:
                capex = self._get_latest_value(ticker, ANN_CF, 'capitalExpenditure')
                net_income = self._get_latest_value(ticker, ANN_INCOME, 'netIncome', default_value=None)

                gm_metrics = self._calc_gross_margin_sec(ticker)
                eps_metrics = self._calc_eps_sec(ticker)
                rev_metrics = self._calc_revenue_sec(ticker)
                roe_metrics = self._calc_roe_sec(ticker)

                metrics = {
                    'Mind Share': None,
                    'Market Share': None,
                    'CAPEX / Net Income': self._safe_div(capex, net_income),

                    **gm_metrics,
                    **eps_metrics,
                    **rev_metrics,
                    **roe_metrics,
                }

                for k, v in metrics.items():
                    self.data_invest_metrics[k].append(v)

            time.sleep(1.5)

    def _get_investment_risk(self):
        '''
        se = shareholders
        rec = receivables
        inv = inventory
        rev = revenue

        remark: receivable turnover not using because FMP give net receivable not the receivable
        '''
        with st.spinner('Calculating (3/5) - Investment Risks'):
            for ticker in self.ticker_ls:
                net_debt_prev_q = self._get_latest_value(ticker, QUAR_BALANCE, 'netDebt', idx=0)
                tot_equity_prev_q = self._get_latest_value(ticker, ANN_BALANCE, 'totalEquity', idx=0)
                rec_prev_fy = self._get_latest_value(ticker, ANN_CF, 'accountsReceivables', idx=0)
                inv_prev_fy = self._get_latest_value(ticker, ANN_CF, 'inventory', idx=0)
                rev_prev_fy = self._get_latest_value(ticker, ANN_INCOME, 'revenue', idx=0)

                net_debt_to_equity = self._safe_div(net_debt_prev_q, tot_equity_prev_q)
                receivable_turnover = self._safe_div(rec_prev_fy, rev_prev_fy)
                inventory_turnover = self._safe_div(inv_prev_fy, rev_prev_fy)

                metrics = {
                    'Net Debt to Equity (Last Quarter)': net_debt_to_equity,
                    'Receivable / Revenue (Last FY)': receivable_turnover,
                    'Inventory / Revenue (Last FY)': inventory_turnover,
                }

                for k, v in metrics.items():
                    self.data_invest_risks[k].append(v)
            
            time.sleep(1.5)
        
    def _get_valuation(self):
        '''
        peg = price 
        '''
        with st.spinner('Calculating (4/5) - Valuation'):
            for idx, ticker in enumerate(self.ticker_ls):
                div_yield_ttm = self._get_latest_value(ticker, RATIO, 'dividendYield', idx=0)
                pe_ttm = self._get_latest_value(ticker, RATIO_TTM, 'peRatioTTM', idx=0)
                peg_ttm = self._get_latest_value(ticker, RATIO_TTM, 'pegRatioTTM', idx=0)
                peg_1y = self._safe_div(pe_ttm, self.data_invest_metrics['EPS CAGR (1Y)'][idx])
                peg_3y = self._safe_div(pe_ttm, self.data_invest_metrics['EPS CAGR (3Y)'][idx])

                metrics = {
                    'Dividend Yield': div_yield_ttm,
                    'Trailing PE (TTM)': pe_ttm,
                    'PEG Ratio (TTM)': peg_ttm,
                    'PEG Ratio (FY -1)': peg_1y,
                    'PEG Ratio (FY -3)': peg_3y,
                }

                for k, v in metrics.items():
                    self.data_valuation[k].append(v)
            
            time.sleep(1.5)

    def _get_fin(self):
        with st.spinner('Calculating (5/5) - Financials'):
            for ticker in self.ticker_ls:
                tot_rev_prev_q = self._get_latest_value(ticker, QUAR_INCOME, 'revenue', idx=0)
                gross_profit_prev_q = self._get_latest_value(ticker, QUAR_INCOME, 'grossProfit', idx=0)
                capex_prev_yr = self._get_latest_value(ticker, ANN_CF, 'capitalExpenditure', idx=0)

                ni_prev_q = self._get_latest_value(ticker, QUAR_INCOME, 'netIncome', idx=0)
                ni_prev_2q = self._get_latest_value(ticker, QUAR_INCOME, 'netIncome', idx=1)
                ni_prev_3q = self._get_latest_value(ticker, QUAR_INCOME, 'netIncome', idx=2)
                ni_prev_4q = self._get_latest_value(ticker, QUAR_INCOME, 'netIncome', idx=3)
                ni_prev_yr = self._get_latest_value(ticker, ANN_INCOME, 'netIncome', idx=0)
                ni_ttm = ni_prev_q + ni_prev_2q + ni_prev_3q + ni_prev_4q

                payout_r = self._get_latest_value(ticker, RATIO, 'dividendPayoutRatio', idx=0)

                ex_div_dt = self._get_latest_value(ticker, DIV_CAL, 'recordDate', idx=0)
                div = self._get_latest_value(ticker, DIV_CAL, 'dividend', idx=0)

                # Calc EPS TTM
                eps_prev_1q = self._get_latest_value(ticker, QUAR_INCOME, 'eps', idx=0)
                eps_prev_2q = self._get_latest_value(ticker, QUAR_INCOME, 'eps', idx=1)
                eps_prev_3q = self._get_latest_value(ticker, QUAR_INCOME, 'eps', idx=2)
                eps_prev_4q = self._get_latest_value(ticker, QUAR_INCOME, 'eps', idx=3)
                eps_ttm = eps_prev_1q + eps_prev_2q + eps_prev_3q + eps_prev_4q

                metrics = {
                    'Total Revenue (Last Quarter)': tot_rev_prev_q,
                    'Gross Profit (Last Quarter)': gross_profit_prev_q,
                    'Capital Expenditure (Last Year)': capex_prev_yr,
                    'Net Income (Last Quarter)': ni_prev_q,
                    'Net Income (Last Year)': ni_prev_yr,
                    'Net Income (TTM)': ni_ttm,

                    'EPS (TTM)': eps_ttm,
                    'Last Ex-Dividend Date': ex_div_dt,
                    'Last Dividend Value': div,

                    'Payout Ratio': payout_r,
                }

                for k, v in metrics.items():
                    self.data_fin[k].append(v)
            
            time.sleep(1.5)

    def _format_column(self, df: pd.DataFrame):
        copy_df = df.copy()
        for col in copy_df.columns.tolist():
            if col in self.txt_col_ls:
                copy_df[col] = copy_df[col].apply(Formatter.format_number)

        return copy_df


    def _build_downloadable_dataframe(self):
        basic_header = pd.DataFrame([None], columns=['(A) Basic Info'])
        basic_info_df = pd.DataFrame(self.data_basic_info)
        invest_metrics_header = pd.DataFrame([None], columns=['(B) Investment Metrics'])
        invest_metrics_df = pd.DataFrame(self.data_invest_metrics)
        invest_risks_header = pd.DataFrame([None], columns=['(C) Investment Risks'])
        invest_risks_df = pd.DataFrame(self.data_invest_risks)
        valuation_header = pd.DataFrame([None], columns=['(D) Valuation'])
        valuation_df = pd.DataFrame(self.data_valuation)
        fin_header = pd.DataFrame([None], columns=['(E) Financial Ratio'])
        fin_df = pd.DataFrame(self.data_fin)

        raw_data_df = pd.concat([
            basic_header, basic_info_df,
            invest_metrics_header, invest_metrics_df,
            invest_risks_header, invest_risks_df,
            valuation_header, valuation_df,
            fin_header, fin_df,
        ], axis=1)

        reorder_columns = [
            # (A) Basic Info
            'Company Name', 'Ticker', 'Sector', 'Currency', 'Current Price', 'Market Cap', 'Beta',

            # (B) Investment Metrics
            'Mind Share', 'Market Share', 'Dividend Yield', 'CAPEX / Net Income', 'EPS CAGR (5Y)', 'EPS CAGR (10Y)', 
            'Gross Margin (TTM)', 'EPS CAGR (TTM)', 'EPS CAGR (1Y)', 'EPS CAGR (3Y)',
            'Revenue CAGR (1Y)', 'Revenue CAGR (3Y)', 'Revenue CAGR (5Y)', 'Revenue CAGR (10Y)',
            'Gross Margin (Last Quarter)', 'Gross Margin (FY -1)', 'Gross Margin (FY -3)',
            'ROE (TTM)', 'ROE (FY -3)',

            # (C) Investment Metrics
            'Net Debt to Equity (Last Quarter)', 'Receivable / Revenue (Last FY)', 'Inventory / Revenue (Last FY)',

            # (D) Valuation
            'Trailing PE (TTM)', 'PEG Ratio (TTM)', 'PEG Ratio (FY -1)', 'PEG Ratio (FY -3)',

            # (E) Financial Ratio
            'Total Revenue (Last Quarter)', 'Gross Profit (Last Quarter)',
            'Capital Expenditure (Last Year)', 'Net Income (TTM)', 'Net Income (Last Year)', 'Net Income (Last Quarter)',
            'EPS (TTM)', 'Last Ex-Dividend Date', 'Last Dividend Value', 'Payout Ratio',
        ]
        raw_data_df = raw_data_df[reorder_columns]

        st.dataframe(raw_data_df)

        # Option to download the table
        fmt_dt = dt.datetime.now().strftime('%Y-%m-%d ')

        raw_filename = f"financial_data_raw__{fmt_dt.replace(' ', '_')}.xlsx"
        raw_excel = Writer.convert_df_to_excel(raw_data_df)
        raw_b64_excel = base64.b64encode(raw_excel).decode()
        href_excel = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{raw_b64_excel}" download="{raw_filename}">Download as Raw Excel file</a>'
        st.markdown(href_excel, unsafe_allow_html=True)

        fmt_data_df = self._format_column(raw_data_df)
        filename = f"financial_data_formatted__{fmt_dt.replace(' ', '_')}.xlsx"

        excel = Writer.convert_df_to_excel(fmt_data_df, percentage_columns=self.pct_col_ls, decimal_columns=self.num_col_ls)
        b64_excel = base64.b64encode(excel).decode()
        href_excel = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_excel}" download="{filename}">Download as Formatted Excel file</a>'
        st.markdown(href_excel, unsafe_allow_html=True)

    def _get_query(self):
        if not self._is_valid_input(self.ticker_ls):
            return None

        self.ticker_ls = self._split_input(self.ticker_ls)
        
        # Retrieve data
        self._get_raw_financials_statement()
        
        self._get_basic_info()
        self._get_investment_metrics()
        self._get_investment_risk()
        self._get_valuation()
        self._get_fin()



    def _preload(self):
        CommonLayout.load()

        st.title("Financial Analysis")

        default_value = self._get_query_parameter('tickers')
        if default_value:
            default_value = unquote(default_value)
        self.ticker_ls = st.text_input("Enter FMP ticker, separate with comma", value=default_value)

        if st.button('Submit'):
            self._get_query()
            self._build_downloadable_dataframe()

    def main(self):
        load_dotenv()

        self._preload()
    

fa = FinancialAnalysis()
fa.main()