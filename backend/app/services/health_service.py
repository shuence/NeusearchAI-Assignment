"""Health service for system monitoring."""
from typing import Dict, Any, Optional
import sys
import platform
import os
import time
import re
import subprocess
import psutil
from datetime import datetime
from sqlalchemy import text
from app.constants import (
    HEALTH_STATUS_HEALTHY,
    HEALTH_STATUS_DEGRADED,
    MEMORY_THRESHOLD_PERCENT,
    DISK_THRESHOLD_PERCENT,
)
from app.schemas.health import HealthResponse
from app.config.database import engine
from app.config.redis import get_redis_client
from app.utils.logger import get_logger

logger = get_logger("health_service")


class HealthService:
    """Service for health check operations."""
    
    def __init__(self):
        """Initialize health service with start time tracking."""
        self._start_time = time.time()
        self._last_cpu_check = None
    
    def _get_cpu_frequency(self) -> tuple[Optional[float], Optional[float]]:
        """Get CPU frequency using multiple methods for cross-platform support."""
        current_freq = None
        max_freq = None
        
        # Method 1: Try psutil (works on Linux, sometimes on macOS)
        try:
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                if hasattr(cpu_freq, 'current') and cpu_freq.current:
                    current_freq = round(cpu_freq.current, 2)
                if hasattr(cpu_freq, 'max') and cpu_freq.max:
                    max_freq = round(cpu_freq.max, 2)
                if current_freq or max_freq:
                    return current_freq, max_freq
        except (OSError, AttributeError, RuntimeError):
            pass
        
        # Method 2: macOS - try sysctl
        if platform.system() == "Darwin":
            # Try various sysctl keys for CPU frequency
            sysctl_keys = [
                "hw.cpufrequency",
                "hw.cpufrequency_max",
                "hw.cpufrequency_min",
            ]
            
            for key in sysctl_keys:
                try:
                    result = subprocess.run(
                        ["sysctl", "-n", key],
                        capture_output=True,
                        text=True,
                        timeout=1
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        freq_hz = int(result.stdout.strip())
                        if freq_hz > 0:
                            freq_mhz = round(freq_hz / 1_000_000, 2)  # Convert Hz to MHz
                            if current_freq is None:
                                current_freq = freq_mhz
                            if max_freq is None or freq_mhz > max_freq:
                                max_freq = freq_mhz
                except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
                    continue
            
            # If we got any frequency, return it
            if current_freq or max_freq:
                if current_freq is None:
                    current_freq = max_freq
                if max_freq is None:
                    max_freq = current_freq
                return current_freq, max_freq
            
            # Try to get from system_profiler (slower but more reliable on some Macs)
            try:
                result = subprocess.run(
                    ["system_profiler", "SPHardwareDataType"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    # Look for processor speed in output (e.g., "2.4 GHz")
                    match = re.search(r'Processor Speed:\s*(\d+\.?\d*)\s*GHz', result.stdout, re.IGNORECASE)
                    if match:
                        freq_ghz = float(match.group(1))
                        freq_mhz = round(freq_ghz * 1000, 2)
                        return freq_mhz, freq_mhz
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        # Method 3: Linux - try /proc/cpuinfo
        elif platform.system() == "Linux":
            try:
                frequencies = []
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "cpu MHz" in line.lower():
                            try:
                                freq_mhz = float(line.split(":")[1].strip())
                                if freq_mhz > 0:
                                    frequencies.append(freq_mhz)
                            except (ValueError, IndexError):
                                continue
                        elif "model name" in line.lower() and "ghz" in line.lower() and max_freq is None:
                            # Try to extract frequency from model name (e.g., "2.4 GHz")
                            match = re.search(r'(\d+\.?\d*)\s*ghz', line.lower())
                            if match:
                                freq_ghz = float(match.group(1))
                                max_freq = round(freq_ghz * 1000, 2)  # Convert GHz to MHz
                
                if frequencies:
                    # Use average of all cores for current frequency, max for max frequency
                    current_freq = round(sum(frequencies) / len(frequencies), 2)
                    if max_freq is None:
                        max_freq = round(max(frequencies), 2)
                    return current_freq, max_freq
            except (FileNotFoundError, ValueError, IOError):
                pass
        
        return current_freq, max_freq
    
    def get_health_response(self) -> HealthResponse:
        """Get complete health check response with all system information."""
        # CPU information
        cpu_percent = None
        cpu_count = None
        cpu_frequency_mhz = None
        cpu_frequency_max_mhz = None
        try:
            # Get CPU count first
            cpu_count = psutil.cpu_count()
            
            # For CPU percentage, psutil needs a baseline measurement
            # Use interval=None if we've called before, otherwise use a small interval
            if self._last_cpu_check is None:
                # First call - establish baseline with a small interval
                # This is acceptable for health checks (0.2s delay)
                psutil.cpu_percent(interval=None)  # Establish baseline
                time.sleep(0.1)  # Small delay for measurement
                cpu_percent = psutil.cpu_percent(interval=None)
                self._last_cpu_check = time.time()
            else:
                # Subsequent calls use interval=None which measures since last call
                # This is faster and more accurate for frequent polling
                elapsed = time.time() - self._last_cpu_check
                if elapsed > 0.1:
                    cpu_percent = psutil.cpu_percent(interval=None)
                    self._last_cpu_check = time.time()
                else:
                    # If called too soon, use a small interval
                    cpu_percent = psutil.cpu_percent(interval=0.2)
                    self._last_cpu_check = time.time()
            
            # Ensure we have a valid CPU percentage (not None)
            if cpu_percent is None:
                # Fallback: use a small interval measurement
                cpu_percent = psutil.cpu_percent(interval=0.2)
                self._last_cpu_check = time.time()
            
            # Get CPU frequency using cross-platform methods
            cpu_frequency_mhz, cpu_frequency_max_mhz = self._get_cpu_frequency()
            
        except Exception as e:
            logger.debug(f"Error getting CPU information: {e}")
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
        
        # Check component health
        database_status, redis_status, embedding_status, components = self._check_components()
        
        # Determine health status
        status = HEALTH_STATUS_HEALTHY
        if memory_percent and memory_percent > MEMORY_THRESHOLD_PERCENT:
            status = HEALTH_STATUS_DEGRADED
        if disk_percent and disk_percent > DISK_THRESHOLD_PERCENT:
            status = HEALTH_STATUS_DEGRADED
        if database_status != "healthy" or redis_status == "unhealthy":
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
            database_status=database_status,
            redis_status=redis_status,
            embedding_service_status=embedding_status,
            components=components,
        )
    
    def _check_components(self) -> tuple[str, str, str, dict]:
        """Check health of database, Redis, and embedding service."""
        database_status = "unknown"
        redis_status = "unknown"
        embedding_status = "unknown"
        components = {}
        
        # Check database
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            database_status = "healthy"
            components["database"] = {"status": "healthy", "message": "Connected"}
        except Exception as e:
            database_status = "unhealthy"
            components["database"] = {"status": "unhealthy", "error": str(e)}
            logger.warning(f"Database health check failed: {e}")
        
        # Check Redis
        try:
            redis_client = get_redis_client()
            redis_client.ping()
            redis_status = "healthy"
            components["redis"] = {"status": "healthy", "message": "Connected"}
        except Exception as e:
            redis_status = "unavailable"  # Redis is optional, so unavailable not unhealthy
            components["redis"] = {"status": "unavailable", "message": "Redis not available (optional)"}
            logger.debug(f"Redis health check: {e}")
        
        # Check embedding service
        try:
            from app.rag import get_embedding_service
            from app.config.settings import settings
            
            if settings.GEMINI_API_KEY:
                embedding_service = get_embedding_service()
                # Just check if service is initialized (doesn't make API call)
                if embedding_service:
                    embedding_status = "available"
                    components["embedding_service"] = {"status": "available", "message": "Service initialized"}
                else:
                    embedding_status = "unavailable"
                    components["embedding_service"] = {"status": "unavailable", "message": "Service not initialized"}
            else:
                embedding_status = "unavailable"
                components["embedding_service"] = {"status": "unavailable", "message": "API key not configured"}
        except Exception as e:
            embedding_status = "unavailable"
            components["embedding_service"] = {"status": "unavailable", "error": str(e)}
            logger.debug(f"Embedding service health check: {e}")
        
        return database_status, redis_status, embedding_status, components
