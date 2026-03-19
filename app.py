from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import bcrypt
import os
import re
import random
import string
from datetime import datetime, timedelta
from database import get_db_connection, init_database
from notifications import send_email, notify_admin
import sqlite3

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'belgium-bank-secure-key-2024'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'documents')

CORS(app)
jwt = JWTManager(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
ADMIN_EMAIL = 'servicclientt@gmail.com'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_account_number():
    """Generate a Belgian-style account number BE XX XXXX XXXX XXXX"""
    return f"BE{random.randint(10, 99)} {random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}"

def generate_reference():
    """Generate a unique transfer reference"""
    return f"VIR-{datetime.now().strftime('%Y%m%d')}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"

def mask_sensitive_data(data, visible_chars=4):
    """Mask sensitive data showing only last visible_chars"""
    if not data or len(data) <= visible_chars:
        return data
    return '*' * (len(data) - visible_chars) + data[-visible_chars:]

# ========== AUTHENTICATION ROUTES ==========

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        required_fields = ['email', 'password', 'firstName', 'lastName', 'birthDate', 
                          'birthCity', 'address', 'postalCode', 'city', 'phone', 'nationality']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Le champ {field} est requis'}), 400
        
        # Validate email
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, data['email']):
            return jsonify({'error': 'Email invalide'}), 400
        
        # Validate password strength
        if len(data['password']) < 8:
            return jsonify({'error': 'Le mot de passe doit contenir au moins 8 caractères'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if email exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (data['email'],))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Cet email est déjà utilisé'}), 409
        
        # Hash password
        password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Generate account number
        account_number = generate_account_number()
        
        # Insert user
        cursor.execute('''
            INSERT INTO users (email, password_hash, first_name, last_name, birth_date, 
                birth_city, address, postal_code, city, country, phone, nationality, 
                id_number, account_number, is_active, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0)
        ''', (data['email'], password_hash, data['firstName'], data['lastName'], 
              data['birthDate'], data['birthCity'], data['address'], data['postalCode'],
              data['city'], data.get('country', 'Belgique'), data['phone'], 
              data['nationality'], data.get('idNumber', ''), account_number))
        
        user_id = cursor.lastrowid
        
        # Create account
        cursor.execute('''
            INSERT INTO accounts (user_id, balance, iban, bic, account_type)
            VALUES (?, 0.0, ?, 'BBRU BE BB', 'courant')
        ''', (user_id, account_number.replace(' ', '')))
        
        conn.commit()
        conn.close()
        
        # Send notification emails
        send_email(data['email'], 'Bienvenue chez Belgium Bank', 
                   f"Bonjour {data['firstName']},\n\nVotre inscription a été reçue. Notre équipe va vérifier vos documents.\n\nCordialement,\nBelgium Bank")
        notify_admin(f"Nouvelle inscription: {data['firstName']} {data['lastName']} ({data['email']})")
        
        return jsonify({
            'message': 'Inscription réussie. Veuillez téléverser vos documents.',
            'userId': user_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email et mot de passe requis'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'Email ou mot de passe incorrect'}), 401
        
        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({'error': 'Email ou mot de passe incorrect'}), 401
        
        if not user['is_active']:
            return jsonify({'error': 'Compte en attente de validation. Veuillez téléverser vos documents.'}), 403
        
        access_token = create_access_token(identity=str(user['id']))
        
        return jsonify({
            'accessToken': access_token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'firstName': user['first_name'],
                'lastName': user['last_name'],
                'accountNumber': user['account_number'],
                'isVerified': user['is_verified']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/admin-login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        secret_key = data.get('secretKey')
        
        # Additional admin security
        if secret_key != 'BELGIUM-BANK-ADMIN-2024':
            return jsonify({'error': 'Clé de sécurité invalide'}), 403
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ? AND id = 1', (email,))
        admin = cursor.fetchone()
        conn.close()
        
        if not admin or not bcrypt.checkpw(password.encode('utf-8'), admin['password_hash'].encode('utf-8')):
            return jsonify({'error': 'Accès refusé'}), 401
        
        access_token = create_access_token(identity='admin')
        
        return jsonify({
            'accessToken': access_token,
            'admin': {
                'id': admin['id'],
                'email': admin['email'],
                'name': f"{admin['first_name']} {admin['last_name']}"
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== DOCUMENT UPLOAD ROUTES ==========

@app.route('/api/users/<int:user_id>/documents', methods=['POST'])
def upload_documents(user_id):
    try:
        if 'idFront' not in request.files or 'idBack' not in request.files or 'proofOfAddress' not in request.files:
            return jsonify({'error': 'Tous les documents sont requis (pièce recto, verso, justificatif)'}), 400
        
        files = {
            'id_front': request.files['idFront'],
            'id_back': request.files['idBack'],
            'proof_of_address': request.files['proofOfAddress']
        }
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(user_id))
        os.makedirs(user_folder, exist_ok=True)
        
        for doc_type, file in files.items():
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{doc_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                filepath = os.path.join(user_folder, filename)
                file.save(filepath)
                
                cursor.execute('''
                    INSERT INTO documents (user_id, document_type, file_path, file_name)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, doc_type, filepath, filename))
        
        conn.commit()
        conn.close()
        
        notify_admin(f"Nouveaux documents téléversés par l'utilisateur {user_id}")
        
        return jsonify({'message': 'Documents téléversés avec succès'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== USER DASHBOARD ROUTES ==========

@app.route('/api/user/account', methods=['GET'])
@jwt_required()
def get_account():
    try:
        user_id = int(get_jwt_identity())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.*, a.balance, a.iban, a.bic, a.account_type 
            FROM users u 
            JOIN accounts a ON u.id = a.user_id 
            WHERE u.id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        return jsonify({
            'firstName': user['first_name'],
            'lastName': user['last_name'],
            'accountNumber': user['account_number'],
            'balance': user['balance'],
            'iban': user['iban'],
            'bic': user['bic'],
            'accountType': user['account_type']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/transfers', methods=['GET'])
@jwt_required()
def get_user_transfers():
    try:
        user_id = int(get_jwt_identity())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.*, 
                   u1.first_name as from_first_name, u1.last_name as from_last_name,
                   u2.first_name as to_first_name, u2.last_name as to_last_name
            FROM transfers t
            LEFT JOIN users u1 ON t.from_user_id = u1.id
            LEFT JOIN users u2 ON t.to_user_id = u2.id
            WHERE t.from_user_id = ? OR t.to_user_id = ?
            ORDER BY t.created_at DESC
        ''', (user_id, user_id))
        
        transfers = cursor.fetchall()
        conn.close()
        
        result = []
        for t in transfers:
            is_outgoing = t['from_user_id'] == user_id
            result.append({
                'id': t['id'],
                'amount': t['amount'],
                'currency': t['currency'],
                'description': t['description'],
                'status': t['status'],
                'reference': t['reference'],
                'createdAt': t['created_at'],
                'processedAt': t['processed_at'],
                'rejectionReason': t['rejection_reason'],
                'isOutgoing': is_outgoing,
                'counterparty': t['to_first_name'] + ' ' + t['to_last_name'] if is_outgoing else t['from_first_name'] + ' ' + t['from_last_name']
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/transfer', methods=['POST'])
@jwt_required()
def create_transfer():
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        required_fields = ['amount', 'beneficiaryName', 'beneficiaryIban', 'description']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Le champ {field} est requis'}), 400
        
        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({'error': 'Le montant doit être positif'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check balance
        cursor.execute('SELECT balance FROM accounts WHERE user_id = ?', (user_id,))
        account = cursor.fetchone()
        
        if not account or account['balance'] < amount:
            conn.close()
            return jsonify({'error': 'Solde insuffisant'}), 400
        
        reference = generate_reference()
        
        cursor.execute('''
            INSERT INTO transfers (from_user_id, amount, currency, description, 
                beneficiary_name, beneficiary_iban, beneficiary_bic, status, reference)
            VALUES (?, ?, 'EUR', ?, ?, ?, ?, 'en_attente', ?)
        ''', (user_id, amount, data['description'], data['beneficiaryName'], 
              data['beneficiaryIban'], data.get('beneficiaryBic', ''), reference))
        
        conn.commit()
        conn.close()
        
        notify_admin(f"Nouveau virement en attente: {amount} EUR vers {data['beneficiaryName']}")
        
        return jsonify({
            'message': 'Virement soumis pour validation',
            'reference': reference
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== ADMIN ROUTES ==========

@app.route('/api/admin/users', methods=['GET'])
@jwt_required()
def get_all_users():
    try:
        if get_jwt_identity() != 'admin':
            return jsonify({'error': 'Accès refusé'}), 403
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.email, u.first_name, u.last_name, u.birth_date, 
                   u.birth_city, u.city, u.postal_code, u.phone, u.is_active, 
                   u.is_verified, u.account_number, u.created_at,
                   a.balance, a.status as account_status
            FROM users u
            LEFT JOIN accounts a ON u.id = a.user_id
            WHERE u.id != 1
            ORDER BY u.created_at DESC
        ''')
        
        users = cursor.fetchall()
        conn.close()
        
        result = []
        for u in users:
            result.append({
                'id': u['id'],
                'email': u['email'],
                'firstName': u['first_name'],
                'lastName': u['last_name'],
                'birthDate': u['birth_date'],
                'birthCity': u['birth_city'],
                'city': u['city'],
                'postalCode': mask_sensitive_data(u['postal_code']),
                'phone': mask_sensitive_data(u['phone'], 3),
                'isActive': u['is_active'],
                'isVerified': u['is_verified'],
                'accountNumber': mask_sensitive_data(u['account_number'], 8),
                'balance': u['balance'],
                'accountStatus': u['account_status'],
                'createdAt': u['created_at']
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_details(user_id):
    try:
        if get_jwt_identity() != 'admin':
            return jsonify({'error': 'Accès refusé'}), 403
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.*, a.balance, a.iban, a.bic
            FROM users u
            LEFT JOIN accounts a ON u.id = a.user_id
            WHERE u.id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        
        cursor.execute('SELECT * FROM documents WHERE user_id = ?', (user_id,))
        documents = cursor.fetchall()
        
        conn.close()
        
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        docs = [{
            'id': d['id'],
            'type': d['document_type'],
            'fileName': d['file_name'],
            'isVerified': d['is_verified'],
            'uploadedAt': d['uploaded_at']
        } for d in documents]
        
        return jsonify({
            'id': user['id'],
            'email': user['email'],
            'firstName': user['first_name'],
            'lastName': user['last_name'],
            'birthDate': user['birth_date'],
            'birthCity': user['birth_city'],
            'address': user['address'],
            'postalCode': user['postal_code'],
            'city': user['city'],
            'country': user['country'],
            'phone': user['phone'],
            'nationality': user['nationality'],
            'idNumber': user['id_number'],
            'accountNumber': user['account_number'],
            'balance': user['balance'],
            'iban': user['iban'],
            'bic': user['bic'],
            'isActive': user['is_active'],
            'isVerified': user['is_verified'],
            'createdAt': user['created_at'],
            'documents': docs
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>/verify', methods=['POST'])
@jwt_required()
def verify_user(user_id):
    try:
        if get_jwt_identity() != 'admin':
            return jsonify({'error': 'Accès refusé'}), 403
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET is_active = 1, is_verified = 1, updated_at = ?
            WHERE id = ?
        ''', (datetime.now(), user_id))
        
        conn.commit()
        conn.close()
        
        # Get user email to notify
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT email, first_name FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            send_email(user['email'], 'Compte vérifié - Belgium Bank',
                      f"Bonjour {user['first_name']},\n\nVotre compte a été vérifié avec succès. Vous pouvez maintenant effectuer des opérations.\n\nCordialement,\nBelgium Bank")
        
        return jsonify({'message': 'Utilisateur vérifié avec succès'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>/credit', methods=['POST'])
@jwt_required()
def credit_account(user_id):
    try:
        if get_jwt_identity() != 'admin':
            return jsonify({'error': 'Accès refusé'}), 403
        
        data = request.get_json()
        amount = float(data.get('amount', 0))
        description = data.get('description', 'Crédit admin')
        
        if amount <= 0:
            return jsonify({'error': 'Montant invalide'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE accounts SET balance = balance + ? WHERE user_id = ?', 
                      (amount, user_id))
        
        reference = generate_reference()
        cursor.execute('''
            INSERT INTO transfers (to_user_id, amount, currency, description, 
                status, reference, processed_at)
            VALUES (?, ?, 'EUR', ?, 'valide', ?, ?)
        ''', (user_id, amount, description, reference, datetime.now()))
        
        conn.commit()
        conn.close()
        
        # Notify user
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT email, first_name FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            send_email(user['email'], 'Crédit sur votre compte - Belgium Bank',
                      f"Bonjour {user['first_name']},\n\nVotre compte a été crédité de {amount} EUR.\nRéférence: {reference}\n\nCordialement,\nBelgium Bank")
        
        return jsonify({'message': f'Compte crédité de {amount} EUR'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/transfers', methods=['GET'])
@jwt_required()
def get_pending_transfers():
    try:
        if get_jwt_identity() != 'admin':
            return jsonify({'error': 'Accès refusé'}), 403
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.*, u.first_name, u.last_name, u.account_number
            FROM transfers t
            JOIN users u ON t.from_user_id = u.id
            ORDER BY t.created_at DESC
        ''')
        
        transfers = cursor.fetchall()
        conn.close()
        
        result = []
        for t in transfers:
            result.append({
                'id': t['id'],
                'amount': t['amount'],
                'description': t['description'],
                'beneficiaryName': t['beneficiary_name'],
                'beneficiaryIban': mask_sensitive_data(t['beneficiary_iban'], 8),
                'status': t['status'],
                'reference': t['reference'],
                'createdAt': t['created_at'],
                'processedAt': t['processed_at'],
                'rejectionReason': t['rejection_reason'],
                'fromUser': f"{t['first_name']} {t['last_name']}",
                'fromAccount': mask_sensitive_data(t['account_number'], 8)
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/transfers/<int:transfer_id>/process', methods=['POST'])
@jwt_required()
def process_transfer(transfer_id):
    try:
        if get_jwt_identity() != 'admin':
            return jsonify({'error': 'Accès refusé'}), 403
        
        data = request.get_json()
        action = data.get('action')  # 'approve' or 'reject'
        reason = data.get('reason', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM transfers WHERE id = ?', (transfer_id,))
        transfer = cursor.fetchone()
        
        if not transfer:
            conn.close()
            return jsonify({'error': 'Virement non trouvé'}), 404
        
        if action == 'approve':
            # Deduct from sender
            cursor.execute('''
                UPDATE accounts SET balance = balance - ? 
                WHERE user_id = ?
            ''', (transfer['amount'], transfer['from_user_id']))
            
            cursor.execute('''
                UPDATE transfers SET status = 'valide', processed_at = ?
                WHERE id = ?
            ''', (datetime.now(), transfer_id))
            
        elif action == 'reject':
            cursor.execute('''
                UPDATE transfers SET status = 'refuse', processed_at = ?, 
                rejection_reason = ? WHERE id = ?
            ''', (datetime.now(), reason, transfer_id))
        
        conn.commit()
        
        # Notify user
        cursor.execute('SELECT email, first_name FROM users WHERE id = ?', 
                      (transfer['from_user_id'],))
        user = cursor.fetchone()
        
        conn.close()
        
        if user:
            status_text = 'approuvé' if action == 'approve' else 'refusé'
            send_email(user['email'], f'Virement {status_text} - Belgium Bank',
                      f"Bonjour {user['first_name']},\n\nVotre virement de {transfer['amount']} EUR a été {status_text}.\nRéférence: {transfer['reference']}\n" + 
                      (f"\nMotif du refus: {reason}" if action == 'reject' else "") +
                      "\n\nCordialement,\nBelgium Bank")
        
        return jsonify({'message': f'Virement {action} avec succès'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/documents/<int:doc_id>/download', methods=['GET'])
@jwt_required()
def download_document(doc_id):
    try:
        if get_jwt_identity() != 'admin':
            return jsonify({'error': 'Accès refusé'}), 403
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
        doc = cursor.fetchone()
        conn.close()
        
        if not doc:
            return jsonify({'error': 'Document non trouvé'}), 404
        
        return send_file(doc['file_path'], as_attachment=True, download_name=doc['file_name'])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM users WHERE id != 1')
        total_users = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as pending FROM transfers WHERE status = "en_attente"')
        pending_transfers = cursor.fetchone()['pending']
        
        cursor.execute('SELECT SUM(balance) as total FROM accounts')
        total_balance = cursor.fetchone()['total'] or 0
        
        conn.close()
        
        return jsonify({
            'totalUsers': total_users,
            'pendingTransfers': pending_transfers,
            'totalBalance': total_balance
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_database()
    app.run(host='0.0.0.0', port=5000, debug=True)