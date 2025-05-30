import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os
from datetime import date

# قراءة الأسرار من GitHub Secrets
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

# ✅ طباعة القيم للتحقق في اللوج
print(f"✅ Using bot_token: {bot_token}")
print(f"✅ Using chat_id: {chat_id}")

if not bot_token or not chat_id:
    print("❌ مشكلة: لم يتم قراءة الأسرار بشكل صحيح من GitHub Secrets.")
    exit(1)

def fetch_data(symbols, start_date, end_date, interval):
    return yf.download(
        tickers=symbols,
        start=start_date,
        end=end_date,
        interval=interval,
        group_by='ticker',
        auto_adjust=True,
        progress=False,
        threads=True
    )

def detect_sell_breakout(df, lose_body_percent=0.55):
    o, h, l, c = df['Open'].values, df['High'].values, df['Low'].values, df['Close'].values
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = np.where((h - l) != 0, np.abs(o - c) / (h - l), 0)
    valid = (c < o) & (ratio >= lose_body_percent)
    highs = np.full(len(df), np.nan)
    breakout = np.zeros(len(df), dtype=bool)
    for i in range(1, len(df)):
        if not np.isnan(highs[i - 1]) and c[i] > highs[i - 1] and not valid[i]:
            breakout[i] = True
            highs[i] = np.nan
        else:
            highs[i] = h[i] if valid[i] else highs[i - 1]
    df['breakout'] = breakout
    return df

# رموز السوق السعودي
symbols_input = "1120 2380 1050"
symbols = [sym.strip() + ".SR" for sym in symbols_input.split()]
start_date = '2023-01-01'
end_date = str(date.today())
interval = '1d'

data = fetch_data(symbols, start_date, end_date, interval)
results = []

if data is not None:
    for code in symbols:
        try:
            df = data[code].reset_index()
            res = detect_sell_breakout(df)
            if res['breakout'].iloc[-1]:
                results.append((code.replace('.SR', ''), round(res['Close'].iloc[-1], 2)))
        except:
            continue

if results:
    message = f"📊 تقرير اختراقات السوق السعودي ({date.today()}):\n"
    for sym, price in results:
        message += f"🔹 {sym} – {price} ريال\n"
    message += "\n✅ تقرير تلقائي عبر Triple Power Bot"
else:
    message = f"🔎 لا توجد اختراقات جديدة اليوم ({date.today()})."

url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
params = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}
response = requests.post(url, params=params)

print(f"✅ Telegram response status: {response.status_code}")
print(f"✅ Telegram response text: {response.text}")

if response.status_code == 200:
    print("✅ تم إرسال التقرير عبر Telegram!")
else:
    print(f"❌ فشل الإرسال، رمز الخطأ: {response.status_code}")
