
import os
import sys
import csv
import yfinance as fyf
import numpy as np
import pandas as pd
from datetime import date
from pandas_datareader import data as pdr
import requests
from configinfo import client_id

macslash = '/'
windowslash = r'\\'


# the following function creates new files for user desktop, Windows OS or MacOS
def create_folders_by_system():
    if sys.platform.startswith('win32'):
        create_new_desktop_folder_windows()

    elif sys.platform.startswith('darwin'):
        create_new_desktop_folder_mac()


# the following creates new folder and its subfolders on user desktop for windows OS
def create_new_desktop_folder_windows():

    desktop_path = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    new_path = desktop_path + r'\StockData'
    if not os.path.exists(new_path):
        os.makedirs(new_path)
        print("Created StockData Folder")
    else:
        print("StockData Folder already exists")

    create_subfolders_windows(new_path)

    return new_path


# the following creates 3 subfolders for windows OS
def create_subfolders_windows(path):
    subfolders = [r'\OHLC', r'\Earnings', r'\Merged']

    for f in subfolders:
        if not os.path.exists(path + f):
            os.makedirs(path + f)
        else:
            print(f[1:] + ' already exists')


# the following creates new folder on user desktop for mac OS
def create_new_desktop_folder_mac():
    home = os.path.expanduser("~")
    path = (home + '/Desktop/StockData')
    if os.path.exists(path):
        print("StockData Folder already exists")

    else:
        os.makedirs(path)
        print("Created StockData Folder")
    create_subfolders_mac(path)

    return path


# the following creates 3 subfolders for Mac OS
def create_subfolders_mac(path):
    subfolders = ['/OHLC', '/Earnings', '/Merged']

    for f in subfolders:
        if not os.path.exists(path + str(f)):
            os.makedirs(path + str(f))
        else:
            print(f[1:] + ' already exists')


# The following gets the directory of subfolders
def subfolder_dir(subfolder):
    if sys.platform.startswith('win32'):
        desktop_path = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        subfolder_path = desktop_path + r'\StockData' + r'\\' + str(subfolder)

    elif sys.platform.startswith('darwin'):
        home = os.path.expanduser("~")
        subfolder_path = (home + '/Desktop/StockData/' + str(subfolder))

    return subfolder_path


Today = date.today()


def grab_OHLC_to_csv(ticker):
    ohlc_dir = subfolder_dir('OHLC')

    if sys.platform.startswith('win32'):
        filename = ohlc_dir + '{}'.format(windowslash) + ticker + '_ohlc.csv'
    elif sys.platform.startswith('darwin'):
        filename = ohlc_dir + '{}'.format(macslash) + ticker + '_ohlc.csv'

    data = pdr.get_data_yahoo(ticker, start='1970-1-1', end=Today)
    data.dropna(inplace=True)
    data.to_csv(filename, index=True)


def calc_Vol(ticker):
    ohlc_dir = subfolder_dir('OHLC')

    if sys.platform.startswith('win32'):
        filename = ohlc_dir + '{}'.format(windowslash) + ticker + '_ohlc.csv'
    elif sys.platform.startswith('darwin'):
        filename = ohlc_dir + '{}'.format(macslash) + ticker + '_ohlc.csv'

    file = pd.read_csv(filename)
    file['Volatility'] = file['Adj Close'].rolling(window=30, center=False).std()*np.sqrt(252)
    file.to_csv(filename, index=True)                                               # replacing the previous file.

    return file


def grab_historical_EPS(ticker):
    source = pd.read_html('https://www.macrotrends.net/stocks/charts/' + ticker + '/' + ticker +'/pe-ratio')    # source of the ticker

    # type(source) #check source type 'list'

    earnings_dir = subfolder_dir('Earnings')

    if sys.platform.startswith('win32'):                                                # save location
        filename = earnings_dir + '{}'.format(windowslash) + ticker + '_eps.csv'
    elif sys.platform.startswith('darwin'):
        filename = earnings_dir + '{}'.format(macslash) + ticker + '_eps.csv'

    df = source[0]                                                                      # grabbing the table directly
    df.dropna(inplace=True)                                                             # remove NaN
    df.to_csv(filename, index=False, header=["Date", "Stock_Price", "TTM_Net_EPS", "PE_Ratio"])     # covert dataframe to csv

    # reading the data back in to sort
    data = pd.read_csv(filename)            # reading back the data
    data['Date'] = pd.to_datetime(data['Date'])                     # converting table str to "dates" to be able to sort
    data = data.sort_values(by="Date")                              # sorting
    data.to_csv(filename, index=False)

    return data


# this function reads in OHLC and earnings, loops through columns of OHLC creating a new series with a date index.
# if market data date is less than the eps date then assign EPS
def merge_OHLC_EPS(ticker):
    ohlc_dir = subfolder_dir('OHLC')
    earnings_dir = subfolder_dir('Earnings')
    merged_dir = subfolder_dir('Merged')

    if sys.platform.startswith('win32'):
        filepath1 = ohlc_dir + '{}'.format(windowslash) + ticker + '_ohlc.csv'           # get the 1st file to be edited
        filepath2 = earnings_dir + '{}'.format(windowslash) + ticker + '_eps.csv'           # get 2nd file
        filepath3 = merged_dir + '{}'.format(windowslash) + ticker + '_merged.csv'
    elif sys.platform.startswith('darwin'):
        filepath1 = ohlc_dir + '{}'.format(macslash) + ticker + '_ohlc.csv'
        filepath2 = earnings_dir + '{}'.format(macslash) + ticker + '_eps.csv'
        filepath3 = merged_dir + '{}'.format(macslash) + ticker + '_merged.csv'

    ohlc_data = pd.read_csv(filepath1, index_col=0)  # get the Main File and set indexcolumn to 0
    eps_data = pd.read_csv(filepath2)  # get eps from fps file

    eps = []                # create empty array
    j = 0                   # set beginning step

    for i in ohlc_data.index:           # allow indexing
        while j < len(eps_data) and ohlc_data.loc[i, 'Date'] >= eps_data.loc[j, 'Date']:  # while the date of ohlc is greater than the eps date
            j += 1                      # increment

        if j != 0:                      # checks base case
            j -= 1                      # if passes use the previous

        eps.append(eps_data.loc[j, 'TTM_Net_EPS'])          # appending into empty eps file
        df_eps = pd.DataFrame(eps, columns=["EPS"])         # convert to dataframe to be able to add later

    ohlc_data['EPS'] = df_eps                               # add EPS to the ohlc_data
    ohlc_data.to_csv(filepath3, index=False)                # create a new ohlc_data

    return ohlc_data


# the following calculates the PE ratio
def calc_PE(ticker):
    merged_dir = subfolder_dir('Merged')

    if sys.platform.startswith('win32'):                                                # get the filename
        filename = merged_dir + '{}'.format(windowslash) + ticker + '_merged.csv'
    elif sys.platform.startswith('darwin'):
        filename = merged_dir + '{}'.format(macslash) + ticker + '_merged.csv'

    file = pd.read_csv(filename)                                                        # get the file
    if file['EPS'].dtypes != np.float:
        file['EPS'] = file['EPS'].str.replace('$', '')
    else:
        pass
    file['EPS'] = file.EPS.astype(float)
    file['PE_ratio'] = file['Adj Close']/file['EPS']
    file.to_csv(filename, index=False)                                                 # replacing the previous file.

    return file


# TDAmeritrade API 
def get_quotes(**kwargs):
    
    url = 'https://api.tdameritrade.com/v1/marketdata/quotes'
    
    params = {}
    params.update({'apikey':client_id})
    
    symbol_list = []
    
    for symbol in kwargs.get('symbol'):
        symbol_list.append(symbol)
    params.update({'symbol' : symbol_list})
    
    return requests.get(url,params=params).json()

## method to get lastprice of stock
def get_lastPrice(**kwargs):
    data = get_quotes(symbol=kwargs.get('symbol'))
    for symbol in kwargs.get('symbol'):
        print(symbol)
        print(data[symbol]['lastPrice'])


# get latest EPS from EPS file
def get_latestEPS(ticker):
    earnings_dir = subfolder_dir('Earnings')

    if sys.platform.startswith('win32'):
        filename = earnings_dir + '{}'.format(windowslash) + ticker + '_eps.csv'
    elif sys.platform.startswith('darwin'):
        filename = earnings_dir + '{}'.format(macslash) + ticker + '_eps.csv'

    data = pd.read_csv(filename)
    latestEPS = data['TTM_Net_EPS'][data.index[-1]] #grabs latest EPS from the already created File
    latestEPS = float(latestEPS.replace('$', ''))
    #print(latestEPS)
    #print(type(latestEPS))
    return latestEPS


#calculate current PE - curr share price / last eps
def get_curr_pe(ticker):
    return None

def get_prob(ticker):
    create_folders_by_system()
    grab_OHLC_to_csv(ticker)
    calc_Vol(ticker)
    grab_historical_EPS(ticker)
    merge_OHLC_EPS(ticker)
    calc_PE(ticker)
    get_lastPrice(symbol=[ticker])


def get_allMeans(csv, ticker):
    readdata = csv.reader(open('C:\\desktop\\StockData\\{}merged.csv'.f(ticker), 'r'))
    data = []

    for row in readdata:
      data.append(row)

    #incase you have a header/title in the first row of your csv file, do the next line else skip it
    data.pop(0) 

    q1 = []  

    for i in range(len(data)):
      q1.append(int(data[i][your_column_number]))

    print ('Mean of your_column_number :            ', (np.mean(q1)))


calc_Vol('TSLA')

'''
create_folders_by_system()
grab_OHLC_to_csv('TSLA')
calc_Vol('TSLA')
grab_historical_EPS('TSLA')
merge_OHLC_EPS('TSLA')
calc_PE('TSLA')
get_lastPrice(symbol=['TSLA'])
get_latestEPS('TSLA')
'''


# calculates current PE 
# calculate the mean of PE
# calculate the std of PE
# from scipy.stats import norm
## print(norm.cdf(x, mean, std))

#calc_PE('TSLA')

