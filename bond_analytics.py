import pandas as pd
import numpy as np
import datetime
import QuantLib as ql

def QLDate(dt: datetime.datetime):
    return ql.Date(dt.day, dt.month, dt.year)

kw_config = {
    'MARKET BASED NOTE':{
        'frequency':ql.Period('6M'),
        'convention':ql.Unadjusted,
        'endOfMonth':True,
        'daycount':ql.ActualActual(), 
        'compound': ql.Compounded, 
        'frequency_for_yield': ql.Semiannual, 
        'settlementDays':2, 
        'faceAmount':100,
    }
}
kw_config['MARKET BASED BOND'] = kw_config['MARKET BASED NOTE']

class USConventional:

    def __init__(self, security_type, 
        dt_start: datetime.datetime, 
        dt_maturity: datetime.datetime, coupon):

        dt_s = QLDate(dt_start)
        dt_e = QLDate(dt_maturity)

        self.bond_config = kw_config[security_type]
        kw = self.bond_config
        self.schedule = ql.MakeSchedule(dt_s, dt_e, 
                kw['frequency'], 
                convention=kw['convention'],
                endOfMonth=kw['endOfMonth'],
                calendar=ql.UnitedStates())
        self.bond = ql.FixedRateBond(kw['settlementDays'], kw['faceAmount'], self.schedule, 
                [coupon], kw['daycount'])
        
    
    def get_yield(self, dt_today: datetime.datetime, clean_price):
        ql.Settings.instance().evaluationDate  = QLDate(dt_today)
        kw = self.bond_config
        y = self.bond.bondYield(clean_price, kw['daycount'], kw['compound'], kw['frequency_for_yield'])
        return y


        
