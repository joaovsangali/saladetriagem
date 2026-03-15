"""WSGI middleware for forcing HTTPS in production."""

import uuid


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
        # CORREÇÃO: Só redireciona se force_https estiver True
        if self.force_https:
            proto = environ.get("HTTP_X_FORWARDED_PROTO", "")
            # CORREÇÃO: Só redireciona se o header existir E for http
            if proto and proto.lower() == "http":
                host = environ.get("HTTP_HOST", "")
                path = environ.get("PATH_INFO", "/")
                query = environ.get("QUERY_STRING", "")
                url = f"https://{host}{path}"
                if query:
                    url += f"?{query}"
                start_response("301 Moved Permanently", [("Location", url)])
                return [b""]
        return self.app(environ, start_response)


class RequestIDMiddleware:
    """Attach a unique ``X-Request-ID`` header to every request and response.

    If the client already supplies a ``X-Request-ID`` header (e.g. from a
    reverse proxy), that value is reused; otherwise a new UUID is generated.
    The ID is injected into the WSGI environ as ``HTTP_X_REQUEST_ID`` so
    that Flask request handlers can read it via ``request.environ``.
    """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request_id = (
            environ.get("HTTP_X_REQUEST_ID") or uuid.uuid4().hex
        )
        environ["HTTP_X_REQUEST_ID"] = request_id

        def _start_response(status, headers, exc_info=None):
            headers.append(("X-Request-ID", request_id))
            return start_response(status, headers, exc_info)

        return self.app(environ, _start_response)