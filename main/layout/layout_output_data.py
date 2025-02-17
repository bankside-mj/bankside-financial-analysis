from main.constants import c_text


class LayoutOutputData:
    # (A) Basic Info
    col_basic_info = [
        c_text.COMPANY_NAME, c_text.TICKER, c_text.SECTOR, c_text.CCY, c_text.CUR_PRICE, c_text.MKT_CAP, c_text.BETA,
    ]

    # (B) Investment Metrics
    col_inv_metrics = [
        c_text.MIND_SHARE, c_text.MKT_SHARE, c_text.ROIC,
        c_text.EPS_CAGR_TTM, c_text.EPS_CAGR_3Y_TTM, c_text.EPS_CAGR_5Y_TTM, c_text.EPS_CAGR_10Y_TTM, 
        c_text.REV_CAGR_1Y, c_text.REV_CAGR_3Y, c_text.REV_CAGR_5Y, c_text.REV_CAGR_10Y,
        c_text.GM_TTM, c_text.GM_LAST_Q, c_text.GM_FY1, c_text.GM_FY3,
        c_text.CAPEX_NI_TTM, c_text.CAPEX_NI_5Y_AVG, c_text.CAPEX_NI_10Y_AVG,
        c_text.TRAILING_PE_TTM, c_text.NDTE_LAST_Q, c_text.RR_LAST_FY, c_text.IR_LAST_FY,
        c_text.DIV_YIELD_TTM, c_text.NEXT_EARN_DATE, c_text.NEXT_EARN_EST_EPS, c_text.NEXT_EARN_EST_REV,
        c_text.BEAT_EST, c_text.BEST_EST_LAST_UPDATE,

        c_text.PEG_R_TTM, c_text.ROE_TTM, c_text.ROE_FY3, c_text.PEG_R_FY1, c_text.PEG_R_FY3,
    ]

    # (C) Investment Risks
    col_inv_risks = [
        
    ]

    # (D) Valuation
    col_val = [
        
    ]

    # (E) Financial Ratio
    col_fin_ratio = [
        c_text.TOT_REV_LAST_Q, c_text.GP_LAST_Q,
        c_text.CAPEX_LAST_Y, c_text.NI_TTM, c_text.NI_LAST_Y, c_text.NI_LAST_Q,
        c_text.EPS_TTM, c_text.LAST_EX_DIV_DT, c_text.LAST_DIV_VAL, c_text.PR_TTM, 

    ]

    col_order = col_basic_info + col_inv_metrics + col_inv_risks + col_val + col_fin_ratio
    