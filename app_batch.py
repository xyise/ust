from db_manager_UST import *
import datetime
import time
import pandas as pd

def run_me(final_date):
    date_range = pd.date_range(start='2022/06/02', end=final_date)

    dn = db_manager_UST()

    for idx, dt in enumerate(date_range):
        print('***** ' + str(dt) + ' *****')
        dn.update(dt)
        if idx < len(date_range) - 7:
            print('setting the date as confirmed')
            dn._update_confirmed_date(dt, True)
        time.sleep(.5)
        
if __name__ == '__main__':

    today = datetime.datetime.today()    
    run_me(today)