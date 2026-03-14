"""WSGI middleware for forcing HTTPS in production."""


class HTTPSRedirectMiddleware:
    """Redirect HTTP requests to HTTPS when FORCE_HTTPS is enabled.

    Reads the ``X-Forwarded-Proto`` header set by reverse proxies (Nginx,
    Caddy, etc.) and issues a permanent 301 redirect when the original
    request arrived over plain HTTP.
    """

    def __init__(self, app, force_https: bool = False):
        self.app = app
        self.force_https = force_https

    def __call__(self, environ, start_response):
        if self.force_https:
            proto = environ.get("HTTP_X_FORWARDED_PROTO", "http")
            if proto == "http":
                host = environ.get("HTTP_HOST", "")
                path = environ.get("PATH_INFO", "/")
                query = environ.get("QUERY_STRING", "")
                url = f"https://{host}{path}"
                if query:
                    url += f"?{query}"
                start_response("301 Moved Permanently", [("Location", url)])
                return [b""]
        return self.app(environ, start_response)
