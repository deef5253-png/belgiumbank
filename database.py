import sqlite3
import os
from datetime import datetime
import bcrypt

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'belgiumbank.db')

def init_database():
    """Initialize the database with all tables"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            birth_city TEXT NOT NULL,
            address TEXT NOT NULL,
            postal_code TEXT NOT NULL,
            city TEXT NOT NULL,
            country TEXT DEFAULT 'Belgique',
            phone TEXT,
            nationality TEXT DEFAULT 'Belge',
            id_number TEXT,
            account_number TEXT UNIQUE,
            is_active BOOLEAN DEFAULT 0,
            is_verified BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Accounts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            balance REAL DEFAULT 0.0,
            currency TEXT DEFAULT 'EUR',
            account_type TEXT DEFAULT 'courant',
            iban TEXT UNIQUE,
            bic TEXT DEFAULT 'BBRU BE BB',
            status TEXT DEFAULT 'actif',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Documents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            document_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_name TEXT NOT NULL,
            is_verified BOOLEAN DEFAULT 0,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Transfers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_account_id INTEGER,
            to_account_id INTEGER,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'EUR',
            description TEXT,
            beneficiary_name TEXT,
            beneficiary_iban TEXT,
            beneficiary_bic TEXT,
            status TEXT DEFAULT 'en_attente',
            reference TEXT UNIQUE,
            processed_at TIMESTAMP,
            processed_by INTEGER,
            rejection_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_user_id) REFERENCES users(id),
            FOREIGN KEY (to_user_id) REFERENCES users(id),
            FOREIGN KEY (processed_by) REFERENCES users(id)
        )
    ''')
    
    # Admin logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            action TEXT NOT NULL,
            target_type TEXT,
            target_id INTEGER,
            details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create default admin account
    admin_password = bcrypt.hashpw('AdminSecure2024!'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute('''
        INSERT OR IGNORE INTO users (id, email, password_hash, first_name, last_name, 
            birth_date, birth_city, address, postal_code, city, is_active, is_verified)
        VALUES (1, 'admin@belgiumbank.be', ?, 'Administrateur', 'System', 
            '1990-01-01', 'Bruxelles', 'Rue de la Banque 1', '1000', 'Bruxelles', 1, 1)
    ''', (admin_password,))
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

if __name__ == '__main__':
    init_database()