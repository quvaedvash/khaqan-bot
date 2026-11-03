NAME = "Donchian Breakout"
DESCRIPTION = "Close breaks N-candle high/low"
PARAMS = {"period": 20}


def signal(df, p):
    n = p["period"]
    hh = df.high.iloc[-n - 1:-1].max()
    ll = df.low.iloc[-n - 1:-1].min()
    if df.close.iloc[-1] > hh: return "long"
    if df.close.iloc[-1] < ll: return "short"
