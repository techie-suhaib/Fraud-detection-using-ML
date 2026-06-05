import sys
import hashlib
import os
import mysql.connector
from db_connection import get_db_connection, ENV

def hash_password(password):
    salt = os.urandom(16)
    hash_val = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return salt.hex() + '$' + hash_val.hex()

def setup_database():
    db_name = ENV.get('DB_NAME', 'fraud_detection_db')
    print(f"Connecting to MySQL server to check/create database '{db_name}'...")
    
    try:
        # Connect to MySQL server without specifying database
        conn = get_db_connection(include_db=False)
        cursor = conn.cursor()
        
        # Create database if it does not exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print(f"Database '{db_name}' ready.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error checking/creating database: {e}")
        print("Please verify your MySQL server is running and the credentials in .env are correct.")
        sys.exit(1)
        
    print("Connecting to the database to create tables...")
    try:
        conn = get_db_connection(include_db=True)
        cursor = conn.cursor()
        
        # Disable foreign key checks temporarily to drop tables cleanly if they exist
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        
        # Drop tables if we want a fresh start, or we can just CREATE TABLE IF NOT EXISTS
        # Let's use CREATE TABLE IF NOT EXISTS to avoid losing data, or drop and recreate for clean run
        # Since this is a setup script, let's create tables if not exist.
        
        # 1. users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(15) UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                balance DECIMAL(10,2) DEFAULT 5000.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;
        """)
        
        # 2. transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                amount DECIMAL(10,2) NOT NULL,
                transaction_type VARCHAR(50),
                location VARCHAR(100),
                device_id VARCHAR(100),
                ip_address VARCHAR(45),
                transaction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            ) ENGINE=InnoDB;
        """)
        
        # 3. fraud_results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fraud_results (
                result_id INT AUTO_INCREMENT PRIMARY KEY,
                transaction_id INT,
                is_fraud BOOLEAN,
                fraud_score DECIMAL(5,2),
                model_version VARCHAR(50),
                rules_triggered VARCHAR(255),
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE
            ) ENGINE=InnoDB;
        """)
        
        # 4. user_devices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_devices (
                device_id VARCHAR(100),
                user_id INT,
                device_type VARCHAR(50),
                os VARCHAR(50),
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (device_id, user_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            ) ENGINE=InnoDB;
        """)
        
        # 5. login_activity table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_activity (
                login_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                ip_address VARCHAR(45),
                location VARCHAR(100),
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            ) ENGINE=InnoDB;
        """)
        
        # 6. security_settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_settings (
                setting_key VARCHAR(50) PRIMARY KEY,
                setting_value VARCHAR(255) NOT NULL
            ) ENGINE=InnoDB;
        """)
        
        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conn.commit()
        print("Database tables initialized successfully.")
        
        # Seed default data
        print("Seeding initial settings and default users...")
        
        # Default security settings
        default_settings = [
            ('auto_block_threshold', '75.00'),
            ('block_international', 'false'),
            ('blacklist_accounts', 'ACC-99201,ACC-44122'),
            ('active_model', 'random_forest')
        ]
        
        for key, val in default_settings:
            cursor.execute("""
                INSERT INTO security_settings (setting_key, setting_value) 
                VALUES (%s, %s) 
                ON DUPLICATE KEY UPDATE setting_value = %s;
            """, (key, val, val))
            
        # Default Admin User
        admin_email = 'admin@fraudguard.ai'
        cursor.execute("SELECT user_id FROM users WHERE email = %s;", (admin_email,))
        if not cursor.fetchone():
            admin_pass = hash_password('admin123')
            cursor.execute("""
                INSERT INTO users (full_name, email, phone, password_hash, balance)
                VALUES (%s, %s, %s, %s, %s);
            """, ('Admin User', admin_email, '1234567890', admin_pass, 0.00))
            print("Default admin user created (admin@fraudguard.ai / admin123).")
            
        # Default Test User
        user_email = 'user@test.com'
        cursor.execute("SELECT user_id FROM users WHERE email = %s;", (user_email,))
        if not cursor.fetchone():
            user_pass = hash_password('user123')
            cursor.execute("""
                INSERT INTO users (full_name, email, phone, password_hash, balance)
                VALUES (%s, %s, %s, %s, %s);
            """, ('Test User', user_email, '9876543210', user_pass, 5000.00))
            print("Default test user created (user@test.com / user123).")
            
        conn.commit()
        cursor.close()
        conn.close()
        print("Database seeding completed.")
        
    except Exception as e:
        print(f"Error seeding/creating tables: {e}")
        sys.exit(1)

if __name__ == '__main__':
    setup_database()
