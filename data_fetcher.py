import sqlite3
import math
from datetime import date

SP500 = [
    'MMM','AOS','ABT','ABBV','ACN','ADBE','AMD','AES','AFL','A','APD','ABNB',
    'AKAM','ALB','ARE','ALGN','ALLE','LNT','ALL','GOOGL','GOOG','MO','AMZN',
    'AEE','AAL','AEP','AXP','AIG','AMT','AWK','AMP','AME','AMGN','APH','ADI',
    'ANSS','AON','APA','AAPL','AMAT','APTV','ACGL','ADM','ANET','AJG','AIZ',
    'T','ATO','ADSK','ADP','AZO','AVB','AVY','AXON','BKR','BALL','BAC','BK',
    'BBWI','BAX','BDX','BRK-B','BBY','BIIB','BLK','BX','BA','BMY','AVGO',
    'BR','BRO','BSX','BWA','CDNS','CPT','CPB','COF','CAH','KMX','CCL','CARR',
    'CAT','CBOE','CBRE','CDW','CE','COR','CNC','CDAY','CF','CRL','SCHW',
    'CHTR','CVX','CMG','CB','CHD','CI','CINF','CTAS','CSCO','C','CFG','CLX',
    'CME','CMS','KO','CTSH','CL','CMCSA','CAG','COP','ED','STZ','CEG','COO',
    'CPRT','GLW','CTVA','CSGP','COST','CTRA','CCI','CSX','CMI','CVS','DHI',
    'DHR','DRI','DVA','DECK','DE','DAL','DVN','DXCM','FANG','DLR','DFS','DG',
    'DLTR','D','DPZ','DOV','DOW','DTE','DUK','DD','EMN','ETN','EBAY','ECL',
    'EIX','EW','EA','ELV','LLY','EMR','ENPH','ETR','EOG','EPAM','EQT','EFX',
    'EQIX','EQR','ESS','EL','ETSY','EG','ES','EXC','EXPE','EXPD','EXR','XOM',
    'FFIV','FDS','FICO','FAST','FRT','FDX','FIS','FITB','FSLR','FE','FI',
    'FLT','FMC','F','FTNT','FTV','FOXA','FOX','BEN','FCX','GRMN','IT','GE',
    'GEHC','GEN','GNRC','GD','GIS','GM','GPC','GILD','GPN','GL','GS','HAL',
    'HIG','HAS','HCA','HSIC','HSY','HES','HPE','HLT','HOLX','HD','HON','HRL',
    'HST','HWM','HPQ','HUBB','HUM','HBAN','HII','IBM','IEX','IDXX','ITW',
    'ILMN','INCY','IR','INTC','ICE','IFF','IP','IPG','INTU','ISRG','IVZ',
    'INVH','IQV','IRM','JBHT','JBL','JKHY','J','JNJ','JCI','JPM','JNPR','K',
    'KVUE','KDP','KEY','KEYS','KMB','KIM','KMI','KLAC','KHC','KR','LHX','LH',
    'LRCX','LW','LVS','LDOS','LEN','LIN','LYV','LKQ','LMT','L','LOW','LYB',
    'MTB','MRO','MPC','MKTX','MAR','MMC','MLM','MAS','MA','MTCH','MKC','MCD',
    'MCK','MDT','MRK','META','MET','MTD','MGM','MCHP','MU','MSFT','MAA',
    'MRNA','MHK','MOH','TAP','MDLZ','MPWR','MNST','MCO','MS','MOS','MSI',
    'MSCI','NDAQ','NTAP','NFLX','NEM','NWSA','NWS','NEE','NKE','NI','NDSN',
    'NSC','NTRS','NOC','NCLH','NRG','NUE','NVDA','NVR','NXPI','ORLY','OXY',
    'ODFL','OMC','ON','OKE','ORCL','OTIS','PCAR','PKG','PANW','PH','PAYX',
    'PAYC','PYPL','PNR','PEP','PFE','PCG','PM','PSX','PNW','PNC','POOL',
    'PPG','PPL','PFG','PG','PGR','PRU','PEG','PTC','PSA','PHM','PWR','QCOM',
    'DGX','RL','RJF','RTX','O','REG','REGN','RF','RSG','RMD','ROK','ROL',
    'ROP','ROST','RCL','SPGI','CRM','SBAC','SLB','STX','SRE','NOW','SHW',
    'SPG','SWKS','SJM','SNA','SO','LUV','SWK','SBUX','STT','STLD','STE',
    'SYK','SYF','SNPS','SYY','TMUS','TROW','TTWO','TPR','TRGP','TGT','TEL',
    'TDY','TFX','TER','TSLA','TXN','TXT','TMO','TJX','TSCO','TT','TDG',
    'TRV','TRMB','TFC','TYL','TSN','USB','UBER','UDR','ULTA','UNP','UAL',
    'UPS','URI','UNH','UHS','VLO','VTR','VRSN','VRSK','VZ','VRTX','V','VST',
    'VICI','VMC','GWW','WAB','WBA','WMT','DIS','WM','WAT','WEC','WFC','WELL',
    'WST','WDC','WY','WHR','WMB','WTW','WYNN','XEL','XYL','YUM','ZBRA','ZBH',
    'ZTS','AMCR','SOLV','WBD','PODD','VLTO'
]

def get_sp500_symbols():
    seen = set()
    result = []
    for s in SP500:
        if s not in seen:
            seen.add(s)
            result.append(s)
    return result

def _clean(v):
    try:
        if v is None: return None
        f = float(v)
        return None if math.isnan(f) or math.isinf(f) else f
    except Exception:
        return None

def fetch_stock_data(symbol):
    import yfinance as yf
    price = volume = revenue = cogs = sgna = interest = net_profit = None
    today_str = str(date.today())
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='5d')
        if not hist.empty:
            last = hist.iloc[-1]
            p = _clean(float(last['Close']))
            v = _clean(float(last['Volume']))
            if p: price = round(p, 2)
            if v: volume = int(v)
        if price is None:
            info = ticker.info
            raw = (info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose'))
            if raw: price = round(float(raw), 2)
            raw_v = info.get('regularMarketVolume') or info.get('volume')
            if raw_v: volume = int(raw_v)
        fin = ticker.financials
        if fin is not None and not fin.empty:
            def gf(*labels):
                for lbl in labels:
                    if lbl in fin.index:
                        c = _clean(fin.loc[lbl].iloc[0])
                        if c is not None: return float(c)
                return None
            revenue    = gf('Total Revenue')
            cogs       = gf('Cost Of Revenue','Cost of Revenue')
            sgna       = gf('Selling General Administrative','Selling General And Administration')
            interest   = gf('Interest Expense','Interest Expense Non Operating')
            net_profit = gf('Net Income','Net Income Common Stockholders')
    except Exception as e:
        print(f'yfinance error for {symbol}: {e}')
        cached = _get_cached(symbol)
        if cached: return cached

    if price is None:
        cached = _get_cached(symbol)
        if cached: return cached

    gross_margin = net_margin = None
    if revenue and revenue != 0:
        if cogs is not None: gross_margin = round(((revenue - cogs) / revenue) * 100, 2)
        if net_profit is not None: net_margin = round((net_profit / revenue) * 100, 2)

    stock_info = {
        'symbol': symbol, 'date': today_str,
        'price': _clean(price),
        'volume': int(volume) if volume else None,
        'revenue': _clean(revenue), 'cogs': _clean(cogs),
        'sgna': _clean(sgna), 'interest_expense': _clean(interest),
        'net_profit': _clean(net_profit),
        'gross_margin': _clean(gross_margin), 'net_margin': _clean(net_margin),
    }
    if stock_info['price']:
        save_to_db(stock_info)
    return stock_info

def _get_cached(symbol):
    try:
        conn = sqlite3.connect('stocks.db')
        c = conn.cursor()
        c.execute('''SELECT symbol,date,price,volume,revenue,cogs,sgna,
                     interest_expense,net_profit,gross_margin,net_margin
                     FROM daily_metrics WHERE symbol=?
                     ORDER BY fetched_at DESC LIMIT 1''', (symbol,))
        row = c.fetchone()
        conn.close()
        if row:
            cols = ['symbol','date','price','volume','revenue','cogs','sgna',
                    'interest_expense','net_profit','gross_margin','net_margin']
            return {k: _clean(v) if k not in ('symbol','date') else v
                    for k,v in zip(cols,row)}
    except Exception as e:
        print(f'Cache lookup failed for {symbol}: {e}')
    return None

def save_to_db(data):
    conn = sqlite3.connect('stocks.db')
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO daily_metrics
        (symbol,date,price,volume,revenue,cogs,sgna,
         interest_expense,net_profit,gross_margin,net_margin)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)''', (
        data['symbol'],data['date'],data['price'],data['volume'],
        data['revenue'],data['cogs'],data['sgna'],data['interest_expense'],
        data['net_profit'],data['gross_margin'],data['net_margin']))
    conn.commit()
    conn.close()

def get_all_stocks_with_fallback():
    symbols = get_sp500_symbols()
    try:
        conn = sqlite3.connect('stocks.db')
        c = conn.cursor()
        c.execute('''SELECT symbol,date,price,volume,revenue,cogs,sgna,
                     interest_expense,net_profit,gross_margin,net_margin
                     FROM daily_metrics WHERE fetched_at=(
                     SELECT MAX(fetched_at) FROM daily_metrics d2
                     WHERE d2.symbol=daily_metrics.symbol)''')
        rows = c.fetchall()
        conn.close()
        cols = ['symbol','date','price','volume','revenue','cogs','sgna',
                'interest_expense','net_profit','gross_margin','net_margin']
        cached = {r[0]: {k: _clean(v) if k not in ('symbol','date') else v
                         for k,v in zip(cols,r)} for r in rows}
    except Exception:
        cached = {}
    result = []
    for sym in symbols:
        if sym in cached and cached[sym].get('price'):
            result.append(cached[sym])
        else:
            result.append({'symbol':sym,'date':None,'price':None,'volume':None,
                          'revenue':None,'cogs':None,'sgna':None,
                          'interest_expense':None,'net_profit':None,
                          'gross_margin':None,'net_margin':None})
    return result
