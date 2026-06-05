import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import json
import os

def generate_synthetic_data(num_rows=50000):
    print(f"PaySim dataset not found. Generating {num_rows} rows of realistic synthetic transaction data...")
    np.random.seed(42)
    
    # Generate random features
    step = np.random.randint(1, 744, size=num_rows)
    hour = (step - 1) % 24
    
    types = ['PAYMENT', 'TRANSFER', 'CASH_OUT', 'DEBIT', 'CASH_IN']
    type_col = np.random.choice(types, size=num_rows, p=[0.35, 0.20, 0.35, 0.02, 0.08])
    
    amount = np.random.exponential(scale=500, size=num_rows) + 1.0
    # Add some high-value spikes
    spikes = np.random.choice([0, 1], size=num_rows, p=[0.98, 0.02])
    amount += spikes * np.random.exponential(scale=15000, size=num_rows)
    
    oldbalanceOrg = np.random.exponential(scale=10000, size=num_rows)
    newbalanceOrig = np.maximum(0, oldbalanceOrg - amount)
    
    oldbalanceDest = np.random.exponential(scale=20000, size=num_rows)
    # CASH_IN increases sender balance; CASH_OUT/TRANSFER/DEBIT/PAYMENT increase destination balance
    newbalanceDest = np.where(
        (type_col == 'CASH_OUT') | (type_col == 'TRANSFER'),
        oldbalanceDest + amount,
        np.where(type_col == 'CASH_IN', np.maximum(0, oldbalanceDest - amount), oldbalanceDest)
    )
    
    # Generate isFraud label based on anomalies
    # Fraud criteria:
    # 1. High value TRANSFER or CASH_OUT
    # 2. Large amount but sender balance is unchanged or recipient balance doesn't increase
    # 3. Operations at late night hours (1am - 5am) with high amounts
    is_fraud = np.zeros(num_rows, dtype=int)
    
    for i in range(num_rows):
        fraud_prob = 0.001  # Base fraud rate (0.1%)
        
        t = type_col[i]
        amt = amount[i]
        hr = hour[i]
        
        if t in ['TRANSFER', 'CASH_OUT']:
            if amt > 10000:
                fraud_prob += 0.60
            if abs(newbalanceDest[i] - oldbalanceDest[i]) < 0.01:
                fraud_prob += 0.30
        
        if hr >= 1 and hr <= 5:
            if amt > 5000:
                fraud_prob += 0.25
                
        if amt > 50000:
            fraud_prob += 0.50
            
        is_fraud[i] = np.random.choice([0, 1], p=[max(0.0, 1.0 - fraud_prob), min(1.0, fraud_prob)])
        
    df = pd.DataFrame({
        'step': step,
        'type': type_col,
        'amount': amount,
        'oldbalanceOrg': oldbalanceOrg,
        'newbalanceOrig': newbalanceOrig,
        'oldbalanceDest': oldbalanceDest,
        'newbalanceDest': newbalanceDest,
        'isFraud': is_fraud
    })
    return df

def main():
    csv_path = os.path.join(os.path.dirname(__file__), 'new_file.csv')
    
    if os.path.exists(csv_path):
        print("Loading PaySim dataset from CSV...")
        chunk_size = 500000
        print(f"Reading first {chunk_size} rows...")
        df = pd.read_csv(csv_path, nrows=chunk_size)
    else:
        df = generate_synthetic_data(50000)
        
    print(f"Dataset shape: {df.shape}")
    print(f"Fraud distribution:\n{df['isFraud'].value_counts()}")
    
    # Feature Engineering
    print("Engineering features...")
    df['hour'] = (df['step'] - 1) % 24
    
    # Drop unused columns
    df.drop(['nameOrig', 'nameDest', 'isFlaggedFraud'], axis=1, errors='ignore', inplace=True)
    
    # One-hot encode the 'type' column
    df_enc = pd.get_dummies(df, columns=['type'])
    
    # Ensure all expected dummy columns are present
    expected_dummies = ['type_CASH_IN', 'type_CASH_OUT', 'type_DEBIT', 'type_PAYMENT', 'type_TRANSFER']
    for col in expected_dummies:
        if col not in df_enc.columns:
            df_enc[col] = False
            
    # Prepare features and labels
    X = df_enc.drop('isFraud', axis=1)
    y = df_enc['isFraud']
    
    # Align feature columns to a fixed order
    feature_cols = [
        'step', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 
        'oldbalanceDest', 'newbalanceDest', 'hour',
        'type_CASH_IN', 'type_CASH_OUT', 'type_DEBIT', 'type_PAYMENT', 'type_TRANSFER'
    ]
    X = X[feature_cols]
    
    # Split dataset
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    
    # Define models
    models = {
        'random_forest': RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1, class_weight='balanced'),
        'decision_tree': DecisionTreeClassifier(max_depth=10, random_state=42, class_weight='balanced'),
        'logistic_regression': make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
        )
    }
    
    # Train and evaluate each model
    for name, clf in models.items():
        print(f"\n==================================================")
        print(f"Training {name} Classifier...")
        clf.fit(X_train, y_train)
        
        y_pred = clf.predict(X_test)
        print(f"Evaluating {name}...")
        print("Confusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        print("Classification Report:")
        print(classification_report(y_test, y_pred))
        
        # Save model
        model_path = os.path.join(os.path.dirname(__file__), f"{name}.pkl")
        print(f"Saving model to {model_path}...")
        joblib.dump(clf, model_path)
        
    # Save feature configuration
    features_path = os.path.join(os.path.dirname(__file__), 'model_features.json')
    print(f"Saving features list to {features_path}...")
    with open(features_path, 'w') as f:
        json.dump(feature_cols, f)
        
    print("\nAll model training tasks completed successfully!")

if __name__ == '__main__':
    main()
