from collections import defaultdict
import datetime as dt
from dotenv import load_dotenv
import os
import re
import streamlit as st
from urllib.parse import urlparse, parse_qs, quote, unquote

import pandas as pd
from main.data.data_layout import DataLayout
from main.util import c_text
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
ANN_RATIO = 'ann_ratio'
QUAR_RATIO = 'quarratio'
RATIO_TTM = 'ratio_ttm'
DIV_CAL = 'div_cal'
EARNINGS_CAL = 'earnings_cal'

class FinancialAnalysis:
    
    def __init__(self):
        self.ticker_ls = []
        self.data_basic_info = defaultdict(list)
        self.data_invest_metrics = defaultdict(list)
        self.data_invest_risks = defaultdict(list)
        self.data_valuation = defaultdict(list)
        self.data_fin = defaultdict(list)

        # Storing data
        self.raw_basic_info = defaultdict(dict)
        self.data_raw_financials = defaultdict(dict)

        self.pct_col_ls = [
            'Gross Margin (Last Quarter)', 'Gross Margin (TTM)', 'Gross Margin (FY -1)', 
            'Gross Margin (FY -3)', 'Gross Margin (FY -5)', 'Gross Margin (FY -10)',
            'EPS CAGR (TTM)', 'EPS CAGR (1Y)', 'EPS CAGR (3Y)', 'EPS CAGR (5Y)', 'EPS CAGR (10Y)',
            'Revenue CAGR (1Y)', 'Revenue CAGR (3Y)', 'Revenue CAGR (5Y)', 'Revenue CAGR (10Y)',
            'ROE (TTM)', 'ROE (FY -1)', 'ROE (FY -3)', 'ROE (FY -5)', 'ROE (FY -10)',
            'Dividend Yield (TTM)', 'Payout Ratio (TTM)', 
            'CAPEX / Net Income (TTM)', 'CAPEX / Net Income (5Y AVG)', 'CAPEX / Net Income (10Y AVG)',
            'Net Debt to Equity (Last Quarter)', 'Receivable / Revenue (Last FY)', 'Inventory / Revenue (Last FY)',
            'Beat Estimate', 'ROIC',
        ]
        self.num_col_ls = [
            'Current Price', 'Beta',  
            'Trailing PE (TTM)', 'PEG Ratio (TTM)', 'PEG Ratio (FY -1)', 'PEG Ratio (FY -3)',
            'EPS (TTM)', 'Last Dividend Value', 'Next Earnings Estimate EPS',
        ]
        self.txt_col_ls = [
            'Market Cap', 'Total Revenue (Last Quarter)', 'Gross Profit (Last Quarter)',
            'Capital Expenditure (Last Year)', 'Net Income (Last Quarter)',
            'Net Income (Last Year)', 'Net Income (TTM)', 'Next Earnings Estimate Revenue',
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

    def _get_basic_info(self):
        with st.spinner('Calculating (1/5) - Basic Info'):
            not_found_ticker_ls = []
            for ticker in self.ticker_ls:
                if not ticker in self.raw_basic_info.keys():
                    url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={os.getenv('FMP_KEY')}"
                    result_ls = fetch_data(url)

                    if len(result_ls) == 0:
                        not_found_ticker_ls.append(ticker)
                        continue

                    self.raw_basic_info[ticker] = result_ls[0]  # Store the result
                
                result = self.raw_basic_info[ticker]

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

            # Remove non found ticker
            if len(not_found_ticker_ls) > 0:
                st.warning(f'The following ticker are not found: {not_found_ticker_ls}')
                self.ticker_ls = list(filter(lambda x: x not in not_found_ticker_ls, self.ticker_ls))

    def _fetch_multi_financials(self, ticker, limit=15):
        result = defaultdict(dict)
        
        api_key = os.getenv('FMP_KEY')
        endpoints = [
            (ANN_INCOME, f"https://financialmodelingprep.com/stable/income-statement?symbol={ticker}&period=annual&limit={limit}&apikey={api_key}"),
            (QUAR_INCOME, f"https://financialmodelingprep.com/stable/income-statement?symbol={ticker}&period=quarterly&limit={limit}&apikey={api_key}"),
            (ANN_BALANCE, f"https://financialmodelingprep.com/stable/balance-sheet-statement?symbol={ticker}&period=annual&limit={limit}&apikey={api_key}"),
            (QUAR_BALANCE, f"https://financialmodelingprep.com/stable/balance-sheet-statement?symbol={ticker}&period=quarterly&limit={limit}&apikey={api_key}"),
            (ANN_CF, f"https://financialmodelingprep.com/stable/cash-flow-statement?symbol={ticker}&period=annual&limit={limit}&apikey={api_key}"),
            (QUAR_CF, f"https://financialmodelingprep.com/stable/cash-flow-statement?symbol={ticker}&period=quarterly&limit={limit}&apikey={api_key}"),
            (ANN_RATIO, f"https://financialmodelingprep.com/stable/ratios?symbol={ticker}&period=annual&apikey={api_key}"),
            (QUAR_RATIO, f"https://financialmodelingprep.com/stable/ratios?symbol={ticker}&period=quarterly&apikey={api_key}"),
            (RATIO_TTM, f"https://financialmodelingprep.com/stable/ratios-ttm?symbol={ticker}&apikey={api_key}"),
            (DIV_CAL, f"https://financialmodelingprep.com/stable/dividends?symbol={ticker}&apikey={api_key}"),
            (EARNINGS_CAL, f"https://financialmodelingprep.com/stable/earnings?symbol={ticker}&apikey={api_key}")
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

    def _get_latest_value(self, ticker, fin_key, metrics, idx=0, default_value=0.0, is_est=True):
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
            if len(self.data_raw_financials[ticker][fin_key]) == 0:
                return None
            
            val = self.data_raw_financials[ticker][fin_key][idx].get(metrics, default_value)

        if fin_key == EARNINGS_CAL:
            for cal in self.data_raw_financials[ticker][fin_key]:
                if is_est and cal['revenueEstimated'] is not None:
                    val = cal[metrics]
                    break
                elif not is_est and cal['revenueActual'] is not None:
                    val = cal[metrics]
                    break

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
        gm_prev_1q = self._get_latest_value(ticker, QUAR_RATIO, 'grossProfitMargin', idx=0)

        # Gross margin previous year
        gm_prev_1y = self._get_latest_value(ticker, ANN_RATIO, 'grossProfitMargin', idx=0, default_value=None)
        gm_prev_3y = self._get_latest_value(ticker, ANN_RATIO, 'grossProfitMargin', idx=2, default_value=None)
        gm_prev_5y = self._get_latest_value(ticker, ANN_RATIO, 'grossProfitMargin', idx=4, default_value=None)
        gm_prev_10y = self._get_latest_value(ticker, ANN_RATIO, 'grossProfitMargin', idx=9, default_value=None)

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
        eps_cagr_ttm = self._safe_div(eps_prev_1q + eps_prev_2q + eps_prev_3q + eps_prev_4q,
                                      eps_prev_5q + eps_prev_6q + eps_prev_7q + eps_prev_8q) - 1.0

        metrics = {
            'EPS CAGR (TTM)': eps_cagr_ttm,
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

    def _calc_capex_ni(self, ticker):
        capex_prev_1q = self._get_latest_value(ticker, QUAR_CF, 'capitalExpenditure', idx=0)
        capex_prev_2q = self._get_latest_value(ticker, QUAR_CF, 'capitalExpenditure', idx=1)
        capex_prev_3q = self._get_latest_value(ticker, QUAR_CF, 'capitalExpenditure', idx=2)
        capex_prev_4q = self._get_latest_value(ticker, QUAR_CF, 'capitalExpenditure', idx=3)

        ni_prev_1q = self._get_latest_value(ticker, QUAR_INCOME, 'netIncome', idx=0)
        ni_prev_2q = self._get_latest_value(ticker, QUAR_INCOME, 'netIncome', idx=1)
        ni_prev_3q = self._get_latest_value(ticker, QUAR_INCOME, 'netIncome', idx=2)
        ni_prev_4q = self._get_latest_value(ticker, QUAR_INCOME, 'netIncome', idx=3)
        capex_ni_ttm = self._safe_div(capex_prev_1q + capex_prev_2q + capex_prev_3q + capex_prev_4q,
                                        ni_prev_1q + ni_prev_2q + ni_prev_3q + ni_prev_4q)

        tot_5y_capex = sum([
            self._get_latest_value(ticker, ANN_CF, 'capitalExpenditure', idx=i) for i in range(5)
        ])
        tot_5y_ni = sum([
            self._get_latest_value(ticker, ANN_INCOME, 'netIncome', idx=i) for i in range(5)
        ])
        capex_ni_5y = self._safe_div(tot_5y_capex, tot_5y_ni)

        tot_10y_capex = sum([
            self._get_latest_value(ticker, ANN_CF, 'capitalExpenditure', idx=i) for i in range(10)
        ])
        tot_10y_ni = sum([
            self._get_latest_value(ticker, ANN_INCOME, 'netIncome', idx=i) for i in range(10)
        ])
        capex_ni_10y = self._safe_div(tot_10y_capex, tot_10y_ni)

        metrics = {
            'CAPEX / Net Income (TTM)': capex_ni_ttm,
            'CAPEX / Net Income (5Y AVG)': capex_ni_5y,
            'CAPEX / Net Income (10Y AVG)': capex_ni_10y,
        }

        return metrics

    def _get_investment_metrics(self):
        with st.spinner('Calculating (2/5) - Investment Metrics'):
            for ticker in self.ticker_ls:
                gm_metrics = self._calc_gross_margin_sec(ticker)
                eps_metrics = self._calc_eps_sec(ticker)
                rev_metrics = self._calc_revenue_sec(ticker)
                roe_metrics = self._calc_roe_sec(ticker)
                capex_ni_metrics = self._calc_capex_ni(ticker)

                metrics = {
                    'Mind Share': None,
                    'Market Share': None,

                    **gm_metrics,
                    **eps_metrics,
                    **rev_metrics,
                    **roe_metrics,
                    **capex_ni_metrics,
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
                div_yield_ttm = self._get_latest_value(ticker, RATIO_TTM, 'dividendYieldTTM', idx=0)
                pe_ttm = self._get_latest_value(ticker, RATIO_TTM, 'priceToEarningsRatioTTM', idx=0)
                peg_ttm = self._get_latest_value(ticker, RATIO_TTM, 'priceToEarningsGrowthRatioTTM', idx=0)
                peg_1y = self._safe_div(pe_ttm, self.data_invest_metrics['EPS CAGR (1Y)'][idx])
                peg_3y = self._safe_div(pe_ttm, self.data_invest_metrics['EPS CAGR (3Y)'][idx])

                metrics = {
                    'Dividend Yield (TTM)': div_yield_ttm,
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

                payout_r = self._get_latest_value(ticker, RATIO_TTM, 'dividendPayoutRatioTTM', idx=0)

                ex_div_dt = self._get_latest_value(ticker, DIV_CAL, 'recordDate', idx=0)
                div = self._get_latest_value(ticker, DIV_CAL, 'dividend', idx=0)

                # Calc EPS TTM
                eps_prev_1q = self._get_latest_value(ticker, QUAR_INCOME, 'eps', idx=0)
                eps_prev_2q = self._get_latest_value(ticker, QUAR_INCOME, 'eps', idx=1)
                eps_prev_3q = self._get_latest_value(ticker, QUAR_INCOME, 'eps', idx=2)
                eps_prev_4q = self._get_latest_value(ticker, QUAR_INCOME, 'eps', idx=3)
                eps_ttm = eps_prev_1q + eps_prev_2q + eps_prev_3q + eps_prev_4q

                # Earnings Date
                next_earnings_date = self._get_latest_value(ticker, EARNINGS_CAL, 'date')
                next_earnings_estimate_eps = self._get_latest_value(ticker, EARNINGS_CAL, 'epsEstimated')
                next_earnings_estimate_revenue = self._get_latest_value(ticker, EARNINGS_CAL, 'revenueEstimated')

                # Beat Estimate
                est_eps = self._get_latest_value(ticker, EARNINGS_CAL, 'epsEstimated', is_est=False)
                act_eps = self._get_latest_value(ticker, EARNINGS_CAL, 'epsActual', is_est=False)
                act_eps_update_date = self._get_latest_value(ticker, EARNINGS_CAL, 'date', is_est=False)
                beat_estimate = self._safe_div(act_eps, est_eps) - 1.0

                # ROIC (Return on Investment Capital)
                ebit_ttm = sum([
                    self._get_latest_value(ticker, QUAR_INCOME, 'ebit', idx=i) for i in range(4)
                ])
                tax_rate = self._get_latest_value(ticker, ANN_RATIO, 'effectiveTaxRate')
                total_debt = self._get_latest_value(ticker, QUAR_BALANCE, 'totalDebt')
                total_equity = self._get_latest_value(ticker, QUAR_BALANCE, 'totalEquity')
                cash_equiv = self._get_latest_value(ticker, QUAR_BALANCE, 'cashAndCashEquivalents')
                roic = self._safe_div(ebit_ttm * (1 - tax_rate), total_debt + total_equity - cash_equiv)

                st.json({
                    'ebit_ttm': ebit_ttm,
                    'tax_rate': tax_rate,
                    'total_debt': total_debt,
                    'total_equity': total_equity,
                    'cash_equiv': cash_equiv,
                })

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
                    'ROIC': roic,

                    'Payout Ratio (TTM)': payout_r,
                    'Next Earnings Date': next_earnings_date,
                    'Next Earnings Estimate EPS': next_earnings_estimate_eps,
                    'Next Earnings Estimate Revenue': next_earnings_estimate_revenue,
                    'Beat Estimate': beat_estimate,
                    'Beat Estimate (Updated On)': act_eps_update_date,
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
            'Mind Share', 'Market Share', 'Dividend Yield (TTM)', 'CAPEX / Net Income (TTM)', 
            'CAPEX / Net Income (5Y AVG)', 'CAPEX / Net Income (10Y AVG)',
            'EPS CAGR (TTM)', 'EPS CAGR (5Y)', 'EPS CAGR (10Y)', 
            'Gross Margin (TTM)', 'Trailing PE (TTM)', 'PEG Ratio (TTM)',
            
            'EPS CAGR (1Y)', 'EPS CAGR (3Y)', 'Net Debt to Equity (Last Quarter)',
            'Revenue CAGR (1Y)', 'Revenue CAGR (3Y)', 'Revenue CAGR (5Y)', 'Revenue CAGR (10Y)',
            'Gross Margin (Last Quarter)', 'Gross Margin (FY -1)', 'Gross Margin (FY -3)',
            'ROE (TTM)', 'ROE (FY -3)',

            # (C) Investment Metrics
            'Receivable / Revenue (Last FY)', 'Inventory / Revenue (Last FY)',

            # (D) Valuation
            'PEG Ratio (FY -1)', 'PEG Ratio (FY -3)',

            # (E) Financial Ratio
            'Total Revenue (Last Quarter)', 'Gross Profit (Last Quarter)',
            'Capital Expenditure (Last Year)', 'Net Income (TTM)', 'Net Income (Last Year)', 'Net Income (Last Quarter)',
            'EPS (TTM)', 'Last Ex-Dividend Date', 'Last Dividend Value', 'Payout Ratio (TTM)', 'ROIC',
            'Next Earnings Date', 'Next Earnings Estimate EPS', 'Next Earnings Estimate Revenue', 'Beat Estimate', 'Beat Estimate (Updated On)',
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

        # us_tab, cn_tab, jp_tab = st.tabs(["US", "CN", "JP"])

        # us_data_layout = DataLayout()
        # cn_data_layout = DataLayout()
        # jp_data_layout = DataLayout()

        # with us_tab:
        #     us_data_layout.input_ticker__value = st.text_input(c_text.INPUT_HINT__TICKER, value=us_data_layout.input_ticker__value)

        default_value = self._get_query_parameter('tickers')
        if default_value:
            default_value = unquote(default_value)

        self.ticker_ls = st.text_input(c_text.INPUT_HINT__TICKER, value=default_value)

        if st.button('Submit'):
            self._get_query()
            self._build_downloadable_dataframe()

    def main(self):
        load_dotenv()

        self._preload()
    

fa = FinancialAnalysis()
fa.main()