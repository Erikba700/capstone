import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import click
import fastapi
import fastapi.middleware.cors
import fastapi.security
import uvicorn
from fastapi.responses import ORJSONResponse

from app.api import (
    debug,
    reminders,
    root,
    users,
)
from app.config import settings
from app.db.async_pgsql_pool import AsyncPostgresPool
from app.exceptions import DomainError
from app.log import LoggingManager
from app.middlewares import LoggingMiddleware
from app.structs.error_structs import ErrorMessage


@asynccontextmanager
async def fastapi_lifespan(app: fastapi.FastAPI) -> AsyncGenerator[None]:
    """Lifespan for fastapi.

    Everything above `yield` will be executed on app creation,
    everything below -- on app destruction.
    """
    app.state.pgsql_session_pool = AsyncPostgresPool()
    yield
    await app.state.pgsql_session_pool.close()


def default_exception_handler(
    request: fastapi.Request,
    exc: Exception,
) -> fastapi.Response:
    """Exception handler for unhandled exceptions."""
    message = ErrorMessage(detail='Server error')
    return ORJSONResponse(
        content=message.model_dump(),
        status_code=500,
    )


def domain_exception_handler(
    request: fastapi.Request,
    exc: DomainError,
) -> fastapi.Response:
    """Exception handler for DomainError exceptions."""
    message = ErrorMessage(detail=exc.message)
    return ORJSONResponse(
        status_code=exc.status_code,
        content=message.model_dump(),
    )


class FastApiAbstractFactory:
    """Factory for FastAPI application factories."""

    def __init__(
        self,
        *,
        app_logging: LoggingManager,
        debug: bool = False,
    ) -> None:
        self.app_logging = app_logging
        self.debug = debug

    def __call__(self) -> fastapi.FastAPI:
        """Factory for fastapi app.

        Can't have any arguments.

        This differs from what you would see in fastapi documentation.
        Global state object is an easy way of doing things, but it requires
        discipline from all contributors.
        With this approach we avoid multiple pitfalls like:
        - importing it in other modules and facing circular imports
        - accidentally increasing import time, due to reading a file or etc.
        - having all root dependencies like settings to be global too
        - having to monkeypatch everything in tests
        """
        # configure logging for child uvicorn process
        self.app_logging.configure_stdlib()
        # configure logging for us
        self.app_logging.configure_structlog()

        # our domain exceptions may be handled, unless it's server error (500),
        # which is not necessary to handle
        # however, raising HTTPException is recommended within routes
        exception_handlers: dict = {
            DomainError: domain_exception_handler,
            Exception: default_exception_handler,
        }

        app = fastapi.FastAPI(
            title=settings.app_name,
            debug=self.debug,
            exception_handlers=exception_handlers,
            # see starlette.routing.Router.lifespan
            lifespan=fastapi_lifespan,
            # use fast orjson responses
            default_response_class=fastapi.responses.ORJSONResponse,
            # defined for visibility, should be changed later
            docs_url='/docs',
            # defined for visibility, should be changed later
            redoc_url='/redoc',
            root_path='/api',
        )

        # you might want to attach some stuff to the app itself, not to
        # initialize
        # it more than once
        # app.state is a good place for it, making it accessible almost
        # anywhere
        # example: app.state['settings'] = Settings()

        # don't keep too much stuff here, cause it's a simple untyped dict
        # see: starlette.datastructures.State

        # middlewares resemble stack, so first added will be the innermost one
        # app.add_middleware(a)
        # app.add_middleware(b)
        # app.add_middleware(c)
        # => c(b(a(app)))
        # see: starlette.applications.Starlette.build_middleware_stack()

        if self.debug:
            # allows cross origins for dev SPA
            app.add_middleware(
                fastapi.middleware.cors.CORSMiddleware,
                allow_origins=[
                    'http://localhost:5173',
                    'http://localhost:8000',
                    'http://127.0.0.1:5173',
                ],
                allow_credentials=True,
                allow_methods=['*'],
                allow_headers=['*'],
            )

        app.add_middleware(LoggingMiddleware)

        # for more grained control use Pure ASGI middleware
        # see: https://www.starlette.dev/middleware/#pure-asgi-middleware

        # all routes and routers should be defined in corresponding modules and
        # included here with predefined routers with prefixes

        api_router = fastapi.APIRouter()
        api_router.include_router(router=root.router)
        api_router.include_router(router=users.router)
        api_router.include_router(router=reminders.router)

        # useful for easy debug
        if self.debug:
            api_router.include_router(debug.router)

        app.include_router(api_router)
        # app.include_router(api_v1_router)

        # remember, that Router can also have its own dependencies, lifespan,
        # default_response_class and other settings we set in the app

        return app


class UvicornFactory:
    """Factory for uvicorn server."""

    def __init__(
        self,
        *,
        app_logging: LoggingManager,
        app: str,
        host: str,
        port: int,
        reload: bool,
    ) -> None:
        self.app_logging = app_logging
        self.app = app
        self.host = host
        self.port = port
        self.reload = reload

    def run(self) -> None:
        """Entrypoint method."""
        # configure logging for main uvicorn process
        self.app_logging.configure_stdlib()

        uvicorn.run(
            app=self.app,
            host=self.host,
            port=self.port,
            # don't configure logging, we have our own
            log_config=None,
            access_log=False,
            reload=self.reload,
            workers=1,
            factory=True,
            lifespan='on',
        )


# bake logging, app and server together to avoid mistakes
prod_app_logging = LoggingManager(
    renderer='json',
    level=logging.INFO,
    sqlalchemy_level=logging.ERROR,
)
prod_app_factory = FastApiAbstractFactory(
    app_logging=prod_app_logging,
    debug=False,
)
prod_server = UvicornFactory(
    app_logging=prod_app_logging,
    app='app.main:prod_app_factory',
    host='0.0.0.0',  # noqa: S104
    port=8000,
    reload=False,
)

dev_app_logging = LoggingManager(
    renderer='console',
    level=logging.DEBUG,
    sqlalchemy_level=logging.WARNING,
)
dev_app_factory = FastApiAbstractFactory(
    app_logging=dev_app_logging,
    debug=True,
)
dev_server = UvicornFactory(
    app_logging=dev_app_logging,
    app='app.main:dev_app_factory',
    host='0.0.0.0',  # noqa: S104
    port=8000,
    reload=True,
)


def run(mode: str) -> None:
    """Entrypoint method."""
    servers = {
        'prod': prod_server,
        'dev': dev_server,
    }
    server = servers[mode]
    server.run()


@click.command()
@click.option(
    '--mode',
    type=click.Choice(['prod', 'dev']),
    default='prod',
    show_default=True,
)
def main(mode: str) -> None:
    """Entrypoint CLI."""
    run(mode=mode)


if __name__ == '__main__':
    main()
