import io, os, shutil
from time import sleep, time
import pandas as pd
import lxml.html as lh
import requests
import json
import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as WDW


kw_security_type_to_cusip_type = {
    'MARKET BASED NOTE': 'Note',
    'MARKET BASED BOND': 'Bond',
    'MARKET BASED BILL': 'Bill',
    'TIPS': 'TIPS',
    'MARKET BASED FRN': 'FRN'
}

a_cusip_keys = ['cusip', 'issueDate', 'securityType', 'securityTerm', 'maturityDate', 'interestRate', 'interestPaymentFrequency', 'spread', 'type']

def read_hist_data_from_treasurydirectgov_deprecated(dt):
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

url_price_date = r'https://www.treasurydirect.gov/GA-FI/FedInvest/selectSecurityPriceDate'
url_price_detail = r'https://www.treasurydirect.gov/GA-FI/FedInvest/securityPriceDetail'

def wait_until(somepredicate, timeout, period=0.25, *args, **kwargs):
  mustend = time() + timeout
  while time() < mustend:
    if somepredicate(*args, **kwargs): return True
    sleep(period)
  return False


def read_hist_data_from_treasurydirectgov(
    dt: datetime.datetime, 
    temp_folder, 
    temp_download_folder_tag = "default",
    run_headless = True,
    chromedriver_path = None):

    dn_folder = os.path.join(temp_folder, temp_download_folder_tag + '_' + dt.strftime('%Y%m%d') + '_' + str(int(time())))
    if os.path.exists(dn_folder):
        raise Exception('download folder ' + dn_folder + " already exists. Something is not quite right.")
    os.makedirs(dn_folder)

    options = webdriver.ChromeOptions()
    if run_headless:
        options.add_argument('--headless')
    prefs = {"download.default_directory":dn_folder}    
    options.add_experimental_option("prefs", prefs)

    if chromedriver_path is None:
        driver = webdriver.Chrome(options=options)
    else:
        driver = webdriver.Chrome(executable_path=chromedriver_path, options=options)

    wait_time_out = 15
    wait_variable = WDW(driver, wait_time_out)

    # set the date
    print('setting the date ' + str(dt))
    driver.get(url_price_date)
    box_m = wait_variable.until(EC.presence_of_element_located((By.ID, 'priceDate.month')))
    box_m.clear()
    box_m.send_keys(dt.month)

    box_d = wait_variable.until(EC.presence_of_element_located((By.ID, 'priceDate.day')))
    box_d.clear()
    box_d.send_keys(dt.day)

    box_y = wait_variable.until(EC.presence_of_element_located((By.ID, 'priceDate.year')))
    box_y.clear()
    box_y.send_keys(dt.year)

    btn_sbmt = wait_variable.until(EC.presence_of_element_located((By.NAME, 'submit')))
    btn_sbmt.click()

    # wait until the price detail site
    EC.url_to_be(url_price_detail)

    print('going to the data paging')
    btn_csv = wait_variable.until(EC.presence_of_element_located((By.NAME, 'csv')))
    print('downloading csv')
    btn_csv.click()

    dn_file = os.path.join(dn_folder, 'securityprice.csv')

    wait_until(lambda : os.path.exists(dn_file), timeout = 5.0)
    sleep(0.1) # sleep another interval just in case. 

    columns = ['CUSIP', 'SECURITY TYPE', 'RATE', 'MATURITY DATE', 'CALL DATE', 'BUY', 'SELL', 'END OF DAY']
    with open(dn_file, 'r') as f:
        csv_str = f.read().strip()

    print('deleting the downfolder: ' + dn_folder)
    shutil.rmtree(dn_folder)
    # ensure to remove the folder before sending the data
    wait_until(lambda : not os.path.exists(dn_folder), timeout = 5.0)

    # process the data
    if csv_str == '':
        return None
    else:
        df = pd.read_csv(io.StringIO(csv_str), header=None)
        df.columns = columns
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




    


