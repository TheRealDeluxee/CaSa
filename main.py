import configparser
import classes as cl
import pandas as pd
import plotly.figure_factory as ff
import os
import time
import func
import schedule
import sys
import subprocess

class CryptoStockManager:
    def __init__(self, config_file_path, test_mode=False, output_dir='plots'):
        self.config_file_path = config_file_path
        self.test_mode = test_mode
        self.output_dir = output_dir
        self.df_crypto_hd = pd.DataFrame(columns=['Name', 'Piece [€]', 'Profit [€]', 'Profit [%]', '7 days [%]', '1 day [%]', 'dEMA [%]', 'Rating'])
        self.df_stock_hd = pd.DataFrame(columns=['Name', 'Piece [€]', 'Profit [€]', 'Profit [%]', '7 days [%]', '1 day [%]', 'dEMA [%]', 'Rating'])
        self.df_crypto_hh = pd.DataFrame(columns=['Name', 'Piece [€]', 'Profit [€]', 'Profit [%]', '7 Hours [%]', '1 Hour [%]', 'dEMA [%]', 'Rating'])
        self.df_stock_hh = pd.DataFrame(columns=['Name', 'Piece [€]', 'Profit [€]', 'Profit [%]', '7 Hours [%]', '1 Hour [%]', 'dEMA [%]', 'Rating'])

        self.crypto_items = []
        self.stock_items = []

        self.stock_update = False
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.load_config()

    def load_config(self):
        self.crypto_items = []
        self.stock_items = []
        config = configparser.ConfigParser()
        if not config.read(self.config_file_path):
            raise FileNotFoundError(f"Die INI-Datei '{self.config_file_path}' konnte nicht gefunden oder geladen werden.")

        try:
            func.token_pushover = config.get('pushover', 'token')
            func.user_pushover = config.get('pushover', 'user')
            func.one_day_price_change = int(config.get('alarm', 'one_day_price_change'))
            func.seven_day_price_change = int(config.get('alarm', 'seven_day_price_change'))
            func.one_day_profit_limit = int(config.get('alarm', 'one_day_profit_limit'))
            self.previous_alarm_change = int(config.get('alarm', 'previous_alarm_change'))
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            print(f"Fehler in der Konfiguration: {e}")

        if "crypto" in config.sections():
            crypto_config_items = config.items("crypto")
            self.load_crypto_items(crypto_config_items)
        else:
            print("Fehler: Abschnitt 'crypto' fehlt in der INI-Datei.")

        if "stocks" in config.sections():
            stock_config_items = config.items("stocks")
            self.load_stock_items(stock_config_items)
        else:
            print("Fehler: Abschnitt 'stocks' fehlt in der INI-Datei.")

    def load_crypto_items(self, crypto_config_items):
        for crypto, transactions in crypto_config_items:
            try:
                name, transaction_data = transactions.split(";", 1)
                crypto_obj = cl.crypto_stock(crypto, name.strip(), 'crypto', self.previous_alarm_change)
                self.crypto_items.append(crypto_obj)
                
                for transaction in transaction_data.split(";"):
                    try:
                        spend_str, quantity_str, date_str = transaction.strip().split(",")
                        spend = float(spend_str)
                        quantity = float(quantity_str)
                        date = date_str.strip()
                        crypto_obj.buy(spend, quantity, date)
                    except ValueError:
                        print(f"Fehler beim Parsen von spend oder quantity für {name}")
            except ValueError:
                print(f"Fehler beim Parsen der Transaktionsdaten für {crypto}")

    def load_stock_items(self, stock_config_items):
        for stock, transactions in stock_config_items:
            try:
                name, transaction_data = transactions.split(";", 1)
                stock_obj = cl.crypto_stock(stock, name.strip(), 'stock', self.previous_alarm_change)
                self.stock_items.append(stock_obj)

                for transaction in transaction_data.split(";"):
                    try:
                        spend_str, quantity_str, date_str = transaction.strip().split(",")
                        spend = float(spend_str)
                        quantity = float(quantity_str)
                        date = date_str.strip()
                        stock_obj.buy(spend, quantity, date)
                    except ValueError:
                        print(f"Fehler beim Parsen von spend oder quantity für {name}")
            except ValueError:
                print(f"Fehler beim Parsen der Transaktionsdaten für {stock}")

    def restart_program(self):
        python = sys.executable
        return_code = subprocess.call([python] + sys.argv)
        if return_code != 0:
            print(f"Warning: Restart failed with return code {return_code}")

    def schedule_on_weekdays(self):
        now = time.localtime()
        current_day = time.strftime("%A", now)
        current_hour = now.tm_hour
        self.stock_update = False

        if current_day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]: #Sunday
            if current_hour >= 8 and current_hour < 22:
                self.stock_update = True

    def hundred_day_analysis(self):
        now = time.localtime()
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", now)

        print(f"Hundred day analysis started: {current_time}")

        self.df_crypto_hd = self.df_crypto_hd[0:0]
        self.df_stock_hd = self.df_stock_hd[0:0]

        self.schedule_on_weekdays()
        if self.stock_update:
            for item in self.stock_items:
                if self.test_mode: item.activate_test_mode()
                self.df_stock_hd.loc[len(self.df_stock_hd)] = item.refresh('100d')

        for item in self.crypto_items:
            if self.test_mode: item.activate_test_mode()
            self.df_crypto_hd.loc[len(self.df_crypto_hd)] = item.refresh('100d')
        #func.pushover("Hundred day analysis complete")

    def hundred_hour_analysis(self): 
        now = time.localtime()
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", now)

        print(f"Hundred hour analysis started: {current_time}")

        self.df_crypto_hh = self.df_crypto_hh[0:0]
        self.df_stock_hh = self.df_stock_hh[0:0]

        self.schedule_on_weekdays()
        if self.stock_update:
            for item in self.stock_items:
                if self.test_mode: item.activate_test_mode()
                self.df_stock_hh.loc[len(self.df_stock_hh)] = item.refresh('100h')

        for item in self.crypto_items:
            if self.test_mode: item.activate_test_mode()
            self.df_crypto_hh.loc[len(self.df_crypto_hh)] = item.refresh('100h')
            
        #func.pushover("Hundred hour analysis complete")

    def send_summary(self):
        now = time.localtime()

        self.df_crypto_hd = self.df_crypto_hd.sort_values(by=['Rating'], ascending=False)
        self.df_stock_hd = self.df_stock_hd.sort_values(by=['Rating'], ascending=False)

        if not self.df_crypto_hd.empty:
            self.df_crypto_hd.loc[len(self.df_crypto_hd)] = [
                'Total', '-', 
                self.df_crypto_hd['Profit [€]'].sum(), 
                self.df_crypto_hd['Profit [%]'].mean(), 
                self.df_crypto_hd['7 days [%]'].mean(), 
                self.df_crypto_hd['1 day [%]'].mean(), 
                self.df_crypto_hd['dEMA [%]'].mean(), '-'
            ]

        print(f"\nLast refresh {time.asctime(now)}")
        print(self.df_crypto_hd.round(2))

        if self.stock_update and not self.df_stock_hd.empty:
            self.df_stock_hd.loc[len(self.df_stock_hd)] = [
                'Total', '-', 
                self.df_stock_hd['Profit [€]'].sum(), 
                self.df_stock_hd['Profit [%]'].mean(), 
                self.df_stock_hd['7 days [%]'].mean(), 
                self.df_stock_hd['1 day [%]'].mean(), 
                self.df_stock_hd['dEMA [%]'].mean(), '-'
            ]
            print('\n')
            print(self.df_stock_hd.round(2))

        # Send daily summary
        try:
            output_path = os.path.join(self.output_dir, 'summary_crypto.png')
            fig = ff.create_table(self.df_crypto_hd.round(2))
            fig.update_layout(autosize=True)
            fig.write_image(output_path, scale=2)
            func.pushover_image('summary_crypto', 'Daily summary crypto')
        except AttributeError:
            print("Error: `pushover_image` function is not defined in `func`")

        if self.stock_update:
            try:
                output_path = os.path.join(self.output_dir, 'summary_stock.png')
                fig = ff.create_table(self.df_stock_hd.round(2))
                fig.update_layout(autosize=True)
                fig.write_image(output_path, scale=2)
                func.pushover_image('summary_stock', 'Daily summary stock')
            except AttributeError:
                print("Error: `pushover_image` function is not defined in `func`")


# Initialize the manager
manager = CryptoStockManager(config_file_path="config.ini")
func.pushover("Initialization complete")

start_time = time.time()  # Define start_time here
manager.hundred_hour_analysis() #Test
manager.hundred_hour_analysis() #Test
manager.hundred_day_analysis() #Test

# Schedule tasks
schedule.every().hour.do(manager.hundred_hour_analysis)          
schedule.every().day.at("09:30").do(manager.hundred_day_analysis)
schedule.every().day.at("12:30").do(manager.hundred_day_analysis)
schedule.every().day.at("00:30").do(lambda: manager.load_config())
schedule.every().day.at("18:30").do(manager.send_summary)

while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except KeyboardInterrupt:
        break
    except configparser.NoSectionError as e:
        func.pushover(f"Konfigurationsfehler: {e}")
        break
    except configparser.NoOptionError as e:
        func.pushover(f"Fehlende Option in der Konfiguration: {e}")
        break
    except Exception as e:
        end_time = time.time()
        total_time = end_time - start_time
        hours, rem = divmod(total_time, 3600)
        minutes, seconds = divmod(rem, 60)
        infos = {'hours': int(hours), 'minutes': int(minutes), 'seconds': int(seconds), 'exception': e}
        msg = "Script stopped because of an exception \nRuntime: %(hours)s h %(minutes)s min %(seconds)s sec \n\n%(exception)s" % infos
        func.pushover(msg)
        print(e)
        time.sleep(600)  # Wartezeit von 10 Minuten vor dem Neustart
        manager.restart_program()

