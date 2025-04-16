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

# Dell API Service - Podman Setup Guide

This guide will help you set up and run the Dell API service using Podman.

## Prerequisites

1. **Podman Installation**
   - Windows: Install Podman Desktop from [Podman Desktop](https://podman-desktop.io/)
   - Linux: 
     ```bash
     # For Ubuntu/Debian
     sudo apt-get update
     sudo apt-get install podman
     
     # For RHEL/CentOS
     sudo dnf install podman
     ```

2. **Required Environment Variables**
   - `DELL_API_CLIENT_ID`: Your Dell API client ID
   - `DELL_API_CLIENT_SECRET`: Your Dell API client secret

## Quick Start

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd dell_asset_tag_api
   ```

2. **Build the Container**
   ```bash
   # Using the default Containerfile
   podman build -t dell-api .
   
   # Or explicitly specify the Containerfile
   podman build -t dell-api -f Containerfile .
   ```

3. **Run the Container**
   ```bash
   podman run -d \
     -p 5000:5000 \
     -e DELL_API_CLIENT_ID=your_client_id \
     -e DELL_API_CLIENT_SECRET=your_client_secret \
     --name dell-api \
     dell-api
   ```

## SSL Configuration (Optional)

To enable SSL, you'll need to:
1. Prepare your SSL certificates
2. Mount them into the container
3. Enable SSL in the configuration

```bash
podman run -d \
  -p 5000:5000 \
  -e DELL_API_CLIENT_ID=your_client_id \
  -e DELL_API_CLIENT_SECRET=your_client_secret \
  -e SSL_ENABLED=true \
  -v /path/to/your/certs:/app/certs:ro \
  --name dell-api \
  dell-api
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DELL_API_CLIENT_ID` | Dell API client ID | Required |
| `DELL_API_CLIENT_SECRET` | Dell API client secret | Required |
| `SSL_ENABLED` | Enable SSL | false |
| `SSL_CERT_PATH` | Path to SSL certificate | /app/certs/server.crt |
| `SSL_KEY_PATH` | Path to SSL private key | /app/certs/server.key |
| `SSL_CA_CERT_PATH` | Path to CA certificate | /app/certs/ca.crt |

### Configuration File

The service uses a YAML configuration file located at `/app/config/config.yaml`. You can mount your own configuration file:

```bash
podman run -d \
  -p 5000:5000 \
  -v /path/to/your/config.yaml:/app/config/config.yaml:ro \
  -e DELL_API_CLIENT_ID=your_client_id \
  -e DELL_API_CLIENT_SECRET=your_client_secret \
  --name dell-api \
  dell-api
```

## Managing the Container

### View Logs
```bash
# View all logs
podman logs dell-api

# Follow logs in real-time
podman logs -f dell-api

# View last 100 lines
podman logs --tail 100 dell-api
```

### Stop the Container
```bash
podman stop dell-api
```

### Remove the Container
```bash
podman rm dell-api
```

### Restart the Container
```bash
podman restart dell-api
```

### Container Management
```bash
# List running containers
podman ps

# List all containers (including stopped)
podman ps -a

# Inspect container
podman inspect dell-api

# View container resource usage
podman stats dell-api
```

## API Endpoints

- `GET /api/health`: Health check endpoint
- `GET /api/entitlement/<service_tag>`: Get entitlement information for a service tag
- `POST /api/entitlement`: Get entitlement information using POST method

## Troubleshooting

1. **Container Won't Start**
   - Check if required environment variables are set
   - Verify port 5000 is not in use
   - Check logs: `podman logs dell-api`
   - Verify Containerfile syntax: `podman build --no-cache -t dell-api .`

2. **SSL Issues**
   - Verify certificates are properly mounted
   - Check certificate permissions
   - Ensure SSL paths match your configuration
   - Check SELinux context if applicable: `chcon -Rt container_file_t /path/to/certs`

3. **API Connection Issues**
   - Verify Dell API credentials
   - Check network connectivity
   - Ensure proper port forwarding
   - Check container network: `podman network inspect bridge`

## Security Considerations

1. **Environment Variables**
   - Never commit sensitive credentials to version control
   - Use environment variables or secure secret management
   - Consider using Podman secrets for sensitive data:
     ```bash
     # Create a secret
     podman secret create dell-api-secrets secrets.json
     
     # Use the secret in your container
     podman run --secret dell-api-secrets ...
     ```

2. **SSL Certificates**
   - Keep certificates secure and up to date
   - Use read-only mounts for certificates
   - Regularly rotate certificates
   - Consider using Podman volumes for certificate storage

3. **Container Security**
   - Run as non-root user (already configured)
   - Use read-only mounts where possible
   - Keep the container image updated
   - Use Podman's security features:
     ```bash
     # Run with additional security options
     podman run --cap-drop=ALL --security-opt=no-new-privileges ...
     ```

## Support

For issues or questions:
1. Check the logs using `podman logs dell-api`
2. Verify your configuration
3. Ensure all prerequisites are met
4. Contact the development team for assistance 