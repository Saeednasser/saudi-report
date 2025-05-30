import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os
from datetime import date

# قراءة الأسرار من GitHub Secrets وتنظيفها
bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
chat_id   = os.getenv('TELEGRAM_CHAT_ID',   '').strip()

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
    # ← استبدلنا هذه القائمة لتشمل كل الرموز المطلوبة
    symbols = [s + ".SR" for s in """
    3010 3040 6014 4071 4162 6040 8210 2082 4346 2090 2180 4031 4263 4180 1820 4292
    6013 4072 4210 2280 2282 2284 6001 4082 4083 8050 8060 8160 8180 2084 4331 4335
    4100 2170 3002 4008 8010 4200 1201 1304 2010 2223 2330 2040 2160 2370 4142 1835
    2340 4012 4170 6002 6016 4070 4240 4006 2281 6060 6090 4004 4130 7040 4334 4090
    4701 4702 2030 2222 2380 2381 2382 4030 1202 1210 1211 1301 1320 1321 1322 2001
    2020 2060 2150 2200 2210 2220 2240 2250 2290 2300 2310 2350 2360 3003 3004 3005
    3007 3008 3030 3050 3060 3080 3090 3091 1212 1214 1302 1303 2320 4140 4141 4143
    4144 1831 1832 4270 6004 2190 4040 4260 4261 4262 2130 4011 1810 1830 4290 4291
    6012 6015 6017 4003 4050 4051 4190 4192 4193 4001 4061 4160 4161 4163 4164 2050
    2100 2270 2283 2285 4080 6010 6020 6050 6070 2230 4005 4007 4009 4013 4017 2070
    4015 4016 1020 1060 1080 1140 1150 1180 1111 1182 1183 2120 4081 4280 8012 8020
    8030 8040 8070 8100 8120 8150 8170 8190 8200 8230 8240 8250 8260 8270 8280 8300
    8310 8311 7200 7201 7202 7203 7204 7020 2080 2081 2083 5110 4330 4332 4333 4336
    4337 4338 4339 4340 4342 4344 4345 4347 4348 4350 4020 4150 4220 4230 4310 4320
    4321 4322 4324 4700 4703 4165 4110 2286 4002 4014 1010 1030 4349
    """.split()]
    start = '2023-01-01'
    end   = str(date.today())
    data  = fetch_data(symbols, start, end, '1d')
    report = []

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

    # إعداد نصّ الرسالة
    if report:
        text = f"📊 تقرير اختراقات السوق السعودي ({date.today()}):\n"
        for sym, pr in report:
            text += f"🔹 {sym} – {pr} ريال\n"
    else:
        text = f"🔎 لا توجد اختراقات جديدة اليوم ({date.today()})."

    # الإرسال إلى Telegram
    url    = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {'chat_id': chat_id, 'text': text, 'parse_mode':'HTML'}
    resp   = requests.post(url, params=params)
    if resp.status_code == 200:
        print("✅ تم الإرسال إلى Telegram")
    else:
        print(f"❌ خطأ {resp.status_code}: {resp.text}")

if __name__ == "__main__":
    run_report()
