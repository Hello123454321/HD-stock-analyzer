from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
from database import init_db
from data_fetcher import fetch_stock_data, get_sp500_symbols
from analyzer import analyze_stock, get_top_picks

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Initialize database on startup
init_db()

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/stock/<symbol>', methods=['GET'])
def get_stock(symbol):
    """Fetch and return data for a single stock"""
    symbol = symbol.upper()
    data = fetch_stock_data(symbol)
    if not data:
        return jsonify({'error': f'Could not fetch data for {symbol}'}), 404
    return jsonify(data)

@app.route('/api/analyze/<symbol>', methods=['GET'])
def analyze(symbol):
    """Get Claude's analysis for a stock"""
    symbol = symbol.upper()
    data = fetch_stock_data(symbol)
    if not data:
        return jsonify({'error': f'No data found for {symbol}'}), 404
    
    analysis = analyze_stock(symbol, data)
    return jsonify({
        'symbol': symbol,
        'data': data,
        'analysis': analysis
    })

@app.route('/api/top-picks', methods=['GET'])
def top_picks():
    """Return top stocks by net margin"""
    picks = get_top_picks(limit=10)
    return jsonify(picks)

@app.route('/api/sp500-symbols', methods=['GET'])
def sp500_symbols():
    """Return list of all S&P 500 symbols"""
    symbols = get_sp500_symbols()
    return jsonify(symbols)

if __name__ == '__main__':
    app.run(debug=True, port=5000)