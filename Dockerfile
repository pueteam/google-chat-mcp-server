FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY stateless_streamable_server.py .
COPY credentials/ ./credentials/

# Set environment variables
ENV PYTHONPATH=/app
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/google-chat-mcp-server-key.json

# Expose port
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f -H "Accept: application/json, text/event-stream" \
             -H "Content-Type: application/json" \
             -X POST http://localhost:8004/mcp \
             -d '{"jsonrpc":"2.0","id":"health","method":"ping","params":{}}' \
    || exit 1

# Run the MCP Streamable HTTP server
CMD ["python", "stateless_streamable_server.py", "--port", "8004", "--response", "json"]