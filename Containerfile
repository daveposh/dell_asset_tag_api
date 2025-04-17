# Use Alpine Linux as base image
FROM alpine:3.19

# Install Python and required packages using the system package manager
# Also install build dependencies and shared libraries
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-flask \
    py3-requests \
    py3-dotenv \
    py3-gunicorn \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    ca-certificates

# Create a non-root user
RUN adduser -D -u 1000 appuser

# Create necessary directories
RUN mkdir -p /app/config /app/scripts /app/certs

# Set working directory
WORKDIR /app

# Copy start.sh script first and set permissions
COPY scripts/start.sh /app/scripts/
RUN chmod +x /app/scripts/start.sh

# Copy application code
COPY . .

# Set permissions for all files
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CONFIG_PATH=/app/config/config.yaml
ENV SSL_ENABLED=false
ENV SSL_CERT_PATH=/app/certs/server.crt
ENV SSL_KEY_PATH=/app/certs/server.key
ENV SSL_CA_CERT_PATH=/app/certs/ca.crt

# Expose port
EXPOSE 5000

# Set the entrypoint to the startup script
ENTRYPOINT ["/app/scripts/start.sh"] 