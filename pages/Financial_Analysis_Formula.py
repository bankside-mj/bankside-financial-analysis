import streamlit as st
from main.common.common_layout import CommonLayout
from main.constants import c_text

def get_no_space(txt: str):
    return txt.replace('\n', ' ')

def run():
    CommonLayout.load()
    st.title("Financial Analysis Formula")

    # CAPEX
    st.markdown(f'''
    #### CAPEX / Net Income
    
    1. {get_no_space(c_text.CAPEX_NI_TTM)} $ = \\frac{{ CAPEX~Prev~1Q~+~CAPEX~Prev~2Q~+~CAPEX~Prev~3Q~+~CAPEX~Prev~4Q }}{{ NI~Prev~1Q~+~NI~Prev~2Q~+~NI~Prev~3Q~+~NI~Prev~4Q }} $ 

    2. {get_no_space(c_text.CAPEX_NI_5Y_AVG)} $ = (\\sum^{{5}}_{{n=1}} CAPEX~Prev~N~Year) ~ / ~ (\\sum^{{5}}_{{n=1}} NI~Prev~N~Year) $ 

    2. {get_no_space(c_text.CAPEX_NI_10Y_AVG)} $ = (\\sum^{{10}}_{{n=1}} CAPEX~Prev~N~Year) ~ / ~ (\\sum^{{10}}_{{n=1}} NI~Prev~N~Year) $ 

    Note: CAPEX = Capital Expenditure, NI = Net Income

    ---
    ''')


    # EPS CAGR
    st.markdown(f'''
    #### EPS CAGR
    
    1. {get_no_space(c_text.EPS_CAGR_TTM)} $ = (\\frac{{ EPS~Prev~1Q~+~EPS~Prev~2Q~+~EPS~Prev~3Q~+~EPS~Prev~4Q }}{{ EPS~Prev~5Q~+~EPS~Prev~6Q~+~EPS~Prev~7Q~+~EPS~Prev~8Q }}) - 1.0 $ 

    2. {get_no_space(c_text.EPS_CAGR_3Y_TTM)} $ = (\\frac{{ EPS~Prev~1Q~+~EPS~Prev~2Q~+~EPS~Prev~3Q~+~EPS~Prev~4Q }}{{ EPS~Prev~9Q~+~EPS~Prev~10Q~+~EPS~Prev~11Q~+~EPS~Prev~12Q }}) ^{{ \\frac{{1}}{{3}} }} - 1.0 $ 

    3. {get_no_space(c_text.EPS_CAGR_5Y_TTM)} $ = (\\frac{{ EPS~Prev~1Q~+~EPS~Prev~2Q~+~EPS~Prev~3Q~+~EPS~Prev~4Q }}{{ EPS~Prev~17Q~+~EPS~Prev~18Q~+~EPS~Prev~19Q~+~EPS~Prev~20Q }}) ^{{ \\frac{{1}}{{5}} }} - 1.0 $ 

    4. {get_no_space(c_text.EPS_CAGR_10Y_TTM)} $ = (\\frac{{ EPS~Prev~1Q~+~EPS~Prev~2Q~+~EPS~Prev~3Q~+~EPS~Prev~4Q }}{{ EPS~Prev~37Q~+~EPS~Prev~38Q~+~EPS~Prev~39Q~+~EPS~Prev~40Q }}) ^{{ \\frac{{1}}{{10}} }} - 1.0 $ 

    Note: EPS = Earnings Per Share

    ---
    ''')

    # Gross Margin
    st.markdown(f'''
    #### Gross Margin
    
    1. {get_no_space(c_text.GM_TTM)} $ = \\frac{{ GP~Prev~1Q~+~GP~Prev~2Q~+~GP~Prev~3Q~+~GP~Prev~4Q }}{{ Rev~Prev~1Q~+~Rev~Prev~2Q~+~Rev~Prev~3Q~+~Rev~Prev~4Q }} $
    
    2. {get_no_space(c_text.GM_LAST_Q)} $ = $ Using latest quarter gross profit margin
    
    3. {get_no_space(c_text.GM_FY1)} $ = $ Using previous 1 financial year's gross profit margin
    
    4. {get_no_space(c_text.GM_FY3)} $ = $ Using previous 3 financial year's gross profit margin
    
    5. {get_no_space(c_text.GM_FY5)} $ = $ Using previous 5 financial year's gross profit margin
    
    6. {get_no_space(c_text.GM_FY10)} $ = $ Using previous 10 financial year's gross profit margin
    
    Note: GP = Gross Profit, Rev = Revenue

    ---
    ''')

    st.markdown(f'''
    #### Price to Earnings Growth
                
    1. {get_no_space(c_text.PEG_R_TTM)} $ = $ Using financial ratio ttm's PEG Ratio TTM
    
    2. {get_no_space(c_text.PEG_R_FY1)} $ = \\frac{{ Calculated~PE~TTM }}{{ Calculated~EPS~CAGR~TTM }}  $ 

    3. {get_no_space(c_text.PEG_R_FY3)} $ = \\frac{{ Calculated~PE~TTM }}{{ Calculated~EPS~CAGR~3Y~TTM }}  $ 

    ---
    ''')

    # Revenue CAGR
    st.markdown(f'''
    #### Revenue CAGR
    
    1. {get_no_space(c_text.REV_CAGR_1Y)} $ = \\frac{{ REV~Prev~1Y }}{{ REV~Prev~2Y }} - 1.0 $

    2. {get_no_space(c_text.REV_CAGR_3Y)} $ = \\frac{{ REV~Prev~1Y }}{{ REV~Prev~3Y }} ^{{ \\frac{{1}}{{3}} }} - 1.0 $
    
    3. {get_no_space(c_text.REV_CAGR_5Y)} $ = \\frac{{ REV~Prev~1Y }}{{ REV~Prev~5Y }} ^{{ \\frac{{1}}{{5}} }} - 1.0 $

    4. {get_no_space(c_text.REV_CAGR_10Y)} $ = \\frac{{ REV~Prev~1Y }}{{ REV~Prev~10Y }} ^{{ \\frac{{1}}{{10}} }} - 1.0 $

    Note: REV = Revenue

    ---
    ''')

    # ROE TTM
    st.markdown(f'''
    #### Return on Equity
    
    1. {get_no_space(c_text.ROE_TTM)} $ = \\frac{{ NI~Prev~1Q~+~NI~Prev~2Q~+~NI~Prev~3Q~+~NI~Prev~4Q  }}{{ TE~Prev~1Q }}$ 

    2. {get_no_space(c_text.ROE_FY1)} $ = \\frac{{ NI~Prev~1Y }}{{ TE~Prev~1Y }}$ 
    
    3. {get_no_space(c_text.ROE_FY3)} $ = \\frac{{ NI~Prev~3Y }}{{ TE~Prev~3Y }}$ 

    4. {get_no_space(c_text.ROE_FY5)} $ = \\frac{{ NI~Prev~5Y }}{{ TE~Prev~5Y }}$ 

    5. {get_no_space(c_text.ROE_FY10)} $ = \\frac{{ NI~Prev~10Y }}{{ TE~Prev~10Y }}$ 

    Note: NI = Net Income, TE = Total Equity
    
    ---
    ''')

    # Others
    st.markdown(f'''
    #### Others
                
    01. {get_no_space(c_text.BEAT_EST)} $ = $ Using earnings calendar's latest beat estimate

    02. {get_no_space(c_text.BEAT_EST_LAST_UPDATE)} $ = $ Using earnings calendar's latest update date for beat estimate
                
    03. {get_no_space(c_text.CAPEX_LAST_Y)} $ = $ Using previous 1 financial year's capital expenditure

    04. {get_no_space(c_text.DIV_YIELD_TTM)} $ = $ Using financial ratio ttm's Dividend Yield TTM

    05. {get_no_space(c_text.EPS_TTM)} $ = \\sum^{{4}}_{{n=1}} EPS~Prev~N~Quarter $
    
    06. {get_no_space(c_text.GP_LAST_Q)} $ = $ Using previous 1 financial quarter's gross profit

    07. {get_no_space(c_text.IR_LAST_FY)} $ = \\frac{{ INV~Prev~1Y }}{{ REV~Prev~1Y }} $

    08. {get_no_space(c_text.LAST_DIV_VAL)} $ = $ Using the latest dividend value

    09. {get_no_space(c_text.LAST_EX_DIV_DT)} $ = $ Using the latest ex-dividend date
   
    10. {get_no_space(c_text.NDTE_LAST_Q)} $ = \\frac{{ ND~Prev~1Q  }}{{ TE~Prev~1Q }} $

    11. {get_no_space(c_text.NEXT_EARN_DATE)} $ = $ Using earnings calendar's next earnings date

    12. {get_no_space(c_text.NEXT_EARN_EST_EPS)} $ = $ Using earnings calendar's next earnings estimate EPS

    13. {get_no_space(c_text.NEXT_EARN_EST_REV)} $ = $ Using earnings calendar's next earnings estimate revenue
    
    14. {get_no_space(c_text.NI_LAST_Q)} $ = $ Using previous 1 financial quarter's net income

    15. {get_no_space(c_text.NI_LAST_Y)} $ = $ Using previous 1 financial year's net income
    
    16. {get_no_space(c_text.NI_TTM)} $ = \\sum^{{4}}_{{n=1}} NI~Prev~N~Quarter $
    
    17. {get_no_space(c_text.PR_TTM)} $ = $ Using financial ratio ttm's Dividend Payout Ratio TTM
    
    18. {get_no_space(c_text.ROIC)} $ = \\frac{{ EBIT~TTM \\times (1 - Tax~Rate) }}{{ TD + TE - CASH EQUIV }}  $
    
    19. {get_no_space(c_text.RR_LAST_FY)} $ = \\frac{{ REC~Prev~1Y }}{{ REV~Prev~1Y }} $

    20. {get_no_space(c_text.TOT_REV_LAST_Q)} $ = $ Using previous 1 financial quarter's total revenue

    21. {get_no_space(c_text.TRAILING_PE_TTM)} $ = $ Using financial ratio ttm's PE Ratio TTM

    Note: CASH EQUIV = Cash and Equivalent, INV = Inventory, NI = Net Income, ND = Net Debt, REC = Receivables, REV = Revenue, TE = Total Equity, TD = Total Debt
    
    ---
    ''')
    

run()
