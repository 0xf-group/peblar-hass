class PeblarApiHelper:
    def get_peblar_api_endpoint(host: str) -> str:
        """Get the Peblar API endpoint."""
        return host.rstrip("/").rstrip(" ").rstrip("\\") + "/api/wlac/v1"
