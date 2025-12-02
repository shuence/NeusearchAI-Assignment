"use client";

import { useState, useEffect } from "react";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getHealth, getMetrics, validateAccessCode } from "@/lib/api/health";
import type { HealthResponse, PerformanceMetrics } from "@/types/health";
import { RefreshCw, CheckCircle2, XCircle, AlertTriangle, Activity, Database, Server, Cpu, HardDrive, Network, MemoryStick, Clock, Lock } from "lucide-react";
import { toast } from "sonner";

const STATUS_ACCESS_KEY = "status_access_granted";

export default function StatusPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [accessCode, setAccessCode] = useState("");
  const [isValidating, setIsValidating] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // Check if user is already authenticated
  useEffect(() => {
    const accessGranted = sessionStorage.getItem(STATUS_ACCESS_KEY);
    if (accessGranted === "true") {
      setIsAuthenticated(true);
    }
  }, []);

  const handleCodeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accessCode.trim()) {
      toast.error("Please enter an access code");
      return;
    }

    setIsValidating(true);
    try {
      const response = await validateAccessCode(accessCode.trim());
      if (response.access_granted) {
        setIsAuthenticated(true);
        sessionStorage.setItem(STATUS_ACCESS_KEY, "true");
        toast.success("Access granted");
      } else {
        toast.error("Invalid access code");
        setAccessCode("");
      }
    } catch (error) {
      toast.error("Invalid access code", {
        description: error instanceof Error ? error.message : "Please check your code and try again.",
      });
      setAccessCode("");
    } finally {
      setIsValidating(false);
    }
  };

  const fetchStatus = async () => {
    try {
      setIsLoading(true);
      const [healthData, metricsData] = await Promise.all([
        getHealth(),
        getMetrics(),
      ]);
      setHealth(healthData);
      setMetrics(metricsData);
      setLastUpdate(new Date());
    } catch (error) {
      console.error("Error fetching status:", error);
      toast.error("Failed to fetch status", {
        description: error instanceof Error ? error.message : "Please check if the backend is running.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchStatus();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchStatus();
    }, 10000); // Refresh every 10 seconds

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const getStatusColor = (status?: string) => {
    switch (status?.toLowerCase()) {
      case "healthy":
      case "available":
        return "bg-green-500";
      case "degraded":
        return "bg-yellow-500";
      case "unhealthy":
      case "unavailable":
        return "bg-red-500";
      default:
        return "bg-gray-500";
    }
  };

  const getStatusBadgeVariant = (status?: string): "default" | "destructive" | "outline" => {
    switch (status?.toLowerCase()) {
      case "healthy":
      case "available":
        return "default";
      case "degraded":
        return "outline";
      case "unhealthy":
      case "unavailable":
        return "destructive";
      default:
        return "outline";
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status?.toLowerCase()) {
      case "healthy":
      case "available":
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case "degraded":
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case "unhealthy":
      case "unavailable":
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Activity className="h-5 w-5 text-gray-500" />;
    }
  };

  const formatBytes = (bytes?: number): string => {
    if (!bytes) return "N/A";
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    if (bytes === 0) return "0 B";
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  const formatNumber = (num?: number, decimals = 2): string => {
    if (num === undefined || num === null) return "N/A";
    return num.toFixed(decimals);
  };

  // Show access code form if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="h-screen w-screen bg-background flex flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-md">
          <Card className="border-2">
            <CardHeader className="text-center space-y-4 pb-6">
              <div className="flex justify-center">
                <div className="rounded-full bg-muted p-4">
                  <Lock className="h-8 w-8 text-muted-foreground" />
                </div>
              </div>
              <div className="space-y-2">
                <CardTitle className="text-3xl font-bold">Protected Status Page</CardTitle>
                <CardDescription className="text-base">
                  Please enter the access code to view system status
                </CardDescription>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <form onSubmit={handleCodeSubmit} className="space-y-6">
                <div className="space-y-2">
                    <Label htmlFor="access-code" className="text-base font-medium">
                      Access Code
                    </Label>
                    <Input
                    id="access-code"
                    type="text"
                    placeholder="Enter access code"
                    value={accessCode}
                    onChange={(e) => setAccessCode(e.target.value)}
                    disabled={isValidating}
                    autoFocus
                    className="text-center text-lg h-12 focus-visible:ring-0 focus-visible:ring-offset-0"
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !isValidating && accessCode.trim()) {
                        handleCodeSubmit(e as any);
                      }
                    }}
                  />
                </div>
                <Button
                  type="submit"
                  className="w-full h-12 text-base font-semibold"
                  disabled={isValidating || !accessCode.trim()}
                  size="lg"
                >
                  {isValidating ? (
                    <>
                      <RefreshCw className="h-5 w-5 mr-2 animate-spin" />
                      Validating...
                    </>
                  ) : (
                    <>
                      <Lock className="h-5 w-5 mr-2" />
                      Access Status Page
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />
      
      <main className="container mx-auto px-4 py-8 flex-1 w-full max-w-7xl">
        <div className="mb-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold mb-2">System Status</h1>
            <p className="text-muted-foreground">
              Real-time health monitoring and performance metrics
            </p>
          </div>
          <div className="flex items-center gap-4 flex-wrap">
            <Button
              variant="outline"
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={autoRefresh ? "bg-primary/10" : ""}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? "animate-spin" : ""}`} />
              Auto-refresh {autoRefresh ? "ON" : "OFF"}
            </Button>
            <Button
              variant="outline"
              onClick={fetchStatus}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>

        {lastUpdate && (
          <div className="mb-6 text-sm text-muted-foreground flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Last updated: {lastUpdate.toLocaleTimeString()}
          </div>
        )}

        {isLoading && !health ? (
          <div className="text-center py-12">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-muted-foreground" />
            <p className="text-muted-foreground">Loading status...</p>
          </div>
        ) : (
          <>
            {/* Overall Status */}
            <Card className="mb-6">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(health?.status)}
                    <div>
                      <CardTitle>Overall System Status</CardTitle>
                      <CardDescription>
                        {health?.timestamp
                          ? `Last checked: ${new Date(health.timestamp).toLocaleString()}`
                          : "System health overview"}
                      </CardDescription>
                    </div>
                  </div>
                  <Badge variant={getStatusBadgeVariant(health?.status)} className="text-lg px-4 py-2">
                    {health?.status?.toUpperCase() || "UNKNOWN"}
                  </Badge>
                </div>
              </CardHeader>
            </Card>

            {/* Component Health */}
            <div className="mb-6">
              <h2 className="text-2xl font-semibold mb-4">Component Health</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Database */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Database className="h-5 w-5" />
                        <CardTitle className="text-lg">Database</CardTitle>
                      </div>
                      {getStatusIcon(health?.database_status)}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <Badge variant={getStatusBadgeVariant(health?.database_status)} className="mb-2">
                      {health?.database_status?.toUpperCase() || "UNKNOWN"}
                    </Badge>
                    {health?.components?.database && (
                      <p className="text-sm text-muted-foreground mt-2">
                        {health.components.database.message || health.components.database.error || "No details available"}
                      </p>
                    )}
                  </CardContent>
                </Card>

                {/* Redis */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Server className="h-5 w-5" />
                        <CardTitle className="text-lg">Redis</CardTitle>
                      </div>
                      {getStatusIcon(health?.redis_status)}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <Badge variant={getStatusBadgeVariant(health?.redis_status)} className="mb-2">
                      {health?.redis_status?.toUpperCase() || "UNKNOWN"}
                    </Badge>
                    {health?.components?.redis && (
                      <p className="text-sm text-muted-foreground mt-2">
                        {health.components.redis.message || health.components.redis.error || "No details available"}
                      </p>
                    )}
                  </CardContent>
                </Card>

                {/* Embedding Service */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Activity className="h-5 w-5" />
                        <CardTitle className="text-lg">Embedding Service</CardTitle>
                      </div>
                      {getStatusIcon(health?.embedding_service_status)}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <Badge variant={getStatusBadgeVariant(health?.embedding_service_status)} className="mb-2">
                      {health?.embedding_service_status?.toUpperCase() || "UNKNOWN"}
                    </Badge>
                    {health?.components?.embedding_service && (
                      <p className="text-sm text-muted-foreground mt-2">
                        {health.components.embedding_service.message || health.components.embedding_service.error || "No details available"}
                      </p>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>

            {/* System Resources */}
            <div className="mb-6">
              <h2 className="text-2xl font-semibold mb-4">System Resources</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* CPU */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <Cpu className="h-5 w-5" />
                      <CardTitle className="text-lg">CPU</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Usage</span>
                        <span className="text-sm font-semibold">{formatNumber(health?.cpu_percent)}%</span>
                      </div>
                      <div className="w-full bg-secondary rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${getStatusColor(
                            health?.cpu_percent && health.cpu_percent > 80 ? "degraded" : "healthy"
                          )}`}
                          style={{ width: `${Math.min(health?.cpu_percent || 0, 100)}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>Cores: {health?.cpu_count || "N/A"}</span>
                        <span>{health?.cpu_frequency_mhz ? `${formatNumber(health.cpu_frequency_mhz)} MHz` : "N/A"}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Memory */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <MemoryStick className="h-5 w-5" />
                      <CardTitle className="text-lg">Memory</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Usage</span>
                        <span className="text-sm font-semibold">{formatNumber(health?.memory_percent)}%</span>
                      </div>
                      <div className="w-full bg-secondary rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${getStatusColor(
                            health?.memory_percent && health.memory_percent > 80 ? "degraded" : health?.status
                          )}`}
                          style={{ width: `${Math.min(health?.memory_percent || 0, 100)}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>{formatNumber(health?.memory_used_gb)} GB</span>
                        <span>/{formatNumber(health?.memory_total_gb)} GB</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Disk */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <HardDrive className="h-5 w-5" />
                      <CardTitle className="text-lg">Disk</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Usage</span>
                        <span className="text-sm font-semibold">{formatNumber(health?.disk_percent)}%</span>
                      </div>
                      <div className="w-full bg-secondary rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${getStatusColor(health?.status)}`}
                          style={{ width: `${Math.min(health?.disk_percent || 0, 100)}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>{formatNumber(health?.disk_used_gb)} GB</span>
                        <span>/{formatNumber(health?.disk_total_gb)} GB</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Network */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <Network className="h-5 w-5" />
                      <CardTitle className="text-lg">Network</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Sent</span>
                        <span className="font-semibold">{formatBytes(health?.network_bytes_sent)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Received</span>
                        <span className="font-semibold">{formatBytes(health?.network_bytes_recv)}</span>
                      </div>
                      <div className="flex justify-between text-xs text-muted-foreground pt-2 border-t">
                        <span>Packets Sent: {health?.network_packets_sent?.toLocaleString() || "N/A"}</span>
                      </div>
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>Packets Recv: {health?.network_packets_recv?.toLocaleString() || "N/A"}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>

            {/* Process Information */}
            {health?.process_memory_mb && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Process Information</CardTitle>
                  <CardDescription>Application process metrics</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Memory Usage</p>
                      <p className="text-lg font-semibold">{formatNumber(health.process_memory_mb)} MB</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">CPU Usage</p>
                      <p className="text-lg font-semibold">{formatNumber(health.process_cpu_percent)}%</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Threads</p>
                      <p className="text-lg font-semibold">{health.process_num_threads || "N/A"}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Performance Metrics */}
            {metrics && (
              <Card>
                <CardHeader>
                  <CardTitle>Performance Metrics</CardTitle>
                  <CardDescription>Request statistics and endpoint performance</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Total Requests</p>
                      <p className="text-2xl font-bold">{metrics.total_requests.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Total Errors</p>
                      <p className="text-2xl font-bold text-red-500">{metrics.total_errors.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Avg Response Time</p>
                      <p className="text-2xl font-bold">{formatNumber(metrics.average_response_time_seconds * 1000)} ms</p>
                    </div>
                  </div>

                  {metrics.status_codes && Object.keys(metrics.status_codes).length > 0 && (
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold mb-3">Status Codes</h3>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(metrics.status_codes).map(([code, count]) => (
                          <Badge key={code} variant="outline" className="text-sm">
                            {code}: {count.toLocaleString()}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {metrics.top_endpoints && metrics.top_endpoints.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3">Top Endpoints</h3>
                      <div className="space-y-2">
                        {metrics.top_endpoints.map((endpoint, index) => (
                          <div
                            key={endpoint.endpoint}
                            className="flex items-center justify-between p-3 bg-secondary rounded-lg"
                          >
                            <div className="flex-1">
                              <p className="font-medium">{endpoint.endpoint}</p>
                              <p className="text-sm text-muted-foreground">
                                {endpoint.count.toLocaleString()} requests
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="font-semibold">{formatNumber(endpoint.avg_time_seconds * 1000)} ms</p>
                              <p className="text-xs text-muted-foreground">avg</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </>
        )}
      </main>

      <Footer />
    </div>
  );
}

