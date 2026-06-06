import os
import sys
import datetime
from db_setup import setup_database
from app import app
from db_connection import execute_query, get_db_connection

def clear_transactions():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("TRUNCATE TABLE transactions;")
        cursor.execute("TRUNCATE TABLE fraud_results;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def clear_all_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("TRUNCATE TABLE fraud_results;")
        cursor.execute("TRUNCATE TABLE transactions;")
        cursor.execute("TRUNCATE TABLE user_devices;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conn.commit()
        print("Database tables cleared successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Error clearing tables: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

def reset_test_state():
    clear_transactions()
    execute_query("UPDATE users SET balance = 5000.00 WHERE user_id = 2;", commit=True)

def main():
    print("Initializing and seeding database...")
    setup_database()
    
    # Clean tables within a single session
    clear_all_tables()
    
    # Ensure default settings are active
    execute_query("UPDATE security_settings SET setting_value = '75.00' WHERE setting_key = 'auto_block_threshold';", commit=True)
    execute_query("UPDATE security_settings SET setting_value = 'false' WHERE setting_key = 'block_international';", commit=True)
    execute_query("UPDATE security_settings SET setting_value = 'ACC-99201,ACC-44122' WHERE setting_key = 'blacklist_accounts';", commit=True)
    execute_query("UPDATE security_settings SET setting_value = 'random_forest' WHERE setting_key = 'active_model';", commit=True)
    
    # Configure test client
    client = app.test_client()
    
    print("\nStarting Scenarios Verification...\n")
    
    # ----------------------------------------------------
    # SCENARIO 1: Safe Payment
    # Amount: $150.00, Location: Local, Device: Same
    # Expected: Approved (is_fraud=False, risk score low, balance debited)
    # ----------------------------------------------------
    print("--- Scenario 1: Safe Payment ---")
    reset_test_state()
    # First ensure a device is linked to make it "Same"
    execute_query("INSERT INTO user_devices (device_id, user_id, device_type, os) VALUES ('dev_same_123', 2, 'Desktop', 'Windows');", commit=True)
    
    payload1 = {
        'user_id': 2,
        'amount': 150.00,
        'transaction_type': 'PAYMENT',
        'location': 'Local',
        'device_id': 'dev_same_123'
    }
    res1 = client.post('/api/transactions', json=payload1)
    data1 = res1.get_json()
    print(f"Status: {res1.status_code}")
    print(f"Response: {data1}")
    
    assert data1['is_fraud'] is False, "Scenario 1 failed: transaction should be approved"
    assert data1['new_balance'] == 4850.00, f"Scenario 1 failed: balance should be 4850.00, got {data1['new_balance']}"
    print("Scenario 1 PASSED!\n")
    
    # ----------------------------------------------------
    # SCENARIO 2: New Device
    # Amount: $200.00, Location: Local, Device: New
    # Expected: Approved (is_fraud=False, risk ~27%, balance debited)
    # ----------------------------------------------------
    print("--- Scenario 2: New Device ---")
    reset_test_state()
    payload2 = {
        'user_id': 2,
        'amount': 200.00,
        'transaction_type': 'PAYMENT',
        'location': 'Local',
        'device_id': 'dev_new_scenario2'
    }
    res2 = client.post('/api/transactions', json=payload2)
    data2 = res2.get_json()
    print(f"Status: {res2.status_code}")
    print(f"Response: {data2}")
    
    assert data2['is_fraud'] is False, "Scenario 2 failed: transaction should be approved"
    assert data2['fraud_score'] >= 25.0, f"Scenario 2 failed: risk score should include +25% penalty, got {data2['fraud_score']}"
    assert "New Device Login" in data2['rules_triggered'], "Scenario 2 failed: rule 'New Device Login' should be triggered"
    assert data2['new_balance'] == 4800.00, f"Scenario 2 failed: balance should be 4800.00, got {data2['new_balance']}"
    print("Scenario 2 PASSED!\n")
    
    # ----------------------------------------------------
    # SCENARIO 3: Velocity Block
    # Amount: $50.00, Location: Local, Device: Same
    # Expected: Blocked (is_fraud=True, submit 3 times in 60s -> velocity penalty)
    # ----------------------------------------------------
    print("--- Scenario 3: Velocity Block ---")
    reset_test_state()
    # Link the device
    execute_query("INSERT INTO user_devices (device_id, user_id, device_type, os) VALUES ('dev_same_123', 2, 'Desktop', 'Windows') ON DUPLICATE KEY UPDATE os='Windows';", commit=True)
    
    # Submit 1st transaction (amount $10.00)
    payload3_1 = {
        'user_id': 2,
        'amount': 10.00,
        'transaction_type': 'PAYMENT',
        'location': 'Local',
        'device_id': 'dev_same_123'
    }
    r3_1 = client.post('/api/transactions', json=payload3_1)
    print(f"Txn 1 response: {r3_1.get_json()}")
    
    # Submit 2nd transaction (amount $10.00)
    payload3_2 = {
        'user_id': 2,
        'amount': 10.00,
        'transaction_type': 'PAYMENT',
        'location': 'Local',
        'device_id': 'dev_same_123'
    }
    r3_2 = client.post('/api/transactions', json=payload3_2)
    print(f"Txn 2 response: {r3_2.get_json()}")
    
    # Submit 3rd transaction (amount $50.00)
    payload3_3 = {
        'user_id': 2,
        'amount': 50.00,
        'transaction_type': 'PAYMENT',
        'location': 'Local',
        'device_id': 'dev_same_123'
    }
    res3 = client.post('/api/transactions', json=payload3_3)
    data3 = res3.get_json()
    print(f"Status: {res3.status_code}")
    print(f"Response: {data3}")
    
    assert data3['is_fraud'] is True, "Scenario 3 failed: transaction should be blocked"
    assert "High Velocity" in data3['rules_triggered'], "Scenario 3 failed: rule 'High Velocity' should be triggered"
    assert data3['fraud_score'] >= 50.0, f"Scenario 3 failed: risk score should include +50% penalty, got {data3['fraud_score']}"
    # Balance should not decrease from previous balance (5000.00 - 10.00 - 10.00 = 4980.00)
    # The 3rd transaction is blocked, so the balance should remain 4980.00
    assert data3['new_balance'] == 4980.00, f"Scenario 3 failed: balance should be 4980.00 (not debited), got {data3['new_balance']}"
    print("Scenario 3 PASSED!\n")
    
    # ----------------------------------------------------
    # SCENARIO 4: Large Amount
    # Amount: $12,000.00, Location: Local, Device: Same
    # Expected: Blocked (is_fraud=True)
    # ----------------------------------------------------
    print("--- Scenario 4: Large Amount ---")
    reset_test_state()
    execute_query("INSERT INTO user_devices (device_id, user_id, device_type, os) VALUES ('dev_same_123', 2, 'Desktop', 'Windows') ON DUPLICATE KEY UPDATE os='Windows';", commit=True)
    
    payload4 = {
        'user_id': 2,
        'amount': 12000.00,
        'transaction_type': 'PAYMENT',
        'location': 'Local',
        'device_id': 'dev_same_123'
    }
    res4 = client.post('/api/transactions', json=payload4)
    data4 = res4.get_json()
    print(f"Status: {res4.status_code}")
    print(f"Response: {data4}")
    
    assert data4['is_fraud'] is True, "Scenario 4 failed: transaction should be blocked"
    print("Scenario 4 PASSED!\n")
    
    # ----------------------------------------------------
    # SCENARIO 5: Int'l Payment
    # Amount: $100.00, Location: International, Device: Same
    # Expected: Blocked (is_fraud=True, triggers international restriction rule)
    # ----------------------------------------------------
    print("--- Scenario 5: Int'l Payment ---")
    reset_test_state()
    execute_query("INSERT INTO user_devices (device_id, user_id, device_type, os) VALUES ('dev_same_123', 2, 'Desktop', 'Windows') ON DUPLICATE KEY UPDATE os='Windows';", commit=True)
    
    # First, let's enable block_international in security_settings
    execute_query("UPDATE security_settings SET setting_value = 'true' WHERE setting_key = 'block_international';", commit=True)
    
    payload5 = {
        'user_id': 2,
        'amount': 100.00,
        'transaction_type': 'PAYMENT',
        'location': 'International',
        'device_id': 'dev_same_123'
    }
    res5 = client.post('/api/transactions', json=payload5)
    data5 = res5.get_json()
    print(f"Status: {res5.status_code}")
    print(f"Response: {data5}")
    
    assert data5['is_fraud'] is True, "Scenario 5 failed: transaction should be blocked"
    assert "International Payment Blocked" in data5['rules_triggered'], "Scenario 5 failed: rule should be triggered"
    
    # Disable block_international and make a payment, should only have warning penalty (+35)
    execute_query("UPDATE security_settings SET setting_value = 'false' WHERE setting_key = 'block_international';", commit=True)
    payload5_warn = {
        'user_id': 2,
        'amount': 100.00,
        'transaction_type': 'PAYMENT',
        'location': 'International',
        'device_id': 'dev_same_123'
    }
    res5_warn = client.post('/api/transactions', json=payload5_warn)
    data5_warn = res5_warn.get_json()
    print(f"Response with warning only: {data5_warn}")
    assert data5_warn['is_fraud'] is False, "Scenario 5 warning failed: should be approved if block_international is false"
    assert "Unusual Location" in data5_warn['rules_triggered'], "Scenario 5 warning failed: Unusual Location rule should trigger"
    assert data5_warn['fraud_score'] >= 35.0, f"Scenario 5 warning failed: score should include +35% penalty, got {data5_warn['fraud_score']}"
    print("Scenario 5 PASSED!\n")
    
    # ----------------------------------------------------
    # SCENARIO 6: Blacklist Match
    # Amount: Any, Location: Local, Device: Any
    # Expected: Blocked (is_fraud=True, user ID banned in admin)
    # ----------------------------------------------------
    print("--- Scenario 6: Blacklist Match ---")
    reset_test_state()
    # Ban user ID 2 by adding to blacklist_accounts in security_settings
    execute_query("UPDATE security_settings SET setting_value = 'ACC-99201,ACC-44122,2' WHERE setting_key = 'blacklist_accounts';", commit=True)
    
    payload6 = {
        'user_id': 2,
        'amount': 50.00,
        'transaction_type': 'PAYMENT',
        'location': 'Local',
        'device_id': 'dev_same_123'
    }
    res6 = client.post('/api/transactions', json=payload6)
    data6 = res6.get_json()
    print(f"Status: {res6.status_code}")
    print(f"Response: {data6}")
    
    assert data6['is_fraud'] is True, "Scenario 6 failed: transaction should be blocked"
    assert "Blacklisted Account" in data6['rules_triggered'], "Scenario 6 failed: Blacklisted Account rule should trigger"
    assert data6['fraud_score'] == 100.0, f"Scenario 6 failed: score should be 100%, got {data6['fraud_score']}"
    print("Scenario 6 PASSED!\n")
    
    print("==========================================")
    print("ALL 6 SCENARIOS SUCCESSFULLY VERIFIED!")
    print("==========================================")

if __name__ == '__main__':
    main()
