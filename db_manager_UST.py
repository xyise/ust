import os
import sys
import pathlib
import pandas as pd
import pymongo as mdb
import numpy as np
from access_treasurydirectgov import *

class db_manager_UST:

    def __init__(self,  db_name='UST', host='mongodb://localhost', port=27017):

        # set up the mongo db
        self.db_client = mdb.MongoClient(host=host, port=port)
        self.db_name = db_name
        self.db = self.db_client[db_name]

        self.col_cusip_info = 'cusip info'
        self.col_price_name = 'price data'
        self.col_confirmed_date_name = 'date confirmation'

        self._initialise_collections()

    def _initialise_collections(self):

        #### empty for now.        
        #cols = self.db.list_collection_names()
        return None

    def _update_confirmed_date(self, dt, b_indicator):
        col = self.db[self.col_confirmed_date_name]
        found = col.find_one({'Date':dt})
        if found is None:
            col.insert_one({'Date':dt, 'Confirmed':b_indicator})
        else:
            col.update_one(found, {'$set': {'Confirmed': b_indicator}})

    def update(self, dt):

        # get the confirmation information
        
        col = self.db[self.col_confirmed_date_name]
        confirm_info = col.find_one({'Date':dt})

        if confirm_info is None:
            # no previous data, update
            akw_pd_new = self._read_price_data_from_treasury(dt)
            if akw_pd_new is None:
                print(str(dt) + ': no data in treasury')
                return
            else:
                print(str(dt) + ': new date & new data')
                self.db[self.col_price_name].insert_many(akw_pd_new)
                self.insert_cusip_info_if_required(akw_pd_new)
                self._update_confirmed_date(dt, False)

                return

        isConfirmed = confirm_info['Confirmed']
        if isConfirmed:
            print(str(dt) + ': already confirmed')
            # nothing to do as it is already confirmed
            return

        # now, it is not confirmed. 
        # get the existing data
        akw_pd_new = self._read_price_data_from_treasury(dt)
        akw_pd_ex = list(self.db[self.col_price_name].find({'date':dt}))
        areSame = self._are_same_price_data(akw_pd_ex, akw_pd_new)

        # in either case, update the cusip if missing
        self.insert_cusip_info_if_required(akw_pd_new)

        if areSame:
            print(str(dt) + ': same data. to confirm')
            # update the confirmed date, then do nothing as we have the same data
            self._update_confirmed_date(dt, True)
            print('done')
            return
        else:
            print('delete the existing ones and replace with the new ones and not confirmed')
            # remove the existing ones and replace with the new one
            self.db[self.col_price_name].delete_many({'date': dt})
            self.db[self.col_price_name].insert_many(akw_pd_new)
            self._update_confirmed_date(dt, False)
            print('done')
            return


    def _read_price_data_from_treasury(self, dt):
        df = read_hist_data_from_treasurydirectgov(dt)
        if df is None:
            return None

        df = df[['CUSIP', 'BUY', 'SELL','END OF DAY']].copy()
        df = df.rename(columns = {'CUSIP':'cusip', 'BUY':'buy', 'SELL':'sell', 'END OF DAY':'endOfDay'})
        df['date'] = dt
        return df.to_dict(orient='record')
    
    def _are_same_price_data(self, akw1, akw2):
        key = 'cusip'
        to_compares = ['buy', 'sell', 'endOfDay']

        if len(akw1) != len(akw2):
            return False
        
        df1 = pd.DataFrame(akw1).set_index(key)[to_compares]
        df2 = pd.DataFrame(akw2).set_index(key)[to_compares]
        return np.max(np.abs(df1 - df2).values) < 0.000001

    def insert_cusip_info_if_required(self, akw_price_data):
        for kw_pd in akw_price_data:
            cusip = kw_pd['cusip']
            col = self.db[self.col_cusip_info]
            found = col.find_one({'cusip':cusip})
            if found is None:
                print('adding cusip: ' + cusip)
                kw = get_cusip_info(cusip)[0]
                print(kw)
                col.insert_one(kw)
