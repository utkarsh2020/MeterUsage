# Electricity Consumption Microservice

A gRPC-based microservice system for serving time-based electricity consumption data with an HTTP API and web frontend.

## 🏗️ Architecture

```
┌─────────────────┐    HTTP     ┌─────────────────┐    gRPC     ┌─────────────────┐
│   HTML5         │ ◄──────────► │   FastAPI       │ ◄──────────► │   gRPC Server   │
│   Frontend      │              │   HTTP Server   │              │   (Python)      │
│                 │              │                 │              │                 │
└─────────────────┘              └─────────────────┘              └─────────────────┘
                                                                           │
                                                                           ▼
                                                                  ┌─────────────────┐
                                                                  │   CSV Data      │
                                                                  │   meterusage.csv│
                                                                  └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)

### Local Development

1. **Clone and setup the project:**
   ```bash
   git clone [<repository>](https://github.com/utkarsh2020/MeterUsage.git)
   cd electricity-consumption-microservice
   ```

2. **Create and activate a virtual environment (recommended):**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
   Note: `.venv` is git-ignored and can be safely deleted and regenerated anytime.

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Generate gRPC code:**
   ```bash
   cd grpc_server
   python -m grpc_tools.protoc --python_out=. --grpc_python_out=. -I. proto/consumption.proto
   cd ..
   ```

5. **Start the gRPC server:**
   ```bash
   cd grpc_server
   python server.py
   ```
   The gRPC server will start on port `50051`.

6. **Start the HTTP server** (in a new terminal):
   ```bash
   cd http_server
   python app.py
   ```
   The HTTP server will start on port `8000`.

7. **Access the web interface:**
   Open your browser and navigate to: `http://localhost:8000/static/index.html`

### Docker Deployment

1. **Build the Docker image:**
   ```bash
   docker build -t consumption-microservice .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 -p 50051:50051 consumption-microservice
   ```

3. **Access the application:**
   - Web Interface: `http://localhost:8000/static/index.html`
   - API Documentation: `http://localhost:8000/docs`

## 📡 API Endpoints

### REST API (HTTP Server - Port 8000)

#### GET `/api/consumption`
Get electricity consumption data with optional datetime filtering.

**Query Parameters:**
- `start_datetime` (optional): Start date in ISO 8601 format (e.g., `2024-01-01T00:00:00`)
- `end_datetime` (optional): End date in ISO 8601 format (e.g., `2024-01-02T23:59:59`)

**Example Requests:**
```bash
# Get all data
curl "http://localhost:8000/api/consumption"

# Get data for a specific date range
curl "http://localhost:8000/api/consumption?start_datetime=2024-01-01T00:00:00&end_datetime=2024-01-01T12:00:00"

# Get data from a specific start time
curl "http://localhost:8000/api/consumption?start_datetime=2024-01-01T06:00:00"
```

**Response Format:**
```json
{
  "records": [
    {
      "datetime": "2024-01-01T00:00:00",
      "energy_usage": 12.5
    }
  ],
  "total_count": 1
}
```

#### GET `/health`
Health check endpoint.

#### GET `/docs`
Interactive API documentation (Swagger UI).

### gRPC API (gRPC Server - Port 50051)

#### GetConsumptionData
Get consumption data via gRPC.

**Message Types:**
```protobuf
message ConsumptionRequest {
  string start_datetime = 1; // Optional, ISO 8601 format
  string end_datetime = 2;   // Optional, ISO 8601 format
}

message ConsumptionResponse {
  repeated ConsumptionRecord records = 1;
}

message ConsumptionRecord {
  string datetime = 1;
  double energy_usage = 2;
}
```

**Example gRPC Client (Python):**
```python
import grpc
import consumption_pb2
import consumption_pb2_grpc

# Connect to gRPC server
channel = grpc.insecure_channel('localhost:50051')
stub = consumption_pb2_grpc.ConsumptionServiceStub(channel)

# Make request
request = consumption_pb2.ConsumptionRequest(
    start_datetime='2024-01-01T00:00:00',
    end_datetime='2024-01-01T12:00:00'
)

response = stub.GetConsumptionData(request)

# Process response
for record in response.records:
    print(f"DateTime: {record.datetime}")
    print(f"Energy Usage: {record.energy_usage} kWh")
```

## 📊 Data Format

The system expects CSV data with the following columns:

| Column       | Type    | Description                          |
|-------------|---------|--------------------------------------|
| DateTime    | string  | ISO 8601 formatted datetime string  |
| EnergyUsage | float   | Energy consumption in kWh            |

**Example CSV:**
```csv
DateTime,EnergyUsage
2024-01-01T00:00:00,12.5
2024-01-01T01:00:00,11.2
2024-01-01T02:00:00,10.8
```

## 🌐 Web Interface Features

The HTML5 frontend provides:

- **📊 Interactive Data Table**: View consumption records in a sortable, responsive table
- **🔍 Date Range Filtering**: Filter data by start and end datetime
- **📈 Real-time Statistics**: Total energy consumption, average usage, and record counts
- **📱 Responsive Design**: Works on desktop, tablet, and mobile devices
- **⚡ Fast Loading**: Efficient data fetching and rendering
- **🎨 Modern UI**: Clean, professional design with hover effects and animations

## 🐳 Docker Configuration

The included `Dockerfile` creates a multi-service container that runs both the gRPC server and HTTP server using a process manager.

**Container Features:**
- Python 3.11 slim base image
- Multi-stage build for optimized image size
- Health checks for both services
- Proper signal handling and graceful shutdown
- Environment variable configuration

**Environment Variables:**
- `GRPC_PORT`: gRPC server port (default: 50051)
- `HTTP_PORT`: HTTP server port (default: 8000)
- `LOG_LEVEL`: Logging level (default: INFO)

## 🔧 Development

### Project Structure
```
project/
├── grpc_server/
│   ├── server.py              # gRPC server implementation
│   ├── meterusage.csv         # Sample consumption data
│   ├── proto/
│   │   └── consumption.proto  # Protocol buffer definition
│   ├── consumption_pb2.py     # Generated protobuf classes
│   └── consumption_pb2_grpc.py # Generated gRPC stubs
├── http_server/
│   └── app.py                 # FastAPI HTTP server
├── frontend/
│   └── index.html            # HTML5 web interface
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container configuration
└── README.md               # This file
```

### Regenerating gRPC Code

When you modify the `.proto` file, regenerate the Python bindings:

```bash
cd grpc_server
python -m grpc_tools.protoc --python_out=. --grpc_python_out=. -I. proto/consumption.proto
```

### Adding New Data

To use your own consumption data:

1. Replace `grpc_server/meterusage.csv` with your data file
2. Ensure the CSV has the required columns: `DateTime`, `EnergyUsage`, `Temperature`
3. Restart the gRPC server to load the new data

### Testing

Test the gRPC service directly:

```python
# test_grpc.py
import grpc
import consumption_pb2
import consumption_pb2_grpc

channel = grpc.insecure_channel('localhost:50051')
stub = consumption_pb2_grpc.ConsumptionServiceStub(channel)

# Test without filters
request = consumption_pb2.ConsumptionRequest()
response = stub.GetConsumptionData(request)
print(f"Total records: {len(response.records)}")

# Test with date filter
request = consumption_pb2.ConsumptionRequest(
    start_datetime='2024-01-01T00:00:00'
)
response = stub.GetConsumptionData(request)
print(f"Filtered records: {len(response.records)}")
```

## 🚨 Troubleshooting

### Common Issues

1. **gRPC Connection Refused**
   - Ensure the gRPC server is running on port 50051
   - Check if the port is available: `netstat -an | grep 50051`

2. **HTTP Server Can't Connect to gRPC**
   - Verify gRPC server is started before HTTP server
   - Check network connectivity between services

3. **CSV File Not Found**
   - Ensure `meterusage.csv` exists in `grpc_server/` directory
   - Check file permissions and format

4. **Frontend Not Loading**
   - Verify HTTP server is running on port 8000
   - Check browser console for errors
   - Ensure CORS is properly configured

### Logs and Debugging

Enable debug logging:

```bash
# For gRPC server
export PYTHONPATH=$PYTHONPATH:.
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"

# For HTTP server
uvicorn app:app --host 0.0.0.0 --port 8000 --log-level debug
```

## 📈 Performance Notes

- The gRPC server loads all CSV data into memory at startup for fast query performance
- For large datasets, consider implementing pagination or database storage
- The HTTP server maintains a persistent gRPC connection for efficient communication
- Frontend uses efficient DOM manipulation and avoids unnecessary re-renders

## 🔒 Security Considerations

- Both servers run on insecure channels for development
- For production, implement TLS/SSL encryption
- Add authentication and authorization as needed
- Validate and sanitize all input parameters
- Consider rate limiting for production deployments

## 📄 License

This project is provided as-is for educational and development purposes.
