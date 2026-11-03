# Futures Bot (Streamlit)

## Start
    pip install -r requirements.txt
    streamlit run app.py
Optional password for the web UI:  APP_PASSWORD=yourpass streamlit run app.py

## Desktop / Android / iPhone
Streamlit runs on a computer or server, not natively inside Android/iOS.
- Best for 24/7: run on a VPS (or home PC that never sleeps), open the URL on phone/desktop,
  then "Add to Home Screen" (Android/iOS) or "Install app" (Chrome/Edge desktop) -> app-like icon.
- Serve it over HTTPS (Caddy / nginx / Cloudflare Tunnel) and ALWAYS set APP_PASSWORD.
- Pure desktop .exe/.app: wrap with pywebview or PyInstaller later.

## Safety
- Default mode = paper (simulation) + testnet. Switch to LIVE only after testing.
- API keys: enable only "Futures trading", NEVER "Withdraw"; whitelist the server IP.
- SL/TP are checked by the bot every loop (default 30s), not placed on the exchange.
  If the server dies, an open position stays unprotected.
- One position per symbol (exchanges net positions per symbol). PnL ignores fees/funding.
- Not financial advice; backtest strategies before real money.

## Strategies
Every file strategies/sNN_name.py is a plugin: NAME, DESCRIPTION, PARAMS, signal(df, p) -> "long"|"short"|None.
Edit code in the app (Strategies tab) or add a new file with "New strategy".
