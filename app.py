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

    q_financials = stock.quarterly_financials
    q_balance_sheet = stock.quarterly_balance_sheet

    net_debt_to_equity = (
        (q_balance_sheet.loc['Total Debt'][0] - q_balance_sheet.loc['Cash Cash Equivalents And Short Term Investments'][0]) 
        / q_balance_sheet.loc['Stockholders Equity'][0]
    )

    roe_ttm = q_financials.loc['Net Income'][:4].sum() / q_balance_sheet.loc['Stockholders Equity'][0]
    roe_3y = a_financials.loc['Net Income'][2] / a_balance_sheet.loc['Stockholders Equity'][2]

    # st.write(a_financials.sort_index())

    eps_growth_cagr_1y = (a_financials.loc['Basic EPS'][0] / a_financials.loc['Basic EPS'][1]) - 1.0
    eps_growth_cagr_3y = ((a_financials.loc['Basic EPS'][0] / a_financials.loc['Basic EPS'][2]) ** (1/3)) - 1.0
    eps_growth_cagr_4y = ((a_financials.loc['Basic EPS'][0] / a_financials.loc['Basic EPS'][3]) ** (1/4)) - 1.0

    revenue_cagr_1y = (a_financials.loc['Total Revenue'][0] / a_financials.loc['Total Revenue'][1]) - 1.0
    revenue_cagr_3y = ((a_financials.loc['Total Revenue'][0] / a_financials.loc['Total Revenue'][2]) ** (1/3)) - 1.0
    revenue_cagr_4y = ((a_financials.loc['Total Revenue'][0] / a_financials.loc['Total Revenue'][3]) ** (1/4)) - 1.0

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
        'PEG Ratio': info.get('pegRatio'),
        'Trailing EPS (TTM)': info.get('trailingEps'),
        'ROE (TTM)': roe_ttm,
        'ROE (3Y)': roe_3y,
        'Net Debt to Equity (Quarterly)': net_debt_to_equity,

        # Dividend
        '(C) Dividend': None,
        'Dividend Yield': info.get('dividendYield'),
        'Last Dividend Date': info.get('lastDividendDate'),
        'Last Dividend Value': info.get('lastDividendValue'),
        'Payout Ratio': info.get('payoutRatio'),

        # Profitability
        '(D) Profitability': None,
        'Total Revenue (Quarterly)': q_financials.loc['Total Revenue'][0],
        'Gross Profit (Quarterly)': q_financials.loc['Gross Profit'][0],
        'Gross Margin (Quarterly)': q_financials.loc['Gross Profit'][0] / q_financials.loc['Total Revenue'][0],
        'Net Income (Quarterly)': q_financials.loc['Net Income'][0],

        'Revenue CAGR (1Y)': revenue_cagr_1y,
        'Revenue CAGR (3Y)': revenue_cagr_3y,
        'Revenue CAGR (4Y)': revenue_cagr_4y,

        'Gross Margin (TTM)': q_financials.loc['Gross Profit'][:4].sum() / q_financials.loc['Total Revenue'][:4].sum(),
        'Gross Margin (1Y)': a_financials.loc['Gross Profit'][0] / a_financials.loc['Total Revenue'][0],
        'Gross Margin (3Y)': a_financials.loc['Gross Profit'][2] / a_financials.loc['Total Revenue'][2],

        'EPS Growth CAGR (1Y)': eps_growth_cagr_1y,
        'EPS Growth CAGR (3Y)': eps_growth_cagr_3y,
        'EPS Growth CAGR (4Y)': eps_growth_cagr_4y,
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
    if np.isnan(n):
        return n

    if abs(n) // 1e9 != 0:
        return f'{n / 1e9:,.1f}B'

    elif abs(n) // 1e6 != 0:
        return f'{n / 1e6:,.1f}M'
    
    elif abs(n) // 1e3 != 0:
        return f'{n / 1e3:,.1f}K'
    
    return f'{n:,.2f}'

def format_percentage(n):
    if np.isnan(n):
        return n

    return f'{n * 100:.1f}%'

def get_query_parameter(param_name):
    if param_name not in st.query_params.keys():
        return None
    
    query_params = st.query_params[param_name]
    return query_params

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
    result_df['Last Dividend Date'] = result_df['Last Dividend Date'].apply(dt.datetime.fromtimestamp) + dt.timedelta(days=1)
    result_df['Last Dividend Date'] = result_df['Last Dividend Date'].dt.strftime('%Y-%m-%d')
    result_df['Last Dividend Date'] = pd.to_datetime(result_df['Last Dividend Date'])

    formatted_df = result_df.copy()
    formatted_df['Current Price'] = formatted_df['Current Price'].apply(format_number)
    formatted_df['Mkt Cap'] = formatted_df['Mkt Cap'].apply(format_number)

    formatted_df['Trailing PE (TTM)'] = formatted_df['Trailing PE (TTM)'].apply(format_number)
    formatted_df['PEG Ratio'] = formatted_df['PEG Ratio'].apply(format_number)
    formatted_df['Trailing EPS (TTM)'] = formatted_df['Trailing EPS (TTM)'].apply(format_number)
    formatted_df['ROE (TTM)'] = formatted_df['ROE (TTM)'].apply(format_percentage)
    formatted_df['ROE (3Y)'] = formatted_df['ROE (3Y)'].apply(format_percentage)
    formatted_df['Net Debt to Equity (Quarterly)'] = formatted_df['Net Debt to Equity (Quarterly)'].apply(format_percentage)
    
    formatted_df['Dividend Yield'] = formatted_df['Dividend Yield'].apply(format_percentage)
    formatted_df['Last Dividend Date'] = formatted_df['Last Dividend Date'].dt.strftime('%Y-%m-%d')
    formatted_df['Last Dividend Value'] = formatted_df['Last Dividend Value'].apply(format_number)
    formatted_df['Payout Ratio'] = formatted_df['Payout Ratio'].apply(format_number)
    
    formatted_df['Total Revenue (Quarterly)'] = formatted_df['Total Revenue (Quarterly)'].apply(format_number)
    formatted_df['Gross Profit (Quarterly)'] = formatted_df['Gross Profit (Quarterly)'].apply(format_number)
    formatted_df['Gross Margin (Quarterly)'] = formatted_df['Gross Margin (Quarterly)'].apply(format_percentage)
    formatted_df['Net Income (Quarterly)'] = formatted_df['Net Income (Quarterly)'].apply(format_number)

    formatted_df['Revenue CAGR (1Y)'] = formatted_df['Revenue CAGR (1Y)'].apply(format_percentage)
    formatted_df['Revenue CAGR (3Y)'] = formatted_df['Revenue CAGR (3Y)'].apply(format_percentage)
    formatted_df['Revenue CAGR (4Y)'] = formatted_df['Revenue CAGR (4Y)'].apply(format_percentage)

    formatted_df['Gross Margin (TTM)'] = formatted_df['Gross Margin (TTM)'].apply(format_percentage)
    formatted_df['Gross Margin (1Y)'] = formatted_df['Gross Margin (1Y)'].apply(format_percentage)
    formatted_df['Gross Margin (3Y)'] = formatted_df['Gross Margin (3Y)'].apply(format_percentage)
    
    formatted_df['EPS Growth CAGR (1Y)'] = formatted_df['EPS Growth CAGR (1Y)'].apply(format_percentage)
    formatted_df['EPS Growth CAGR (3Y)'] = formatted_df['EPS Growth CAGR (3Y)'].apply(format_percentage)
    formatted_df['EPS Growth CAGR (4Y)'] = formatted_df['EPS Growth CAGR (4Y)'].apply(format_percentage)

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
if user_input is not None and len(user_input) > 0:
    get_result()

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