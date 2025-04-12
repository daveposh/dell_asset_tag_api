#!/usr/bin/env python3
import os
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)

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
                error_info = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.text
                }
                raise Exception(f"API error: {json.dumps(error_info)}")
            
            return response.json()
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
    app.run(host='0.0.0.0', port=port, debug=True) 