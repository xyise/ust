import pandas as pd
import lxml.html as lh
import requests
import json
import datetime

kw_security_type_to_cusip_type = {
    'MARKET BASED NOTE': 'Note',
    'MARKET BASED BOND': 'Bond',
    'MARKET BASED BILL': 'Bill',
    'TIPS': 'TIPS',
    'MARKET BASED FRN': 'FRN'
}

a_cusip_keys = ['cusip', 'issueDate', 'securityType', 'securityTerm', 'maturityDate', 'interestRate', 'interestPaymentFrequency', 'spread', 'type']

def read_hist_data_from_treasurydirectgov(dt):
    """get historical data from treasurydirect.gov

        they should provide the data on the following columns: 
            'CUSIP', 'SECURITY TYPE', 'RATE', 'MATURITY DATE', 'CALL DATE', 'BUY',
       'SELL', 'END OF DAY'

        return clean and removed dataframe
    Args:
        dt (datetime)
    """
    year = dt.year
    month = dt.month
    day = dt.day

    args = {
        'priceDate.day': str(day),
        'priceDate.month': str(month),
        'priceDate.year': str(year),
        'submit': 'Show Prices'
    }
    # settings
    num_expected_cols = 8

    # request
    response = requests.post('https://www.treasurydirect.gov/GA-FI/FedInvest/selectSecurityPriceDate.htm', data=args, verify=True)
    doc = lh.fromstring(response.content)
    tr_elements = doc.xpath('//tr')

    # read the table
    table_data = []
    for row in tr_elements:
        if len(row) != num_expected_cols:
            continue
        table_data.append([c.text_content() for c in row])

    # if no data is available, throw an exception
    if len(table_data) == 0:
        date_str = str(datetime.datetime(year, month, day))
        print(date_str + ': no data to retrieve')
        return None

    # put them into a data frame 
    columns = table_data[0]
    data = table_data[1:]
    df = pd.DataFrame(data=data, columns = columns)

    # now clean them
    df = parse_and_clean(df)

    return df

def parse_and_clean(df):
    """parse the raw data from the site and remove data if not clean
    Args:
        df ([type]): dataframe with
    """

    #df['RATE'] = df['RATE'].apply(parse_rate)
    #df['MATURITY DATE'] = pd.to_datetime(df['MATURITY DATE'], format='%m/%d/%Y')
    for c in ['BUY', 'SELL', 'END OF DAY']:
        df[c] = df[c].astype(float)

    return df
    
def parse_rate(x):
    unit = x[-1]
    if unit == '%':
        return float(x[0:-1]) / 100
    else:
         raise Exception('unknown rate type ' + unit)


def get_cusip_info(cusip):

    args = {
        'cusip': cusip, 
        'format': 'json'
    }

    response = requests.get(r'https://www.treasurydirect.gov/TA_WS/securities/search', params=args)

    ainfo = json.loads(response.text)

    # if nothing is find, return None
    if len(ainfo) == 0:
        print('no cusip is found')
        return None

    # pick the one with the first issue date
    ainfo.sort(key = lambda j: j['issueDate'])

    info = ainfo[0]
    for dt_k in ['maturityDate', 'issueDate']:
        info[dt_k] = datetime.datetime.strptime(info[dt_k], '%Y-%m-%dT00:00:00')

    for r_k in ['interestRate', 'spread']:
        if info[r_k] == '':
            info[r_k] = 0.0
        else:
            info[r_k] = float(info[r_k]) / 100.0
            
    return {k:info[k] for k in a_cusip_keys}, ainfo




    


