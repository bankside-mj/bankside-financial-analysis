import pandas as pd
from io import BytesIO

from main.data.data_container import DataContainer
from openpyxl import load_workbook

import streamlit as st

class Writer:
    


    @classmethod
    def convert_df_to_excel(self, df: pd.DataFrame, data_layout_dict, percentage_columns=None, decimal_columns=None):
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        for sheetname, data_container in data_layout_dict.items():
            st.json({'data_container': data_container, 'sheetname': sheetname})
            df.to_excel(writer, sheet_name=sheetname, index=False)

            # Access the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets[sheetname]

            percent_format = workbook.add_format({'num_format': '0.0%'})
            one_decimal_format = workbook.add_format({'num_format': '0.0'})
            two_decimal_format = workbook.add_format({'num_format': '#,##0.00'})
            

            # Apply percentage format to specified columns
            if percentage_columns:
                for col in percentage_columns:
                    if col in df.columns:
                        col_idx = df.columns.get_loc(col)
                        worksheet.set_column(col_idx, col_idx, None, percent_format)

            # Apply 2-decimal format to specified columns
            if decimal_columns:
                for col in decimal_columns:
                    if col in df.columns:
                        col_idx = df.columns.get_loc(col)
                        worksheet.set_column(col_idx, col_idx, None, one_decimal_format)

            break

        writer.close()
        processed_data = output.getvalue()
 
        return processed_data
    