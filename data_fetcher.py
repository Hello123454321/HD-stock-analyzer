import yfinance as yf
import sqlite3

def fetch_stock_data(symbol):
    ticker = yf.Ticker(symbol)
    
    # Get price and volume
    hist = ticker.history(period="1d")
    info = ticker.info
    financials = ticker.financials
    
    if hist.empty:
        return None
    
    latest = hist.iloc[-1]
    
    # Pull financials safely
    def get_fin(label):
        try:
            return float(financials.loc[label].iloc[0]) if label in financials.index else None
        except:
            return None

    revenue = get_fin('Total Revenue')
    cogs = get_fin('Cost Of Revenue')
    sgna = get_fin('Selling General Administrative')
    interest = get_fin('Interest Expense')
    net_profit = get_fin('Net Income')

    gross_margin = ((revenue - (cogs or 0)) / revenue * 100) if revenue else None
    net_margin = (net_profit / revenue * 100) if (revenue and net_profit) else None

    stock_info = {
        'symbol': symbol,
        'date': str(latest.name.date()),
        'price': round(float(latest['Close']), 2),
        'volume': int(latest['Volume']),
        'revenue': revenue,
        'cogs': cogs,
        'sgna': sgna,
        'interest_expense': interest,
        'net_profit': net_profit,
        'gross_margin': round(gross_margin, 2) if gross_margin else None,
        'net_margin': round(net_margin, 2) if net_margin else None,
    }

    save_to_db(stock_info)
    return stock_info

def save_to_db(data):
    conn = sqlite3.connect('stocks.db')
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO daily_metrics 
        (symbol, date, price, volume, revenue, cogs, sgna, interest_expense, net_profit, gross_margin, net_margin)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['symbol'], data['date'], data['price'], data['volume'],
        data['revenue'], data['cogs'], data['sgna'], data['interest_expense'],
        data['net_profit'], data['gross_margin'], data['net_margin']
    ))
    conn.commit()
    conn.close()

def get_sp500_symbols():
    import requests
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = __import__('pandas').read_html(url)
    return tables[0]['Symbol'].tolist()