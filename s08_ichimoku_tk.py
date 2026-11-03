from indicators import ichimoku

NAME = "Ichimoku TK Cross"
DESCRIPTION = "Tenkan/Kijun cross with price above/below the cloud"
PARAMS = {"tenkan": 9, "kijun": 26, "senkou_b": 52}


def signal(df, p):
    t, k, sa, sb = ichimoku(df, p["tenkan"], p["kijun"], p["senkou_b"])
    top, bot = max(sa.iloc[-1], sb.iloc[-1]), min(sa.iloc[-1], sb.iloc[-1])
    c = df.close.iloc[-1]
    if t.iloc[-2] <= k.iloc[-2] and t.iloc[-1] > k.iloc[-1] and c > top: return "long"
    if t.iloc[-2] >= k.iloc[-2] and t.iloc[-1] < k.iloc[-1] and c < bot: return "short"
