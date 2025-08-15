#!/usr/bin/env python3
"""
gRPC Server for Electricity Consumption Data

This server loads electricity consumption data from a CSV file and serves it
via gRPC with optional datetime filtering capabilities.
"""

import csv
import logging
import os
from concurrent import futures
from datetime import datetime
from typing import List, Optional

import grpc
from google.protobuf import timestamp_pb2

# Import generated protobuf classes
import consumption_pb2
import consumption_pb2_grpc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConsumptionRecord:
    """Data structure for consumption records."""
    
    def __init__(self, datetime_str: str, energy_usage: float):
        self.datetime_str = datetime_str
        self.energy_usage = energy_usage
        # Parse datetime for filtering
        try:
            self.datetime_obj = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"Invalid datetime format: {datetime_str}")
            self.datetime_obj = None


class ConsumptionServicer(consumption_pb2_grpc.ConsumptionServiceServicer):
    """gRPC service implementation for consumption data."""
    
    def __init__(self):
        self.records: List[ConsumptionRecord] = []
        self._load_csv_data()
    
    def _load_csv_data(self):
        """Load consumption data from CSV file."""
        csv_path = os.path.join(os.path.dirname(__file__), 'meterusage.csv')
        
        try:
            with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    try:
                        record = ConsumptionRecord(
                            datetime_str=row['DateTime'],
                            energy_usage=float(row['EnergyUsage'])
                        )
                        self.records.append(record)
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping invalid row: {row}, error: {e}")
                        
            logger.info(f"Loaded {len(self.records)} consumption records")
            
        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading CSV data: {e}")
            raise
    
    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """Parse ISO datetime string."""
        if not datetime_str:
            return None
            
        try:
            # Handle both with and without timezone info
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"Invalid datetime format: {datetime_str}")
            return None
    
    def _filter_records(
        self, 
        start_datetime: Optional[datetime], 
        end_datetime: Optional[datetime]
    ) -> List[ConsumptionRecord]:
        """Filter records by datetime range."""
        filtered_records = []
        
        for record in self.records:
            if record.datetime_obj is None:
                continue
                
            # Apply start datetime filter
            if start_datetime and record.datetime_obj < start_datetime:
                continue
                
            # Apply end datetime filter
            if end_datetime and record.datetime_obj > end_datetime:
                continue
                
            filtered_records.append(record)
            
        return filtered_records
    
    def GetConsumptionData(self, request, context):
        """Handle gRPC request for consumption data."""
        try:
            # Parse datetime filters
            start_datetime = self._parse_datetime(request.start_datetime)
            end_datetime = self._parse_datetime(request.end_datetime)
            
            # Validate datetime range
            if start_datetime and end_datetime and start_datetime > end_datetime:
                context.set_details('start_datetime must be before end_datetime')
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                return consumption_pb2.ConsumptionResponse()
            
            # Filter records
            filtered_records = self._filter_records(start_datetime, end_datetime)
            
            # Build response
            response = consumption_pb2.ConsumptionResponse()
            
            for record in filtered_records:
                grpc_record = consumption_pb2.ConsumptionRecord(
                    datetime=record.datetime_str,
                    energy_usage=record.energy_usage
                )
                response.records.append(grpc_record)
            
            logger.info(f"Returning {len(filtered_records)} records")
            return response
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            context.set_details(f'Internal server error: {str(e)}')
            context.set_code(grpc.StatusCode.INTERNAL)
            return consumption_pb2.ConsumptionResponse()


def serve():
    """Start the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    consumption_pb2_grpc.add_ConsumptionServiceServicer_to_server(
        ConsumptionServicer(), server
    )
    
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting gRPC server on {listen_addr}")
    server.start()
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server")
        server.stop(0)


if __name__ == '__main__':
    serve()