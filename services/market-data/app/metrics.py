from prometheus_client import Counter, Histogram, Info

APP_INFO = Info("app", "Application build info", namespace="signals", subsystem="market_data")

REQUESTS = Counter(
    "http_requests_total",
    "HTTP requests",
    ["method", "path", "status"],
    namespace="signals",
    subsystem="market_data",
)

LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
    namespace="signals",
    subsystem="market_data",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

FETCH = Counter(
    "market_data_fetch_total",
    "Price fetches",
    ["source", "status"],
    namespace="signals",
    subsystem="market_data",
)

# Latencia solo de llamadas HTTP a Tiingo / Twelve Data (no incluye mock ni lectura Postgres).
PROVIDER_LATENCY = Histogram(
    "market_data_provider_request_seconds",
    "Duration of outbound HTTP requests to external price APIs",
    ["provider"],
    namespace="signals",
    subsystem="market_data",
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 15.0, 30.0),
)
