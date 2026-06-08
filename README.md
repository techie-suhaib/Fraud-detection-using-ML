# FraudGuard AI - Fraud Detection System

## 1. Project Overview
FraudGuard AI combines **heuristic rules** (velocity checks, location anomalies, amount thresholds) with a **machine-learning model** to produce a risk score for every transaction. A web-based dashboard lets administrators configure security policies and review transaction logs in real time.

## 2. Technologies Used
* **Python 3.10+**: Core backend language; runs Flask API and ML inference.
* **Flask**: Lightweight REST API server (`app.py`). Serves all `/api/` endpoints.
* **MySQL**: Relational database storing users, transactions, and security config.
* **HTML / CSS / JS**: Frontend pages in the `frontend/` directory (user, admin, transactions).
* **scikit-learn**: ML library used to train Random Forest, Decision Tree, and Logistic Regression models.
* **pandas / numpy**: Data manipulation and feature engineering for model training.
* **joblib**: Serialises trained models to `.pkl` files for fast loading at runtime.

## 3. Key Definitions
* **Velocity Rule**: Detects >= 2 transactions from the same device within 60 s. Triggers an immediate HIGH RISK block (+50 risk pts).
* **Unusual Location**: Transaction from a different country than the user's registered location. Adds +35 risk points (warning, not blocked by default).
* **High Amount Anomaly**: Amount > $10,000. Adds +50 risk points and causes an immediate block.
* **Risk Score**: Cumulative score from heuristic rules + ML probability. Score >= 100 = HIGH RISK.
* **Risk Levels**: Low (0-49), Medium (50-99), High (>=100 blocked).
* **New Device Login**: Transaction from a device ID not previously linked to the account. Shows a warning badge but does not block.
* **Blacklisted Account**: Admin has manually banned the user ID. All transactions blocked immediately.
* **Int'l Payment Block**: Admin security policy that blocks all transactions flagged as International.
* **fraud_model.pkl**: Primary Random Forest model loaded by `app.py` for real-time inference.

## 4. Terminal Instructions (How to Run)

### Prerequisites
* **Python 3.10+**
* **MySQL Server 8.0+** (must be running before executing `db_setup.py`)
* **pip** (latest version)

### Step 1 - Clone the Repository
```bash
git clone https://github.com/techie-suhaib/Fraud-detection-using-ML.git
cd "Fraud Detection using ML"
```

### Step 2 - Create a Virtual Environment (Recommended)
```bash
# Create the virtual environment
python -m venv venv

# Activate it (Windows PowerShell)
.\venv\Scripts\activate

# Activate it (Windows CMD)
venv\Scripts\activate.bat

# Activate it (macOS / Linux)
source venv/bin/activate
```

### Step 3 - Install Python Dependencies
```bash
python -m pip install --upgrade pip
python -m pip install flask mysql-connector-python scikit-learn pandas numpy joblib reportlab
```

### Step 4 - Configure the .env File
The project reads database credentials from a `.env` file in the project root. Create or edit it:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=fraud_detection_db

SECRET_KEY=fraud_guard_ai_secret_key_123!@#
```

### Step 5 - Train the Machine Learning Models
Run the training script **before** starting the Flask server.
```bash
python ml/train_model.py
```
*(If no CSV dataset is present, it automatically synthesises 50,000 realistic transactions for training.)*

### Step 6 - Initialise the Database
Creates the `fraud_detection_db` MySQL database and seeds default accounts and settings.
```bash
python db_setup.py
```

### Step 7 - Start the Flask Server
```bash
python app.py
```
The server will start on `http://127.0.0.1:5000`.

## 5. Default Login Credentials
* **Admin**: `admin@fraudguard.ai` / `admin123` -> `http://127.0.0.1:5000/admin.html`
* **Regular User**: `user@test.com` / `user123` -> `http://127.0.0.1:5000/user.html`

## 6. Admin Setup (Security Policies)
1. Open `http://127.0.0.1:5000/admin.html` and log in as Admin.
2. Click the **Security** link to open `security.html`.
3. Toggle **Block International Payments** ON.
4. In **Account Blacklist**, type `2` (test user ID) and click **Ban Account**.
5. Click **Save Changes**.

## 7. Verification Scenario Table
Use the Location and Device selectors in the transaction form (`user.html`) for each scenario. Complete the admin setup (Section 6) before running scenarios 6 and 7.

| # | Amount ($) | Location | Device | Expected Outcome |
|---|---|---|---|---|
| 1 | 150 | Local | Same Device (Linked) | Transaction Safe |
| 2 | 200 | Local | New Device (Unlinked) | Transaction Safe + New Device Login badge |
| 3 | 10->10->50 (same) | Local | Same Device (Linked) | HIGH RISK BLOCKED (High Velocity) |
| 4 | 12,000 | Local | Same Device (Linked) | HIGH RISK BLOCKED (High Amount Anomaly) |
| 5 | 100 | International | Same Device (Linked) | Transaction Safe (Unusual Location warning) |
| 6 | 100 | International | Same Device (Linked) after enabling Block Int'l Payments | HIGH RISK BLOCKED (Int'l Payment Blocked) |
| 7 | 50 | Local | Same Device (Linked) after blacklisting user 2 | HIGH RISK BLOCKED (Blacklisted Account) |

## 8. Viewing the Transaction Log
After running the scenarios, open `http://127.0.0.1:5000/transaction.html` to verify each row shows the correct Risk Level and Status badge.
