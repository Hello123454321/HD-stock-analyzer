import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

def analyze_stock(symbol, stock_data):
    from groq import Groq
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        return "AI analysis unavailable — no API key configured."
    client = Groq(api_key=api_key)
    prompt = f"""You are a financial analyst. Analyze this stock data for {symbol} and provide clear educational insights. Do NOT give direct buy/sell recommendations.

Stock Data for {symbol}:
- Current Price: ${stock_data.get('price', 'N/A')}
- Daily Volume: {stock_data.get('volume', 'N/A')}
- Quarterly Revenue: ${stock_data.get('revenue', 'N/A')}
- Cost of Goods: ${stock_data.get('cogs', 'N/A')}
- SG&A Expenses: ${stock_data.get('sgna', 'N/A')}
- Interest Expense: ${stock_data.get('interest_expense', 'N/A')}
- Net Profit: ${stock_data.get('net_profit', 'N/A')}
- Gross Margin: {stock_data.get('gross_margin', 'N/A')}%
- Net Margin: {stock_data.get('net_margin', 'N/A')}%

Please provide:
1. **Health Summary** - Is this company financially strong, moderate, or concerning? Why?
2. **Key Strengths** - What does the data show that is positive?
3. **Key Risks** - What concerns does the data raise?
4. **What to Watch** - What should an investor monitor?

Keep it clear, educational, and under 300 words."""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    return response.choices[0].message.content

def get_top_picks(limit=10):
    conn = sqlite3.connect('stocks.db')
    c = conn.cursor()
    c.execute('''
        SELECT symbol, price, volume, revenue, net_profit, gross_margin, net_margin
        FROM daily_metrics
        WHERE net_margin IS NOT NULL AND revenue > 0
        ORDER BY net_margin DESC
        LIMIT ?
    ''', (limit,))
    rows = c.fetchall()
    conn.close()
    columns = ['symbol','price','volume','revenue','net_profit','gross_margin','net_margin']
    return [dict(zip(columns, row)) for row in rows]
