from indicators import bbands

NAME = "Bollinger Reversion"
DESCRIPTION = "Close back inside Bollinger band after a breakout"
PARAMS = {"period": 20, "mult": 2.0}


def signal(df, p):
    up, _, lo = bbands(df.close, p["period"], p["mult"])
    c = df.close
    if c.iloc[-2] < lo.iloc[-2] and c.iloc[-1] >= lo.iloc[-1]: return "long"
    if c.iloc[-2] > up.iloc[-2] and c.iloc[-1] <= up.iloc[-1]: return "short"
