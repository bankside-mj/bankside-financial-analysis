import numpy as np


class Formatter:
    @classmethod
    def format_number(self, n):
        if np.isnan(n):
            return n
        
        if np.abs(n) // 1e9 != 0:
            return f'{n / 1e9:,.1f}B'

        elif np.abs(n) // 1e6 != 0:
            return f'{n / 1e6:,.1f}M'
        
        elif np.abs(n) // 1e3 != 0:
            return f'{n / 1e3:,.1f}K'
        
        return f'{n:,.2f}'
    
    @classmethod
    def format_percentage(self, n):
        if np.isnan(n):
            return n
        return f'{n * 100:.1f}%'