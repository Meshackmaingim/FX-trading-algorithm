# FX-trading-algorithm
An algorithm for analyzing the market based on a strategy and set rules , to find and execute trades at favourable prices.
<img width="975" height="1219" alt="image" src="https://github.com/user-attachments/assets/a64748a5-b439-45db-86d8-7646a19ae385" />
MT5 Trading Bot Infrastructure

This is a Python-based trading system built to interface with MetaTrader 5. The project focuses on solving the common headaches of automated trading: handling concurrent tasks, managing broker timezones, and ensuring trades are exited exactly when they are supposed to be.
How it Works

The system is split into two main parts: the Pipeline (the brain) and the Execution Engine (the hands).
1. The Multi-Threaded Approach

Instead of the bot "freezing" while waiting for a trade to fill, I used the threading library.

    When a signal is found, the system spins up a new background thread to handle that specific trade.

    This allows the main loop to keep watching the markets for other opportunities without any downtime.
    2. Smart Entry Logic (Slippage Handling)

I didn't want the bot to just blindly fire market orders.

    The trade_timing function acts as a gatekeeper. It watches the price for up to 25 seconds.

    It only hits the "Buy" or "Sell" button if the price is within a specific range of our target.

    It uses IOC (Immediate or Cancel) filling to make sure we don't get filled at a bad price if the market jumps.

3. Automated Exits

Managing the exit is just as important as the entry.

    The system calculates the holding time dynamically.

    Once a trade is opened, it starts a threading.Timer that triggers the close_trade function automatically after a set number of seconds.

    This means even if the main loop crashes, the exit command is already scheduled in memory.

    🏗 Project Structure

    engine.py: The main loop. It handles the "when" and "where" of the strategy, including the timezone math to sync my local Nairobi time with the broker’s GMT+2 clock.

    execution.py: The heavy lifter. It handles all the MT5 API calls, order requests, and position tracking.

    run_pipeline: (Abstracted) This is where the technical indicators and signal math live.

🚀 Technical Features

    Timezone Sync: Uses pytz to handle the offset between local time and broker time, ensuring data is pulled from the correct candle.

    Connection Management: The code explicitly calls mt5.initialize() and mt5.shutdown() for every major action. This prevents the "memory leak" and connection hang-ups that happen when keeping an MT5 session open for days.

    Parallel Execution: Can manage multiple different currency pairs at once without them interfering with each other.
