from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app, supports_credentials=True)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'apex-fallback-2025')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)


class User(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    email    = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    alert_daily     = db.Column(db.Float, default=2.5)
    alert_monthly   = db.Column(db.Float, default=10.0)
    alert_quarterly = db.Column(db.Float, default=20.0)
    alert_revenue   = db.Column(db.Float, default=20.0)
    alert_earnings  = db.Column(db.Float, default=25.0)
    watchlist = db.relationship('Watchlist', backref='user', lazy=True)

    def get_id(self): return str(self.id)
    def is_authenticated(self): return True
    def is_active(self): return True
    def is_anonymous(self): return False


class Watchlist(db.Model):
    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol  = db.Column(db.String(10), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    from database import init_db
    init_db()
    db.create_all()


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/me')
def me():
    if current_user.is_authenticated:
        return jsonify({'email': current_user.email})
    return jsonify({'email': None})


@app.route('/api/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 400
        user = User(email=email, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        login_user(user)
        try:
            from emailer import send_welcome_email
            send_welcome_email(email)
        except Exception as e:
            print(f'Welcome email failed: {e}')
        return jsonify({'success': True, 'email': user.email})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, data.get('password', '')):
            return jsonify({'error': 'Invalid email or password'}), 401
        login_user(user)
        return jsonify({'success': True, 'email': user.email})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    logout_user()
    return jsonify({'success': True})


@app.route('/api/alerts', methods=['POST'])
def update_alerts():
    try:
        data = request.get_json()
        if current_user.is_authenticated:
            current_user.alert_daily     = float(data.get('daily', 2.5))
            current_user.alert_monthly   = float(data.get('monthly', 10.0))
            current_user.alert_quarterly = float(data.get('quarterly', 20.0))
            current_user.alert_revenue   = float(data.get('revenue', 20.0))
            current_user.alert_earnings  = float(data.get('earnings', 25.0))
            db.session.commit()
            try:
                from emailer import send_alerts_email
                send_alerts_email(current_user.email, data)
            except Exception as e:
                print(f'Alerts email failed: {e}')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    if not current_user.is_authenticated:
        return jsonify([])
    items = Watchlist.query.filter_by(user_id=current_user.id).all()
    return jsonify([{'symbol': w.symbol} for w in items])


@app.route('/api/watchlist', methods=['POST'])
def add_watchlist():
    try:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Please log in first'}), 401
        symbol = request.get_json().get('symbol', '').upper().strip()
        if Watchlist.query.filter_by(user_id=current_user.id, symbol=symbol).first():
            return jsonify({'error': f'{symbol} already in watchlist'}), 400
        db.session.add(Watchlist(user_id=current_user.id, symbol=symbol))
        db.session.commit()
        try:
            from emailer import send_watchlist_email
            send_watchlist_email(current_user.email, symbol)
        except Exception as e:
            print(f'Watchlist email failed: {e}')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/watchlist/<symbol>', methods=['DELETE'])
def remove_watchlist(symbol):
    try:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Please log in first'}), 401
        item = Watchlist.query.filter_by(
            user_id=current_user.id, symbol=symbol.upper()).first()
        if item:
            db.session.delete(item)
            db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/send-confirmation', methods=['POST'])
def send_confirmation():
    try:
        data = request.get_json()
        to_email = data.get('email')
        action = data.get('action')
        detail = data.get('detail', '')
        stock_data = data.get('stock_data')
        if not to_email:
            return jsonify({'error': 'No email'}), 400
        if action == 'watchlist':
            from emailer import send_watchlist_email
            send_watchlist_email(to_email, detail, stock_data)
        elif action == 'alerts':
            from emailer import send_alerts_email
            send_alerts_email(to_email, detail if isinstance(detail, dict) else {})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stock/<symbol>')
def get_stock(symbol):
    try:
        from data_fetcher import fetch_stock_data
        data = fetch_stock_data(symbol.upper())
        if not data:
            return jsonify({'error': f'No data for {symbol}'}), 404
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze/<symbol>')
def analyze(symbol):
    try:
        from data_fetcher import fetch_stock_data
        from analyzer import analyze_stock
        symbol = symbol.upper()
        data = fetch_stock_data(symbol)
        if not data:
            return jsonify({'error': f'No data for {symbol}'}), 404
        analysis = analyze_stock(symbol, data)
        return jsonify({'symbol': symbol, 'data': data, 'analysis': analysis})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/top-picks')
def top_picks():
    try:
        from analyzer import get_top_picks
        return jsonify(get_top_picks(limit=10))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sp500-symbols')
def sp500_symbols():
    try:
        from data_fetcher import get_sp500_symbols
        return jsonify(get_sp500_symbols())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sp500-all')
def sp500_all():
    try:
        from data_fetcher import get_all_stocks_with_fallback
        return jsonify(get_all_stocks_with_fallback())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/prefetch', methods=['POST'])
def prefetch():
    try:
        from data_fetcher import fetch_stock_data
        symbols = request.get_json().get('symbols', [])
        results = []
        for sym in symbols[:20]:
            try:
                d = fetch_stock_data(sym)
                if d and d.get('price'):
                    results.append(d)
            except Exception:
                pass
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/news')
def get_news():
    try:
        import requests as req
        key = os.getenv('NEWS_API_KEY', '')
        if not key:
            return jsonify([])
        url = f'https://newsapi.org/v2/everything?q=stock+market+S%26P500&sortBy=publishedAt&pageSize=12&language=en&apiKey={key}'
        r = req.get(url, timeout=10).json()
        return jsonify([{
            'title': a['title'],
            'description': a.get('description', ''),
            'url': a['url'],
            'source': a['source']['name'],
            'publishedAt': a['publishedAt']
        } for a in r.get('articles', []) if a.get('title')])
    except Exception as e:
        return jsonify([])


@app.route('/api/test-email')
def test_email():
    try:
        from emailer import send_welcome_email
        sender = os.getenv('EMAIL_ADDRESS')
        send_welcome_email(sender)
        return jsonify({'success': True, 'message': f'Test email sent to {sender}'})
    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
