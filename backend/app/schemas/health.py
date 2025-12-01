"""Health check schema."""
from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    """Health check response with all system resource information."""
    status: str
    timestamp: Optional[str] = None
    
    # CPU Information
    cpu_percent: Optional[float] = None
    cpu_count: Optional[int] = None
    cpu_frequency_mhz: Optional[float] = None
    cpu_frequency_max_mhz: Optional[float] = None
    
    # Memory Information
    memory_total_gb: Optional[float] = None
    memory_available_gb: Optional[float] = None
    memory_used_gb: Optional[float] = None
    memory_percent: Optional[float] = None
    
    # Swap Information
    swap_total_gb: Optional[float] = None
    swap_used_gb: Optional[float] = None
    swap_percent: Optional[float] = None
    
    # Disk Information
    disk_total_gb: Optional[float] = None
    disk_used_gb: Optional[float] = None
    disk_free_gb: Optional[float] = None
    disk_percent: Optional[float] = None
    
    # Network Information
    network_bytes_sent: Optional[int] = None
    network_bytes_recv: Optional[int] = None
    network_packets_sent: Optional[int] = None
    network_packets_recv: Optional[int] = None
    
    # Process Information
    process_memory_mb: Optional[float] = None
    process_cpu_percent: Optional[float] = None
    process_num_threads: Optional[int] = None
