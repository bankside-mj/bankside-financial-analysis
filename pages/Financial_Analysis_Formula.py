import streamlit as st
from main.common.common_layout import CommonLayout
from main.constants import c_text


def run():
    CommonLayout.load()
    st.title("Financial Analysis Formula")

    # EPS CAGR
    st.markdown(f'''
    #### EPS CAGR
    
    1. {c_text.EPS_CAGR_TTM} $ = (\\frac{{ EPS~Prev~1Q~+~EPS~Prev~2Q~+~EPS~Prev~3Q~+~EPS~Prev~4Q }}{{ EPS~Prev~5Q~+~EPS~Prev~6Q~+~EPS~Prev~7Q~+~EPS~Prev~8Q }}) - 1.0 $ 

    2. {c_text.EPS_CAGR_3Y_TTM} $ = (\\frac{{ EPS~Prev~1Q~+~EPS~Prev~2Q~+~EPS~Prev~3Q~+~EPS~Prev~4Q }}{{ EPS~Prev~9Q~+~EPS~Prev~10Q~+~EPS~Prev~11Q~+~EPS~Prev~12Q }}) ^{{ \\frac{{1}}{{3}} }} - 1.0 $ 

    3. {c_text.EPS_CAGR_5Y_TTM} $ = (\\frac{{ EPS~Prev~1Q~+~EPS~Prev~2Q~+~EPS~Prev~3Q~+~EPS~Prev~4Q }}{{ EPS~Prev~17Q~+~EPS~Prev~18Q~+~EPS~Prev~19Q~+~EPS~Prev~20Q }}) ^{{ \\frac{{1}}{{5}} }} - 1.0 $ 

    4. {c_text.EPS_CAGR_10Y_TTM} $ = (\\frac{{ EPS~Prev~1Q~+~EPS~Prev~2Q~+~EPS~Prev~3Q~+~EPS~Prev~4Q }}{{ EPS~Prev~37Q~+~EPS~Prev~38Q~+~EPS~Prev~39Q~+~EPS~Prev~40Q }}) ^{{ \\frac{{1}}{{10}} }} - 1.0 $ 

    ---
    ''')

    # Gross Margin
    st.markdown(f'''
    #### Gross Margin
    
    1. {c_text.GM_TTM} $ = \\frac{{ GP~Prev~1Q~+~GP~Prev~2Q~+~GP~Prev~3Q~+~GP~Prev~4Q }}{{ Rev~Prev~1Q~+~Rev~Prev~2Q~+~Rev~Prev~3Q~+~Rev~Prev~4Q }}$
    
    2. {c_text.GM_LAST_Q} $ = $ Using latest quarter gross profit margin
    
    3. {c_text.GM_FY1} $ = $ Using previous 1 financial year's gross profit margin
    
    4. {c_text.GM_FY3} $ = $ Using previous 3 financial year's gross profit margin
    
    5. {c_text.GM_FY5} $ = $ Using previous 5 financial year's gross profit margin
    
    6. {c_text.GM_FY10} $ = $ Using previous 10 financial year's gross profit margin
    
    Note: GP = Gross Profit, Rev = Revenue

    ---
    ''')

    # ROE TTM
    st.markdown(f'''
    #### Return on Investment
    
    1. {c_text.ROE_TTM} $ = \\frac{{ NI~Prev~1Q~+~NI~Prev~2Q~+~NI~Prev~3Q~+~NI~Prev~4Q  }}{{ TE~Prev~1Q }}$ 

    2. {c_text.ROE_FY1} $ = \\frac{{ NI~Prev~1Y  }}{{ TE~Prev~1Y }}$ 
    
    3. {c_text.ROE_FY3} $ = \\frac{{ NI~Prev~3Y  }}{{ TE~Prev~3Y }}$ 

    4. {c_text.ROE_FY5} $ = \\frac{{ NI~Prev~5Y  }}{{ TE~Prev~5Y }}$ 

    5. {c_text.ROE_FY10} $ = \\frac{{ NI~Prev~10Y  }}{{ TE~Prev~10Y }}$ 

    Note: NI = Net Income, TE = Total Equity
    
    ''')
    

run()
