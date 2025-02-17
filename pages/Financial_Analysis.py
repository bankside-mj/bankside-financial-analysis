from collections import defaultdict
import datetime as dt
from dotenv import load_dotenv
import os
import re
import streamlit as st
from urllib.parse import urlparse, parse_qs, quote, unquote

import pandas as pd
from main.data.data_container import DataContainer
from main.constants import c_api_text, c_text
from main.layout.layout_output_data import LayoutOutputData
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
            c_text.GM_LAST_Q, c_text.GM_TTM, c_text.GM_FY1, c_text.GM_FY3, c_text.GM_FY5, c_text.GM_FY10,
            c_text.EPS_CAGR_TTM, c_text.EPS_CAGR_3Y_TTM, c_text.EPS_CAGR_5Y_TTM, c_text.EPS_CAGR_10Y_TTM,
            c_text.REV_CAGR_1Y, c_text.REV_CAGR_3Y, c_text.REV_CAGR_5Y, c_text.REV_CAGR_10Y,
            c_text.ROE_TTM, c_text.ROE_FY1, c_text.ROE_FY3, c_text.ROE_FY5, c_text.ROE_FY10,
            c_text.DIV_YIELD_TTM, c_text.PR_TTM,
            c_text.CAPEX_NI_TTM, c_text.CAPEX_NI_5Y_AVG, c_text.CAPEX_NI_10Y_AVG,
            c_text.NDTE_LAST_Q, c_text.RR_LAST_FY, c_text.IR_LAST_FY,
            c_text.BEAT_EST, c_text.ROIC,
        ]
        self.num_col_ls = [
            c_text.CUR_PRICE, c_text.BETA,
            c_text.TRAILING_PE_TTM, c_text.PEG_R_TTM, c_text.PEG_R_FY1, c_text.PEG_R_FY3,
            c_text.EPS_TTM, c_text.LAST_DIV_VAL, c_text.NEXT_EARN_EST_EPS,
        ]
        self.txt_col_ls = [
            c_text.MKT_CAP, c_text.TOT_REV_LAST_Q, c_text.GP_LAST_Q,
            c_text.CAPEX_LAST_Y, c_text.NEXT_EARN_EST_REV,
            c_text.NI_LAST_Q, c_text.NI_LAST_Y, c_text.NI_TTM,
        ]

    # def _get_query_parameter(self, param_name):
    #     if param_name not in st.query_params.keys():
    #         return None
        
    #     query_params = st.query_params[param_name]
    #     return query_params

    def _has_ticket(self, txt):
        if len(txt) == 0:
            st.error(c_text.ERR__EMPTY_INPUT)
            return False

        return True

    def _split_input(self, txt):
        try:
            txt = re.split('[;, ]+', txt)
            txt = [t.upper().strip() for t in txt]
            txt = list(filter(lambda x: x != '', txt))
        except:
            st.error(c_text.ERR__WRONG_DELIMITER)

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

                cur_ticker = result.get(c_api_text.FMP_SYMBOL)

                self.data_basic_info[c_text.COMPANY_NAME].append(result.get(c_api_text.FMP_COMP_NAME))
                self.data_basic_info[c_text.TICKER].append(cur_ticker)
                self.data_basic_info[c_text.SECTOR].append(result.get(c_api_text.FMP_SECTOR))
                self.data_basic_info[c_text.CCY].append(result.get(c_api_text.FMP_CCY))
                self.data_basic_info[c_text.CUR_PRICE].append(result.get(c_api_text.FMP_PRICE))
                self.data_basic_info[c_text.MKT_CAP].append(result.get(c_api_text.FMP_MKT_CAP))
                self.data_basic_info[c_text.BETA].append(result.get(c_api_text.FMP_BETA))

            # Remove non found ticker
            if len(not_found_ticker_ls) > 0:
                st.warning(f'{c_text.ERR__TICKER_NOT_FOUND}: {not_found_ticker_ls}')
                self.ticker_ls = list(filter(lambda x: x not in not_found_ticker_ls, self.ticker_ls))

    def _fetch_multi_financials(self, ticker, limit=10):
        result = defaultdict(dict)
        
        base_url = 'https://financialmodelingprep.com/stable'
        api_key = os.getenv('FMP_KEY')
        endpoints = [
            (ANN_INCOME, f"{base_url}/income-statement?symbol={ticker}&period=annual&limit={limit}&apikey={api_key}"),
            (QUAR_INCOME, f"{base_url}/income-statement?symbol={ticker}&period=quarterly&limit={limit}&apikey={api_key}"),
            (ANN_BALANCE, f"{base_url}/balance-sheet-statement?symbol={ticker}&period=annual&limit={limit}&apikey={api_key}"),
            (QUAR_BALANCE, f"{base_url}/balance-sheet-statement?symbol={ticker}&period=quarterly&limit={limit}&apikey={api_key}"),
            (ANN_CF, f"{base_url}/cash-flow-statement?symbol={ticker}&period=annual&limit={limit}&apikey={api_key}"),
            (QUAR_CF, f"{base_url}/cash-flow-statement?symbol={ticker}&period=quarterly&limit={limit}&apikey={api_key}"),
            (ANN_RATIO, f"{base_url}/ratios?symbol={ticker}&period=annual&apikey={api_key}&limit={limit}"),
            (QUAR_RATIO, f"{base_url}/ratios?symbol={ticker}&period=quarterly&apikey={api_key}&limit={limit}"),
            (RATIO_TTM, f"{base_url}/ratios-ttm?symbol={ticker}&apikey={api_key}&limit={limit}"),
            (DIV_CAL, f"{base_url}/dividends?symbol={ticker}&apikey={api_key}&limit={limit}"),
            (EARNINGS_CAL, f"{base_url}/earnings?symbol={ticker}&apikey={api_key}&limit={limit + 40}")
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
                if is_est and cal[c_api_text.FMP_REV_EST] is not None:
                    val = cal[metrics]
                    break
                elif not is_est and cal[c_api_text.FMP_REV_ACT] is not None:
                    val = cal[metrics]
                    break

        else:
            val = self.data_raw_financials[ticker][fin_key][idx].get(metrics, default_value)

        return val

    def _get_earnings_cal(self, ticker, fin_key, metrics, is_est=True, beg_n: int=None, end_n: int=None):
        if beg_n is None:
            for cal in self.data_raw_financials[ticker][fin_key]:
                if is_est and cal[c_api_text.FMP_REV_EST] is not None:
                    val = cal[metrics]
                    break
                elif not is_est and cal[c_api_text.FMP_REV_ACT] is not None:
                    val = cal[metrics]
                    break
        else:
            val = 0
            counter = 0
            for cal in self.data_raw_financials[ticker][fin_key]:
                if cal[metrics] is not None:
                    counter += 1

                    if counter >= beg_n:
                        val += cal[metrics]
                
                if counter == end_n:
                    break
    
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

    def _calc_GM_sec(self, ticker):
        '''
        gm = gross margin
        gp = gross profit
        rev = revenue
        '''
        # Gross margin previous quarter
        gm_prev_1q = self._get_latest_value(ticker, QUAR_RATIO, c_api_text.FMP_GPM, idx=0)

        # Gross margin previous year
        gm_prev_1y = self._get_latest_value(ticker, ANN_RATIO, c_api_text.FMP_GPM, idx=0, default_value=None)
        gm_prev_3y = self._get_latest_value(ticker, ANN_RATIO, c_api_text.FMP_GPM, idx=2, default_value=None)
        gm_prev_5y = self._get_latest_value(ticker, ANN_RATIO, c_api_text.FMP_GPM, idx=4, default_value=None)
        gm_prev_10y = self._get_latest_value(ticker, ANN_RATIO, c_api_text.FMP_GPM, idx=9, default_value=None)

        # Gross margin TTM
        gp_prev_1q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_GP, idx=0)
        gp_prev_2q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_GP, idx=1)
        gp_prev_3q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_GP, idx=2)
        gp_prev_4q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_GP, idx=3)

        rev_prev_1q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_REV, idx=0)
        rev_prev_2q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_REV, idx=1)
        rev_prev_3q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_REV, idx=2)
        rev_prev_4q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_REV, idx=3)

        gm_ttm = self._safe_div(gp_prev_1q + gp_prev_2q + gp_prev_3q + gp_prev_4q, rev_prev_1q + rev_prev_2q + rev_prev_3q + rev_prev_4q)


        metrics = {
            c_text.GM_LAST_Q: gm_prev_1q,
            c_text.GM_TTM: gm_ttm,
            c_text.GM_FY1: gm_prev_1y,
            c_text.GM_FY3: gm_prev_3y,
            c_text.GM_FY5: gm_prev_5y,
            c_text.GM_FY10: gm_prev_10y,
        }

        return metrics
    
    def _calc_eps_sec(self, ticker):
        '''
        eps = earnings per share
        '''
        eps_prev_1y = self._get_earnings_cal(ticker, EARNINGS_CAL, c_api_text.FMP_EPS_ACT, beg_n=1, end_n=4)
        eps_prev_2y = self._get_earnings_cal(ticker, EARNINGS_CAL, c_api_text.FMP_EPS_ACT, beg_n=5, end_n=8)
        eps_prev_3y = self._get_earnings_cal(ticker, EARNINGS_CAL, c_api_text.FMP_EPS_ACT, beg_n=9, end_n=12)
        eps_prev_5y = self._get_earnings_cal(ticker, EARNINGS_CAL, c_api_text.FMP_EPS_ACT, beg_n=17, end_n=20)
        eps_prev_10y = self._get_earnings_cal(ticker, EARNINGS_CAL, c_api_text.FMP_EPS_ACT, beg_n=37, end_n=40)

        eps_cagr_ttm = self._calc_cagr(eps_prev_1y, eps_prev_2y, 1)
        eps_cagr_3y = self._calc_cagr(eps_prev_1y, eps_prev_3y, 3)
        eps_cagr_5y = self._calc_cagr(eps_prev_1y, eps_prev_5y, 5)
        eps_cagr_10y = self._calc_cagr(eps_prev_1y, eps_prev_10y, 10)
        
        metrics = {
            c_text.EPS_CAGR_TTM: eps_cagr_ttm,
            c_text.EPS_CAGR_3Y_TTM: eps_cagr_3y,
            c_text.EPS_CAGR_5Y_TTM: eps_cagr_5y,
            c_text.EPS_CAGR_10Y_TTM: eps_cagr_10y,
        }

        return metrics
    
    def _calc_revenue_sec(self, ticker):
        '''
        rev = revenue
        '''
        rev_prev_1y = self._get_latest_value(ticker, ANN_INCOME, c_api_text.FMP_REV, idx=0)
        rev_prev_2y = self._get_latest_value(ticker, ANN_INCOME, c_api_text.FMP_REV, idx=1)
        rev_prev_3y = self._get_latest_value(ticker, ANN_INCOME, c_api_text.FMP_REV, idx=2)
        rev_prev_5y = self._get_latest_value(ticker, ANN_INCOME, c_api_text.FMP_REV, idx=4)
        rev_prev_10y = self._get_latest_value(ticker, ANN_INCOME, c_api_text.FMP_REV, idx=9)

        rev_cagr_1y = self._calc_cagr(rev_prev_1y, rev_prev_2y, 1)
        rev_cagr_3y = self._calc_cagr(rev_prev_1y, rev_prev_3y, 3)
        rev_cagr_5y = self._calc_cagr(rev_prev_1y, rev_prev_5y, 5)
        rev_cagr_10y = self._calc_cagr(rev_prev_1y, rev_prev_10y, 10)

        metrics = {
            c_text.REV_CAGR_1Y: rev_cagr_1y,
            c_text.REV_CAGR_3Y: rev_cagr_3y,
            c_text.REV_CAGR_5Y: rev_cagr_5y,
            c_text.REV_CAGR_10Y: rev_cagr_10y,
        }

        return metrics

    def _calc_roe_sec(self, ticker):
        '''
        roe = return on equity
        se = shareholder equity
        ni = net income
        '''
        # Net Income prev FY
        ni_prev_1y = self._get_latest_value(ticker, ANN_INCOME, c_api_text.FMP_NI, idx=0)
        ni_prev_3y = self._get_latest_value(ticker, ANN_INCOME, c_api_text.FMP_NI, idx=2)
        ni_prev_5y = self._get_latest_value(ticker, ANN_INCOME, c_api_text.FMP_NI, idx=4)
        ni_prev_10y = self._get_latest_value(ticker, ANN_INCOME, c_api_text.FMP_NI, idx=9)

        # Sharesholder prev FY
        se_prev_1y = self._get_latest_value(ticker, ANN_BALANCE, c_api_text.FMP_TOT_EQ, idx=0)
        se_prev_3y = self._get_latest_value(ticker, ANN_BALANCE, c_api_text.FMP_TOT_EQ, idx=2)
        se_prev_5y = self._get_latest_value(ticker, ANN_BALANCE, c_api_text.FMP_TOT_EQ, idx=4)
        se_prev_10y = self._get_latest_value(ticker, ANN_BALANCE, c_api_text.FMP_TOT_EQ, idx=9)

        # ROE TTM
        ni_prev_1q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_NI, idx=0)
        ni_prev_2q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_NI, idx=1)
        ni_prev_3q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_NI, idx=2)
        ni_prev_4q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_NI, idx=3)
        
        se_prev_1q = self._get_latest_value(ticker, QUAR_BALANCE, c_api_text.FMP_TOT_EQ, idx=0)

        # Calculation
        roe_ttm = self._safe_div(ni_prev_1q + ni_prev_2q + ni_prev_3q + ni_prev_4q, se_prev_1q)
        roe_prev_1y = self._safe_div(ni_prev_1y, se_prev_1y)
        roe_prev_3y = self._safe_div(ni_prev_3y, se_prev_3y)
        roe_prev_5y = self._safe_div(ni_prev_5y, se_prev_5y)
        roe_prev_10y = self._safe_div(ni_prev_10y, se_prev_10y)

        metrics = {
            c_text.ROE_TTM: roe_ttm,
            c_text.ROE_FY1: roe_prev_1y,
            c_text.ROE_FY3: roe_prev_3y,
            c_text.ROE_FY5: roe_prev_5y,
            c_text.ROE_FY10: roe_prev_10y,
        }

        return metrics

    def _calc_capex_ni(self, ticker):
        capex_prev_1q = self._get_latest_value(ticker, QUAR_CF, c_api_text.FMP_CAPEX, idx=0)
        capex_prev_2q = self._get_latest_value(ticker, QUAR_CF, c_api_text.FMP_CAPEX, idx=1)
        capex_prev_3q = self._get_latest_value(ticker, QUAR_CF, c_api_text.FMP_CAPEX, idx=2)
        capex_prev_4q = self._get_latest_value(ticker, QUAR_CF, c_api_text.FMP_CAPEX, idx=3)

        ni_prev_1q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_NI, idx=0)
        ni_prev_2q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_NI, idx=1)
        ni_prev_3q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_NI, idx=2)
        ni_prev_4q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_NI, idx=3)
        capex_ni_ttm = self._safe_div(capex_prev_1q + capex_prev_2q + capex_prev_3q + capex_prev_4q,
                                        ni_prev_1q + ni_prev_2q + ni_prev_3q + ni_prev_4q)

        tot_5y_capex = sum([
            self._get_latest_value(ticker, ANN_CF, c_api_text.FMP_CAPEX, idx=i) for i in range(5)
        ])
        tot_5y_ni = sum([
            self._get_latest_value(ticker, ANN_INCOME, c_api_text.FMP_NI, idx=i) for i in range(5)
        ])
        capex_ni_5y = self._safe_div(tot_5y_capex, tot_5y_ni)

        tot_10y_capex = sum([
            self._get_latest_value(ticker, ANN_CF, c_api_text.FMP_CAPEX, idx=i) for i in range(10)
        ])
        tot_10y_ni = sum([
            self._get_latest_value(ticker, ANN_INCOME, c_api_text.FMP_NI, idx=i) for i in range(10)
        ])
        capex_ni_10y = self._safe_div(tot_10y_capex, tot_10y_ni)

        metrics = {
            c_text.CAPEX_NI_TTM: capex_ni_ttm,
            c_text.CAPEX_NI_5Y_AVG: capex_ni_5y,
            c_text.CAPEX_NI_10Y_AVG: capex_ni_10y,
        }

        return metrics

    def _get_investment_metrics(self):
        with st.spinner('Calculating (2/5) - Investment Metrics'):
            for ticker in self.ticker_ls:
                gm_metrics = self._calc_GM_sec(ticker)
                eps_metrics = self._calc_eps_sec(ticker)
                rev_metrics = self._calc_revenue_sec(ticker)
                roe_metrics = self._calc_roe_sec(ticker)
                capex_ni_metrics = self._calc_capex_ni(ticker)

                metrics = {
                    c_text.MIND_SHARE: None,
                    c_text.MKT_SHARE: None,

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
                net_debt_prev_q = self._get_latest_value(ticker, QUAR_BALANCE, c_api_text.FMP_NET_DEBT, idx=0)
                tot_equity_prev_q = self._get_latest_value(ticker, ANN_BALANCE, c_api_text.FMP_TOT_EQ, idx=0)
                rec_prev_fy = self._get_latest_value(ticker, ANN_CF, c_api_text.FMP_AR, idx=0)
                inv_prev_fy = self._get_latest_value(ticker, ANN_CF, c_api_text.FMP_INV, idx=0)
                rev_prev_fy = self._get_latest_value(ticker, ANN_INCOME, c_api_text.FMP_REV, idx=0)

                net_debt_to_equity = self._safe_div(net_debt_prev_q, tot_equity_prev_q)
                receivable_turnover = self._safe_div(rec_prev_fy, rev_prev_fy)
                inventory_turnover = self._safe_div(inv_prev_fy, rev_prev_fy)

                metrics = {
                    c_text.NDTE_LAST_Q: net_debt_to_equity,
                    c_text.RR_LAST_FY: receivable_turnover,
                    c_text.IR_LAST_FY: inventory_turnover,
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
                div_yield_ttm = self._get_latest_value(ticker, RATIO_TTM, c_api_text.FMP_DIV_TTM, idx=0)
                pe_ttm = self._get_latest_value(ticker, RATIO_TTM, c_api_text.FMP_PE_TTM, idx=0)
                peg_ttm = self._get_latest_value(ticker, RATIO_TTM, c_api_text.FMP_PEG_TTM, idx=0)
                peg_1y = self._safe_div(pe_ttm, self.data_invest_metrics[c_text.EPS_CAGR_TTM][idx])
                peg_3y = self._safe_div(pe_ttm, self.data_invest_metrics[c_text.EPS_CAGR_3Y_TTM][idx])

                metrics = {
                    c_text.DIV_YIELD_TTM: div_yield_ttm,
                    c_text.TRAILING_PE_TTM: pe_ttm,
                    c_text.PEG_R_TTM: peg_ttm,
                    c_text.PEG_R_FY1: peg_1y,
                    c_text.PEG_R_FY3: peg_3y,
                }

                for k, v in metrics.items():
                    self.data_valuation[k].append(v)
            
            time.sleep(1.5)

    def _get_fin(self):
        with st.spinner('Calculating (5/5) - Financials'):
            for ticker in self.ticker_ls:
                tot_rev_prev_q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_REV, idx=0)
                gross_profit_prev_q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_GP, idx=0)
                capex_prev_yr = self._get_latest_value(ticker, ANN_CF, c_api_text.FMP_CAPEX, idx=0)

                ni_prev_q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_NI, idx=0)
                ni_prev_2q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_NI, idx=1)
                ni_prev_3q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_NI, idx=2)
                ni_prev_4q = self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_NI, idx=3)
                ni_prev_yr = self._get_latest_value(ticker, ANN_INCOME, c_api_text.FMP_NI, idx=0)
                ni_ttm = ni_prev_q + ni_prev_2q + ni_prev_3q + ni_prev_4q

                payout_r = self._get_latest_value(ticker, RATIO_TTM, c_api_text.FMP_DIV_PR_TTM, idx=0)

                ex_div_dt = self._get_latest_value(ticker, DIV_CAL, c_api_text.FMP_RECORD_DT, idx=0)
                div = self._get_latest_value(ticker, DIV_CAL, c_api_text.FMP_DIV, idx=0)

                # Calc EPS TTM
                eps_ttm = self._get_earnings_cal(ticker, EARNINGS_CAL, c_api_text.FMP_EPS_ACT, beg_n=1, end_n=4)

                # Earnings Date
                next_earnings_date = self._get_latest_value(ticker, EARNINGS_CAL, c_api_text.FMP_DT)
                next_earnings_estimate_eps = self._get_latest_value(ticker, EARNINGS_CAL, c_api_text.FMP_EPS_EST)
                next_earnings_estimate_revenue = self._get_latest_value(ticker, EARNINGS_CAL, c_api_text.FMP_REV_EST)

                # Beat Estimate
                est_eps = self._get_latest_value(ticker, EARNINGS_CAL, c_api_text.FMP_EPS_EST, is_est=False)
                act_eps = self._get_latest_value(ticker, EARNINGS_CAL, c_api_text.FMP_EPS_ACT, is_est=False)
                act_eps_update_date = self._get_latest_value(ticker, EARNINGS_CAL, c_api_text.FMP_DT, is_est=False)
                beat_estimate = self._safe_div(act_eps, est_eps) - 1.0

                # ROIC (Return on Investment Capital)
                ebit_ttm = sum([
                    self._get_latest_value(ticker, QUAR_INCOME, c_api_text.FMP_EBIT, idx=i) for i in range(4)
                ])
                tax_rate = self._get_latest_value(ticker, ANN_RATIO, c_api_text.FMP_EFF_TAX_R)
                total_debt = self._get_latest_value(ticker, QUAR_BALANCE, c_api_text.FMP_TOT_DEBT)
                total_equity = self._get_latest_value(ticker, QUAR_BALANCE, c_api_text.FMP_TOT_EQ)
                cash_equiv = self._get_latest_value(ticker, QUAR_BALANCE, c_api_text.FMP_CNC)
                roic = self._safe_div(ebit_ttm * (1 - tax_rate), total_debt + total_equity - cash_equiv)

                metrics = {
                    c_text.TOT_REV_LAST_Q: tot_rev_prev_q,
                    c_text.GP_LAST_Q: gross_profit_prev_q,
                    c_text.CAPEX_LAST_Y: capex_prev_yr,
                    c_text.NI_LAST_Q: ni_prev_q,
                    c_text.NI_LAST_Y: ni_prev_yr,
                    c_text.NI_TTM: ni_ttm,

                    c_text.EPS_TTM: eps_ttm,
                    c_text.LAST_EX_DIV_DT: ex_div_dt,
                    c_text.LAST_DIV_VAL: div,
                    c_text.ROIC: roic,

                    c_text.PR_TTM: payout_r,
                    c_text.NEXT_EARN_DATE: next_earnings_date,
                    c_text.NEXT_EARN_EST_EPS: next_earnings_estimate_eps,
                    c_text.NEXT_EARN_EST_REV: next_earnings_estimate_revenue,
                    c_text.BEAT_EST: beat_estimate,
                    c_text.BEST_EST_LAST_UPDATE: act_eps_update_date,
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
        if len(self.ticker_ls) == 0:
            return None

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

        raw_data_df = raw_data_df[LayoutOutputData.col_order]

        # Display Raw Data
        st.dataframe(raw_data_df)

        # Format Table
        fmt_data_df = self._format_column(raw_data_df)
        excel = Writer.convert_df_to_excel(fmt_data_df, self.data_layout_dict, percentage_columns=self.pct_col_ls, decimal_columns=self.num_col_ls)

        # Option to download the table
        fmt_dt = dt.datetime.now().strftime('%Y-%m-%d')
        filename = f"financial_data_formatted__{fmt_dt.replace(' ', '_')}.xlsx"
        b64_excel = base64.b64encode(excel).decode()
        href_excel = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_excel}" download="{filename}">Download as Formatted Excel file</a>'
        st.markdown(href_excel, unsafe_allow_html=True)

    def _get_query(self, data_layout_dict):
        # Process Data
        for data_layout in data_layout_dict.values():
            data_layout.batch_process_ticker()

        self.ticker_ls = []
        for data_layout in data_layout_dict.values():
            self.ticker_ls.extend(data_layout.master_ticker_ls)

        st.json(data_layout_dict)
                
        if not self._has_ticket(self.ticker_ls):
            return None
        
        
        # Retrieve data
        self._get_raw_financials_statement()

        # Calculate data
        self._get_basic_info()
        self._get_investment_metrics()
        self._get_investment_risk()
        self._get_valuation()
        self._get_fin()

    def _preload(self):
        CommonLayout.load()

        st.title(c_text.TITLE__FINANCIAL_ANALYSIS)

        value_tab, growth_tab, theme_tab, watchlist_tab = st.tabs([c_text.LABEL__VALUE_STOCK, c_text.LABEL__GROWTH_STOCK,
                                                                   c_text.LABEL__THEME_STOCK, c_text.LABEL__WATCHLIST_STOCK])

        value_data_layout = DataContainer()
        growth_data_layout = DataContainer()
        theme_data_layout = DataContainer()
        watchlist_data_layout = DataContainer()

        self.data_layout_dict = {
            c_text.LABEL__VALUE_STOCK: value_data_layout, 
            c_text.LABEL__GROWTH_STOCK: growth_data_layout, 
            c_text.LABEL__THEME_STOCK: theme_data_layout,
            c_text.LABEL__WATCHLIST_STOCK: watchlist_data_layout,
        }

        with value_tab:
            st.markdown(c_text.INPUT_HINT__TICKER)
            value_data_layout.input_ticker__us = st.text_input(c_text.LABEL__US, value=value_data_layout.input_ticker__us, key='value_stock__us')
            value_data_layout.input_ticker__cn = st.text_input(c_text.LABEL__CN, value=value_data_layout.input_ticker__cn, key='value_stock__cn')
            value_data_layout.input_ticker__jp = st.text_input(c_text.LABEL__JP, value=value_data_layout.input_ticker__jp, key='value_stock__jp')

        with growth_tab:
            st.markdown(c_text.INPUT_HINT__TICKER)
            growth_data_layout.input_ticker__us = st.text_input(c_text.LABEL__US, value=growth_data_layout.input_ticker__us, key='growth_stock__us')
            growth_data_layout.input_ticker__cn = st.text_input(c_text.LABEL__CN, value=growth_data_layout.input_ticker__cn, key='growth_stock__cn')
            growth_data_layout.input_ticker__jp = st.text_input(c_text.LABEL__JP, value=growth_data_layout.input_ticker__jp, key='growth_stock__jp')

        with theme_tab:
            st.markdown(c_text.INPUT_HINT__TICKER)
            theme_data_layout.input_ticker__us = st.text_input(c_text.LABEL__US, value=theme_data_layout.input_ticker__us, key='theme_stock__us')
            theme_data_layout.input_ticker__cn = st.text_input(c_text.LABEL__CN, value=theme_data_layout.input_ticker__cn, key='theme_stock__cn')
            theme_data_layout.input_ticker__jp = st.text_input(c_text.LABEL__JP, value=theme_data_layout.input_ticker__jp, key='theme_stock__jp')

        with watchlist_tab:
            st.markdown(c_text.INPUT_HINT__TICKER)
            watchlist_data_layout.input_ticker__us = st.text_input(c_text.LABEL__US, value=watchlist_data_layout.input_ticker__us, key='watchlist_stock__us')
            watchlist_data_layout.input_ticker__cn = st.text_input(c_text.LABEL__CN, value=watchlist_data_layout.input_ticker__cn, key='watchlist_stock__cn')
            watchlist_data_layout.input_ticker__jp = st.text_input(c_text.LABEL__JP, value=watchlist_data_layout.input_ticker__jp, key='watchlist_stock__jp')


        if st.button(c_text.LABEL__SUBMIT):
            st.divider()
            self._get_query(self.data_layout_dict)
            self._build_downloadable_dataframe()



    def main(self):
        load_dotenv()

        self._preload()
    

fa = FinancialAnalysis()
fa.main()