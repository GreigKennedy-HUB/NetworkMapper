"""
Network Device Geolocation Mapper - API Server
Flask REST API for PostgreSQL database operations

Run: python api_server.py
Access: http://localhost:5001/api/
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ============================================
# Database Configuration
# ============================================
# Try to load password from config.py file first
DB_PASSWORD = ''
try:
    from config import DB_PASSWORD
    print("Loaded password from config.py")
except ImportError:
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'database': os.environ.get('DB_NAME', 'network_mapper_db'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': DB_PASSWORD
}

def get_db():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def init_db_config(password):
    """Initialize DB config with password"""
    DB_CONFIG['password'] = password

# ============================================
# Health Check
# ============================================
@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        conn = get_db()
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# ============================================
# Office Locations
# ============================================
@app.route('/api/offices', methods=['GET'])
def get_offices():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT id, name, latitude, longitude FROM office_locations ORDER BY name')
        offices = cur.fetchall()
        conn.close()
        return jsonify(offices)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/offices', methods=['POST'])
def add_office():
    try:
        data = request.json
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO office_locations (name, latitude, longitude) VALUES (%s, %s, %s) RETURNING id, name, latitude, longitude',
            (data['name'], data['latitude'], data['longitude'])
        )
        office = cur.fetchone()
        conn.commit()
        conn.close()
        return jsonify(office), 201
    except psycopg2.errors.UniqueViolation:
        return jsonify({'error': 'Office with this name already exists'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/offices/<int:office_id>', methods=['DELETE'])
def delete_office(office_id):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('DELETE FROM office_locations WHERE id = %s RETURNING id', (office_id,))
        deleted = cur.fetchone()
        conn.commit()
        conn.close()
        if deleted:
            return jsonify({'deleted': office_id})
        return jsonify({'error': 'Office not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# Clients
# ============================================
@app.route('/api/clients', methods=['GET'])
def get_clients():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            SELECT c.id, c.name, c.created_at, c.updated_at,
                   COUNT(DISTINCT cm.id) as mapping_count,
                   COUNT(DISTINCT cd.id) as device_count
            FROM clients c
            LEFT JOIN client_mappings cm ON c.id = cm.client_id
            LEFT JOIN client_devices cd ON c.id = cd.client_id
            GROUP BY c.id
            ORDER BY c.updated_at DESC
        ''')
        clients = cur.fetchall()
        conn.close()
        # Convert datetime objects to strings
        for client in clients:
            client['created_at'] = client['created_at'].isoformat() if client['created_at'] else None
            client['updated_at'] = client['updated_at'].isoformat() if client['updated_at'] else None
        return jsonify(clients)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clients', methods=['POST'])
def create_client():
    try:
        data = request.json
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO clients (name) VALUES (%s) RETURNING id, name',
            (data['name'],)
        )
        client = cur.fetchone()
        conn.commit()
        conn.close()
        return jsonify(client), 201
    except psycopg2.errors.UniqueViolation:
        # Client exists, return existing
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT id, name FROM clients WHERE name = %s', (data['name'],))
        client = cur.fetchone()
        conn.close()
        return jsonify(client), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    try:
        conn = get_db()
        cur = conn.cursor()
        # Cascading delete will remove mappings and devices
        cur.execute('DELETE FROM clients WHERE id = %s RETURNING id, name', (client_id,))
        deleted = cur.fetchone()
        conn.commit()
        conn.close()
        if deleted:
            return jsonify({'deleted': deleted})
        return jsonify({'error': 'Client not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# Client Mappings
# ============================================
@app.route('/api/clients/<int:client_id>/mappings', methods=['GET'])
def get_client_mappings(client_id):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            'SELECT id, subnet, office_name, mapping_type FROM client_mappings WHERE client_id = %s',
            (client_id,)
        )
        mappings = cur.fetchall()
        conn.close()
        return jsonify(mappings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clients/<int:client_id>/mappings', methods=['POST'])
def save_client_mappings(client_id):
    """Replace all mappings for a client"""
    try:
        data = request.json  # List of mappings
        conn = get_db()
        cur = conn.cursor()
        
        # Delete existing mappings
        cur.execute('DELETE FROM client_mappings WHERE client_id = %s', (client_id,))
        
        # Insert new mappings
        for mapping in data:
            cur.execute(
                'INSERT INTO client_mappings (client_id, subnet, office_name, mapping_type) VALUES (%s, %s, %s, %s)',
                (client_id, mapping['subnet'], mapping['office_name'], mapping['mapping_type'])
            )
        
        # Update client timestamp
        cur.execute('UPDATE clients SET updated_at = %s WHERE id = %s', (datetime.now(), client_id))
        
        conn.commit()
        conn.close()
        return jsonify({'saved': len(data)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# Client Devices
# ============================================
@app.route('/api/clients/<int:client_id>/devices', methods=['GET'])
def get_client_devices(client_id):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            'SELECT id, name, ip_address, mac_address, device_type, manufacturer, os FROM client_devices WHERE client_id = %s',
            (client_id,)
        )
        devices = cur.fetchall()
        conn.close()
        return jsonify(devices)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clients/<int:client_id>/devices', methods=['POST'])
def save_client_devices(client_id):
    """Replace all devices for a client"""
    try:
        data = request.json  # List of devices
        conn = get_db()
        cur = conn.cursor()
        
        # Delete existing devices
        cur.execute('DELETE FROM client_devices WHERE client_id = %s', (client_id,))
        
        # Insert new devices
        for device in data:
            cur.execute(
                '''INSERT INTO client_devices 
                   (client_id, name, ip_address, mac_address, device_type, manufacturer, os) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                (client_id, device.get('name', ''), device.get('ip_address', ''),
                 device.get('mac_address', ''), device.get('device_type', ''),
                 device.get('manufacturer', ''), device.get('os', ''))
            )
        
        # Update client timestamp
        cur.execute('UPDATE clients SET updated_at = %s WHERE id = %s', (datetime.now(), client_id))
        
        conn.commit()
        conn.close()
        return jsonify({'saved': len(data)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# Full Client Load (mappings + devices)
# ============================================
@app.route('/api/clients/<int:client_id>/full', methods=['GET'])
def get_client_full(client_id):
    """Get client with all mappings and devices"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Get client info
        cur.execute('SELECT id, name FROM clients WHERE id = %s', (client_id,))
        client = cur.fetchone()
        if not client:
            conn.close()
            return jsonify({'error': 'Client not found'}), 404
        
        # Get mappings
        cur.execute(
            'SELECT subnet, office_name, mapping_type FROM client_mappings WHERE client_id = %s',
            (client_id,)
        )
        mappings = cur.fetchall()
        
        # Get devices
        cur.execute(
            'SELECT name, ip_address, mac_address, device_type, manufacturer, os FROM client_devices WHERE client_id = %s',
            (client_id,)
        )
        devices = cur.fetchall()
        
        conn.close()
        
        return jsonify({
            'client': client,
            'mappings': mappings,
            'devices': devices
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# Main Entry Point
# ============================================
if __name__ == '__main__':
    import sys
    
    # Password priority: config.py > environment variable > command line
    if not DB_CONFIG['password'] and len(sys.argv) > 1:
        DB_CONFIG['password'] = sys.argv[1]
    
    if not DB_CONFIG['password']:
        print("=" * 50)
        print("WARNING: No database password provided!")
        print("Options:")
        print("  1. Create config.py with: DB_PASSWORD = 'your_password'")
        print("  2. Set DB_PASSWORD environment variable")
        print("  3. Pass as argument: python api_server.py password")
        print("=" * 50)
    
    print(f"Starting API server...")
    print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print(f"API URL: http://localhost:5001/api/")
    print(f"Health check: http://localhost:5001/api/health")
    print("-" * 50)
    
    app.run(host='0.0.0.0', port=5050, debug=False)