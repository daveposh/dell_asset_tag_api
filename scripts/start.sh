#!/bin/bash

# Ensure the script fails on any error
set -e

echo "Starting Dell API Service..."

# Check if config file exists
if [ ! -f "$CONFIG_PATH" ]; then
    echo "Error: Configuration file not found at $CONFIG_PATH"
    exit 1
fi

# Check for required environment variables
if [ -z "$DELL_API_CLIENT_ID" ] || [ -z "$DELL_API_CLIENT_SECRET" ]; then
    echo "Error: DELL_API_CLIENT_ID and DELL_API_CLIENT_SECRET must be set"
    exit 1
fi

# Create certificates directory if it doesn't exist
mkdir -p /app/certs

# Check for SSL certificates if SSL is enabled
if [ "$SSL_ENABLED" = "true" ]; then
    echo "SSL is enabled, checking certificates..."
    
    # Check for server certificate
    if [ ! -f "$SSL_CERT_PATH" ]; then
        echo "Error: SSL certificate not found at $SSL_CERT_PATH"
        exit 1
    fi
    
    # Check for private key
    if [ ! -f "$SSL_KEY_PATH" ]; then
        echo "Error: SSL private key not found at $SSL_KEY_PATH"
        exit 1
    fi
    
    # Check for CA certificate if specified
    if [ ! -z "$SSL_CA_CERT_PATH" ] && [ ! -f "$SSL_CA_CERT_PATH" ]; then
        echo "Error: CA certificate not found at $SSL_CA_CERT_PATH"
        exit 1
    fi
    
    echo "SSL certificates found and validated"
fi

# Start the application with gunicorn
echo "Starting Gunicorn server..."

# Base gunicorn command
GUNICORN_CMD="gunicorn --bind 0.0.0.0:5000 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output \
    --enable-stdio-inheritance"

# Add SSL configuration if enabled
if [ "$SSL_ENABLED" = "true" ]; then
    GUNICORN_CMD="$GUNICORN_CMD \
        --certfile $SSL_CERT_PATH \
        --keyfile $SSL_KEY_PATH"
    
    if [ ! -z "$SSL_CA_CERT_PATH" ]; then
        GUNICORN_CMD="$GUNICORN_CMD --ca-certs $SSL_CA_CERT_PATH"
    fi
fi

# Add the application module
GUNICORN_CMD="$GUNICORN_CMD dell_api:app"

# Execute the command
exec $GUNICORN_CMD 