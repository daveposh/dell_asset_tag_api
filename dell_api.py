#!/usr/bin/env python3
import os
import json
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests
import yaml

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Load configuration
config_path = os.getenv('CONFIG_PATH', 'config/config.yaml')
try:
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
except Exception as e:
    print(f"Error loading config: {e}")
    config = {}

# Initialize cache
cache = {}
cache_enabled = config.get('cache', {}).get('enabled', True)
cache_ttl = config.get('cache', {}).get('ttl', 3600)  # Default 1 hour

class DellEntitlementClient:
    def __init__(self):
        self.client_id = os.getenv('DELL_API_CLIENT_ID')
        self.client_secret = os.getenv('DELL_API_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("DELL_API_CLIENT_ID and DELL_API_CLIENT_SECRET environment variables must be set")
        
        # Authentication URL is different from the base URL
        self.auth_url = "https://apigtwb2c.us.dell.com/auth/oauth/v2/token"
        # Use the correct base URL
        self.base_url = "https://apigtwb2c.us.dell.com/PROD/sbil/eapi/v5"
        self.entitlements_url = f"{self.base_url}/asset-entitlements"
        self.access_token = None

    def authenticate(self):
        """Get OAuth2 access token from Dell API."""
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = requests.post(self.auth_url, data=auth_data)
            response.raise_for_status()
            self.access_token = response.json()['access_token']
        except requests.exceptions.RequestException as e:
            raise Exception(f"Authentication failed: {str(e)}")

    def get_entitlement(self, service_tag: str):
        """Get entitlement information for a specific service tag."""
        # Check cache first if enabled
        if cache_enabled and service_tag in cache:
            cache_entry = cache[service_tag]
            # Check if cache entry is still valid
            if time.time() - cache_entry['timestamp'] < cache_ttl:
                print(f"Cache hit for service tag: {service_tag}")
                return cache_entry['data']
            else:
                print(f"Cache expired for service tag: {service_tag}")
                # Remove expired cache entry
                del cache[service_tag]
        
        # If not in cache or expired, fetch from API
        if not self.access_token:
            self.authenticate()

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Use query parameters with 'servicetags' instead of 'servicetag'
        params = {
            'servicetags': service_tag
        }
        
        try:
            response = requests.get(
                self.entitlements_url,
                headers=headers,
                params=params
            )
            
            # Print detailed error information
            if response.status_code != 200:
                print(f"Status Code: {response.status_code}")
                print(f"Response Headers: {response.headers}")
                try:
                    print(f"Response Body: {response.text}")
                except:
                    print("Could not read response body")
            
            response.raise_for_status()
            data = response.json()
            
            # Store in cache if enabled
            if cache_enabled:
                cache[service_tag] = {
                    'data': data,
                    'timestamp': time.time()
                }
                print(f"Cached data for service tag: {service_tag}")
            
            return data
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 401:
                # Token might be expired, try to authenticate again
                self.authenticate()
                return self.get_entitlement(service_tag)
            raise Exception(f"Error fetching entitlement data: {str(e)}")

def extract_entitlement_fields(entitlement_data):
    """Extract specific fields from the entitlement data."""
    result = {
        "serviceTag": "",
        "productLineDescription": "",
        "serviceLevelDescription": "",
        "countryCode": "",
        "startDate": "",
        "endDate": "",
        "shipDate": ""
    }
    
    # Check if the data is a list of items that might contain entitlements
    if isinstance(entitlement_data, list):
        for item in entitlement_data:
            if isinstance(item, dict):
                # Extract asset information
                if 'serviceTag' in item:
                    result['serviceTag'] = item['serviceTag']
                if 'productLineDescription' in item:
                    result['productLineDescription'] = item['productLineDescription']
                if 'countryCode' in item:
                    result['countryCode'] = item['countryCode']
                if 'shipDate' in item:
                    result['shipDate'] = item['shipDate']
                
                # Check if this item has an 'entitlements' key
                if 'entitlements' in item and isinstance(item['entitlements'], list):
                    for entitlement in item['entitlements']:
                        if isinstance(entitlement, dict):
                            if 'serviceLevelDescription' in entitlement:
                                result['serviceLevelDescription'] = entitlement['serviceLevelDescription']
                            if 'startDate' in entitlement:
                                result['startDate'] = entitlement['startDate']
                            if 'endDate' in entitlement:
                                result['endDate'] = entitlement['endDate']
                            # If we found all the entitlement fields, break out of the loop
                            if result['serviceLevelDescription'] and result['startDate'] and result['endDate']:
                                break
    # Check if the data is a dictionary that might contain entitlements
    elif isinstance(entitlement_data, dict):
        # Check if there's a 'data' key that contains the entitlements
        if 'data' in entitlement_data and isinstance(entitlement_data['data'], list):
            for item in entitlement_data['data']:
                if isinstance(item, dict):
                    # Extract asset information
                    if 'serviceTag' in item:
                        result['serviceTag'] = item['serviceTag']
                    if 'productLineDescription' in item:
                        result['productLineDescription'] = item['productLineDescription']
                    if 'countryCode' in item:
                        result['countryCode'] = item['countryCode']
                    if 'shipDate' in item:
                        result['shipDate'] = item['shipDate']
                    
                    # Check if this item has an 'entitlements' key
                    if 'entitlements' in item and isinstance(item['entitlements'], list):
                        for entitlement in item['entitlements']:
                            if isinstance(entitlement, dict):
                                if 'serviceLevelDescription' in entitlement:
                                    result['serviceLevelDescription'] = entitlement['serviceLevelDescription']
                                if 'startDate' in entitlement:
                                    result['startDate'] = entitlement['startDate']
                                if 'endDate' in entitlement:
                                    result['endDate'] = entitlement['endDate']
                                # If we found all the entitlement fields, break out of the loop
                                if result['serviceLevelDescription'] and result['startDate'] and result['endDate']:
                                    break
    
    return result

@app.route('/api/entitlement/<service_tag>', methods=['GET'])
def get_entitlement_info(service_tag):
    """API endpoint to get entitlement information for a service tag."""
    try:
        client = DellEntitlementClient()
        entitlement_data = client.get_entitlement(service_tag)
        
        # Extract the specific fields we want
        result = extract_entitlement_fields(entitlement_data)
        
        # Add the service tag from the URL if it's not in the result
        if not result['serviceTag']:
            result['serviceTag'] = service_tag
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/entitlement', methods=['POST'])
def get_entitlement_info_post():
    """API endpoint to get entitlement information for a service tag using POST."""
    try:
        data = request.get_json()
        
        if not data or 'serviceTag' not in data:
            return jsonify({"error": "Missing serviceTag in request body"}), 400
        
        service_tag = data['serviceTag']
        
        client = DellEntitlementClient()
        entitlement_data = client.get_entitlement(service_tag)
        
        # Extract the specific fields we want
        result = extract_entitlement_fields(entitlement_data)
        
        # Add the service tag from the request if it's not in the result
        if not result['serviceTag']:
            result['serviceTag'] = service_tag
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    ssl_enabled = os.environ.get('SSL_ENABLED', 'false').lower() == 'true'
    
    if ssl_enabled:
        cert_path = os.environ.get('SSL_CERT_PATH', '/app/certs/server.crt')
        key_path = os.environ.get('SSL_KEY_PATH', '/app/certs/server.key')
        
        if not os.path.exists(cert_path):
            print(f"Error: SSL certificate not found at {cert_path}")
            exit(1)
        if not os.path.exists(key_path):
            print(f"Error: SSL private key not found at {key_path}")
            exit(1)
            
        print(f"Starting API server with SSL enabled (cert: {cert_path}, key: {key_path})")
        app.run(
            host='0.0.0.0',
            port=port,
            debug=True,
            ssl_context=(cert_path, key_path)
        )
    else:
        print("Starting API server without SSL")
        app.run(host='0.0.0.0', port=port, debug=True) 