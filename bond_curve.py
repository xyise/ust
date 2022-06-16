import numpy as np
import pandas as pd
from db_manager_UST import *
from bond_analytics import *

Conventional_Type = ['Note', 'Bond']

def yield_from_conventional(
    cob: datetime.datetime, 
    df: pd.DataFrame, price_col = 'endOfDay') -> pd.DataFrame:

    df = df.copy()    
    df['Time-to-maturity'] = (df['maturityDate'] - df['date']).dt.days / 365.0
    df['Term'] = (df['maturityDate'] - df['issueDate']).dt.days / 365.0
    df['Coupon'] = [str(r * 100) + '\%' for r in df['interestRate'].values]
    df['Price'] = df[price_col]

    def find_yield(ds):
        bond = USConventional(ds['type'], ds['issueDate'], 
        ds['maturityDate'], ds['interestRate'])
        price = ds['endOfDay'] 
        if price > 0.01:
            y = bond.get_yield(cob, ds['endOfDay'])
        else:
            y = np.nan
        return y

        
    df['Yield'] = df.apply(find_yield, axis=1)

    return df

def plot_backbone_residual(x: np.array, y: np.array):

    pass
