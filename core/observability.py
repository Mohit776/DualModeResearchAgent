"""
Central Logfire bootstrap.

Import `logfire` from here everywhere else in the project so that
`logfire.configure()` is only called once and all instrumentation
hooks are active before any library uses them.
"""
import logfire
from .config import LOGFIRE_TOKEN

logfire.configure(
    token=LOGFIRE_TOKEN or None,
    service_name="dual-mode-research-agent",
    send_to_logfire="if-token-present",  # silently no-ops when token is absent
)

# Auto-trace every `requests` call (Gemini embed + SEC EDGAR + Polygon)
logfire.instrument_requests()
