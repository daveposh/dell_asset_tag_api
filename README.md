# Dell Asset Tag API

A Python tool for interacting with Dell's API to retrieve asset and entitlement information. This tool provides both a command-line interface (CLI) and a REST API for integration with other systems.

## Features

- Authentication with Dell API using OAuth2
- Check warranty and entitlement status for service tags
- Export data to CSV format
- Import data from CSV files
- Debug mode for troubleshooting
- Secure TLS configuration with strong ciphers
- Production-ready WSGI server support
- Command-line interface for direct usage

## Prerequisites

- Python 3.6 or higher
- Required Python packages (see requirements.txt)
- Dell API credentials
- SSL certificates (if using HTTPS)

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
```bash
# Copy the example configuration
cp config/config.yaml.example config/config.yaml

# Create .env file with your credentials
cat > .env << EOF
# Dell API Credentials
DELL_API_CLIENT_ID=your_client_id_here
DELL_API_CLIENT_SECRET=your_client_secret_here

# Server Configuration
PORT=5001
DEBUG=false
USE_WSGI=false
LOG_LEVEL=info
LOG_FILE=null

# SSL Configuration
SSL_ENABLED=false
SSL_CERT_PATH=certs/server.crt
SSL_KEY_PATH=certs/server.key
SSL_CA_CERT_PATH=certs/ca.crt

# Cache Configuration
CACHE_ENABLED=true
CACHE_TYPE=memory
CACHE_TTL=3600

# Export Configuration
CSV_DELIMITER=,
CSV_ENCODING=utf-8
CSV_INCLUDE_HEADERS=true
EOF
```

4. Generate SSL certificates (if using HTTPS):
```bash
./scripts/generate_certs.sh
```

## Configuration

The application uses a YAML configuration file (`config/config.yaml`) for settings. Key configuration options include:

### Server Configuration
```yaml
server:
  host: "0.0.0.0"
  port: "${PORT:-5001}"
  debug: "${DEBUG:-false}"
  workers: 4
  timeout: 120
  keepalive: 5
  use_wsgi: "${USE_WSGI:-false}"
  wsgi_worker_class: "gthread"
```

### SSL Configuration
```yaml
ssl:
  enabled: "${SSL_ENABLED:-false}"
  cert_path: "${SSL_CERT_PATH:-certs/server.crt}"
  key_path: "${SSL_KEY_PATH:-certs/server.key}"
  ca_cert_path: "${SSL_CA_CERT_PATH:-certs/ca.crt}"
  tls_version: "TLSv1_2"
  ciphers: "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256"
```

## Running the API Server

### Development Mode
```bash
python dell_api.py
```

### Production Mode with WSGI
```bash
USE_WSGI=true python dell_api.py
```

### With SSL Enabled
```bash
SSL_ENABLED=true python dell_api.py
```

### Production Mode with SSL
```bash
USE_WSGI=true SSL_ENABLED=true python dell_api.py
```

## Command Line Interface (CLI)

The tool provides a command-line interface for checking Dell service tag entitlements. All commands support the following common options:
- `--debug`: Enable debug mode for detailed output

### Available Commands

#### Check Entitlement Information

```bash
python dell_entitlement.py check-entitlement <service_tag> [--debug] [--export]
```

Example:
```bash
python dell_entitlement.py check-entitlement <service_tag> --debug
```

#### Process Multiple Assets from CSV

```bash
python dell_entitlement.py process-assets <input_file.csv> [--output output.csv] [--debug]
```

Example:
```bash
python dell_entitlement.py process-assets assets.csv --output entitlements.csv --debug
```

## Security Features

- TLS 1.2 or higher enforced
- Strong cipher suites only
- Perfect forward secrecy enabled
- No weak or deprecated protocols
- No compression (prevents CRIME attacks)
- Server cipher preference enforced
- DH/ECDH parameters not reused

## Example Data

The repository includes an `example.csv` file with dummy data to demonstrate the expected format for importing data.

## Security

- Never commit your `.env` file or any files containing sensitive information
- The `.gitignore` file is configured to exclude sensitive files and CSV outputs
- Only example files are included in the repository
- Always use proper TLS certificate verification in production environments
- Avoid disabling SSL verification unless absolutely necessary
- Use appropriate authentication methods for API access

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