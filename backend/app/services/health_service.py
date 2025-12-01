"""Health service for system monitoring."""
from typing import Dict, Any
import sys
import platform
import os
import time
import psutil
from datetime import datetime
from app.constants import (
    HEALTH_STATUS_HEALTHY,
    HEALTH_STATUS_DEGRADED,
    MEMORY_THRESHOLD_PERCENT,
    DISK_THRESHOLD_PERCENT,
)
from app.schemas.health import HealthResponse


class HealthService:
    """Service for health check operations."""
    
    def __init__(self):
        """Initialize health service with start time tracking."""
        self._start_time = time.time()
    
    def get_health_response(self) -> HealthResponse:
        """Get complete health check response with all system information."""
        # CPU information
        cpu_percent = None
        cpu_count = None
        cpu_frequency_mhz = None
        cpu_frequency_max_mhz = None
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            try:
                cpu_freq = psutil.cpu_freq()
                if cpu_freq:
                    cpu_frequency_mhz = cpu_freq.current
                    cpu_frequency_max_mhz = cpu_freq.max
            except (OSError, AttributeError):
                pass
        except Exception:
            pass
        
        # Memory information
        memory_total_gb = None
        memory_available_gb = None
        memory_used_gb = None
        memory_percent = None
        try:
            memory = psutil.virtual_memory()
            memory_total_gb = round(memory.total / (1024**3), 2)
            memory_available_gb = round(memory.available / (1024**3), 2)
            memory_used_gb = round(memory.used / (1024**3), 2)
            memory_percent = memory.percent
        except Exception:
            pass
        
        # Swap information
        swap_total_gb = None
        swap_used_gb = None
        swap_percent = None
        try:
            swap = psutil.swap_memory()
            swap_total_gb = round(swap.total / (1024**3), 2)
            swap_used_gb = round(swap.used / (1024**3), 2)
            swap_percent = swap.percent
        except Exception:
            pass
        
        # Disk information
        disk_total_gb = None
        disk_used_gb = None
        disk_free_gb = None
        disk_percent = None
        try:
            disk = psutil.disk_usage('/')
            disk_total_gb = round(disk.total / (1024**3), 2)
            disk_used_gb = round(disk.used / (1024**3), 2)
            disk_free_gb = round(disk.free / (1024**3), 2)
            disk_percent = round((disk.used / disk.total) * 100, 2)
        except Exception:
            pass
        
        # Network information
        network_bytes_sent = None
        network_bytes_recv = None
        network_packets_sent = None
        network_packets_recv = None
        try:
            network = psutil.net_io_counters()
            network_bytes_sent = network.bytes_sent
            network_bytes_recv = network.bytes_recv
            network_packets_sent = network.packets_sent
            network_packets_recv = network.packets_recv
        except Exception:
            pass
        
        # Process information
        process_memory_mb = None
        process_cpu_percent = None
        process_num_threads = None
        try:
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info()
            process_memory_mb = round(process_memory.rss / (1024**2), 2)
            process_cpu_percent = process.cpu_percent(interval=0.1)
            process_num_threads = process.num_threads()
        except Exception:
            pass
        
        # Determine health status
        status = HEALTH_STATUS_HEALTHY
        if memory_percent and memory_percent > MEMORY_THRESHOLD_PERCENT:
            status = HEALTH_STATUS_DEGRADED
        if disk_percent and disk_percent > DISK_THRESHOLD_PERCENT:
            status = HEALTH_STATUS_DEGRADED
        
        return HealthResponse(
            status=status,
            timestamp=datetime.utcnow().isoformat() + "Z",
            cpu_percent=cpu_percent,
            cpu_count=cpu_count,
            cpu_frequency_mhz=cpu_frequency_mhz,
            cpu_frequency_max_mhz=cpu_frequency_max_mhz,
            memory_total_gb=memory_total_gb,
            memory_available_gb=memory_available_gb,
            memory_used_gb=memory_used_gb,
            memory_percent=memory_percent,
            swap_total_gb=swap_total_gb,
            swap_used_gb=swap_used_gb,
            swap_percent=swap_percent,
            disk_total_gb=disk_total_gb,
            disk_used_gb=disk_used_gb,
            disk_free_gb=disk_free_gb,
            disk_percent=disk_percent,
            network_bytes_sent=network_bytes_sent,
            network_bytes_recv=network_bytes_recv,
            network_packets_sent=network_packets_sent,
            network_packets_recv=network_packets_recv,
            process_memory_mb=process_memory_mb,
            process_cpu_percent=process_cpu_percent,
            process_num_threads=process_num_threads,
        )
