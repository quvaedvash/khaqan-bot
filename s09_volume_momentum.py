NAME = "Volume Momentum"
DESCRIPTION = "Strong candle with a volume spike"
PARAMS = {"vol_period": 20, "vol_mult": 2.0, "min_body_pct": 0.5}


def signal(df, p):
    v = df.volume.iloc[-1]
    avg = df.volume.iloc[-p["vol_period"] - 1:-1].mean()
    o, c = df.open.iloc[-1], df.close.iloc[-1]
    body = abs(c - o) / o * 100
    if v > avg * p["vol_mult"] and body >= p["min_body_pct"]:
        return "long" if c > o else "short"
