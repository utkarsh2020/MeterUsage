#!/usr/bin/env python3
"""
FastAPI HTTP Server

This server acts as a client to the gRPC service and exposes REST endpoints
for electricity consumption data. It also serves the static frontend.
"""

import logging
from datetime import datetime
from typing import List, Optional

import grpc
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError

# Import generated protobuf classes
import consumption_pb2
import consumption_pb2_grpc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConsumptionRecord(BaseModel):
    """Pydantic model for consumption record."""
    datetime: str
    energy_usage: float
    temperature: float


class ConsumptionResponse(BaseModel):
    """Pydantic model for API response."""
    records: List[ConsumptionRecord]
    total_count: int


# Initialize FastAPI app
app = FastAPI(
    title="Electricity Consumption API",
    description="REST API for electricity consumption data via gRPC backend",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="../frontend"), name="static")


class GRPCClient:
    """gRPC client for consumption service."""
    
    def __init__(self, server_address: str = 'localhost:50051'):
        self.server_address = server_address
        self.channel = None
        self.stub = None
        self._connect()
    
    def _connect(self):
        """Establish gRPC connection."""
        try:
            self.channel = grpc.insecure_channel(self.server_address)
            self.stub = consumption_pb2_grpc.ConsumptionServiceStub(self.channel)
            logger.info(f"Connected to gRPC server at {self.server_address}")
        except Exception as e:
            logger.error(f"Failed to connect to gRPC server: {e}")
            raise
    
    def get_consumption_data(
        self, 
        start_datetime: Optional[str] = None, 
        end_datetime: Optional[str] = None
    ) -> List[ConsumptionRecord]:
        """Fetch consumption data from gRPC service."""
        try:
            request = consumption_pb2.ConsumptionRequest(
                start_datetime=start_datetime or '',
                end_datetime=end_datetime or ''
            )
            
            response = self.stub.GetConsumptionData(request)
            
            records = []
            for record in response.records:
                records.append(ConsumptionRecord(
                    datetime=record.datetime,
                    energy_usage=record.energy_usage,
                    temperature=record.temperature
                ))
            
            return records
            
        except grpc.RpcError as e:
            logger.error(f"gRPC error: {e.details()}")
            raise HTTPException(
                status_code=500, 
                detail=f"gRPC service error: {e.details()}"
            )
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Internal server error"
            )
    
    def close(self):
        """Close gRPC connection."""
        if self.channel:
            self.channel.close()


# Global gRPC client
grpc_client = GRPCClient()


def validate_datetime(datetime_str: str) -> bool:
    """Validate ISO datetime string."""
    try:
        datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False


@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Electricity Consumption API",
        "version": "1.0.0",
        "endpoints": {
            "consumption": "/api/consumption",
            "frontend": "/static/index.html"
        }
    }


@app.get("/api/consumption", response_model=ConsumptionResponse)
async def get_consumption(
    start_datetime: Optional[str] = Query(
        None, 
        description="Start datetime in ISO 8601 format (e.g., 2024-01-01T00:00:00)"
    ),
    end_datetime: Optional[str] = Query(
        None, 
        description="End datetime in ISO 8601 format (e.g., 2024-01-02T23:59:59)"
    )
):
    """
    Get electricity consumption data with optional datetime filtering.
    
    - **start_datetime**: Optional start date filter (ISO 8601 format)
    - **end_datetime**: Optional end date filter (ISO 8601 format)
    """
    
    # Validate datetime parameters
    if start_datetime and not validate_datetime(start_datetime):
        raise HTTPException(
            status_code=400, 
            detail="Invalid start_datetime format. Use ISO 8601 format."
        )
    
    if end_datetime and not validate_datetime(end_datetime):
        raise HTTPException(
            status_code=400, 
            detail="Invalid end_datetime format. Use ISO 8601 format."
        )
    
    # Validate datetime range
    if start_datetime and end_datetime:
        try:
            start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
            if start_dt > end_dt:
                raise HTTPException(
                    status_code=400, 
                    detail="start_datetime must be before end_datetime"
                )
        except ValueError:
            pass  # Already validated above
    
    try:
        # Fetch data from gRPC service
        records = grpc_client.get_consumption_data(start_datetime, end_datetime)
        
        return ConsumptionResponse(
            records=records,
            total_count=len(records)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "consumption-api"}


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    grpc_client.close()


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )