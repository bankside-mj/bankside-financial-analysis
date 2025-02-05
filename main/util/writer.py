import pandas as pd
from io import BytesIO

class Writer:
    @classmethod
    def convert_df_to_excel(self, df: pd.DataFrame):
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Sheet1')
        writer.close()
        processed_data = output.getvalue()
        return processed_data
    