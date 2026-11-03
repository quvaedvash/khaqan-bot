from indicators import rsi

NAME = "RSI Reversal"
DESCRIPTION = "RSI leaves oversold/overbought zone"
PARAMS = {"period": 14, "low": 30, "high": 70}


def signal(df, p):
    r = rsi(df.close, p["period"])
    if r.iloc[-2] < p["low"] <= r.iloc[-1]: return "long"
    if r.iloc[-2] > p["high"] >= r.iloc[-1]: return "short"
