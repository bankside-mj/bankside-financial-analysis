from collections import defaultdict
import re
import datetime as dt

import numpy as np
import pandas as pd
import streamlit as st
import base64
from io import BytesIO
from urllib.parse import urlparse, parse_qs, quote, unquote

import yfinance as yf

# State
ticker_ls = []
result_df = None

# Util function
def get_financial_stats(ticker):
    stock = yf.Ticker(ticker)

    info = stock.info

    a_financials = stock.financials
    a_balance_sheet = stock.balance_sheet
    a_cash_flow = stock.cash_flow

    q_financials = stock.quarterly_financials
    q_balance_sheet = stock.quarterly_balance_sheet

    #TODO to check if stock dividends got anything
    if not stock.dividends.empty:
        dividend = stock.dividends.iloc[-1]
        payout_ratio = dividend / a_financials.loc['Basic EPS'][0]
    else:
        dividend = np.nan
        payout_ratio = np.nan

    # st.write(info)
    # st.write('Annual')
    # st.write(a_financials.sort_index())
    # st.write(a_balance_sheet.sort_index())

    # st.write('Quarter')
    # st.write(q_financials.sort_index())
    # st.write(q_balance_sheet.sort_index())

    if 'Cash Cash Equivalents And Short Term Investments' in q_balance_sheet.index:
        net_debt_to_equity = (
                    (q_balance_sheet.loc['Total Debt'][0] - q_balance_sheet.loc['Cash Cash Equivalents And Short Term Investments'][0]) 
                    / q_balance_sheet.loc['Stockholders Equity'][0]
                )
    else:
        net_debt_to_equity = np.nan

    if 'Gross Profit' in q_financials.index:
        gross_profit = q_financials.loc['Gross Profit'][0]
        gross_margin = q_financials.loc['Gross Profit'][0] / q_financials.loc['Total Revenue'][0]
        gross_margin_TTM = q_financials.loc['Gross Profit'][:4].sum() / q_financials.loc['Total Revenue'][:4].sum()
        gross_margin_1y = a_financials.loc['Gross Profit'][0] / a_financials.loc['Total Revenue'][0]
        gross_margin_3y =  a_financials.loc['Gross Profit'][2] / a_financials.loc['Total Revenue'][2]
    else: 
        gross_profit = np.nan
        gross_margin = np.nan
        gross_margin_TTM = np.nan
        gross_margin_1y = np.nan
        gross_margin_3y = np.nan

    roe_ttm = q_financials.loc['Net Income'][:4].sum() / q_balance_sheet.loc['Stockholders Equity'][0]
    roe_3y = a_financials.loc['Net Income'][2] / a_balance_sheet.loc['Stockholders Equity'][2]

    eps_growth_cagr_1y = (a_financials.loc['Basic EPS'][0] / a_financials.loc['Basic EPS'][1]) - 1.0
    eps_growth_cagr_3y = ((a_financials.loc['Basic EPS'][0] / a_financials.loc['Basic EPS'][2]) ** (1/3)) - 1.0
    # eps_growth_cagr_4y = ((a_financials.loc['Basic EPS'][0] / a_financials.loc['Basic EPS'][3]) ** (1/4)) - 1.0

    revenue_cagr_1y = (a_financials.loc['Total Revenue'][0] / a_financials.loc['Total Revenue'][1]) - 1.0
    revenue_cagr_3y = ((a_financials.loc['Total Revenue'][0] / a_financials.loc['Total Revenue'][2]) ** (1/3)) - 1.0
    revenue_cagr_4y = ((a_financials.loc['Total Revenue'][0] / a_financials.loc['Total Revenue'][3]) ** (1/4)) - 1.0

    capex = a_cash_flow.loc['Capital Expenditure'][0]

    data = {
        'ID': info.get('shortName'),
        
        # Basic Info
        '(A) Basic Info': None,
        'Ticker': ticker,
        'Sector': info.get('sector'),
        'Currency': info.get('currency'),
        'Current Price': info.get('currentPrice'),
        'Mkt Cap': info.get('marketCap'),

        # Financial Ratio
        '(B) Financial Ratio': None,
        'Trailing PE (TTM)': info.get('trailingPE'),
        'PEG Ratio (1Y)': info.get('trailingPE') / eps_growth_cagr_1y / 100,
        'PEG Ratio (3Y)': info.get('trailingPE') / eps_growth_cagr_3y / 100,
        # 'PEG Ratio (4Y)': info.get('trailingPE') / eps_growth_cagr_4y / 100,

        'Trailing EPS (TTM)': info.get('trailingEps'),
        'ROE (TTM)': roe_ttm,
        'ROE (3Y)': roe_3y,
        'Net Debt to Equity (Quarterly)': net_debt_to_equity,

        # Dividend
        '(C) Dividend': None,
        'Dividend Yield': info.get('dividendYield'),
        'Last Ex-Dividend Date': info.get('exDividendDate'),
        'Last Dividend Value': info.get('dividendRate'),
        'Payout Ratio': payout_ratio,

        # Profitability
        '(D) Profitability': None,
        'Total Revenue (Quarterly)': q_financials.loc['Total Revenue'][0],
        'Gross Profit (Quarterly)': gross_profit,
        'Gross Margin (Quarterly)': gross_margin,
        'Net Income (Quarterly)': q_financials.loc['Net Income'][0],
        'Capital Expenditure': capex,

        'Revenue CAGR (1Y)': revenue_cagr_1y,
        'Revenue CAGR (3Y)': revenue_cagr_3y,
        'Revenue CAGR (4Y)': revenue_cagr_4y,

        'Gross Margin (TTM)': gross_margin_TTM,
        'Gross Margin (1Y)': gross_margin_1y,
        'Gross Margin (3Y)': gross_margin_3y,

        'EPS Growth CAGR (1Y)': eps_growth_cagr_1y,
        'EPS Growth CAGR (3Y)': eps_growth_cagr_3y,
        # 'EPS Growth CAGR (4Y)': eps_growth_cagr_4y,
    }

    return data

def convert_df_to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    writer.close()
    processed_data = output.getvalue()
    return processed_data

def format_number(n):
    if pd.isna(n):
        return n
    
    if np.abs(n) // 1e9 != 0:
        return f'{n / 1e9:,.1f}B'

    elif np.abs(n) // 1e6 != 0:
        return f'{n / 1e6:,.1f}M'
    
    elif np.abs(n) // 1e3 != 0:
        return f'{n / 1e3:,.1f}K'
    
    return f'{n:,.2f}'

def format_percentage(n):
    if pd.isna(n):
        return n
    return f'{n * 100:.1f}%'

def get_query_parameter(param_name):
    if param_name not in st.query_params.keys():
        return None
    
    query_params = st.query_params[param_name]
    return query_params

def convert_timestamp(x):
    if pd.notnull(x):  # Check if the value is not None/NaN
        return dt.datetime.fromtimestamp(x) + dt.timedelta(days=1)
    return None  # Return None if the value is None/NaN

def get_result():
    ticker_ls = re.split(',|;', user_input)
    ticker_ls = [t.upper().strip() for t in ticker_ls]

    cur_dt = dt.datetime.now()
    fmt_dt = cur_dt.strftime('%Y-%m-%d %H:%M:%S')
    
    st.write(f"Last updated {fmt_dt}")
    st.markdown('---')
    st.write(f"Selected tickers: {', '.join(ticker_ls)}")

    result = defaultdict(list)
    for t in ticker_ls:
        stats = get_financial_stats(t)

        for k, v in stats.items():
            result[k].append(v)

    # Formatted 
    result_df = pd.DataFrame(result).set_index('ID')
    result_df['Last Ex-Dividend Date'] = result_df['Last Ex-Dividend Date'].apply(convert_timestamp)
    result_df['Last Ex-Dividend Date'] = pd.to_datetime(result_df['Last Ex-Dividend Date'], errors='coerce')
    result_df['Last Ex-Dividend Date'] = result_df['Last Ex-Dividend Date'].dt.strftime('%Y-%m-%d')
    result_df['Last Ex-Dividend Date'] = pd.to_datetime(result_df['Last Ex-Dividend Date'])

    # result_df.fillna(-np.inf, inplace=True)

    formatted_df = result_df.copy()
    formatted_df['Current Price'] = formatted_df['Current Price'].apply(format_number)
    formatted_df['Mkt Cap'] = formatted_df['Mkt Cap'].apply(format_number)

    formatted_df['Trailing PE (TTM)'] = formatted_df['Trailing PE (TTM)'].apply(format_number)
    # formatted_df['PEG Ratio'] = formatted_df['PEG Ratio'].apply(format_number)
    formatted_df['PEG Ratio (1Y)'] = formatted_df['PEG Ratio (1Y)'].apply(format_number)
    formatted_df['PEG Ratio (3Y)'] = formatted_df['PEG Ratio (3Y)'].apply(format_number)
    # formatted_df['PEG Ratio (4Y)'] = formatted_df['PEG Ratio (4Y)'].apply(format_number)
    formatted_df['Trailing EPS (TTM)'] = formatted_df['Trailing EPS (TTM)'].apply(format_number)
    formatted_df['ROE (TTM)'] = formatted_df['ROE (TTM)'].apply(format_percentage)
    formatted_df['ROE (3Y)'] = formatted_df['ROE (3Y)'].apply(format_percentage)
    #formatted_df['Net Debt to Equity (Quarterly)'] = formatted_df['Net Debt to Equity (Quarterly)'].apply(format_percentage)
    formatted_df['Net Debt to Equity (Quarterly)'] = formatted_df['Net Debt to Equity (Quarterly)'].apply(format_number)
    
    formatted_df['Dividend Yield'] = formatted_df['Dividend Yield'].apply(format_percentage)
    formatted_df['Last Ex-Dividend Date'] = formatted_df['Last Ex-Dividend Date'].dt.strftime('%Y-%m-%d')
    formatted_df['Last Dividend Value'] = formatted_df['Last Dividend Value'].apply(format_number)
    formatted_df['Payout Ratio'] = formatted_df['Payout Ratio'].apply(format_number)
    
    formatted_df['Total Revenue (Quarterly)'] = formatted_df['Total Revenue (Quarterly)'].apply(format_number)
    formatted_df['Gross Profit (Quarterly)'] = formatted_df['Gross Profit (Quarterly)'].apply(format_number)
    formatted_df['Gross Margin (Quarterly)'] = formatted_df['Gross Margin (Quarterly)'].apply(format_number)
    formatted_df['Net Income (Quarterly)'] = formatted_df['Net Income (Quarterly)'].apply(format_number)
    formatted_df['Capital Expenditure'] = formatted_df['Capital Expenditure'].apply(format_number)

    formatted_df['Revenue CAGR (1Y)'] = formatted_df['Revenue CAGR (1Y)'].apply(format_percentage)
    formatted_df['Revenue CAGR (3Y)'] = formatted_df['Revenue CAGR (3Y)'].apply(format_percentage)
    formatted_df['Revenue CAGR (4Y)'] = formatted_df['Revenue CAGR (4Y)'].apply(format_percentage)

    formatted_df['Gross Margin (TTM)'] = formatted_df['Gross Margin (TTM)'].apply(format_percentage)
    formatted_df['Gross Margin (1Y)'] = formatted_df['Gross Margin (1Y)'].apply(format_percentage)
    formatted_df['Gross Margin (3Y)'] = formatted_df['Gross Margin (3Y)'].apply(format_percentage)
    
    formatted_df['EPS Growth CAGR (1Y)'] = formatted_df['EPS Growth CAGR (1Y)'].apply(format_percentage)
    formatted_df['EPS Growth CAGR (3Y)'] = formatted_df['EPS Growth CAGR (3Y)'].apply(format_percentage)
    # formatted_df['EPS Growth CAGR (4Y)'] = formatted_df['EPS Growth CAGR (4Y)'].apply(format_percentage)

    # Display the table
    st.dataframe(formatted_df.T, height=1180)

    # Option to download the table
    filename = f"financial_data__{fmt_dt.replace(' ', '_')}.xlsx"

    excel = convert_df_to_excel(result_df.T)
    b64_excel = base64.b64encode(excel).decode()
    href_excel = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_excel}" download="{filename}">Download as Excel file</a>'
    st.markdown(href_excel, unsafe_allow_html=True)

# Page config
st.set_page_config(
    page_title="Financial Analysis",
    layout='wide'
)

st.markdown(
    """
    <style>
    .reportview-container .main .block-container{
        max-width: 100%;
        padding-top: 0rem;
        padding-right: 1rem;
        padding-left: 1rem;
        padding-bottom: 0rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Title and Header
st.title("Financial Analysis")

# Sidebar
st.sidebar.header("Company Ticker List")

default_value = get_query_parameter('tickers')
if default_value:
    default_value = unquote(default_value)

user_input = st.sidebar.text_input("Enter Yahoo Finance ticker, separate with comma", value=default_value)

if st.sidebar.button('Submit'):
    get_result()


    # TODO to show all the result
    # stock = yf.Ticker(ticker_ls[0])
    # company_info = stock.info
    # a_financials = stock.financials
    # a_balance_sheet = stock.balance_sheet
    # a_cashflow = stock.cashflow
    # a_earnings = stock.earnings

    # q_financials = stock.quarterly_financials
    # q_balance_sheet = stock.quarterly_balance_sheet
    # q_cashflow = stock.quarterly_cashflow
    # q_earnings = stock.quarterly_earnings

    # st.write("quarterly company_info:", company_info)
    # st.write("quarterly financials:", q_financials.sort_index())
    # st.write("quarterly balance_sheet:", q_balance_sheet.sort_index())
    # st.write("quarterly cashflow:", q_cashflow.sort_index())
    # st.write("quarterly earnings:", q_earnings.sort_index())

    # st.write("annual financials:", a_financials.sort_index())
    # st.write("annual balance_sheet:", a_balance_sheet.sort_index())
    # st.write("annual cashflow:", a_cashflow.sort_index())
    # st.write("annual earnings:", a_earnings.sort_index())