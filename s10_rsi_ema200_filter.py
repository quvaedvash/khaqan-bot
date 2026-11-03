from indicators import ema, rsi

NAME = "RSI + EMA200 Filter"
DESCRIPTION = "Pullback entries in the direction of the EMA trend"
PARAMS = {"ema": 200, "rsi": 14, "buy_below": 40, "sell_above": 60}


def signal(df, p):
    e = ema(df.close, p["ema"]).iloc[-1]
    r = rsi(df.close, p["rsi"])
    c = df.close.iloc[-1]
    if c > e and r.iloc[-2] < p["buy_below"] <= r.iloc[-1]: return "long"
    if c < e and r.iloc[-2] > p["sell_above"] >= r.iloc[-1]: return "short"
