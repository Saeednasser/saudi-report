import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os
from datetime import date

# قراءة الأسرار من GitHub Secrets وتنظيفها
bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
chat_id   = os.getenv('TELEGRAM_CHAT_ID', '').strip()

def fetch_data(symbols, start, end, interval):
    return yf.download(
        tickers=symbols,
        start=start,
        end=end,
        interval=interval,
        group_by='ticker',
        auto_adjust=True,
        progress=False,
        threads=True
    )

def detect_sell_breakout(df, lose_body=0.55):
    o,h,l,c = df['Open'], df['High'], df['Low'], df['Close']
    ratio   = np.where((h-l)!=0, abs(o-c)/(h-l), 0)
    valid   = (c < o) & (ratio >= lose_body)
    highs   = np.full(len(df), np.nan)
    breakout= np.zeros(len(df), dtype=bool)
    for i in range(1, len(df)):
        if not np.isnan(highs[i-1]) and c.iat[i] > highs[i-1] and not valid[i]:
            breakout[i] = True
            highs[i]    = np.nan
        else:
            highs[i]    = h.iat[i] if valid[i] else highs[i-1]
    df['breakout'] = breakout
    return df

def run_report():
    symbols = [s + ".SR" for s in "1120 2380 1050".split()]
    start   = '2023-01-01'
    end     = str(date.today())
    data    = fetch_data(symbols, start, end, '1d')
    report  = []
    if data is not None:
        for code in symbols:
            try:
                df = data[code].reset_index()
                df = detect_sell_breakout(df)
                if df['breakout'].iloc[-1]:
                    price = round(df['Close'].iloc[-1], 2)
                    report.append((code.replace('.SR',''), price))
            except:
                continue

    if report:
        text = f"📊 تقرير اختراقات السوق السعودي ({date.today()}):\n"
        for sym, pr in report:
            text += f"🔹 {sym} – {pr} ريال\n"
    else:
        text = f"🔎 لا توجد اختراقات جديدة اليوم ({date.today()})."

    url    = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
    resp   = requests.post(url, params=params)
    if resp.status_code == 200:
        print("✅ تم الإرسال إلى Telegram")
    else:
        print(f"❌ خطأ {resp.status_code}: {resp.text}")

if __name__ == "__main__":
    run_report()
