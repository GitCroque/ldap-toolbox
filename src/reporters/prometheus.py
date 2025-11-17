"""Prometheus metrics reporter."""

from prometheus_client import CollectorRegistry, generate_latest, start_http_server

from src.core.models import Config


class PrometheusReporter:
    """Exports metrics in Prometheus format."""

    def __init__(self, config: Config, registry: CollectorRegistry) -> None:
        """Initialize Prometheus reporter.

        Args:
            config: Configuration object
            registry: Prometheus registry
        """
        self.config = config
        self.registry = registry

    def start_server(self) -> None:
        """Start Prometheus HTTP server."""
        port = self.config.integrations.prometheus.get("port", 9090)
        host = self.config.integrations.prometheus.get("host", "0.0.0.0")

        start_http_server(port, addr=host, registry=self.registry)
        print(f"Prometheus metrics server started on {host}:{port}")

    def get_metrics(self) -> bytes:
        """Get current metrics in Prometheus format.

        Returns:
            Metrics as bytes
        """
        return generate_latest(self.registry)
