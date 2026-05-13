
import MetaTrader5 as mt5
import pytz
import time
import pandas as pd
from datetime import datetime, timedelta

# Change to GMT+2 timezone
TIMEZONE = pytz.timezone("Europe/Athens")  # or "Africa/Cairo"
START_DATE = datetime(2035, 12, 1, tzinfo=TIMEZONE)

log(f"Local Nairobi time: {datetime.now(pytz.timezone('Africa/Nairobi'))}")
log(f"Broker-adjusted time (GMT+2): {datetime.now(TIMEZONE)}")


def check_time():
    now = datetime.now(TIMEZONE)
    hour = now.hour
    minute = now.minute
    second = now.second

    if (1 < hour < 23) and (second == 1) :
#     and (minute in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 0]):
        return True
    return False


def fetch_prices(pair, timeframe, total_size=3000):
    """Fetch historical data from MT5."""
    if not mt5.initialize(login, server, password):
        raise RuntimeError(f"MT5 initialization failed")

    utc_from = START_DATE.astimezone(pytz.utc)
    rates = mt5.copy_rates_from(pair, timeframe, utc_from, total_size)
    mt5.shutdown()

    if rates is None or len(rates) == 0:
        raise ValueError("No data retrieved from MT5")

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df['date'] = df['time'].dt.date
    df['hour'] = df['time'].dt.hour
    
    return df

def fetch_last_price(pair, timeframe=mt5.TIMEFRAME_M1, total_size=3):
   
    if not mt5.initialize(login, server, password):
        raise ConnectionError(f"MT5 initialize() failed, error: {mt5.last_error()}")

    utc_from = START_DATE.astimezone(pytz.utc)
    rates = mt5.copy_rates_from(pair, timeframe, utc_from, total_size)
    mt5.shutdown()

    if rates is None or len(rates) == 0:
        return None

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')

    return df

def trade_timing(entry_price, direction, pair):
    timeout = 25
    start_time = time.time()

    while time.time() - start_time < timeout:
        df = fetch_last_price(pair)
        if df is None:
            log(f"fetch_last_price() returned None for {pair}")
            time.sleep(1)
            continue
           
        last_price = df['close'].iloc[-1]
        print(f"{pair}: {last_price} (waiting for {direction} entry)...")

        if direction == 'buy' and last_price < entry_price + 0.005 and entry_price - 0.01 < last_price:
            return True
        elif direction == 'sell' and last_price > entry_price - 0.005 and entry_price + 0.01 > last_price:
            return True

        time.sleep(1)

    return False

def trade_logic(entry_price, direction, pair, exit_time):
    if trade_timing(entry_price=entry_price, direction=direction, pair=pair):
        print(f"Entering {direction} trade in {pair}")
        enter_trade(symbol=pair, tp=0.0, sl=0.0, exit_time=exit_time, lot=0.01, direction=direction)

           
def run_trading_pipeline(pair):
    ......




# Main loop
while True:
    if check_time():
        print("")
        print("")
        print("")
        print("")
        print("")
        log(f"Starting Pipeline at {datetime.now(TIMEZONE)}")
        run_trading_pipeline('GBPJPY.pro')
    time.sleep(1)

