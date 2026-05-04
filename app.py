"""
DriveLegal.ai - Flask Application
Main server for the Indian traffic law assistant.
IIT Madras Road Safety Hackathon 2026
"""

import os, json, sqlite3, datetime
from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
from dotenv import load_dotenv
import jwt
import bcrypt

# Load environment variables
load_dotenv()

# Initialize core modules
from rules_database import RulesDatabase
from challan_calculator import ChallanCalculator
from nlp_engine import NLPEngine

# App initialization
app = Flask(__name__, static_folder='static', static_url_path='')
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

# Initialize engines
db = RulesDatabase()
calc = ChallanCalculator(db)
nlp = NLPEngine(db)

# --- Database Setup ---
DATABASE = 'drivelegal.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                safety_score INTEGER DEFAULT 100
            )
        ''')
        # Chat history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_id TEXT NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        # Community hazards table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS community_hazards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT NOT NULL,
                lat REAL NOT NULL,
                lng REAL NOT NULL,
                description TEXT,
                upvotes INTEGER DEFAULT 0,
                reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()

# Initialize DB on startup
if not os.path.exists(DATABASE):
    init_db()


# --- Authentication Middleware ---
def token_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            parts = request.headers['Authorization'].split()
            if len(parts) == 2 and parts[0] == 'Bearer':
                token = parts[1]
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
            
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user_id = data['user_id']
        except Exception as e:
            return jsonify({'error': 'Token is invalid'}), 401
            
        return f(current_user_id, *args, **kwargs)
    return decorated


# --- Static Routes ---
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js')


# --- Auth Endpoints ---
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400
        
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (data['email'],))
        if cursor.fetchone():
            return jsonify({'error': 'Email already registered'}), 409
            
        # Hash password
        hashed = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        
        cursor.execute('''
            INSERT INTO users (email, password_hash, full_name, phone)
            VALUES (?, ?, ?, ?)
        ''', (data['email'], hashed.decode('utf-8'), data.get('full_name', ''), data.get('phone', '')))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'User registered successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400
        
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, password_hash, full_name FROM users WHERE email = ?', (data['email'],))
        user = cursor.fetchone()
        
        if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({'error': 'Invalid email or password'}), 401
            
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user['id'],
                'full_name': user['full_name'],
                'email': data['email']
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- Core Endpoints ---
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'db_loaded': db.is_data_loaded(),
        'ai_ready': nlp.gemini_model is not None
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    if not data or not data.get('message'):
        return jsonify({'error': 'Message is required'}), 400
        
    message = data['message']
    session_id = data.get('session_id', 'default')
    
    # Process through NLP engine
    response = nlp.process(message, session_id=session_id)
    
    # Log to DB if auth token provided (optional)
    if 'Authorization' in request.headers:
        try:
            parts = request.headers['Authorization'].split()
            if len(parts) == 2 and parts[0] == 'Bearer':
                token_data = jwt.decode(parts[1], app.config['SECRET_KEY'], algorithms=["HS256"])
                conn = get_db()
                conn.execute('''
                    INSERT INTO chat_history (user_id, session_id, message, response)
                    VALUES (?, ?, ?, ?)
                ''', (token_data['user_id'], session_id, message, response['text']))
                conn.commit()
        except Exception:
            pass # Ignore auth errors for chat logging
            
    return jsonify(response)

@app.route('/api/calculate', methods=['POST'])
def calculate_fine():
    data = request.json
    if not data or not data.get('violations'):
        return jsonify({'error': 'Violations array is required'}), 400
        
    vehicle_type = data.get('vehicle_type', 'car')
    state = data.get('state', None)
    is_repeat = data.get('is_repeat', False)
    
    result = calc.calculate_multiple(data['violations'], vehicle_type, state, is_repeat)
    return jsonify(result)

@app.route('/api/compare', methods=['GET'])
def compare_states():
    violation_key = request.args.get('violation')
    if not violation_key:
        return jsonify({'error': 'Violation key is required'}), 400
        
    vehicle_type = request.args.get('vehicle_type', 'car')
    is_repeat = request.args.get('is_repeat', 'false').lower() == 'true'
    
    result = calc.compare_states(violation_key, vehicle_type, is_repeat)
    return jsonify(result)

@app.route('/api/violations', methods=['GET'])
def get_violations():
    return jsonify(db.get_violation_names())

@app.route('/api/states', methods=['GET'])
def get_states():
    return jsonify({k: db.get_state_name(k) for k in db.get_all_state_keys()})

@app.route('/api/hazards', methods=['GET', 'POST'])
def hazards():
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        data = request.json
        # Allow anonymous hazard reporting for hackathon demo
        user_id = 0 
        
        if 'Authorization' in request.headers:
            try:
                parts = request.headers['Authorization'].split()
                if len(parts) == 2 and parts[0] == 'Bearer':
                    token_data = jwt.decode(parts[1], app.config['SECRET_KEY'], algorithms=["HS256"])
                    user_id = token_data['user_id']
            except Exception:
                pass
                
        cursor.execute('''
            INSERT INTO community_hazards (user_id, type, lat, lng, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, data['type'], data['lat'], data['lng'], data.get('description', '')))
        conn.commit()
        return jsonify({'success': True, 'id': cursor.lastrowid})
        
    else: # GET
        cursor.execute('''
            SELECT id, type, lat, lng, description, upvotes, reported_at 
            FROM community_hazards 
            WHERE reported_at >= date('now', '-7 days')
        ''')
        hazards = [dict(row) for row in cursor.fetchall()]
        return jsonify(hazards)



