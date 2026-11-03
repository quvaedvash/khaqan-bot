from indicators import adx, ema

NAME = "ADX Trend"
DESCRIPTION = "+DI/-DI cross while ADX shows a strong trend"
PARAMS = {"period": 14, "min_adx": 22}


def signal(df, p):
    a, pdi, mdi = adx(df, p["period"])
    if a.iloc[-1] < p["min_adx"]: return None
    if pdi.iloc[-2] <= mdi.iloc[-2] and pdi.iloc[-1] > mdi.iloc[-1]: return "long"
    if pdi.iloc[-2] >= mdi.iloc[-2] and pdi.iloc[-1] < mdi.iloc[-1]: return "short"
