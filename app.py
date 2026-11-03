import os
import sqlite3

import pandas as pd
import streamlit as st

import core

st.set_page_config(page_title="Futures Bot", page_icon="🤖", layout="centered")

LANGS = {"Deutsch": 0, "English": 1, "فارسی": 2, "Türkçe": 3}
CODES = ["de", "en", "fa", "tr"]
# key: [de, en, fa, tr]
T = {
    "dashboard": ["Übersicht", "Dashboard", "داشبورد", "Panel"],
    "exchange": ["Börse", "Exchange", "صرافی", "Borsa"],
    "strategies": ["Strategien", "Strategies", "استراتژی‌ها", "Stratejiler"],
    "settings": ["Handel", "Trading", "معامله", "İşlem"],
    "telegram": ["Telegram", "Telegram", "تلگرام", "Telegram"],
    "trades": ["Trades", "Trades", "تاریخچه", "İşlemler"],
    "start": ["▶ Bot starten", "▶ Start bot", "▶ شروع ربات", "▶ Botu başlat"],
    "stop": ["⏹ Bot stoppen", "⏹ Stop bot", "⏹ توقف ربات", "⏹ Botu durdur"],
    "running": ["Bot läuft 24/7", "Bot is running 24/7", "ربات در حال اجراست", "Bot çalışıyor"],
    "stopped": ["Bot gestoppt", "Bot is stopped", "ربات متوقف است", "Bot durdu"],
    "mode": ["Modus", "Mode", "حالت", "Mod"],
    "paper": ["Simulation (kein echtes Geld)", "Paper (simulation)", "شبیه‌سازی (بدون پول واقعی)", "Simülasyon"],
    "live": ["LIVE (echtes Geld!)", "LIVE (real money!)", "واقعی (پول واقعی!)", "CANLI (gerçek para!)"],
    "testnet": ["Testnet verwenden", "Use testnet", "استفاده از تست‌نت", "Testnet kullan"],
    "api_key": ["API-Key", "API key", "کلید API", "API anahtarı"],
    "api_secret": ["API-Secret", "API secret", "سکرت API", "API gizli anahtarı"],
    "passphrase": ["Passphrase (falls nötig)", "Passphrase (if needed)", "پسفریز (در صورت نیاز)", "Parola (gerekirse)"],
    "save": ["Speichern", "Save", "ذخیره", "Kaydet"],
    "saved": ["Gespeichert ✔", "Saved ✔", "ذخیره شد ✔", "Kaydedildi ✔"],
    "symbols": ["Symbole (Komma getrennt)", "Symbols (comma separated)", "نمادها (با کاما)", "Semboller (virgülle)"],
    "timeframe": ["Zeitrahmen", "Timeframe", "تایم‌فریم", "Zaman dilimi"],
    "leverage": ["Hebel", "Leverage", "اهرم", "Kaldıraç"],
    "size": ["Margin pro Trade (USDT)", "Margin per trade (USDT)", "مارجین هر معامله (USDT)", "İşlem başına marjin (USDT)"],
    "sl": ["Stop-Loss %", "Stop loss %", "حد ضرر %", "Zarar durdur %"],
    "tp": ["Take-Profit %", "Take profit %", "حد سود %", "Kâr al %"],
    "loop": ["Prüfintervall (Sek.)", "Check interval (sec)", "فاصله بررسی (ثانیه)", "Kontrol aralığı (sn)"],
    "params": ["Parameter", "Parameters", "پارامترها", "Parametreler"],
    "edit_code": ["Code bearbeiten", "Edit code", "ویرایش کد", "Kodu düzenle"],
    "new_strat": ["➕ Neue Strategie", "➕ New strategy", "➕ استراتژی جدید", "➕ Yeni strateji"],
    "code_saved": ["Code gespeichert", "Code saved", "کد ذخیره شد", "Kod kaydedildi"],
    "code_error": ["Syntaxfehler", "Syntax error", "خطای نحوی", "Sözdizimi hatası"],
    "test": ["Testnachricht senden", "Send test message", "ارسال پیام تست", "Test mesajı gönder"],
    "token": ["Bot-Token", "Bot token", "توکن ربات", "Bot belirteci"],
    "chat_id": ["Telegram-ID / Chat-ID", "Telegram ID / chat ID", "آیدی تلگرام / چت", "Telegram ID / sohbet ID"],
    "on_open": ["Trade-Eröffnung melden", "Notify on open", "اعلام باز شدن معامله", "Açılışta bildir"],
    "on_close": ["Trade-Schließung melden", "Notify on close", "اعلام بسته شدن معامله", "Kapanışta bildir"],
    "daily": ["Tagesbericht", "Daily report", "گزارش روزانه", "Günlük rapor"],
    "weekly": ["Wochenbericht", "Weekly report", "گزارش هفتگی", "Haftalık rapor"],
    "monthly": ["Monatsbericht", "Monthly report", "گزارش ماهانه", "Aylık rapor"],
    "report_hour": ["Berichtszeit (UTC-Stunde)", "Report hour (UTC)", "ساعت گزارش (UTC)", "Rapor saati (UTC)"],
    "open_pos": ["Offene Positionen", "Open positions", "پوزیشن‌های باز", "Açık pozisyonlar"],
    "no_data": ["Keine Daten", "No data", "داده‌ای نیست", "Veri yok"],
    "total_pnl": ["Gesamt-PnL", "Total PnL", "کل سود/زیان", "Toplam K/Z"],
    "win_rate": ["Trefferquote", "Win rate", "درصد برد", "Kazanma oranı"],
    "count": ["Trades", "Trades", "تعداد معاملات", "İşlem sayısı"],
    "logs": ["Protokoll", "Log", "لاگ", "Kayıt"],
    "warning": ["⚠ Handel mit Hebel kann zum Totalverlust führen. Erst im Simulationsmodus/Testnet testen.",
                "⚠ Leveraged trading can lose your whole balance. Test in paper mode / testnet first.",
                "⚠ معامله با اهرم می‌تواند کل سرمایه را از بین ببرد. ابتدا در حالت شبیه‌سازی/تست‌نت تست کنید.",
                "⚠ Kaldıraçlı işlem tüm bakiyenizi kaybettirebilir. Önce simülasyon/testnet ile deneyin."],
    "active": ["Aktiv", "Active", "فعال", "Aktif"],
    "password": ["Passwort", "Password", "رمز عبور", "Parola"],
}


def tr(k):
    return T[k][L]


# ---------- access control (set APP_PASSWORD env var) ----------
pw = os.environ.get("APP_PASSWORD")
if pw and not st.session_state.get("auth"):
    L = 1
    x = st.text_input("Password", type="password")
    if x and x == pw:
        st.session_state.auth = True
        st.rerun()
    st.stop()

cfg = core.load_cfg()
L = CODES.index(cfg["language"]) if cfg["language"] in CODES else 1


@st.cache_resource
def get_bot():
    return core.Bot()          # one background engine per server process


bot = get_bot()

# ---------- sidebar: language ----------
names = list(LANGS)
choice = st.sidebar.selectbox("🌐", names, index=L)
if LANGS[choice] != L:
    cfg["language"] = CODES[LANGS[choice]]
    core.save_cfg(cfg)
    st.rerun()
if L == 2:  # Persian = right-to-left
    st.markdown("<style>.stApp{direction:rtl;text-align:right}</style>", unsafe_allow_html=True)
st.markdown("<style>.block-container{padding-top:2rem}div.stButton>button{width:100%;border-radius:10px}"
            "</style>", unsafe_allow_html=True)

st.title("🤖 Futures Bot")
st.caption(tr("warning"))

tabs = st.tabs([tr("dashboard"), tr("exchange"), tr("strategies"), tr("settings"), tr("telegram"), tr("trades")])

# ---------- dashboard ----------
with tabs[0]:
    @st.fragment(run_every=5)
    def dash():
        if bot.running:
            st.success(f"🟢 {tr('running')} — {cfg['mode'].upper()}")
            if st.button(tr("stop")):
                bot.stop(); st.rerun()
        else:
            st.info(f"⚪ {tr('stopped')}")
            if st.button(tr("start"), type="primary"):
                if not cfg["active"]:
                    st.error(tr("strategies") + " ?")
                else:
                    bot.start(); st.rerun()
        c = core.db()
        closed = pd.read_sql("SELECT pnl FROM trades WHERE status='closed'", c)
        opn = pd.read_sql("SELECT symbol, strategy, side, entry, opened_at FROM trades WHERE status='open'", c)
        c.close()
        m1, m2, m3 = st.columns(3)
        m1.metric(tr("total_pnl"), f"{closed.pnl.sum():+.2f}" if len(closed) else "0")
        m2.metric(tr("win_rate"), f"{(closed.pnl > 0).mean() * 100:.0f}%" if len(closed) else "–")
        m3.metric(tr("count"), len(closed))
        st.subheader(tr("open_pos"))
        if len(opn):
            st.dataframe(opn, use_container_width=True)
        else:
            st.caption(tr("no_data"))
        with st.expander(tr("logs")):
            st.code("\n".join(bot.logs) or "-")
    dash()

# ---------- exchange ----------
with tabs[1]:
    ex_list = ["binance", "bybit", "okx", "bitget", "gate", "kucoinfutures", "mexc", "bingx", "htx"]
    with st.form("ex"):
        cfg["exchange"] = st.selectbox(tr("exchange"), ex_list,
                                       index=ex_list.index(cfg["exchange"]) if cfg["exchange"] in ex_list else 0)
        cfg["api_key"] = st.text_input(tr("api_key"), cfg["api_key"], type="password")
        cfg["api_secret"] = st.text_input(tr("api_secret"), cfg["api_secret"], type="password")
        cfg["password"] = st.text_input(tr("passphrase"), cfg["password"], type="password")
        cfg["testnet"] = st.checkbox(tr("testnet"), cfg["testnet"])
        mode_lbl = [tr("paper"), tr("live")]
        sel = st.radio(tr("mode"), mode_lbl, index=0 if cfg["mode"] == "paper" else 1)
        cfg["mode"] = "paper" if sel == mode_lbl[0] else "live"
        if st.form_submit_button(tr("save")):
            core.save_cfg(cfg); st.success(tr("saved"))

# ---------- strategies ----------
with tabs[2]:
    strats = core.load_strategies()
    with st.form("strats"):
        active = []
        for key, mod in strats.items():
            if isinstance(mod, Exception):
                st.error(f"{key}: {mod}")
                continue
            c1, c2 = st.columns([1, 4])
            on = c1.checkbox(tr("active"), key + "_on", value=key in cfg["active"])
            c2.markdown(f"**{mod.NAME}** — {mod.DESCRIPTION}")
            if on:
                active.append(key)
            with st.expander(tr("params")):
                saved = cfg["params"].get(key, {})
                newp = {}
                for pk, pv in mod.PARAMS.items():
                    cur = saved.get(pk, pv)
                    if isinstance(pv, bool):
                        newp[pk] = st.checkbox(pk, cur, key=f"{key}_{pk}")
                    elif isinstance(pv, int):
                        newp[pk] = int(st.number_input(pk, value=int(cur), step=1, key=f"{key}_{pk}"))
                    else:
                        newp[pk] = float(st.number_input(pk, value=float(cur), key=f"{key}_{pk}"))
                cfg["params"][key] = newp
        if st.form_submit_button(tr("save")):
            cfg["active"] = active
            core.save_cfg(cfg); st.success(tr("saved"))

    st.divider()
    files = sorted(core.STRAT_DIR.glob("s*.py"))
    if not files:
        st.error("strategies/ folder is empty or missing next to app.py (copy the whole project incl. strategies/ and indicators.py)")
        st.stop()
    pick = st.selectbox(tr("edit_code"), [f.name for f in files])
    path = core.STRAT_DIR / pick
    code = st.text_area("code", path.read_text("utf-8"), height=320, label_visibility="collapsed", key="code_" + pick)
    if st.button(tr("save") + " (code)"):
        try:
            compile(code, pick, "exec")
            path.write_text(code, "utf-8"); st.success(tr("code_saved"))
        except SyntaxError as e:
            st.error(f"{tr('code_error')}: {e}")
    if st.button(tr("new_strat")):
        n = len(files) + 1
        (core.STRAT_DIR / f"s{n:02d}_custom{n}.py").write_text(
            core.STRATEGY_TEMPLATE.format(name=f"Custom {n}"), "utf-8")
        st.rerun()

# ---------- trading settings ----------
with tabs[3]:
    with st.form("trade"):
        cfg["symbols"] = [s.strip() for s in st.text_input(tr("symbols"), ", ".join(cfg["symbols"])).split(",") if s.strip()]
        tfs = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
        cfg["timeframe"] = st.selectbox(tr("timeframe"), tfs, index=tfs.index(cfg["timeframe"]) if cfg["timeframe"] in tfs else 2)
        cfg["leverage"] = st.slider(tr("leverage"), 1, 50, int(cfg["leverage"]))
        cfg["size_usdt"] = st.number_input(tr("size"), 1.0, 1e7, float(cfg["size_usdt"]))
        cfg["sl_pct"] = st.number_input(tr("sl"), 0.1, 50.0, float(cfg["sl_pct"]))
        cfg["tp_pct"] = st.number_input(tr("tp"), 0.1, 200.0, float(cfg["tp_pct"]))
        cfg["loop_sec"] = int(st.number_input(tr("loop"), 5, 3600, int(cfg["loop_sec"])))
        if st.form_submit_button(tr("save")):
            core.save_cfg(cfg); st.success(tr("saved"))

# ---------- telegram ----------
with tabs[4]:
    with st.form("tg"):
        t = cfg["tg"]
        t["token"] = st.text_input(tr("token"), t["token"], type="password")
        t["chat_id"] = st.text_input(tr("chat_id"), t["chat_id"])
        t["on_open"] = st.checkbox(tr("on_open"), t["on_open"])
        t["on_close"] = st.checkbox(tr("on_close"), t["on_close"])
        t["daily"] = st.checkbox(tr("daily"), t["daily"])
        t["weekly"] = st.checkbox(tr("weekly"), t["weekly"])
        t["monthly"] = st.checkbox(tr("monthly"), t["monthly"])
        t["report_hour"] = int(st.number_input(tr("report_hour"), 0, 23, int(t["report_hour"])))
        a, b = st.columns(2)
        if a.form_submit_button(tr("save")):
            core.save_cfg(cfg); st.success(tr("saved"))
        if b.form_submit_button(tr("test")):
            core.save_cfg(cfg)
            ok, info = core.tg_send(cfg, "✅ Futures Bot – test")
            if ok:
                st.success("OK")
            else:
                st.error(info)

# ---------- trade history ----------
with tabs[5]:
    c = core.db()
    hist = pd.read_sql("SELECT * FROM trades ORDER BY id DESC LIMIT 500", c)
    c.close()
    if len(hist):
        st.dataframe(hist, use_container_width=True)
        st.download_button("CSV", hist.to_csv(index=False), "trades.csv")
    else:
        st.caption(tr("no_data"))
