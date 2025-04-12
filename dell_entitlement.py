#!/usr/bin/env python3
import os
import json
import csv
from typing import List, Dict, Optional, Union, Any
import click
import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# Load environment variables
load_dotenv()

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
            raise click.ClickException(f"Authentication failed: {str(e)}")

    def get_entitlement(self, service_tag: str) -> Union[Dict, List]:
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
                click.echo(f"Status Code: {response.status_code}")
                click.echo(f"Response Headers: {response.headers}")
                try:
                    click.echo(f"Response Body: {response.text}")
                except:
                    click.echo("Could not read response body")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 401:
                # Token might be expired, try to authenticate again
                self.authenticate()
                return self.get_entitlement(service_tag)
            raise click.ClickException(f"Error fetching entitlement data: {str(e)}")

def display_entitlement(entitlement_data: Union[Dict, List], console: Console):
    """Display entitlement information in a formatted table."""
    table = Table(title="Dell Entitlement Information")
    
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    
    # Handle both dictionary and list responses
    if isinstance(entitlement_data, dict):
        # Add rows based on the entitlement data structure
        for key, value in entitlement_data.items():
            if isinstance(value, (str, int, float)):
                table.add_row(key, str(value))
            elif isinstance(value, dict):
                table.add_row(key, json.dumps(value, indent=2))
            elif isinstance(value, list):
                table.add_row(key, json.dumps(value, indent=2))
    elif isinstance(entitlement_data, list):
        # If it's a list, display each item
        for i, item in enumerate(entitlement_data):
            if isinstance(item, dict):
                table.add_row(f"Item {i+1}", json.dumps(item, indent=2))
            else:
                table.add_row(f"Item {i+1}", str(item))
    else:
        # If it's neither a dict nor a list, just display it as is
        table.add_row("Response", str(entitlement_data))
    
    console.print(table)

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """Flatten a nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def extract_entitlement_fields(entitlement_data: Union[Dict, List], debug: bool = False) -> List[Dict[str, Any]]:
    """Extract specific fields from the entitlement data."""
    entitlement_fields = []
    
    # Define the fields we want to extract
    entitlement_target_fields = ['itemNumber', 'startDate', 'endDate', 'entitlementType', 
                    'serviceLevelCode', 'serviceLevelDescription', 'serviceLevelGroup']
    
    # Define the asset fields we want to extract
    asset_target_fields = ['id', 'serviceTag', 'orderBuid', 'shipDate', 'productCode', 
                          'localChannel', 'productId', 'productLineDescription', 
                          'productFamily', 'systemDescription', 'productLobDescription', 
                          'countryCode', 'duplicated', 'invalid']
    
    if debug:
        click.echo(f"Extracting fields from data: {json.dumps(entitlement_data, indent=2)}")
    
    # Check if the data is a list of items that might contain entitlements
    if isinstance(entitlement_data, list):
        if debug:
            click.echo("Data is a list")
        for item in entitlement_data:
            if isinstance(item, dict):
                # Extract asset information
                asset_data = {}
                for key in asset_target_fields:
                    if key in item:
                        asset_data[key] = item[key]
                
                # Check if this item has an 'entitlements' key
                if 'entitlements' in item and isinstance(item['entitlements'], list):
                    if debug:
                        click.echo(f"Found 'entitlements' key in item with {len(item['entitlements'])} entitlements")
                    # Extract entitlements from this item
                    for entitlement in item['entitlements']:
                        if isinstance(entitlement, dict):
                            # Extract the specific fields we want
                            field_data = {}
                            # Add asset information to each entitlement
                            field_data.update(asset_data)
                            # Add entitlement information
                            for key in entitlement_target_fields:
                                if key in entitlement:
                                    field_data[key] = entitlement[key]
                            if field_data:
                                entitlement_fields.append(field_data)
                                if debug:
                                    click.echo(f"Extracted fields: {field_data}")
                # If no entitlements, just add the asset information
                elif asset_data:
                    entitlement_fields.append(asset_data)
                    if debug:
                        click.echo(f"Extracted asset fields: {asset_data}")
    # Check if the data is a dictionary that might contain entitlements
    elif isinstance(entitlement_data, dict):
        if debug:
            click.echo("Data is a dictionary")
        # Check if there's a 'data' key that contains the entitlements
        if 'data' in entitlement_data and isinstance(entitlement_data['data'], list):
            if debug:
                click.echo("Found 'data' key with list value")
            for item in entitlement_data['data']:
                if isinstance(item, dict):
                    # Extract asset information
                    asset_data = {}
                    for key in asset_target_fields:
                        if key in item:
                            asset_data[key] = item[key]
                    
                    # Check if this item has an 'entitlements' key
                    if 'entitlements' in item and isinstance(item['entitlements'], list):
                        if debug:
                            click.echo(f"Found 'entitlements' key in item with {len(item['entitlements'])} entitlements")
                        # Extract entitlements from this item
                        for entitlement in item['entitlements']:
                            if isinstance(entitlement, dict):
                                # Extract the specific fields we want
                                field_data = {}
                                # Add asset information to each entitlement
                                field_data.update(asset_data)
                                # Add entitlement information
                                for key in entitlement_target_fields:
                                    if key in entitlement:
                                        field_data[key] = entitlement[key]
                                if field_data:
                                    entitlement_fields.append(field_data)
                                    if debug:
                                        click.echo(f"Extracted fields: {field_data}")
                    # If no entitlements, just add the asset information
                    elif asset_data:
                        entitlement_fields.append(asset_data)
                        if debug:
                            click.echo(f"Extracted asset fields: {asset_data}")
        # Check if there's an 'entitlements' key that contains the entitlements
        elif 'entitlements' in entitlement_data and isinstance(entitlement_data['entitlements'], list):
            if debug:
                click.echo("Found 'entitlements' key with list value")
            for item in entitlement_data['entitlements']:
                if isinstance(item, dict):
                    # Extract the specific fields we want
                    field_data = {}
                    for key in entitlement_target_fields:
                        if key in item:
                            field_data[key] = item[key]
                    if field_data:
                        entitlement_fields.append(field_data)
                        if debug:
                            click.echo(f"Extracted fields: {field_data}")
        # Check other keys that might contain entitlements
        else:
            for key, value in entitlement_data.items():
                if isinstance(value, list):
                    if debug:
                        click.echo(f"Found list in key '{key}'")
                    for item in value:
                        if isinstance(item, dict):
                            # Extract asset information
                            asset_data = {}
                            for key in asset_target_fields:
                                if key in item:
                                    asset_data[key] = item[key]
                            
                            # Check if this item has an 'entitlements' key
                            if 'entitlements' in item and isinstance(item['entitlements'], list):
                                if debug:
                                    click.echo(f"Found 'entitlements' key in item with {len(item['entitlements'])} entitlements")
                                # Extract entitlements from this item
                                for entitlement in item['entitlements']:
                                    if isinstance(entitlement, dict):
                                        # Extract the specific fields we want
                                        field_data = {}
                                        # Add asset information to each entitlement
                                        field_data.update(asset_data)
                                        # Add entitlement information
                                        for key in entitlement_target_fields:
                                            if key in entitlement:
                                                field_data[key] = entitlement[key]
                                        if field_data:
                                            entitlement_fields.append(field_data)
                                            if debug:
                                                click.echo(f"Extracted fields: {field_data}")
                            # If no entitlements, just add the asset information
                            elif asset_data:
                                entitlement_fields.append(asset_data)
                                if debug:
                                    click.echo(f"Extracted asset fields: {asset_data}")
                elif isinstance(value, dict):
                    # Check if this dictionary contains entitlement fields
                    field_data = {}
                    for field in entitlement_target_fields:
                        if field in value:
                            field_data[field] = value[field]
                    if field_data:
                        entitlement_fields.append(field_data)
                        if debug:
                            click.echo(f"Extracted fields: {field_data}")
    
    if debug:
        click.echo(f"Extracted {len(entitlement_fields)} entitlement records")
    
    return entitlement_fields

def export_to_csv(entitlement_data: Union[Dict, List], filename: str, debug: bool = False):
    """Export entitlement information to a CSV file."""
    # Extract the specific fields we want
    entitlement_fields = extract_entitlement_fields(entitlement_data, debug)
    
    # Define the fields we want to include in the CSV
    entitlement_target_fields = ['itemNumber', 'startDate', 'endDate', 'entitlementType', 
                    'serviceLevelCode', 'serviceLevelDescription', 'serviceLevelGroup']
    
    # Define the asset fields we want to include in the CSV
    asset_target_fields = ['id', 'serviceTag', 'orderBuid', 'shipDate', 'productCode', 
                          'localChannel', 'productId', 'productLineDescription', 
                          'productFamily', 'systemDescription', 'productLobDescription', 
                          'countryCode', 'duplicated', 'invalid']
    
    # Combine all target fields
    all_target_fields = asset_target_fields + entitlement_target_fields
    
    if not entitlement_fields:
        if debug:
            click.echo("No entitlement fields found, creating a default row with empty values")
        # If no specific fields were found, create a default row with empty values
        entitlement_fields = [{}]
    
    # Write the extracted fields to the CSV
    with open(filename, 'w', newline='') as csvfile:
        # Use the target fields as the column headers
        writer = csv.DictWriter(csvfile, fieldnames=all_target_fields)
        writer.writeheader()
        
        # Write each row, ensuring all fields are present (even if empty)
        for item in entitlement_fields:
            row = {field: item.get(field, '') for field in all_target_fields}
            writer.writerow(row)
            if debug:
                click.echo(f"Wrote row: {row}")

def import_asset_list(filename: str, debug: bool = False) -> List[Dict[str, str]]:
    """Import a list of assets from a CSV file with Name and Asset Tag columns."""
    assets = []
    
    try:
        with open(filename, 'r', newline='', encoding='utf-8-sig') as csvfile:
            # Read the first line to check the column names
            first_line = csvfile.readline().strip()
            if debug:
                click.echo(f"First line of CSV: '{first_line}'")
            
            # Reset the file pointer
            csvfile.seek(0)
            
            # Try to detect the delimiter
            if ',' in first_line:
                delimiter = ','
            elif '\t' in first_line:
                delimiter = '\t'
            else:
                delimiter = ','
            
            if debug:
                click.echo(f"Using delimiter: '{delimiter}'")
            
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            
            # Get the actual column names
            fieldnames = reader.fieldnames
            if debug:
                click.echo(f"CSV columns: {fieldnames}")
            
            # Check if the required columns exist (case-insensitive)
            name_col = None
            asset_tag_col = None
            warranty_col = None
            acquisition_date_col = None
            warranty_expiry_date_col = None
            
            for col in fieldnames:
                if col.lower() == 'name':
                    name_col = col
                elif col.lower() == 'asset tag' or col.lower() == 'asset_tag' or col.lower() == 'assettag':
                    asset_tag_col = col
                elif col.lower() == 'warranty':
                    warranty_col = col
                elif col.lower() == 'acquisition date' or col.lower() == 'acquisition_date':
                    acquisition_date_col = col
                elif col.lower() == 'warranty expiry date' or col.lower() == 'warranty_expiry_date':
                    warranty_expiry_date_col = col
            
            if not name_col or not asset_tag_col:
                raise ValueError(f"CSV file must contain 'Name' and 'Asset Tag' columns. Found columns: {fieldnames}")
            
            # Read each row
            for row in reader:
                name = row[name_col].strip()
                asset_tag = row[asset_tag_col].strip()
                
                if name and asset_tag:
                    asset_data = {
                        'name': name,
                        'service_tag': asset_tag
                    }
                    
                    # Add additional fields if they exist
                    if warranty_col and warranty_col in row:
                        asset_data['warranty'] = row[warranty_col].strip()
                    
                    if acquisition_date_col and acquisition_date_col in row:
                        asset_data['acquisition_date'] = row[acquisition_date_col].strip()
                    
                    if warranty_expiry_date_col and warranty_expiry_date_col in row:
                        asset_data['warranty_expiry_date'] = row[warranty_expiry_date_col].strip()
                    
                    assets.append(asset_data)
                    if debug:
                        click.echo(f"Imported asset: {name} ({asset_tag})")
    
    except FileNotFoundError:
        raise click.ClickException(f"File not found: {filename}")
    except Exception as e:
        raise click.ClickException(f"Error importing asset list: {str(e)}")
    
    if debug:
        click.echo(f"Imported {len(assets)} assets from {filename}")
    
    return assets

def process_asset_list(assets: List[Dict[str, str]], output_file: str, debug: bool = False):
    """Process a list of assets and export their entitlement information to a CSV file."""
    client = DellEntitlementClient()
    all_entitlements = []
    
    # Define the fields we want to include in the CSV
    entitlement_target_fields = ['itemNumber', 'startDate', 'endDate', 'entitlementType', 
                    'serviceLevelCode', 'serviceLevelDescription', 'serviceLevelGroup']
    
    # Define the asset fields we want to include in the CSV
    asset_target_fields = ['id', 'serviceTag', 'orderBuid', 'shipDate', 'productCode', 
                          'localChannel', 'productId', 'productLineDescription', 
                          'productFamily', 'systemDescription', 'productLobDescription', 
                          'countryCode', 'duplicated', 'invalid']
    
    # Add Name field to the asset fields
    asset_target_fields.insert(0, 'name')
    
    # Add additional fields from the input CSV
    additional_fields = ['warranty', 'acquisition_date', 'warranty_expiry_date']
    
    # Combine all target fields
    all_target_fields = asset_target_fields + entitlement_target_fields + additional_fields
    
    # Process each asset
    for asset in assets:
        name = asset['name']
        service_tag = asset['service_tag']
        
        # Get additional fields if they exist
        warranty = asset.get('warranty', '')
        acquisition_date = asset.get('acquisition_date', '')
        warranty_expiry_date = asset.get('warranty_expiry_date', '')
        
        if debug:
            click.echo(f"Processing asset: {name} ({service_tag})")
        
        try:
            # Get entitlement data for this asset
            entitlement_data = client.get_entitlement(service_tag)
            
            # Extract the specific fields we want
            entitlement_fields = extract_entitlement_fields(entitlement_data, debug)
            
            # Add the name and additional fields to each entitlement record
            for field_data in entitlement_fields:
                field_data['name'] = name
                field_data['warranty'] = warranty
                field_data['acquisition_date'] = acquisition_date
                field_data['warranty_expiry_date'] = warranty_expiry_date
                all_entitlements.append(field_data)
            
            if debug:
                click.echo(f"Found {len(entitlement_fields)} entitlement records for {name} ({service_tag})")
        
        except Exception as e:
            click.echo(f"Error processing asset {name} ({service_tag}): {str(e)}")
    
    # Write all entitlements to the CSV file
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=all_target_fields)
        writer.writeheader()
        
        for item in all_entitlements:
            row = {field: item.get(field, '') for field in all_target_fields}
            writer.writerow(row)
            if debug:
                click.echo(f"Wrote row: {row}")
    
    if debug:
        click.echo(f"Exported {len(all_entitlements)} entitlement records to {output_file}")

@click.group()
def cli():
    """Dell Entitlement CLI Tool"""
    pass

@cli.command()
@click.argument('service_tag')
@click.option('--debug', is_flag=True, help='Enable debug mode to show detailed API responses')
@click.option('--export', '-e', help='Export the results to a CSV file')
def check_entitlement(service_tag: str, debug: bool, export: str):
    """Check entitlement information for a Dell service tag."""
    console = Console()
    
    try:
        client = DellEntitlementClient()
        entitlement_data = client.get_entitlement(service_tag)
        
        if debug:
            click.echo(f"API Response: {json.dumps(entitlement_data, indent=2)}")
        
        display_entitlement(entitlement_data, console)
        
        # Export to CSV if requested
        if export:
            export_to_csv(entitlement_data, export, debug)
            console.print(f"[green]Data exported to {export}[/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()

@cli.command()
@click.argument('input_file')
@click.option('--output', '-o', default='entitlements.csv', help='Output CSV file')
@click.option('--debug', is_flag=True, help='Enable debug mode to show detailed API responses')
def process_assets(input_file: str, output: str, debug: bool):
    """Process a list of assets from a CSV file and export their entitlement information."""
    console = Console()
    
    try:
        # Import the asset list
        assets = import_asset_list(input_file, debug)
        
        if not assets:
            console.print("[yellow]No assets found in the input file.[/yellow]")
            return
        
        # Process the assets and export the results
        process_asset_list(assets, output, debug)
        
        console.print(f"[green]Successfully processed {len(assets)} assets and exported data to {output}[/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()

if __name__ == '__main__':
    cli() 