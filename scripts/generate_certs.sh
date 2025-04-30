#!/bin/bash

# Create certificates directory if it doesn't exist
mkdir -p certs

# Generate private key
openssl genrsa -out certs/server.key 2048

# Generate certificate signing request
openssl req -new -key certs/server.key -out certs/server.csr -subj "/CN=localhost"

# Generate self-signed certificate
openssl x509 -req -days 365 -in certs/server.csr -signkey certs/server.key -out certs/server.crt

# Generate CA certificate
openssl req -x509 -newkey rsa:2048 -keyout certs/ca.key -out certs/ca.crt -days 365 -subj "/CN=Local CA" -nodes

# Set appropriate permissions
chmod 600 certs/server.key certs/ca.key
chmod 644 certs/server.crt certs/ca.crt

echo "Certificates generated successfully in the certs directory"
echo "server.crt: Self-signed server certificate"
echo "server.key: Server private key"
echo "ca.crt: CA certificate" 