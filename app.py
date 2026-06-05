import os
import datetime
import hashlib
import json
import joblib
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from db_connection import get_db_connection, execute_query, ENV

app = Flask(__name__, static_folder='frontend', static_url_path='')
app.secret_key = ENV.get('SECRET_KEY', 'default_secret_key_123')

# Load models and features list
MODELS = {}
model_features = None
FEATURES_PATH = 'ml/model_features.json'

model_paths = {
    'random_forest': 'ml/random_forest.pkl',
    'decision_tree': 'ml/decision_tree.pkl',
    'logistic_regression': 'ml/logistic_regression.pkl'
}

for name, path in model_paths.items():
    if os.path.exists(path):
        try:
            MODELS[name] = joblib.load(path)
            print(f"ML model '{name}' loaded successfully.")
        except Exception as e:
            print(f"Error loading ML model '{name}': {e}")
    else:
        print(f"Warning: ML model '{name}' not found.")

if os.path.exists(FEATURES_PATH):
    try:
        with open(FEATURES_PATH) as f:
            model_features = json.load(f)
        print("Features list loaded successfully.")
    except Exception as e:
        print(f"Error loading feature list: {e}")
else:
    print("Warning: Features list file not found.")

# Helper function for password checking
def verify_password(password, hashed):
    try:
        salt_hex, hash_hex = hashed.split('$')
        salt = bytes.fromhex(salt_hex)
        hash_val = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return hash_val.hex() == hash_hex
    except Exception:
        return False

def hash_password(password):
    salt = os.urandom(16)
    hash_val = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return salt.hex() + '$' + hash_val.hex()

# Static routes to serve the frontend pages
@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def serve_page(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return app.send_static_file(path)
    return app.send_static_file('index.html')

# API Route: User Registration
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    full_name = data.get('full_name')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')
    
    if not (full_name and email and password):
        return jsonify({'error': 'Missing required fields'}), 400
        
    hashed_pass = hash_password(password)
    try:
        user_id = execute_query(
            "INSERT INTO users (full_name, email, phone, password_hash, balance) VALUES (%s, %s, %s, %s, %s);",
            (full_name, email, phone, hashed_pass, 5000.00),
            commit=True
        )
        return jsonify({'success': True, 'message': 'Registration successful', 'user_id': user_id})
    except Exception as e:
        if 'Duplicate entry' in str(e):
            return jsonify({'error': 'Email or phone already registered'}), 400
        return jsonify({'error': str(e)}), 500

# API Route: User Login
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    ip_address = request.remote_addr
    location = data.get('location', 'Local')
    
    if not (email and password):
        return jsonify({'error': 'Email and password required'}), 400
        
    user = execute_query("SELECT user_id, full_name, password_hash, balance FROM users WHERE email = %s;", (email,), fetch=True)
    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401
        
    user = user[0]
    if verify_password(password, user['password_hash']):
        # Log successful login activity
        execute_query(
            "INSERT INTO login_activity (user_id, ip_address, location, status) VALUES (%s, %s, %s, %s);",
            (user['user_id'], ip_address, location, 'success'),
            commit=True
        )
        return jsonify({
            'success': True,
            'user_id': user['user_id'],
            'full_name': user['full_name'],
            'balance': float(user['balance']),
            'role': 'customer'
        })
    else:
        # Log failed login activity
        execute_query(
            "INSERT INTO login_activity (user_id, ip_address, location, status) VALUES (%s, %s, %s, %s);",
            (user['user_id'], ip_address, location, 'failed'),
            commit=True
        )
        return jsonify({'error': 'Invalid email or password'}), 401

# API Route: Admin Login
@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not (email and password):
        return jsonify({'error': 'Email and password required'}), 400
        
    user = execute_query("SELECT user_id, full_name, password_hash FROM users WHERE email = %s;", (email,), fetch=True)
    if not user:
        return jsonify({'error': 'Invalid admin credentials'}), 401
        
    user = user[0]
    if email == 'admin@fraudguard.ai' and verify_password(password, user['password_hash']):
        return jsonify({
            'success': True,
            'user_id': user['user_id'],
            'full_name': user['full_name'],
            'role': 'admin'
        })
    else:
        return jsonify({'error': 'Invalid admin credentials'}), 401

# API Route: Get/Post Security Settings
@app.route('/api/security/settings', methods=['GET', 'POST'])
def api_security_settings():
    if request.method == 'GET':
        settings = execute_query("SELECT setting_key, setting_value FROM security_settings;", fetch=True)
        settings_dict = {row['setting_key']: row['setting_value'] for row in settings}
        return jsonify(settings_dict)
    else:
        data = request.json
        for key, val in data.items():
            execute_query(
                "INSERT INTO security_settings (setting_key, setting_value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE setting_value = %s;",
                (key, str(val), str(val)),
                commit=True
            )
        return jsonify({'success': True, 'message': 'Settings updated'})

# API Route: Get Dashboard Statistics
@app.route('/api/dashboard/stats', methods=['GET'])
def api_dashboard_stats():
    total_txns = execute_query("SELECT COUNT(*) as count FROM transactions;", fetch=True)[0]['count']
    blocked_txns = execute_query("SELECT COUNT(*) as count FROM fraud_results WHERE is_fraud = 1;", fetch=True)[0]['count']
    
    # Calculate Trust Score: percentage of safe transactions
    trust_score = 98.5  # default/base
    if total_txns > 0:
        trust_score = round(((total_txns - blocked_txns) / total_txns) * 100, 1)
        
    return jsonify({
        'totalScanned': total_txns,
        'fraudBlocked': blocked_txns,
        'trustScore': f"{trust_score}%"
    })

# API Route: Get Transaction List
@app.route('/api/transactions', methods=['GET'])
def api_get_transactions():
    query = """
        SELECT t.transaction_id, t.user_id, u.full_name, t.amount, t.transaction_type, 
               t.location, t.transaction_time, f.is_fraud, f.fraud_score, f.rules_triggered
        FROM transactions t
        JOIN users u ON t.user_id = u.user_id
        LEFT JOIN fraud_results f ON t.transaction_id = f.transaction_id
        ORDER BY t.transaction_time DESC;
    """
    transactions = execute_query(query, fetch=True)
    # Format database rows for JSON output
    for txn in transactions:
        txn['amount'] = float(txn['amount'])
        txn['fraud_score'] = float(txn['fraud_score']) if txn['fraud_score'] else 0.0
        txn['is_fraud'] = bool(txn['is_fraud']) if txn['is_fraud'] is not None else False
        txn['transaction_time'] = txn['transaction_time'].strftime('%d %b %Y, %H:%M')
    return jsonify(transactions)

# API Route: Analyze and Add Transaction
@app.route('/api/transactions', methods=['POST'])
def api_add_transaction():
    data = request.json
    user_id = data.get('user_id')
    amount = float(data.get('amount', 0))
    txn_type = data.get('transaction_type', 'PAYMENT').upper()
    location = data.get('location', 'Local')
    device_id = data.get('device_id', 'unknown_device')
    ip_address = data.get('ip_address', request.remote_addr)
    device_type = data.get('device_type', 'Desktop')
    os_name = data.get('os', 'Windows')
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
        
    user = execute_query("SELECT full_name, balance FROM users WHERE user_id = %s;", (user_id,), fetch=True)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    user = user[0]
    user_balance = float(user['balance'])
    
    # 1. Fetch Security Settings
    settings = execute_query("SELECT setting_key, setting_value FROM security_settings;", fetch=True)
    settings_dict = {row['setting_key']: row['setting_value'] for row in settings}
    
    auto_block_threshold = float(settings_dict.get('auto_block_threshold', 75.0))
    block_international = settings_dict.get('block_international', 'false').lower() == 'true'
    blacklist = [acc.strip() for acc in settings_dict.get('blacklist_accounts', '').split(',') if acc.strip()]
    
    # 2. Rule Heuristics
    rules_triggered = []
    fraud_score_modifier = 0.0
    
    # Check Blacklist
    # Treat user email or full name matching blacklist as hit, or if user_id is matched
    if str(user_id) in blacklist or f"ACC-{user_id}" in blacklist:
        rules_triggered.append("Blacklisted Account")
        fraud_score_modifier += 100.0
        
    # Check Location Rules
    if location != 'Local':
        if block_international:
            rules_triggered.append("International Payment Blocked")
            fraud_score_modifier += 100.0
        else:
            rules_triggered.append("Unusual Location")
            fraud_score_modifier += 20.0
            
    # Check Device Rules
    # Look up if device_id is already linked to user
    device_linked = execute_query(
        "SELECT 1 FROM user_devices WHERE device_id = %s AND user_id = %s;",
        (device_id, user_id),
        fetch=True
    )
    if not device_linked:
        rules_triggered.append("New Device Login")
        fraud_score_modifier += 25.0
        
    # Check Velocity Rules (more than 3 transactions in the last 5 minutes)
    five_min_ago = datetime.datetime.now() - datetime.timedelta(minutes=5)
    recent_txn_count = execute_query(
        "SELECT COUNT(*) as count FROM transactions WHERE user_id = %s AND transaction_time >= %s;",
        (user_id, five_min_ago),
        fetch=True
    )[0]['count']
    if recent_txn_count >= 3:
        rules_triggered.append("High Velocity")
        fraud_score_modifier += 30.0
        
    # Check High Amount Anomaly
    if amount > 10000.0:
        rules_triggered.append("High Amount Anomaly")
        fraud_score_modifier += 15.0
        
    # 3. Machine Learning Inference
    ml_score = 0.0
    active_model_name = settings_dict.get('active_model', 'random_forest')
    active_model = MODELS.get(active_model_name)
    
    # fallback if specified model is not loaded
    if active_model is None:
        for name, m in MODELS.items():
            active_model = m
            active_model_name = name
            break
            
    if active_model is not None and model_features is not None:
        try:
            # We derive 'step' as number of hours from some starting point. Let's use current hour of the week.
            now = datetime.datetime.now()
            step = (now.weekday() * 24) + now.hour + 1
            hour = (step - 1) % 24
            
            # Prepare feature dictionary matching ML training schema
            features = {
                'step': step,
                'amount': amount,
                'oldbalanceOrg': user_balance,
                'newbalanceOrig': max(0.0, user_balance - amount),
                'oldbalanceDest': 0.0,  # We don't have destination account info in user schema, default 0
                'newbalanceDest': amount,
                'hour': hour,
                'type_CASH_IN': 1 if txn_type == 'CASH_IN' else 0,
                'type_CASH_OUT': 1 if txn_type == 'CASH_OUT' else 0,
                'type_DEBIT': 1 if txn_type == 'DEBIT' else 0,
                'type_PAYMENT': 1 if txn_type == 'PAYMENT' else 0,
                'type_TRANSFER': 1 if txn_type == 'TRANSFER' else 0
            }
            
            # Align features with serialized model feature columns
            df_in = pd.DataFrame([features])[model_features]
            
            # Predict probabilities
            probabilities = active_model.predict_proba(df_in)[0]
            ml_score = float(probabilities[1]) * 100.0  # Fraud probability in %
            print(f"ML Model ({active_model_name}) risk probability: {ml_score:.2f}%")
        except Exception as ex:
            print(f"ML inference exception: {ex}")
            # Fallback score if model inference fails
            ml_score = 10.0 if amount > 5000 else 2.0
    else:
        # Fallback score if model not loaded
        ml_score = 10.0 if amount > 5000 else 2.0
        
    # 4. Compute Combined Score
    # Risk score combines the ML model probability and our rule-based heuristic weights
    total_risk_score = min(100.0, max(0.0, ml_score + fraud_score_modifier))
    is_fraud = total_risk_score >= auto_block_threshold
    
    # 5. Insert transaction & result, update balance if safe
    transaction_id = execute_query(
        """INSERT INTO transactions (user_id, amount, transaction_type, location, device_id, ip_address) 
           VALUES (%s, %s, %s, %s, %s, %s);""",
        (user_id, amount, txn_type, location, device_id, ip_address),
        commit=True
    )
    
    # Record analysis results
    rules_str = ", ".join(rules_triggered) if rules_triggered else "None"
    model_version_str = f"{active_model_name.upper()}_v1.0"
    execute_query(
        """INSERT INTO fraud_results (transaction_id, is_fraud, fraud_score, model_version, rules_triggered) 
           VALUES (%s, %s, %s, %s, %s);""",
        (transaction_id, 1 if is_fraud else 0, total_risk_score, model_version_str, rules_str),
        commit=True
    )
    
    # Link device if new
    if not device_linked:
        execute_query(
            "INSERT INTO user_devices (device_id, user_id, device_type, os) VALUES (%s, %s, %s, %s);",
            (device_id, user_id, device_type, os_name),
            commit=True
        )
        
    new_balance = user_balance
    if not is_fraud:
        # Deduct transaction amount from user's account balance
        new_balance = max(0.0, user_balance - amount)
        execute_query("UPDATE users SET balance = %s WHERE user_id = %s;", (new_balance, user_id), commit=True)
        
    return jsonify({
        'success': True,
        'transaction_id': f"TXN-{transaction_id}",
        'is_fraud': is_fraud,
        'fraud_score': round(total_risk_score, 1),
        'rules_triggered': rules_triggered,
        'new_balance': new_balance
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
