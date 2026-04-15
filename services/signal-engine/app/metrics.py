from prometheus_client import Counter, Histogram, Info

APP_INFO = Info("app", "Application build info", namespace="signals", subsystem="signal_engine")

REQUESTS = Counter(
    "http_requests_total",
    "HTTP requests",
    ["method", "path", "status"],
    namespace="signals",
    subsystem="signal_engine",
)

LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
    namespace="signals",
    subsystem="signal_engine",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0),
)

SIGNAL_GEN = Counter(
    "signal_generation_total",
    "Signals generated",
    ["result", "reason"],
    namespace="signals",
    subsystem="signal_engine",
)

MARKET_FETCH = Counter(
    "market_data_client_fetch_total",
    "Calls to market-data",
    ["status"],
    namespace="signals",
    subsystem="signal_engine",
)
