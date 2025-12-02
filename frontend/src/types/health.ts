/**
 * Health check response types
 */

export interface ComponentHealth {
  status: "healthy" | "unhealthy" | "unavailable" | "degraded";
  message?: string;
  error?: string;
}

export interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp?: string;
  
  // CPU Information
  cpu_percent?: number;
  cpu_count?: number;
  cpu_frequency_mhz?: number;
  cpu_frequency_max_mhz?: number;
  
  // Memory Information
  memory_total_gb?: number;
  memory_available_gb?: number;
  memory_used_gb?: number;
  memory_percent?: number;
  
  // Swap Information
  swap_total_gb?: number;
  swap_used_gb?: number;
  swap_percent?: number;
  
  // Disk Information
  disk_total_gb?: number;
  disk_used_gb?: number;
  disk_free_gb?: number;
  disk_percent?: number;
  
  // Network Information
  network_bytes_sent?: number;
  network_bytes_recv?: number;
  network_packets_sent?: number;
  network_packets_recv?: number;
  
  // Process Information
  process_memory_mb?: number;
  process_cpu_percent?: number;
  process_num_threads?: number;
  
  // Component Health Status
  database_status?: string;
  redis_status?: string;
  embedding_service_status?: string;
  components?: Record<string, ComponentHealth>;
}

export interface PerformanceMetrics {
  total_requests: number;
  total_errors: number;
  average_response_time_seconds: number;
  status_codes: Record<string, number>;
  top_endpoints: Array<{
    endpoint: string;
    count: number;
    avg_time_seconds: number;
    total_time_seconds: number;
  }>;
}

