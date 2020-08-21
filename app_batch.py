from db_manager_UST import *
import datetime
import time
import pandas as pd

def run_me(final_date):
    date_range = pd.date_range(start='2008/06/02', end=final_date)

    dn = db_manager_UST()

    for dt in date_range:
        print('***** ' + str(dt) + ' *****')
        dn.update(dt)
        time.sleep(.5)



if __name__ == '__main__':

    today = datetime.datetime.today()    
    run_me(today)