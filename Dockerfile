FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY grpc_server/ ./grpc_server/
COPY http_server/ ./http_server/
COPY frontend/ ./frontend/

# Generate gRPC code
WORKDIR /app/grpc_server
RUN python -m grpc_tools.protoc --python_out=. --grpc_python_out=. -I. proto/consumption.proto

# Copy generated gRPC files to http_server directory
RUN cp consumption_pb2.py consumption_pb2_grpc.py ../http_server/

# Create startup script
WORKDIR /app
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Function to handle shutdown\n\
cleanup() {\n\
    echo "Shutting down services..."\n\
    kill $GRPC_PID $HTTP_PID 2>/dev/null || true\n\
    wait\n\
    exit 0\n\
}\n\
\n\
# Set trap for cleanup\n\
trap cleanup SIGTERM SIGINT\n\
\n\
# Start gRPC server in background\n\
echo "Starting gRPC server..."\n\
cd /app/grpc_server\n\
python server.py &\n\
GRPC_PID=$!\n\
\n\
# Wait a bit for gRPC server to start\n\
sleep 3\n\
\n\
# Start HTTP server in background\n\
echo "Starting HTTP server..."\n\
cd /app/http_server\n\
python app.py &\n\
HTTP_PID=$!\n\
\n\
echo "Both servers started successfully"\n\
echo "gRPC server PID: $GRPC_PID"\n\
echo "HTTP server PID: $HTTP_PID"\n\
echo "Services are ready!"\n\
\n\
# Wait for both processes\n\
wait' > /app/start.sh

RUN chmod +x /app/start.sh

# Expose ports
EXPOSE 50051 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start services
CMD ["/app/start.sh"]