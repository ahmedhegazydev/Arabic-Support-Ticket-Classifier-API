from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# عدد الطلبات الكلي
REQUEST_COUNT = Counter(
    "ticket_api_requests_total",
    "Total number of classification requests",
)

# عدد الطلبات الفاشلة
REQUEST_FAILURE_COUNT = Counter(
    "ticket_api_request_failures_total",
    "Total number of failed classification requests",
)

# عدد مرات الـ cache miss
CACHE_MISS_COUNT = Counter(
    "ticket_api_cache_miss_total",
    "Total number of cache misses for category prediction",
)

# زمن تنفيذ الطلب بالكامل
REQUEST_LATENCY_MS = Histogram(
    "ticket_api_request_latency_ms",
    "Latency of classification requests in milliseconds",
    buckets=(1, 5, 10, 25, 50, 100, 250, 500, 1000, 5000, 10000, 60000, 300000),
)

# زمن الوصول لنتيجة التصنيف / cache lookup
CACHE_LOOKUP_LATENCY_MS = Histogram(
    "ticket_api_cache_lookup_latency_ms",
    "Latency of cache lookup or model inference in milliseconds",
    buckets=(1, 5, 10, 25, 50, 100, 250, 500, 1000, 5000, 10000, 60000, 300000),
)

# عدد النتائج التي تحتاج مراجعة بشرية
HUMAN_REVIEW_COUNT = Counter(
    "ticket_api_human_review_total",
    "Total number of predictions flagged for human review",
)