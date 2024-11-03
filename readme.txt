# Crypto and Stock Alert - CaSa

## Overview

This project provides a Python-based system for analyzing and monitoring cryptocurrencies and stocks. It uses indicators like Moving Averages, RSI, and EMA to evaluate trends and alert users on significant market conditions. The system can track and visualize data, calculate profits, and send notifications using Pushover.

## Features

- Automatic Data Retrieval:   Fetches crypto data from CoinGecko and stock data from Yahoo Finance.
- Indicator Calculations:     Calculates indicators such as Fast EMA, Slow EMA, RSI, and VWMA for analysis.
- Alarms:                     Sends buy/sell signals based on custom thresholds and market trends.
- Scheduling:                 Configurable scheduling for running hourly and daily analyses.
- Portfolio-list:             In Portfolio-list, the system tracks trends and potential buy and sell signals based on the configured indicators.
- Watch-List:                 In Watch-List, the system tracks trends and potential buy signals based on the configured indicators.

## Project Structure

- classes.py:               Contains the `crypto_stock` class, which manages individual crypto or stock entities, stores transaction data, and processes alarms.
- func.py:                  Utility functions for data retrieval, indicator calculations, alarm handling, and image generation.
- main.py:                  The main script that orchestrates the data analysis process, schedules tasks, and manages notifications.
- config.ini:               Contains a crypto and stock list, alert limits and the API key. Not included in the GitHub structure. Please create this file with the information below.

## Installation

1. Install Python 3
2. Install Dependencies: pip3 install pandas numpy yfinance scipy matplotlib plotly schedule requests pytrends configparser http.client urllib3
3. Create config.ini in root, see #Configuration File section
4. Run the Script: python main.py

Note: I'm using RockPi3 with armbian OS and starting the script over a SSH connection. Over a mapping folder e.g. samba (smb.conf) you can then edit the config.ini.

## Get a Pushover message

- Status message:             Infomation about the program start or errors.
- Potential buy/sell alert:   Review the chart, indicators and external factors to find your decision. The program is only showing a potential you are doing the final decision.
   - Price':                  The 7-day price slope to provide context for the alert.
   - EMA':                    The Slope of the Exponential Moving Average indicator.
   - RSI14:                   The 14-day Relative Strength Index, which shows if an asset is overbought or oversold.
   - MOM10':                  The Slope of the Momentum indicator over a 10-day window, used to assess the speed of price changes.
   - VWMA20':                 The Slope of the 20-day Volume Weighted Moving Average, reflecting the price trend adjusted by trading volume.
   - Amount >1 year:          The quantity of the asset held for more than one year, relevant for long-term position tracking.
   - # [Alert type]:          Indicates the type of alert, such as “#Cross-EMA” for a potential EMA crossover or “#100-Minimum” if the price has reached a 100-day low.
   - # Technical anaysis:     Provides a link or reference to further analysis for deeper insights into the asset’s performance.
- Daily summary:              Overview of all crypto and stock items. Sorted by the Rating. The rating is a number, showing how many indicators are pointing to buy.

## Configuration File (config.ini)

The `config.ini` file should contain sections like `pushover`, `alarm`, `crypto`, and `stocks`. Here’s an example configuration:

[pushover]
token = YOUR_PUSHOVER_TOKEN
user = YOUR_PUSHOVER_USER_KEY

[alarm]
one_day_price_change = 10      #Sets the threshold for a one-day price change alarm in %.
seven_day_price_change = 7   #Sets the threshold for a seven-day price change alarm in %.
one_day_profit_limit = 3      #This is a profitability threshold for a one-day period.
previous_alarm_change = -2     #This parameter defines the minimum change required between consecutive alarm triggers. (currently not active)

[crypto]
bitcoin;Bitcoin;1000,0.05,01/01/2022   #Standard Mode: API ID https://www.coingecko.com/; Displayed name; Investment in €, Quantity; Buy date in DD/MM/YYYY
matic-network = Polygon; 1 , 1, 1      #Watch list mode


[stocks]
AAPL;Apple;1000,10,01/01/2022          #Standard Mode: EURO-Symbol https://finance.yahoo.com/; Displayed name; Investment in €, Quantity, Buy date in DD/MM/YYYY
LHA.DE = Lufthansa; 1, 1, 1            #Watch list mode

## Dependencies

- Python Libraries: `pandas`, `numpy`, `yfinance`, `scipy`, `matplotlib`, `plotly`, `schedule`, `requests`, `pytrends`, `configparser`, `http.client`, `urllib3`
- External API:      Requires access to Pushover (account needed), CoinGecko, and Yahoo Finance APIs. 

---

## License

This project is licensed under the MIT License. 