import requests #instal
import time
import pandas as pd #instal
import numpy as np # install
import http.client #install
import os
from scipy.stats import linregress
from datetime import datetime, timedelta
import matplotlib.ticker as ticker

import urllib # install urllib3
from pytrends.request import TrendReq #Install
import yfinance as yf #Install
import matplotlib #Install
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from scipy.stats import linregress #Install

token_pushover  = ""
user_pushover = ""
one_day_price_change = ""
seven_day_price_change = ""
one_day_profit_limit = ""
output_dir = 'plots'

def get_stock(symbol,period):
    # Fetch historical stock data from Yahoo Finance
    # Attempts multiple tries if data retrieval fails
    # Drops unneeded columns before returning the DataFrame
    df = pd.DataFrame()

    if period =='1mo':
        interval='1h'
    else:
        interval='1d'

    for i in range(5):
        try:
            # Fetch data from Yahoo Finance
            stock = yf.Ticker(symbol)
            df = stock.history(period=period, interval=interval)  # Getting the last 100 days of stock data
            if not df.empty:  # Check whether the retrieval was successful
                break
            else:
                time.sleep(300)
        except Exception as e:
            infos = {'sym': symbol, 'tries': int(i), 'function': 'get_stock','exception': e}
            msg = "Script try number %(tries)s to %(function)s of symbol %(sym)s \n\n%(exception)s" %infos
            pushover(msg) 
            time.sleep(300)
   

    if 'Date' not in df.columns:
        df['Date'] = df.index  # Convert the DatetimeIndex into a 'Date' column

    df = df.tail(100)
    df['Price'] = df['Close']

    df_inverted = df.reset_index(drop=True)

    df_inverted.rename(columns={'index': 'Date'}, inplace=True)

    columns_to_drop = ['Close', 'Open', 'High', 'Low', 'Dividends', 'Stock Splits']
    df_dropped = df_inverted.drop(columns=[col for col in columns_to_drop if col in df_inverted.columns])

    return df_dropped

def get_crypto(symbol,params_historical):
    # Set the API endpoint and parameters for historical data
    url_historical = f'https://api.coingecko.com/api/v3/coins/{symbol}/market_chart'

    for i in range(5):
        try:
            response_historical = requests.get(url_historical, params=params_historical)
            data = response_historical.json()

            if 'prices' in data and data['prices']:
                break
            else:
                time.sleep(300)
        except Exception as e:
            infos = {'sym': symbol, 'tries': i+1, 'function': 'get_crypto', 'exception': e}
            msg = "Script try number %(tries)s to %(function)s of symbol %(sym)s \n\n%(exception)s" % infos
            print(msg)
            time.sleep(300)

    # Extract the data for the last 100 days
    prices = data['prices']
    volumes = data['total_volumes']
    last_100_days_data = {}

    for price, volume in zip(prices, volumes):  # excluding the latest price from the loop
        # Convert timestamp to datetime and shift by one day
        date = pd.Timestamp(price[0], unit='ms')
        last_100_days_data[date.strftime('%Y-%m-%d %H:%M:%S')] = {'Price': price[1], 'Volume': volume[1]}

    # Convert the data to pandas DataFrame for easier analysis
    df = pd.DataFrame(last_100_days_data).T.reset_index()
    df.columns = ['Date', 'Price', 'Volume']

    if len(df) > 100:
        df = df.iloc[:-1]  # Remove the last row to ensure we have only 100 rows

    df['Date'] = pd.to_datetime(df['Date'])
    return df

def calc_indicator_fuctions(df):
   
    # Calculate Fast EMA and Slow EMA
    df['Fast EMA'] = df['Price'].ewm(span=12, adjust=False).mean()
    df['Slow EMA'] = df['Price'].ewm(span=26, adjust=False).mean()
    df['Signal'] = 0.0
    df['Signal'] = np.where(df['Fast EMA'] > df['Slow EMA'], 1.0, 0.0)
    df['Position'] = df['Signal'].diff()
    df['Diff EMA'] = df['Fast EMA'] - df['Slow EMA']

    # Calculate Min Max
    df['High'] = df['Fast EMA'].max()
    df['Low'] = df['Fast EMA'].min()
    df['HighP'] = np.where(df['Fast EMA'] == df['High'], 1, 0)
    df['LowP'] = np.where(df['Fast EMA'] == df['Low'], 1, 0)

    # Calculate the slope of Fast EMA
    df['Fast EMA Slope'] = df['Fast EMA'].diff()

    # Calculate RSI14
    df['RSI14'] = calculate_rsi(df, window=14)
    # Calculate Momentum
    df['Mom10'] = calculate_momentum(df, window=10)
    # Calculate VWMA20
    df['VWMA20'] = calculate_vwma(df, window=20)
    return df


def calculate_rsi(df, window=14):
    delta = df['Price'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=window, min_periods=1).mean()[:window+1]
    avg_loss = loss.rolling(window=window, min_periods=1).mean()[:window+1]

    # Use the formula for the rest of the values
    for i in range(window + 1, len(gain)):
        avg_gain.loc[i] = (avg_gain.loc[i - 1] * (window - 1) + gain.loc[i]) / window
        avg_loss.loc[i] = (avg_loss.loc[i - 1] * (window - 1) + loss.loc[i]) / window

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_momentum(df, window=10):
    momentum = df['Price'] - df['Price'].shift(window)
    return momentum

def calculate_vwma(df, window=20):
    pv = df['Price'] * df['Volume']
    vwma = pv.rolling(window=window).sum() / df['Volume'].rolling(window=window).sum()
    return vwma

def plot_and_save(df, symbol, data_type, zero_line=None):

    matplotlib.use('Agg')  
    fig, ax1 = plt.subplots()

    #Zero line
    df_min = df['Price'].min()
    df_max = df['Price'].max()

    if zero_line is not None:
        if zero_line < df.tail(1)['Price'].values[0]:  
            ax1.set_facecolor('#d0f0d0') #red 
            df['Percentage Deviation'] = df['Price']/zero_line * 100 - 100
        elif zero_line > df.tail(1)['Price'].values[0]:
            ax1.set_facecolor('#f0d0d0') #green
            df['Percentage Deviation'] = df['Price']/zero_line * 100 - 100
        else:
            ax1.set_facecolor('#f0f0f0') #grey
            df['Percentage Deviation'] = df['Price']/zero_line * 100 - 100
        
        if not (zero_line < df_min or zero_line > df_max):
            ax1.axhline(y=zero_line, color='r', linewidth=1, linestyle='-', label=f'Buy at {round(zero_line,2)}€')
        else:
            ax1.axhline(y=df_min, color='r', linestyle='None', label=f'Buy at {round(zero_line,2)} €')

    else:
        ax1.set_facecolor('#f0f0f0') #grey
        mean_price = df['Price'].mean()
        df['Percentage Deviation'] = df['Price']/mean_price * 100 - 100
            
    if data_type == '100h':
        ax1.set_title('100 Hours', fontsize=14)
        ax1.xaxis.set_major_locator(mdates.DayLocator())  # Set ticks at whole days          
    elif data_type == '100d':
        ax1.set_title('100 Days', fontsize=14)
        ax1.xaxis.set_major_locator(mdates.MonthLocator())  # Set ticks at whole days      

    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    ax1.set_ylabel('Price in €')
    plt.ylabel('Price in €', fontsize=12)
    plt.tight_layout()
    for spine in ax1.spines.values():
        spine.set_visible(False)
    ax1.grid(True, color='white')

    # Plot Fast EMA and Slow EMA
    ax1.plot(df['Date'], df['Price'], label='Price',color='k')
    ax1.plot(df['Date'], df['Fast EMA'], label='Fast EMA',linestyle=':')
    ax1.plot(df['Date'], df['Slow EMA'], label='Slow EMA',linestyle=':')
    ax1.plot(df[df['Position'] == 1.0]['Date'], df['Fast EMA'][df['Position'] == 1.0], '^', markersize=10, color='green', label='Buy')
    ax1.plot(df[df['Position'] == -1.0]['Date'], df['Fast EMA'][df['Position'] == -1.0], 'v', markersize=10, color='red', label='Sell')

    # Plot Fast Max Min
    ax1.plot(df[df['HighP'] == 1.0]['Date'], df['Fast EMA'][df['HighP'] == 1.0], 'o', markersize=7, color='red', label='Max')
    ax1.plot(df[df['LowP'] == 1.0]['Date'], df['Fast EMA'][df['LowP'] == 1.0], 'o', markersize=7, color='green', label='Min')

    ax2 = ax1.twinx()
    ax2.plot(df['Date'], df['Percentage Deviation'], color='tab:red', linestyle='None')
    #ax2.set_ylabel('')
    ax2.yaxis.set_major_formatter(mticker.PercentFormatter())

    ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=5, frameon=False)

    output_path = os.path.join(output_dir, symbol + ".png")
    plt.savefig(output_path, bbox_inches='tight')
    matplotlib.pyplot.close()


def get_crypto_price(coin): #in Euro
    url = 'https://api.coingecko.com/api/v3/simple/price?ids={}&vs_currencies=eur'.format(coin)
    
    for i in range(5):
        try:
            response = requests.get(url)
            break
        except Exception as e:
            infos = {'tries': int(i), 'function': 'get_crypto_price','exception': e}
            msg = "Script try number %(tries)s to %(function)s \n\n%(exception)s" %infos
            pushover(msg)
            time.sleep(300)
    
    if response.status_code == 200:
        json_data = response.json()
        price = json_data[coin]['eur']
        return price
    else:
        return -1

def pushover(message):
    
    with open('logfile.txt', 'a') as file:
        now = time.localtime()
        short_date_time = time.strftime("%x %X", now) 
        file.write(short_date_time + '  \n' + message + '\n\n')
    
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
                 urllib.parse.urlencode({
                     "token": token_pushover,
                     "user": user_pushover,
                     "message": message,
                     "url_title" : "Link",
                     "html": 1,  # Enable HTML formatting
                 }), {"Content-type": "application/x-www-form-urlencoded"})
    conn.getresponse()
    
def pushover_image(symbol,message):

    with open('logfile.txt', 'a') as file:
        now = time.localtime()
        short_date_time = time.strftime("%x %X", now) 
        file.write(short_date_time + '  \n' + message + '\n\n')

    file_name = os.path.join(output_dir, symbol + ".png")

    r = requests.post("https://api.pushover.net/1/messages.json", data = {
        "token": token_pushover,
        "user": user_pushover,
        "url_title" : "Link",
        "message": message,
        "html": 1,  # Enable HTML formatting
    },
    files = {
        "attachment": ("image.jpg", open(file_name, "rb"), "image/jpeg")
    })

def google_trends(search):
    
    for i in range(5):
        try:
            pytrends = TrendReq(hl='en-US', tz=360) 
            break
        except Exception as e:
            infos = {'tries': int(i), 'function': __name__,'exception': e}
            msg = "Script try number %(tries)s to %(function)s \n\n%(exception)s" %infos
            pushover(msg)
            time.sleep(300)
    
    kw_list = [search] # list of keywords to get data 
    pytrends.build_payload(kw_list, cat=0, timeframe='today 12-m') #Trend for 12 month
    data = pytrends.interest_over_time() 
    data = data.reset_index() 

    df = pd.DataFrame()
    df = pd.DataFrame(columns=['Datum', 'Interesse'])
    df['Datum'] = data['date']
    df['Interesse'] = data[search]

    return df.tail(1)['Interesse'].values[0], df.tail(2)['Interesse'].values[0]

def seven_day_slope_pct(df, current):
    # Ensure that the DataFrame has at least 8 rows to view both current and previous 7 days
    if len(df) < 8:
        raise ValueError("The DataFrame must contain at least 8 lines.")
    
    y = []

    if current:
        subset_df = df.tail(7)
    else:
        subset_df = df[-8:-1]

    subset_df.reset_index(inplace=True)  # Includes the index in a column called 'index'

    # Linear regression
    try:
        result = linregress(subset_df['index'], subset_df['Price'])
    except Exception as e:
        raise RuntimeError(f"Error in linear regression: {e}")

    steigung = result.slope
    y_achsenabschnitt = result.intercept

    # Calculate the predicted y-values for day 1 and day 7
    y.append(steigung * subset_df['index'].iloc[0] + y_achsenabschnitt)
    y.append(steigung * subset_df['index'].iloc[6] + y_achsenabschnitt)

    # Ensure that y[0] is not 0 to prevent division by zero
    if y[0] == 0:
        raise ValueError("Calculation of the gradient is not possible as y[0] is 0.")

    slope_pct = (y[1] / y[0] - 1)* 100

    return slope_pct


def signal_max_min(value,max,min,sig_count):
    sig = str(round(value,1))
    if value < min: 
        sig += " (buy)"
        sig_count += 1
    elif value > max: 
        sig += " (sell)"
        sig_count += -1
    else: 
        sig += " (neutral)"
        sig_count += 0

    return sig, sig_count

def signal_slope(slope_pct,sig_count):
    
    sig = str(round(slope_pct,1))
    if slope_pct > 2: 
        sig += "% (buy)"
        sig_count += 1
    elif slope_pct < -2: 
        sig += "% (sell)"
        sig_count += -1
    else: 
        sig += "% (neutral)"
        sig_count += 0

    return sig, sig_count


def alarm(df,symbol,watch_list, current_profit_pct, amount_older_than_one_year, amount_older_than_one_year_pct, link, data_type):

    alarms = {}
    signal_count = 0

    RSI14, signal_count= signal_max_min(df['RSI14'].iloc[-1],70,30,signal_count)

    dEMA_pct, signal_count = signal_slope((df['Fast EMA'].iloc[-1] - df['Slow EMA'].iloc[-2])/df['Slow EMA'].iloc[-2]*100,signal_count)

    if df['Mom10'].iloc[-2] != 0:
        dMom10_pct, signal_count = signal_slope((df['Mom10'].iloc[-1] - df['Mom10'].iloc[-2]) / df['Mom10'].iloc[-2] * 100, signal_count)
    else:
        dMom10_pct, signal_count = signal_slope(0, signal_count)  

    dVWMA20_pct, signal_count = signal_slope((df['VWMA20'].iloc[-1] - df['VWMA20'].iloc[-2])/df['VWMA20'].iloc[-2]*100,signal_count)

    current_one_day_price_change_pct = (df['Price'].iloc[-1] - df['Price'].iloc[-2]) / df['Price'].iloc[-2] * 100
    current_EMA_diff_pct = (df['Fast EMA'].iloc[-1] - df['Slow EMA'].iloc[-1]) / df['Slow EMA'].iloc[-1] * 100
    current_seven_days_slope_pct = seven_day_slope_pct(df,True)

    yesterday_EMA_diff_pct = (df['Fast EMA'].iloc[-2] - df['Slow EMA'].iloc[-2]) / df['Slow EMA'].iloc[-2] * 100

    #Watch-list & Portfolio-list
    if yesterday_EMA_diff_pct < 0 and current_EMA_diff_pct > 0 and data_type == "100d":
        alarm_message = "Potential buy {} \nEMA': {} \nRSI14: {} \nMOM10': {} \nVWMA20': {} \n#Cross-EMA ".format(symbol,dEMA_pct, RSI14, dMom10_pct, dVWMA20_pct)
        alarm_symbol = ">&#9650;"
        alarm_symbol_color = "green"
        alarms["101"] = {
            "value": 1,
            "msg": f"<html><body><span style='color: {alarm_symbol_color}; font-size: 24px;'{alarm_symbol}</span><span style='color: black;'>{alarm_message}</span><a href='{link}'>#Technical analysis</a></body></html>"
        }

    if df['LowP'].iloc[-1] < df['LowP'].iloc[-2] and df['LowP'].iloc[-2] > df['LowP'].iloc[-3] and data_type == "100d":
        alarm_message = "Potential buy {} \nEMA': {} \nRSI14: {} \nMOM10': {} \nVWMA20': {} \n#100-Minimum ".format(symbol,dEMA_pct, RSI14, dMom10_pct, dVWMA20_pct)
        alarm_symbol = ">&#9679;"
        alarm_symbol_color = "green"
        alarms["122"] = {
            "value": 1,
            "msg": f"<html><body><span style='color: {alarm_symbol_color}; font-size: 24px;'{alarm_symbol}</span><span style='color: black;'>{alarm_message}</span><a href='{link}'>#Technical analysis</a></body></html>"
        }
        
    #Portfolio-list
    if not watch_list: 
        
        alarm_message_add = "Amount >1 year: {} ({} %)".format(round(amount_older_than_one_year,2),round(amount_older_than_one_year_pct,2))

        if yesterday_EMA_diff_pct > 0 and current_EMA_diff_pct < 0 and data_type == "100d":
            alarm_message = "Potential sell {} \nEMA': {} \nRSI14: {} \nMOM10': {} \nVWMA20': {} \n{} \n#Cross-EMA ".format(symbol,dEMA_pct, RSI14, dMom10_pct, dVWMA20_pct,alarm_message_add)
            alarm_symbol = ">&#9660;"
            alarm_symbol_color = "red"
            alarms["201"] = {
                "value": 1,
                "msg": f"<html><body><span style='color: {alarm_symbol_color}; font-size: 24px;'{alarm_symbol}</span><span style='color: black;'>{alarm_message}</span><a href='{link}'>#Technical analysis</a></body></html>"
            }     

       # if current_profit_pct < one_day_profit_limit and data_type == "100d":
       #     alarm_message = "Potential sell {} \nProfit: {} %\nEMA': {} \nRSI14: {} \nMOM10': {} \nVWMA20': {} \n{} \n#Under buy rate ".format(symbol,round(current_profit_pct,2),dEMA_pct, RSI14, dMom10_pct, dVWMA20_pct,alarm_message_add)
       #     alarm_symbol = ">&#9679;"
       #     alarm_symbol_color = "red"
       #     alarms["202"] = {
       #         "value": current_profit_pct ,
       #         "msg": f"<html><body><span style='color: {alarm_symbol_color}; font-size: 24px;'{alarm_symbol}</span><span style='color: black;'>{alarm_message}</span><a href='{link}'>#Technical analysis</a></body></html>"
       #     }  
        
       # if current_one_day_price_change_pct < (one_day_price_change * -1) and data_type == "100d":
       #     alarm_message = "Potential sell {} \nPrice': {} % \nEMA': {} \nRSI14: {} \nMOM10': {} \nVWMA20': {} \n{} \n#Negative-1 ".format(symbol,round(current_one_day_price_change_pct,2),dEMA_pct, RSI14, dMom10_pct, dVWMA20_pct,alarm_message_add)
       #     alarm_symbol = ">&#9679;"
       #     alarm_symbol_color = "black"
       #     alarms["211"] = {
       #         "value": current_one_day_price_change_pct,
       #         "msg": f"<html><body><span style='color: {alarm_symbol_color}; font-size: 24px;'{alarm_symbol}</span><span style='color: black;'>{alarm_message}</span><a href='{link}'>#Technical analysis</a></body></html>"
       #     }    
        
        if current_seven_days_slope_pct < (seven_day_price_change * -1):
            alarm_message1 = "Potential sell {} \nPrice7': {} % \nEMA': {} \nRSI14: {} \nMOM10': {} \nVWMA20': {} \n{} \n#Negative-7 ".format(symbol,round(current_seven_days_slope_pct,2),dEMA_pct, RSI14, dMom10_pct, dVWMA20_pct,alarm_message_add)
            alarm_message2 = ", ".join(df['Price'].tail(7).round(1).astype(str))
            alarm_message =  alarm_message1 + '\n' + alarm_message2
            alarm_symbol = ">&#9679;"
            alarm_symbol_color = "black"
            alarms["221"] = {
                "value": current_seven_days_slope_pct,
                "msg": f"<html><body><span style='color: {alarm_symbol_color}; font-size: 24px;'{alarm_symbol}</span><span style='color: black;'>{alarm_message}</span><a href='{link}'>#Technical analysis</a></body></html>"
            }  

        if df['HighP'].iloc[-1] < df['HighP'].iloc[-2] and df['HighP'].iloc[-2] > df['HighP'].iloc[-3] and data_type == "100d":
            alarm_message = "Potential sell {} \nEMA': {} \nRSI14: {} \nMOM10': {} \nVWMA20': {} \n{} \n#100-Maximum ".format(symbol,dEMA_pct, RSI14, dMom10_pct, dVWMA20_pct,alarm_message_add)
            alarm_symbol = ">&#9679;"
            alarm_symbol_color = "red"
            alarms["222"] = {
                "value": 1,
                "msg": f"<html><body><span style='color: {alarm_symbol_color}; font-size: 24px;'{alarm_symbol}</span><span style='color: black;'>{alarm_message}</span><a href='{link}'>#Technical analysis</a></body></html>"
            }

        #if current_one_day_price_change_pct > one_day_price_change and data_type == "100d":
        #    alarm_message = "Potential buy {} \nPrice': {} % \nEMA': {} \nRSI14: {} \nMOM10': {} \nVWMA20': {} \n#Positive-1 ".format(symbol,round(current_one_day_price_change_pct,2),dEMA_pct, RSI14, dMom10_pct, dVWMA20_pct)
        #    alarm_symbol = ">&#9679;"
        #    alarm_symbol_color = "black"
        #    alarms["111"] = {
        #        "value": current_one_day_price_change_pct,
        #        "msg": f"<html><body><span style='color: {alarm_symbol_color}; font-size: 24px;'{alarm_symbol}</span><span style='color: black;'>{alarm_message}</span><a href='{link}'>#Technical analysis</a></body></html>"
        #    }

        if current_seven_days_slope_pct > seven_day_price_change:
            alarm_message1 = "Potential buy {} \nPrice7': {} % \nEMA': {} \nRSI14: {} \nMOM10': {} \nVWMA20': {} \n#Positiv-7 ".format(symbol,round(current_seven_days_slope_pct,2),dEMA_pct, RSI14, dMom10_pct, dVWMA20_pct)
            alarm_message2 = ", ".join(df['Price'].tail(7).round(1).astype(str))
            alarm_message =  alarm_message1 + '\n' + alarm_message2
            alarm_symbol = ">&#9679;"
            alarm_symbol_color = "black"
            alarms["121"] = {
                "value": current_seven_days_slope_pct,
                "msg": f"<html><body><span style='color: {alarm_symbol_color}; font-size: 24px;'{alarm_symbol}</span><span style='color: black;'>{alarm_message}</span><a href='{link}'>#Technical analysis</a></body></html>"
            }


    return alarms, signal_count

def older_than_one_year(df):
    current_date = datetime.now()
    one_year_ago = current_date - timedelta(days=365)
    filtered_df = df[df['Date'] < one_year_ago]
    total_amount = filtered_df['Amount'].sum()
    
    return total_amount

