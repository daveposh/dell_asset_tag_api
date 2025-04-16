# Use Alpine Linux as base image
FROM alpine:3.19

# Install Python and required packages using the system package manager
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-flask \
    py3-requests \
    py3-dotenv \
    py3-gunicorn

# Create a non-root user
RUN adduser -D -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/config /app/scripts /app/certs && \
    chown -R appuser:appuser /app && \
    chmod +x /app/scripts/start.sh

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