import pandas as pd
from io import BytesIO

class Writer:
    # @classmethod
    # def convert_df_to_excel(self, df: pd.DataFrame, has_index=False):
    #     output = BytesIO()
    #     writer = pd.ExcelWriter(output, engine='xlsxwriter')
    #     df.to_excel(writer, sheet_name='Sheet1', index=has_index)
    #     writer.close()
    #     processed_data = output.getvalue()
    #     return processed_data
    
    @classmethod
    def convert_df_to_excel(self, df: pd.DataFrame, has_index=False, percentage_columns=None, decimal_columns=None):
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Sheet1', index=has_index)

        # Access the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        
        # Define formats
        percent_format = workbook.add_format({'num_format': '0.0%'})  # One decimal places in percentage
        decimal_format = workbook.add_format({'num_format': '0.0'})   # One decimal places for numbers

        # Apply percentage format to specified columns
        if percentage_columns:
            for col in percentage_columns:
                if col in df.columns:
                    col_idx = df.columns.get_loc(col) + (1 if has_index else 0)  # Adjust for index presence
                    worksheet.set_column(col_idx, col_idx, None, percent_format)

        # Apply 2-decimal format to specified columns
        if decimal_columns:
            for col in decimal_columns:
                if col in df.columns:
                    col_idx = df.columns.get_loc(col) + (1 if has_index else 0)  # Adjust for index presence
                    worksheet.set_column(col_idx, col_idx, None, decimal_format)

        writer.close()
        processed_data = output.getvalue()
        return processed_data
    