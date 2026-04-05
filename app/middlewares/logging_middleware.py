import time
import uuid

import structlog
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


def generate_request_id() -> str:
    """Generate random id for request traceability."""
    return str(uuid.uuid4())


def format_client(scope: Scope) -> str:
    """Format client tuple as a sting."""
    client = scope.get('client')
    if not client:
        return ''

    host, port = scope['client']
    return f'{host}:{port}'


class LoggingMiddleware:
    """Pure ASGI middleware for structlog context for requests."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Bind request parameters to contextvars."""
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)

        # make request id accessible from endpoints
        request_id = generate_request_id()
        scope['asgi_request_id'] = request_id

        # all bound vars here will be attached to all log inside request
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            request_method=scope['method'],
            request_http_version=scope['http_version'],
            request_client_addr=format_client(scope),
            request_user_agent=headers.get('user-agent', ''),
            request_content_length=int(headers.get('content-length', 0)),
            host=headers.get('host', ''),
            path=scope['path'],
            query=scope['query_string'],
        )

        start_time = time.perf_counter()

        async def send_with_context(message: Message) -> None:
            if message['type'] == 'http.response.start':
                end_time = time.perf_counter()
                duration = (end_time - start_time) * 1000

                # modify scope headers in-place
                headers = MutableHeaders(scope=message)
                headers['X-Process-Time'] = f'{duration:.2f}ms'
                headers['X-Request-Id'] = request_id

                structlog.contextvars.bind_contextvars(
                    response_duration=duration,
                    response_status=message['status'],
                    response_content_length=int(headers.get('content-length', 0)),
                )

                logger = structlog.get_logger()
                logger.info('%s %s', scope['method'], scope['path'])

                structlog.contextvars.clear_contextvars()

            await send(message)

        await self.app(scope, receive, send_with_context)
