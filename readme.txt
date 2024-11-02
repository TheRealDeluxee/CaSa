# Crypto and Stock Alert

## Overview

This project provides a Python-based system for analyzing and monitoring cryptocurrencies and stocks. It uses indicators like Moving Averages, RSI, and EMA to evaluate trends and alert users on significant market conditions. The system can track and visualize data, calculate profits, and send notifications using Pushover.

## Features

- **Automatic Data Retrieval**: Fetches crypto data from CoinGecko and stock data from Yahoo Finance.
- **Indicator Calculations**: Calculates indicators such as Fast EMA, Slow EMA, RSI, and VWMA for analysis.
- **Alarms**: Sends buy/sell signals based on custom thresholds and market trends.
- **Scheduling**: Configurable scheduling for running hourly and daily analyses.
- **Standard Mode: In Standard Mode, the system tracks trends and potential buy and sell signals based on the configured indicators.
- **Watch List Mode: In Watch list mode, the system tracks trends and potential buy signals based on the configured indicators.

## Project Structure

- `classes.py`: Contains the `crypto_stock` class, which manages individual crypto or stock entities, stores transaction data, and processes alarms.
- `func.py`: Utility functions for data retrieval, indicator calculations, alarm handling, and image generation.
- `main.py`: The main script that orchestrates the data analysis process, schedules tasks, and manages notifications.

## Installation

1. **Install Dependencies**:

   pip install pandas numpy yfinance scipy matplotlib plotly schedule requests pytrends configparser

   
2. **Configuration**:

   - Update the `config.ini` file with your API credentials for Pushover and configure the threshold values for alarms.

## Usage

1. **Run the Script**:
   python main.py


2. **Scheduled Tasks**:
   - The script automatically performs:
     - **Hourly Analysis**: Runs `hundred_hour_analysis()` every hour.
     - **Daily Analysis**: Runs `hundred_day_analysis()` twice daily.
     - **Configuration Reload**: Reloads configuration daily.
     - **Daily Summary**: Sends a daily summary.

## Configuration File (config.ini)

The `config.ini` file should contain sections like `pushover`, `alarm`, `crypto`, and `stocks`. Here’s an example configuration:

```ini
[pushover]
token = YOUR_PUSHOVER_TOKEN
user = YOUR_PUSHOVER_USER_KEY

[alarm]
one_day_price_change = 10      #Sets the threshold for a one-day price change alarm in %.
seven_day_price_change = 7   #Sets the threshold for a seven-day price change alarm in %.
one_day_profit_limit = 3      #This is a profitability threshold for a one-day period.
previous_alarm_change = -2     #This parameter defines the minimum change required between consecutive alarm triggers. (currently deactive)

[crypto]
bitcoin;Bitcoin;1000,0.05,01/01/2022   #Standard Mode: API ID https://www.coingecko.com/; Displayed name; Investment in €, Quanity; Buy date in DD/MM/YYYY
matic-network = Polygon; 1 , 1, 1      #Watch list mode


[stocks]
AAPL;Apple;1000,10,01/01/2022          #Standard Mode: EURO-Symbol https://finance.yahoo.com/; Displayed name; Investment in €, Quanity, Buy date in DD/MM/YYYY
LHA.DE = Lufthansa; 1, 1, 1            #Watch list mode

- **Crypto and Stocks Sections**: Each entry contains the symbol, name, and transactions in the format `amount,quantity,date`.

## Dependencies

- **Python Libraries**: `pandas`, `numpy`, `yfinance`, `scipy`, `matplotlib`, `plotly`, `schedule`, `requests`, `pytrends`, `configparser`, `http.client`, `urllib3`
- **External API**: Requires Pushover account

---

## License

This project is licensed under the MIT License. 