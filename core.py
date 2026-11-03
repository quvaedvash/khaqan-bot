"""Trading engine: exchange (ccxt), strategies, Telegram, reports, SQLite journal."""
import importlib.util
import json
import sqlite3
import sys
import threading
import time
import traceback
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

BASE = Path(__file__).parent
DATA = BASE / "data"
STRAT_DIR = BASE / "strategies"
DATA.mkdir(exist_ok=True)
STRAT_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(BASE))
CFG_FILE, STATE_FILE, DB_FILE = DATA / "config.json", DATA / "state.json", DATA / "trades.db"

DEFAULT = {
    "language": "en", "exchange": "binance", "api_key": "", "api_secret": "", "password": "",
    "testnet": True, "mode": "paper",
    "symbols": ["BTC/USDT:USDT"], "timeframe": "15m", "leverage": 5, "size_usdt": 50.0,
    "sl_pct": 1.5, "tp_pct": 3.0, "loop_sec": 30,
    "active": [], "params": {},
    "tg": {"token": "", "chat_id": "", "on_open": True, "on_close": True,
           "daily": True, "weekly": False, "monthly": False, "report_hour": 22},
}


# ---------- config / state ----------
def load_cfg():
    cfg = json.loads(json.dumps(DEFAULT))
    if CFG_FILE.exists():
        saved = json.loads(CFG_FILE.read_text("utf-8"))
        tg = saved.pop("tg", {})
        cfg.update(saved)
        cfg["tg"].update(tg)
    return cfg


def save_cfg(cfg):
    CFG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), "utf-8")


def _state():
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}


def _save_state(s):
    STATE_FILE.write_text(json.dumps(s))


# ---------- strategies ----------
def load_strategies():
    """Every strategies/sNN_*.py file is a plugin: NAME, DESCRIPTION, PARAMS, signal(df, p)."""
    out = {}
    for f in sorted(STRAT_DIR.glob("s*.py")):
        try:
            spec = importlib.util.spec_from_file_location("strat_" + f.stem, f)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            out[f.stem] = m
        except Exception as e:  # broken user code must never crash the app
            out[f.stem] = e
    return out


STRATEGY_TEMPLATE = '''from indicators import ema, sma, rsi, atr, macd, bbands, stoch, adx, ichimoku

NAME = "{name}"
DESCRIPTION = "My strategy"
PARAMS = {{"period": 14}}


def signal(df, p):
    """df = closed candles (open, high, low, close, volume).
    Return "long", "short" or None."""
    return None
'''


# ---------- database ----------
def db():
    c = sqlite3.connect(DB_FILE, check_same_thread=False)
    c.execute("""CREATE TABLE IF NOT EXISTS trades(
        id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, strategy TEXT, side TEXT,
        entry REAL, exit REAL, qty REAL, opened_at TEXT, closed_at TEXT,
        pnl REAL, status TEXT, reason TEXT, mode TEXT)""")
    return c


def now_utc():
    return datetime.now(timezone.utc)


def iso(d):
    return d.strftime("%Y-%m-%d %H:%M:%S")


# ---------- telegram ----------
def tg_send(cfg, text):
    t = cfg["tg"]
    if not t["token"] or not str(t["chat_id"]).strip():
        return False, "token/chat_id missing"
    try:
        r = requests.post(f"https://api.telegram.org/bot{t['token'].strip()}/sendMessage",
                          json={"chat_id": str(t["chat_id"]).strip(), "text": text}, timeout=15)
        return r.ok, r.text[:200]
    except Exception as e:
        return False, str(e)


def report_text(title, start, end):
    c = db()
    rows = c.execute("SELECT strategy, pnl FROM trades WHERE status='closed' AND closed_at>=? AND closed_at<=?",
                     (iso(start), iso(end))).fetchall()
    c.close()
    if not rows:
        return f"📊 {title}\nNo closed trades / Keine Trades"
    df = pd.DataFrame(rows, columns=["s", "pnl"])
    wins = int((df.pnl > 0).sum())
    lines = [f"📊 {title}", f"Trades: {len(df)} | Win: {wins} ({wins / len(df) * 100:.0f}%)",
             f"PnL: {df.pnl.sum():+.2f} USDT"]
    for s, g in df.groupby("s"):
        lines.append(f" • {s}: {g.pnl.sum():+.2f} ({len(g)})")
    return "\n".join(lines)


# ---------- bot ----------
class Bot:
    def __init__(self):
        self.thread = None
        self.stop_ev = threading.Event()
        self.logs = deque(maxlen=300)
        self.last_eval = {}

    @property
    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def log(self, msg):
        self.logs.appendleft(f"{now_utc():%H:%M:%S}  {msg}")

    def start(self):
        if self.running:
            return
        self.stop_ev.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_ev.set()

    # --- exchange ---
    def _exchange(self, cfg):
        import ccxt
        ex = getattr(ccxt, cfg["exchange"])({
            "apiKey": cfg["api_key"], "secret": cfg["api_secret"], "password": cfg["password"] or None,
            "enableRateLimit": True, "options": {"defaultType": "swap"}})
        if cfg["testnet"]:
            ex.set_sandbox_mode(True)
        ex.load_markets()
        return ex

    def _run(self):
        self.log("Bot started")
        ex = None
        while not self.stop_ev.is_set():
            cfg = load_cfg()
            try:
                if ex is None:
                    ex = self._exchange(cfg)
                    self.log(f"Connected: {cfg['exchange']} ({cfg['mode']}{', testnet' if cfg['testnet'] else ''})")
                self._cycle(ex, cfg)
                self._reports(cfg)
            except Exception as e:
                self.log(f"ERROR: {e}")
                traceback.print_exc()
            self.stop_ev.wait(max(5, int(cfg["loop_sec"])))
        self.log("Bot stopped")

    # --- one pass over all symbols ---
    def _cycle(self, ex, cfg):
        strategies = {k: v for k, v in load_strategies().items() if k in cfg["active"] and not isinstance(v, Exception)}
        for symbol in cfg["symbols"]:
            ohlcv = ex.fetch_ohlcv(symbol, cfg["timeframe"], limit=300)
            df = pd.DataFrame(ohlcv, columns=["ts", "open", "high", "low", "close", "volume"])
            price = float(ex.fetch_ticker(symbol)["last"])
            c = db()
            pos = c.execute("SELECT id, strategy, side, entry, qty FROM trades WHERE status='open' AND symbol=?",
                            (symbol,)).fetchone()
            c.close()
            # SL / TP on every pass
            if pos:
                _, sname, side, entry, _q = pos
                move = (price - entry) / entry * 100 * (1 if side == "long" else -1)
                if move <= -cfg["sl_pct"]:
                    self._close(ex, cfg, symbol, price, "SL")
                    pos = None
                elif move >= cfg["tp_pct"]:
                    self._close(ex, cfg, symbol, price, "TP")
                    pos = None
            # strategies are evaluated once per newly closed candle
            closed = df.iloc[:-1]
            candle_ts = int(closed.ts.iloc[-1])
            if self.last_eval.get(symbol) == candle_ts:
                continue
            self.last_eval[symbol] = candle_ts
            for key, mod in strategies.items():
                p = {**mod.PARAMS, **cfg["params"].get(key, {})}
                try:
                    sig = mod.signal(closed.reset_index(drop=True), p)
                except Exception as e:
                    self.log(f"{key} error: {e}")
                    continue
                if not sig:
                    continue
                if pos and pos[1] == mod.NAME and pos[2] != sig:      # opposite signal of same strategy
                    self._close(ex, cfg, symbol, price, "signal")
                    pos = None
                if not pos:
                    self._open(ex, cfg, symbol, mod.NAME, sig, price)
                    break                                              # one position per symbol

    def _open(self, ex, cfg, symbol, strat, side, price):
        notional = cfg["size_usdt"] * cfg["leverage"]
        qty = notional / price
        if cfg["mode"] == "live":
            m = ex.market(symbol)
            amount = ex.amount_to_precision(symbol, qty / (m.get("contractSize") or 1))
            try:
                ex.set_leverage(int(cfg["leverage"]), symbol)
            except Exception as e:
                self.log(f"set_leverage: {e}")
            ex.create_order(symbol, "market", "buy" if side == "long" else "sell", float(amount))
        c = db()
        c.execute("INSERT INTO trades(symbol,strategy,side,entry,qty,opened_at,status,mode) VALUES(?,?,?,?,?,?,?,?)",
                  (symbol, strat, side, price, qty, iso(now_utc()), "open", cfg["mode"]))
        c.commit(); c.close()
        self.log(f"OPEN {side} {symbol} @ {price} [{strat}]")
        if cfg["tg"]["on_open"]:
            tg_send(cfg, f"🟢 OPEN {side.upper()} {symbol}\nStrategy: {strat}\nEntry: {price}\n"
                         f"SL {cfg['sl_pct']}% | TP {cfg['tp_pct']}% | x{cfg['leverage']} | {cfg['mode']}")

    def _close(self, ex, cfg, symbol, price, reason):
        c = db()
        row = c.execute("SELECT id, strategy, side, entry, qty FROM trades WHERE status='open' AND symbol=?",
                        (symbol,)).fetchone()
        if not row:
            c.close(); return
        tid, strat, side, entry, qty = row
        if cfg["mode"] == "live":
            m = ex.market(symbol)
            amount = ex.amount_to_precision(symbol, qty / (m.get("contractSize") or 1))
            ex.create_order(symbol, "market", "sell" if side == "long" else "buy", float(amount),
                            params={"reduceOnly": True})
        pnl = (price - entry) * qty * (1 if side == "long" else -1)
        c.execute("UPDATE trades SET exit=?, closed_at=?, pnl=?, status='closed', reason=? WHERE id=?",
                  (price, iso(now_utc()), pnl, reason, tid))
        c.commit(); c.close()
        self.log(f"CLOSE {side} {symbol} @ {price} pnl={pnl:+.2f} ({reason})")
        if cfg["tg"]["on_close"]:
            tg_send(cfg, f"{'✅' if pnl >= 0 else '🔴'} CLOSE {side.upper()} {symbol}\nStrategy: {strat}\n"
                         f"Entry: {entry} → Exit: {price}\nPnL: {pnl:+.2f} USDT ({reason})")

    # --- periodic reports ---
    def _reports(self, cfg):
        t, now, st = cfg["tg"], now_utc(), _state()
        if now.hour < int(t["report_hour"]):
            return
        today = now.strftime("%Y-%m-%d")
        if t["daily"] and st.get("d") != today:
            tg_send(cfg, report_text("Daily / Täglich", now - timedelta(days=1), now)); st["d"] = today
        if t["weekly"] and now.weekday() == 6 and st.get("w") != today:
            tg_send(cfg, report_text("Weekly / Wöchentlich", now - timedelta(days=7), now)); st["w"] = today
        if t["monthly"] and (now + timedelta(days=1)).day == 1 and st.get("m") != today:
            tg_send(cfg, report_text("Monthly / Monatlich", now.replace(day=1, hour=0, minute=0, second=0), now))
            st["m"] = today
        _save_state(st)
