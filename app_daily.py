import sys
import datetime
import time
import pandas as pd
from db_manager_UST import *

        
if __name__ == '__main__':

    dn = db_manager_UST()

    final_date = datetime.date.today() 
    start_date = final_date + datetime.timedelta(
        days=-(dn.confirm_thresholds_in_days+10))

    if len(sys.argv) == 2:
        start_date = datetime.datetime.strptime(sys.argv[1], '%Y%m%d')

    print('start date: ' + str(start_date))
    print('end date: ' + str(final_date))
    
    date_range = pd.date_range(
        start= start_date,
        end=final_date)

    for dt in date_range:
        print('***** ' + str(dt) + ' *****')
        dn.update(dt)
        time.sleep(.005)