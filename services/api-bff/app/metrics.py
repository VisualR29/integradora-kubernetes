from prometheus_client import Counter, Histogram, Info

APP_INFO = Info("app", "Application build info", namespace="signals", subsystem="api_bff")

REQUESTS = Counter(
    "http_requests_total",
    "HTTP requests",
    ["method", "path", "status"],
    namespace="signals",
    subsystem="api_bff",
)

LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
    namespace="signals",
    subsystem="api_bff",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
)
