#!/usr/bin/env python3
import os
import json
import time
import logging
import ssl
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests
import yaml
import re
from gunicorn.app.base import BaseApplication

# Load environment variables
load_dotenv()

def substitute_env_vars(config):
    """Recursively substitute environment variables in config values."""
    if isinstance(config, dict):
        return {k: substitute_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [substitute_env_vars(v) for v in config]
    elif isinstance(config, str):
        # Handle ${VAR:-default} syntax
        match = re.match(r'\${([^:]+):-([^}]+)}', config)
        if match:
            var_name, default = match.groups()
            return os.getenv(var_name, default)
        # Handle ${VAR} syntax
        match = re.match(r'\${([^}]+)}', config)
        if match:
            var_name = match.group(1)
            return os.getenv(var_name, config)
        return config
    return config

class StandaloneApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

def configure_ssl():
    """Configure and verify SSL settings."""
    ssl_config = config.get('ssl', {})
    ssl_enabled = ssl_config.get('enabled', False)
    
    if not ssl_enabled:
        return None, False
        
    cert_path = ssl_config.get('cert_path')
    key_path = ssl_config.get('key_path')
    tls_version = ssl_config.get('tls_version', 'TLSv1_2')
    ciphers = ssl_config.get('ciphers', 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256')
    
    if not cert_path or not key_path:
        logger.error("SSL enabled but certificate or key path not configured")
        return None, False
        
    logger.info(f"SSL certificate path: {cert_path}")
    logger.info(f"SSL key path: {key_path}")
    logger.info(f"TLS version: {tls_version}")
    logger.info(f"SSL ciphers: {ciphers}")
    
    # Check if cert directory exists
    cert_dir = os.path.dirname(cert_path)
    if not os.path.exists(cert_dir):
        logger.error(f"Certificate directory does not exist: {cert_dir}")
        return None, False
    
    # Check certificate files
    if not os.path.exists(cert_path):
        logger.error(f"SSL certificate not found at {cert_path}")
        return None, False
    if not os.path.exists(key_path):
        logger.error(f"SSL private key not found at {key_path}")
        return None, False
        
    # Configure SSL context with strong security settings
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context.load_cert_chain(cert_path, key_path)
    ssl_context.set_ciphers(ciphers)
    
    # Set minimum TLS version
    if hasattr(ssl, 'TLSVersion'):
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    else:
        # Fallback for older Python versions
        ssl_context.options |= (
            ssl.OP_NO_SSLv2 |
            ssl.OP_NO_SSLv3 |
            ssl.OP_NO_TLSv1 |
            ssl.OP_NO_TLSv1_1
        )
    
    # Additional security options
    ssl_context.options |= (
        ssl.OP_NO_COMPRESSION |
        ssl.OP_SINGLE_DH_USE |
        ssl.OP_SINGLE_ECDH_USE |
        ssl.OP_CIPHER_SERVER_PREFERENCE
    )
    
    # Enable forward secrecy
    ssl_context.set_ecdh_curve('prime256v1')
    
    return ssl_context, True

# Load configuration
config_path = os.getenv('CONFIG_PATH', 'config/config.yaml')
try:
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    # Substitute environment variables
    config = substitute_env_vars(config)
    logging.info(f"Successfully loaded configuration from {config_path}")
except Exception as e:
    logging.error(f"Error loading config from {config_path}: {e}")
    config = {}

# Configure logging
logging_config = config.get('logging', {})
logging.basicConfig(
    level=getattr(logging, logging_config.get('level', 'INFO').upper()),
    format=logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
    filename=logging_config.get('file') if logging_config.get('file') != 'null' else None
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize cache
cache = {}
cache_config = config.get('cache', {})
cache_enabled = cache_config.get('enabled', True)
cache_ttl = cache_config.get('ttl', 3600)  # Default 1 hour

# Server configuration
server_config = config.get('server', {})
host = server_config.get('host', '0.0.0.0')
port = int(server_config.get('port', 5001))
debug = server_config.get('debug', False)
use_wsgi = server_config.get('use_wsgi', False)
worker_class = server_config.get('wsgi_worker_class', 'gthread')

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
    logger.info(f"Starting API server on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Using WSGI: {use_wsgi}")
    
    # Configure SSL if enabled
    ssl_context, ssl_enabled = configure_ssl()
    
    if use_wsgi:
        options = {
            'bind': f'{host}:{port}',
            'workers': server_config.get('workers', 4),
            'worker_class': worker_class,
            'timeout': server_config.get('timeout', 120),
            'keepalive': server_config.get('keepalive', 5),
            'loglevel': logging_config.get('level', 'info'),
        }
        
        if ssl_enabled:
            options['certfile'] = config['ssl']['cert_path']
            options['keyfile'] = config['ssl']['key_path']
            options['ssl_version'] = getattr(ssl, f'PROTOCOL_{config["ssl"]["tls_version"]}')
            options['ciphers'] = config['ssl']['ciphers']
        
        StandaloneApplication(app, options).run()
    else:
        if ssl_enabled:
            logger.info("Starting API server with SSL enabled")
            app.run(
                host=host,
                port=port,
                debug=debug,
                ssl_context=ssl_context
            )
        else:
            logger.info("Starting API server without SSL")
            app.run(host=host, port=port, debug=debug) 