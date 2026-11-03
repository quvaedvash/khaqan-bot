from indicators import ema

NAME = "EMA Cross"
DESCRIPTION = "Fast EMA crosses slow EMA / Schnelle EMA kreuzt langsame EMA"
PARAMS = {"fast": 9, "slow": 21}


def signal(df, p):
    """df: closed candles (open, high, low, close, volume). Return 'long', 'short' or None."""
    f, s = ema(df.close, p["fast"]), ema(df.close, p["slow"])
    if f.iloc[-2] <= s.iloc[-2] and f.iloc[-1] > s.iloc[-1]: return "long"
    if f.iloc[-2] >= s.iloc[-2] and f.iloc[-1] < s.iloc[-1]: return "short"
