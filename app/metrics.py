from prometheus_client import Counter, Histogram

task_created_total = Counter(
    "task_created_total",
    "Total number of tasks created",
    ["status"],  # labels: success | error
)

task_request_duration_seconds = Histogram(
    "task_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path", "status_code"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)
