# Dell Asset Tag API

A Python tool for interacting with Dell's API to retrieve asset and entitlement information. This tool provides both a command-line interface (CLI) and a REST API for integration with other systems.

## Features

- Authentication with Dell API using OAuth2
- Retrieve asset information using service tags
- Check warranty and entitlement status
- Export data to CSV format
- Import data from CSV files
- Debug mode for troubleshooting
- TLS certificate verification options
- REST API for integration
- Command-line interface for direct usage

## Prerequisites

- Python 3.6 or higher
- Required Python packages (see requirements.txt)
- Dell API credentials
- TLS certificate (if required by your environment)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/dell_asset_tag_api.git
cd dell_asset_tag_api
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your configuration:
```
DELL_CLIENT_ID=your_client_id
DELL_CLIENT_SECRET=your_client_secret
DELL_API_BASE_URL=your_api_base_url
DELL_CA_CERT=/path/to/your/certificate.pem  # Optional: Path to your CA certificate
DELL_VERIFY_SSL=true  # Optional: Set to false to disable SSL verification (not recommended for production)
```

## Command Line Interface (CLI)

The tool provides a command-line interface for direct usage. All commands support the following common options:
- `--debug`: Enable debug mode for detailed output
- `--no-verify-ssl`: Disable SSL certificate verification (not recommended for production)

### Available Commands

#### Check Asset Information

```bash
python dell_entitlement.py check-asset <service_tag> [--debug] [--no-verify-ssl]
```

Example:
```bash
python dell_entitlement.py check-asset <service_tag> --debug
```

#### Check Entitlement Information

```bash
python dell_entitlement.py check-entitlement <service_tag> [--debug] [--export] [--no-verify-ssl]
```

Example:
```bash
python dell_entitlement.py check-entitlement <service_tag> --debug --export
```

#### Import from CSV

```bash
python dell_entitlement.py import-csv <input_file.csv> [--debug] [--export] [--no-verify-ssl]
```

Example:
```bash
python dell_entitlement.py import-csv assets.csv --debug --export
```

#### Start API Server

```bash
python dell_entitlement.py serve [--host HOST] [--port PORT] [--debug]
```

Example:
```bash
python dell_entitlement.py serve --host 0.0.0.0 --port 5000 --debug
```

## REST API

The tool also provides a REST API for integration with other systems. The API server can be started using the `serve` command.

### API Endpoints

#### GET /api/asset/{service_tag}

Retrieves asset information for a specific service tag.

Example:
```bash
curl -X GET "http://localhost:5000/api/asset/<service_tag>"
```

Response:
```json
{
  "serviceTag": "<service_tag>",
  "productLineDescription": "Product Description",
  "shipDate": "YYYY-MM-DDTHH:MM:SSZ",
  "countryCode": "XX"
}
```

#### GET /api/entitlement/{service_tag}

Retrieves entitlement information for a specific service tag.

Example:
```bash
curl -X GET "http://localhost:5000/api/entitlement/<service_tag>"
```

Response:
```json
{
  "serviceTag": "<service_tag>",
  "entitlements": [
    {
      "itemNumber": "XXXXXX",
      "startDate": "YYYY-MM-DDTHH:MM:SSZ",
      "endDate": "YYYY-MM-DDTHH:MM:SSZ",
      "entitlementType": "Type",
      "serviceLevelCode": "XX",
      "serviceLevelDescription": "Description",
      "serviceLevelGroup": "Group"
    }
  ]
}
```

#### POST /api/import

Import service tags from a CSV file.

Example:
```bash
curl -X POST "http://localhost:5000/api/import" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@assets.csv"
```

Response:
```json
{
  "message": "Import successful",
  "processed": 3,
  "successful": 3,
  "failed": 0
}
```

### API Authentication

The API supports two authentication methods:

1. API Key Authentication:
   - Set the `DELL_API_KEY` environment variable
   - Include the API key in the `X-API-Key` header
   ```bash
   curl -X GET "http://localhost:5000/api/asset/<service_tag>" \
     -H "X-API-Key: your_api_key"
   ```

2. OAuth2 Authentication:
   - Set the `DELL_CLIENT_ID` and `DELL_CLIENT_SECRET` environment variables
   - Include the OAuth2 token in the `Authorization` header
   ```bash
   curl -X GET "http://localhost:5000/api/asset/<service_tag>" \
     -H "Authorization: Bearer your_oauth_token"
   ```

### TLS Certificate Configuration

The tool supports several options for TLS certificate verification:

1. Using a custom CA certificate:
   - Set the `DELL_CA_CERT` environment variable to point to your certificate file
   - The certificate should be in PEM format
   - Example: `DELL_CA_CERT=/path/to/your/certificate.pem`

2. Disabling SSL verification (not recommended for production):
   - Set `DELL_VERIFY_SSL=false` in your `.env` file
   - Or use the `--no-verify-ssl` flag with any command
   - Example: `python dell_entitlement.py check-asset <service_tag> --no-verify-ssl`

3. Using system certificates (default):
   - If no certificate is specified, the tool will use your system's certificate store
   - This is the recommended approach for most environments

### Export to CSV

When using the `--export` flag, the tool will create a CSV file with the following columns:
- itemNumber
- startDate
- endDate
- entitlementType
- serviceLevelCode
- serviceLevelDescription
- serviceLevelGroup

## Example Data

The repository includes an `example.csv` file with dummy data to demonstrate the expected format for both importing and exporting data.

## Security

- Never commit your `.env` file or any files containing sensitive information
- The `.gitignore` file is configured to exclude sensitive files and CSV outputs
- Only example files are included in the repository
- Always use proper TLS certificate verification in production environments
- Avoid disabling SSL verification unless absolutely necessary
- Use appropriate authentication methods for API access
- Implement rate limiting for API endpoints in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 