import time
import pytz
import MetaTrader5 as mt5
from datetime import datetime
import threading

TIMEZONE = pytz.timezone("Europe/Athens")  # broker timezone
def log(msg):
    t = datetime.now().strftime("%H:%M:%S")
    print(f"[{t}] ({threading.current_thread().name}) {msg}")

# ---------- OPEN (ENTRY) ----------
def open_trade(symbol, sl, tp, exit_time, lot=0.01, direction="buy"):
    """
    Places a trade and returns a tuple (ticket, symbol, direction, seconds_to_close).
    This function initializes MT5, places the order, then shuts down MT5 immediately.
    """
    if not mt5.initialize(login, server, password):
        log(f"MT5 initialize failed: {mt5.last_error()}")
        return None, None, None, None

    # validate symbol visibility
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        log(f"{symbol} not found")
        mt5.shutdown()
        return None, None, None, None
    if not symbol_info.visible and not mt5.symbol_select(symbol, True):
        log(f"symbol_select({symbol}) failed")
        mt5.shutdown()
        return None, None, None, None

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        log(f"symbol_info_tick failed: {mt5.last_error()}")
        mt5.shutdown()
        return None, None, None, None

    ask = tick.ask
    bid = tick.bid

    # --- preserve your exit_time handling ---
    if isinstance(exit_time, str):
        target_time = datetime.strptime(exit_time, "%Y-%m-%d %H:%M:%S")
        target_time = TIMEZONE.localize(target_time)  # make tz-aware
    else:
        target_time = exit_time
        if target_time.tzinfo is None:  # if still tz-naive
            target_time = TIMEZONE.localize(target_time)

    now = datetime.now(TIMEZONE)
    diff = target_time - now
    seconds_to_close = int(diff.total_seconds())

    # you had a hard override in your test; keep ability but comment out if not needed
    # seconds_to_close = 118

    # --- order direction ---
    if direction.lower() == "buy":
        order_type = mt5.ORDER_TYPE_BUY
        price = ask
    elif direction.lower() == "sell":
        order_type = mt5.ORDER_TYPE_SELL
        price = bid
    else:
        log("Invalid direction")
        mt5.shutdown()
        return None, None, None, None

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 234000,
        "comment": f"market {direction}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)

    if result is None:
        log(f"order_send() failed, error: {mt5.last_error()}")
        mt5.shutdown()
        return None, None, None, None

    # prefer order ticket, fallback to deal
    ticket = getattr(result, "order", None) or getattr(result, "deal", None) or getattr(result, "position", None)

    if getattr(result, "retcode", None) != mt5.TRADE_RETCODE_DONE:
        log(f"Failed to open order: retcode={getattr(result,'retcode',None)} comment={getattr(result,'comment',None)}")
        mt5.shutdown()
        return None, None, None, None

    log(f"Opened {direction} {symbol} with ticket {ticket}")
    mt5.shutdown()
    return ticket, symbol, direction.lower(), seconds_to_close


# ---------- CLOSE (EXIT) ----------
def close_trade(symbol, ticket, direction, lot=None):
    """
    Initialize MT5, find the position with given ticket and close it.
    Shuts down MT5 when done.
    """
    if ticket is None:
        log("No ticket provided to close_trade()")
        return

    if not mt5.initialize(login, server, password):
        log(f"MT5 initialize failed in close_trade(): {mt5.last_error()}")
        return

    # fetch open positions for the symbol
    positions = mt5.positions_get(symbol=symbol)
    if positions is None:
        log(f"No positions on symbol, error: {mt5.last_error()}")
        mt5.shutdown()
        return

    # find the exact position by ticket
    pos_to_close = next((p for p in positions if p.ticket == ticket), None)

    if not pos_to_close:
        # fallback: if not found by ticket, pick last position on symbol (optional)
        log(f"Ticket {ticket} not found in current positions. Inspecting last position on symbol.")
        if len(positions) == 0:
            log("No positions to close.")
            mt5.shutdown()
            return
        last_pos = sorted(positions, key=lambda p: p.time, reverse=True)[0]
        log(f"Last open position ticket {last_pos.ticket} (will compare)")
        if last_pos.ticket != ticket:
            log(f"Last position ticket {last_pos.ticket} != requested ticket {ticket}. Aborting close.")
            mt5.shutdown()
            return
        pos_to_close = last_pos

    # determine close parameters
    close_type = mt5.ORDER_TYPE_SELL if direction == "buy" else mt5.ORDER_TYPE_BUY
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        log(f"symbol_info_tick failed in close_trade(): {mt5.last_error()}")
        mt5.shutdown()
        return
    close_price = tick.bid if direction == "buy" else tick.ask
    volume = pos_to_close.volume if lot is None else lot

    close_req = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": close_type,
        "position": pos_to_close.ticket,
        "price": close_price,
        "deviation": 25,
        "magic": pos_to_close.magic,
        "comment": "manual close",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    r = mt5.order_send(close_req)
    if r is None:
        log(f"order_send close returned None: {mt5.last_error()}")
        mt5.shutdown()
        return

    if getattr(r, "retcode", None) == mt5.TRADE_RETCODE_DONE:
        log(f"Ticket {ticket} closed successfully.")
    else:
        log(f"Close failed: retcode={getattr(r,'retcode',None)} comment={getattr(r,'comment',None)}")

    mt5.shutdown()


# ---------- USAGE - scheduling the close ----------
def enter_trade(symbol, sl, tp, exit_time, lot=0.01, direction="buy"):
    ticket, sym, dirn, seconds_to_close = open_trade(symbol, sl, tp, exit_time, lot=lot, direction=direction)
    if ticket is None:
        log("Open failed, not scheduling close.")
        return

    # if seconds_to_close is negative or tiny, call close immediately
    if seconds_to_close is None or seconds_to_close <= 0:
        log("seconds_to_close <= 0, closing immediately.")
        close_trade(sym, ticket, dirn, lot=lot)
        return

    log(f"Holding trade for {seconds_to_close} seconds then closing ticket {ticket}")

    # schedule close in a new process-friendly initialization call
    timer = threading.Timer(seconds_to_close, close_trade, args=(sym, ticket, dirn, lot))
    timer.daemon = True
    timer.start()
    # return timer in case caller wants to cancel it
    return ticket, timer
