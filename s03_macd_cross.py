from indicators import macd

NAME = "MACD Cross"
DESCRIPTION = "MACD line crosses signal line"
PARAMS = {"fast": 12, "slow": 26, "signal": 9}


def signal(df, p):
    m, s, _ = macd(df.close, p["fast"], p["slow"], p["signal"])
    if m.iloc[-2] <= s.iloc[-2] and m.iloc[-1] > s.iloc[-1]: return "long"
    if m.iloc[-2] >= s.iloc[-2] and m.iloc[-1] < s.iloc[-1]: return "short"
