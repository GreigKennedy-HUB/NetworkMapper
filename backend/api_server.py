"""
Network Device Geolocation Mapper - API Server
Flask REST API for PostgreSQL database operations + Atera Integration

Run: python api_server.py
Access: http://localhost:5050/api/
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from decimal import Decimal
import os
import requests
from urllib.parse import quote

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ============================================
# Database Configuration
# ============================================
DB_PASSWORD = ''
try:
    from config import DB_PASSWORD
    print("Loaded DB password from config.py")
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

def convert_decimals(obj):
    """Convert Decimal types to float for JSON serialization"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, Decimal):
                obj[key] = float(value)
    return obj

def geolocate_ip(ip_address):
    """Geolocate a public IP address using ip-api.com (free, no API key needed)"""
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}?fields=status,city,regionName,country,lat,lon", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                # Extract state code from regionName (e.g., "Indiana" -> need to map to "IN")
                state_name = data.get('regionName', '')
                state_code = get_state_code(state_name)
                return {
                    'city': data.get('city', ''),
                    'state': state_code,
                    'state_name': state_name,
                    'country': data.get('country', ''),
                    'latitude': data.get('lat'),
                    'longitude': data.get('lon')
                }
    except Exception as e:
        print(f"Geolocation error for {ip_address}: {e}")
    return None

def get_state_code(state_name):
    """Convert state name to state code"""
    state_map = {
        'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
        'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
        'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
        'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
        'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO',
        'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
        'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
        'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
        'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
        'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY',
        'District of Columbia': 'DC'
    }
    return state_map.get(state_name, state_name[:2].upper() if state_name else '')

# ============================================
# Atera Configuration
# ============================================
ATERA_API_KEY = ''

# Try to load from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    ATERA_API_KEY = os.getenv('ATERA_API_KEY', '')
    if ATERA_API_KEY:
        print("Loaded Atera API key from .env")
except ImportError:
    print("python-dotenv not installed, skipping .env loading")

# Fallback to environment variable
if not ATERA_API_KEY:
    ATERA_API_KEY = os.environ.get('ATERA_API_KEY', '')

ATERA_BASE_URL = "https://app.atera.com/api/v3"
ATERA_PAGE_SIZE = 50
ATERA_TIMEOUT = 30

def get_atera_session():
    """Create Atera API session with auth headers"""
    session = requests.Session()
    session.headers.update({
        "X-API-KEY": ATERA_API_KEY,
        "Accept": "application/json"
    })
    return session

def atera_get(url, params=None):
    """Make authenticated GET request to Atera API"""
    session = get_atera_session()
    try:
        r = session.get(url, params=params, timeout=ATERA_TIMEOUT)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (400, 404):
            return None
        if r.status_code == 429:
            raise Exception("Atera API rate limit exceeded. Please wait and try again.")
        raise Exception(f"Atera API error: {r.status_code} - {r.text[:200]}")
    except requests.exceptions.Timeout:
        raise Exception("Atera API timeout")
    except requests.exceptions.ConnectionError:
        raise Exception("Could not connect to Atera API")

def atera_paginate(url):
    """Paginate through Atera API results"""
    page = 1
    all_items = []
    while True:
        data = atera_get(url, params={"Page": page, "ItemsInPage": ATERA_PAGE_SIZE})
        if not data:
            break
        items = data.get("items", [])
        if not items:
            break
        all_items.extend(items)
        # Check if there are more pages
        total_items = data.get("totalItemCount", 0)
        if len(all_items) >= total_items:
            break
        page += 1
    return all_items

# ============================================
# Health Check
# ============================================
@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        conn = get_db()
        conn.close()
        atera_status = 'configured' if ATERA_API_KEY else 'not configured'
        return jsonify({
            'status': 'healthy', 
            'database': 'connected',
            'atera': atera_status
        })
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
        cur.execute('SELECT id, name, city, state, latitude, longitude FROM office_locations ORDER BY state NULLS LAST, city, name')
        offices = cur.fetchall()
        conn.close()
        for office in offices:
            # Handle null coordinates
            office['latitude'] = float(office['latitude']) if office['latitude'] is not None else None
            office['longitude'] = float(office['longitude']) if office['longitude'] is not None else None
        return jsonify(offices)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/offices', methods=['POST'])
def add_office():
    try:
        data = request.json
        # Handle null coordinates
        lat = data.get('latitude')
        lng = data.get('longitude')
        city = data.get('city')
        state = data.get('state')
        name = data.get('name')
        
        # If no custom name provided, generate from city/state
        if not name and city:
            name = f"{city}, {state}" if state else city
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO office_locations (name, city, state, latitude, longitude) VALUES (%s, %s, %s, %s, %s) RETURNING id, name, city, state, latitude, longitude',
            (name, city, state, lat, lng)
        )
        office = cur.fetchone()
        conn.commit()
        conn.close()
        # Handle null coordinates in response
        office['latitude'] = float(office['latitude']) if office['latitude'] is not None else None
        office['longitude'] = float(office['longitude']) if office['longitude'] is not None else None
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
        data = request.json
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute('DELETE FROM client_mappings WHERE client_id = %s', (client_id,))
        
        for mapping in data:
            # Truncate fields to prevent database overflow errors
            subnet = (mapping.get('subnet', '') or '')[:50]
            office_name = (mapping.get('office_name', '') or '')[:255]
            mapping_type = (mapping.get('mapping_type', 'office') or 'office')[:50]
            
            cur.execute(
                'INSERT INTO client_mappings (client_id, subnet, office_name, mapping_type) VALUES (%s, %s, %s, %s)',
                (client_id, subnet, office_name, mapping_type)
            )
        
        cur.execute('UPDATE clients SET updated_at = %s WHERE id = %s', (datetime.now(), client_id))
        
        conn.commit()
        conn.close()
        return jsonify({'saved': len(data)})
    except Exception as e:
        import traceback
        print(f"Error saving mappings for client {client_id}: {str(e)}")
        print(traceback.format_exc())
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
        data = request.json
        conn = get_db()
        cur = conn.cursor()
        
        # Delete existing devices first
        cur.execute('DELETE FROM client_devices WHERE client_id = %s', (client_id,))
        conn.commit()  # Commit the delete before inserting
        
        # Track seen IPs to avoid duplicates within the batch
        seen_ips = set()
        saved_count = 0
        
        for device in data:
            # Truncate fields to prevent database overflow errors
            name = (device.get('name', '') or '')[:255]
            ip_address = (device.get('ip_address', '') or '')[:50]
            mac_address = (device.get('mac_address', '') or '')[:500]
            device_type = (device.get('device_type', '') or '')[:100]
            manufacturer = (device.get('manufacturer', '') or '')[:200]
            os_info = (device.get('os', '') or '')[:200]
            
            # Skip if we've already seen this IP (avoid unique constraint violation)
            if ip_address in seen_ips:
                continue
            seen_ips.add(ip_address)
            
            cur.execute(
                '''INSERT INTO client_devices 
                   (client_id, name, ip_address, mac_address, device_type, manufacturer, os) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                (client_id, name, ip_address, mac_address, device_type, manufacturer, os_info)
            )
            saved_count += 1
        
        cur.execute('UPDATE clients SET updated_at = %s WHERE id = %s', (datetime.now(), client_id))
        
        conn.commit()
        conn.close()
        return jsonify({'saved': saved_count, 'duplicates_skipped': len(data) - saved_count})
    except Exception as e:
        import traceback
        print(f"Error saving devices for client {client_id}: {str(e)}")
        print(traceback.format_exc())
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
        
        cur.execute('SELECT id, name FROM clients WHERE id = %s', (client_id,))
        client = cur.fetchone()
        if not client:
            conn.close()
            return jsonify({'error': 'Client not found'}), 404
        
        cur.execute(
            'SELECT subnet, office_name, mapping_type FROM client_mappings WHERE client_id = %s',
            (client_id,)
        )
        mappings = cur.fetchall()
        
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
# Atera API Endpoints
# ============================================
@app.route('/api/atera/status', methods=['GET'])
def atera_status():
    """Check if Atera API is configured and accessible"""
    if not ATERA_API_KEY:
        return jsonify({
            'configured': False,
            'message': 'Atera API key not configured. Add ATERA_API_KEY to .env file.'
        })
    
    try:
        # Test connection by fetching first page of customers
        data = atera_get(f"{ATERA_BASE_URL}/customers", params={"Page": 1, "ItemsInPage": 1})
        if data is not None:
            return jsonify({
                'configured': True,
                'connected': True,
                'message': 'Atera API connected successfully'
            })
        else:
            return jsonify({
                'configured': True,
                'connected': False,
                'message': 'Atera API returned no data'
            })
    except Exception as e:
        return jsonify({
            'configured': True,
            'connected': False,
            'message': f'Atera API error: {str(e)}'
        })

@app.route('/api/atera/customers', methods=['GET'])
def atera_customers():
    """Get list of all Atera customers"""
    if not ATERA_API_KEY:
        return jsonify({'error': 'Atera API key not configured'}), 400
    
    try:
        customers = atera_paginate(f"{ATERA_BASE_URL}/customers")
        
        # Return fields including full address info
        simplified = []
        for c in customers:
            simplified.append({
                'id': c.get('CustomerID'),
                'name': c.get('CustomerName', 'Unknown'),
                'business_number': c.get('BusinessNumber', ''),
                'address': c.get('Address', ''),
                'city': c.get('City', ''),
                'state': c.get('State', ''),
                'zip': c.get('ZipCodeStr', ''),
                'country': c.get('Country', '')
            })
        
        # Sort alphabetically by name
        simplified.sort(key=lambda x: x['name'].lower())
        
        return jsonify(simplified)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/atera/customers/<int:customer_id>/devices', methods=['GET'])
def atera_customer_devices(customer_id):
    """Get all devices (agents) for an Atera customer with auto-detected office subnets"""
    if not ATERA_API_KEY:
        return jsonify({'error': 'Atera API key not configured'}), 400
    
    try:
        agents = atera_paginate(f"{ATERA_BASE_URL}/agents/customer/{customer_id}")
        
        # Map Atera fields to our device schema
        devices = []
        public_ip_groups = {}  # Group devices by their ReportedFromIP
        
        for a in agents:
            # Get local IP addresses
            ip_addresses = a.get('IpAddresses', '') or ''
            if isinstance(ip_addresses, list):
                ip_addresses = ', '.join(ip_addresses)
            
            # Get the public IP this device reports from (router's external IP)
            reported_from_ip = a.get('ReportedFromIP', '') or ''
            
            # Get primary local IP (first valid one)
            primary_ip = ''
            if ip_addresses:
                ips = [ip.strip() for ip in ip_addresses.replace(';', ',').split(',') if ip.strip()]
                valid_ips = [ip for ip in ips if ip.count('.') == 3]
                if valid_ips:
                    primary_ip = valid_ips[0]
            
            # Skip devices without valid local IPs
            if not primary_ip:
                continue
            
            device = {
                'id': a.get('AgentID'),
                'name': a.get('MachineName', a.get('AgentName', 'Unknown')),
                'ip': primary_ip,
                'all_ips': ip_addresses,
                'reported_from_ip': reported_from_ip,
                'mac': a.get('MacAddresses', ''),
                'type': a.get('MachineType', 'Workstation'),
                'manufacturer': a.get('Vendor', ''),
                'os': a.get('OS', ''),
                'online': a.get('Online', False),
                'last_seen': a.get('LastSeenDate', '')
            }
            devices.append(device)
            
            # Group by ReportedFromIP for office detection
            if reported_from_ip:
                if reported_from_ip not in public_ip_groups:
                    public_ip_groups[reported_from_ip] = []
                public_ip_groups[reported_from_ip].append(device)
        
        # Auto-detect office locations
        # Rule: 3+ devices sharing the same ReportedFromIP = office location
        OFFICE_THRESHOLD = 3
        office_public_ips = {}  # public_ip -> list of subnets
        office_subnets = set()
        
        for public_ip, group_devices in public_ip_groups.items():
            if len(group_devices) >= OFFICE_THRESHOLD:
                # This is likely an office
                subnets_at_location = set()
                for d in group_devices:
                    # Extract subnet from device IP
                    parts = d['ip'].split('.')
                    if len(parts) >= 3:
                        subnet = '.'.join(parts[:3])
                        subnets_at_location.add(subnet)
                        office_subnets.add(subnet)
                
                office_public_ips[public_ip] = {
                    'device_count': len(group_devices),
                    'subnets': list(subnets_at_location)
                }
        
        # Build office_locations array - each unique public IP = separate office
        # Geolocate each office's public IP
        office_locations = []
        import time
        for public_ip, info in office_public_ips.items():
            # Geolocate this office's public IP
            geo = geolocate_ip(public_ip)
            
            office_loc = {
                'public_ip': public_ip,
                'device_count': info['device_count'],
                'subnets': info['subnets'],
                'devices': []  # Will populate after classification
            }
            
            # Add geolocation data if available
            if geo:
                office_loc['city'] = geo['city']
                office_loc['state'] = geo['state']
                office_loc['state_name'] = geo['state_name']
                office_loc['country'] = geo['country']
                office_loc['latitude'] = geo['latitude']
                office_loc['longitude'] = geo['longitude']
                office_loc['auto_name'] = f"{geo['city']}, {geo['state']}" if geo['city'] and geo['state'] else geo['city'] or f"Office at {public_ip}"
                office_loc['geo_source'] = 'ip-api.com'
            else:
                office_loc['city'] = ''
                office_loc['state'] = ''
                office_loc['latitude'] = None
                office_loc['longitude'] = None
                office_loc['auto_name'] = f"Office at {public_ip}"
                office_loc['geo_source'] = 'none'
            
            office_locations.append(office_loc)
            
            # Rate limit: ip-api.com allows 45 requests per minute for free tier
            # Add small delay between requests
            time.sleep(0.1)
        
        # Sort by device count descending (largest office first)
        office_locations.sort(key=lambda x: x['device_count'], reverse=True)
        
        # Classify each device
        for device in devices:
            device_subnet = '.'.join(device['ip'].split('.')[:3])
            
            if device_subnet in office_subnets:
                device['location_type'] = 'office'
                # Find which office this device belongs to
                for idx, loc in enumerate(office_locations):
                    if device.get('reported_from_ip') == loc['public_ip']:
                        device['office_index'] = idx
                        break
                device['detection_reason'] = f"Subnet {device_subnet}.* is used by {len([d for d in devices if d['ip'].startswith(device_subnet + '.')])} devices at same location"
            else:
                device['location_type'] = 'remote'
                device['detection_reason'] = 'Private subnet not associated with office location'
                # For remote devices, we'll use reported_from_ip for geolocation
        
        # Populate devices array for each office_location
        for loc in office_locations:
            loc['devices'] = [d for d in devices if d.get('reported_from_ip') == loc['public_ip'] and d.get('location_type') == 'office']
        
        return jsonify({
            'customer_id': customer_id,
            'device_count': len(devices),
            'devices': devices,
            'analysis': {
                'office_public_ips': office_public_ips,
                'office_subnets': list(office_subnets),
                'office_locations': office_locations,
                'office_location_count': len(office_locations),
                'office_device_count': len([d for d in devices if d.get('location_type') == 'office']),
                'remote_device_count': len([d for d in devices if d.get('location_type') == 'remote']),
                'detection_threshold': OFFICE_THRESHOLD
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# Main Entry Point
# ============================================
if __name__ == '__main__':
    import sys
    
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
    print(f"Atera API: {'Configured' if ATERA_API_KEY else 'Not configured (add ATERA_API_KEY to .env)'}")
    print(f"API URL: http://localhost:5050/api/")
    print(f"Health check: http://localhost:5050/api/health")
    print("-" * 50)
    
    app.run(host='0.0.0.0', port=5050, debug=False)