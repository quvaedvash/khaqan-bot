import numpy as np
import pandas as pd


def ema(s, n): return s.ewm(span=n, adjust=False).mean()
def sma(s, n): return s.rolling(n).mean()


def rsi(s, n=14):
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def atr(df, n=14):
    pc = df.close.shift()
    tr = pd.concat([df.high - df.low, (df.high - pc).abs(), (df.low - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def macd(s, f=12, sl=26, sg=9):
    m = ema(s, f) - ema(s, sl)
    sig = ema(m, sg)
    return m, sig, m - sig


def bbands(s, n=20, k=2.0):
    m = sma(s, n)
    sd = s.rolling(n).std()
    return m + k * sd, m, m - k * sd


def stoch(df, k=14, d=3):
    ll, hh = df.low.rolling(k).min(), df.high.rolling(k).max()
    kk = 100 * (df.close - ll) / (hh - ll)
    return kk, kk.rolling(d).mean()


def adx(df, n=14):
    up, dn = df.high.diff(), -df.low.diff()
    pdm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=df.index)
    mdm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=df.index)
    a = atr(df, n)
    pdi = 100 * pdm.ewm(alpha=1 / n, adjust=False).mean() / a
    mdi = 100 * mdm.ewm(alpha=1 / n, adjust=False).mean() / a
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi)
    return dx.ewm(alpha=1 / n, adjust=False).mean(), pdi, mdi


def ichimoku(df, t=9, k=26, b=52):
    tenkan = (df.high.rolling(t).max() + df.low.rolling(t).min()) / 2
    kijun = (df.high.rolling(k).max() + df.low.rolling(k).min()) / 2
    sa = ((tenkan + kijun) / 2).shift(k)
    sb = ((df.high.rolling(b).max() + df.low.rolling(b).min()) / 2).shift(k)
    return tenkan, kijun, sa, sb
