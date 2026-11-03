from indicators import stoch

NAME = "Stochastic Cross"
DESCRIPTION = "%K crosses %D inside extreme zones"
PARAMS = {"k": 14, "d": 3, "low": 20, "high": 80}


def signal(df, p):
    k, d = stoch(df, p["k"], p["d"])
    if k.iloc[-2] <= d.iloc[-2] and k.iloc[-1] > d.iloc[-1] and k.iloc[-1] < p["low"] + 10: return "long"
    if k.iloc[-2] >= d.iloc[-2] and k.iloc[-1] < d.iloc[-1] and k.iloc[-1] > p["high"] - 10: return "short"
