import json
import logging
import sys
from typing import Literal

import orjson
import structlog
from structlog.typing import Processor


def event_dropper(
    logger: logging.Logger,
    name: str,
    event_dict: structlog.typing.EventDict,
) -> structlog.typing.EventDict:
    """Raise DropEvent when path exists and is in filter_paths."""
    if event_dict.get('ignore'):
        raise structlog.DropEvent

    return event_dict


class LoggingManager:
    """Configurator for different logging backends.

    Each backend supports different renderers:
        json - structured logs for production usage
        console - human readable logs for development and tests
    """

    def __init__(
        self,
        renderer: Literal['json', 'console'],
        level: int,
        sqlalchemy_level: int,
    ) -> None:
        self.renderer = renderer
        self.level = level
        self.sqlalchemy_level = sqlalchemy_level

        self.timestamper = structlog.processors.TimeStamper(
            fmt='iso', utc=True
        )
        self.callsite_adder = structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.PATHNAME,
                structlog.processors.CallsiteParameter.MODULE,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.PROCESS,
                structlog.processors.CallsiteParameter.THREAD,
            }
        )

    def configure_stdlib(self) -> None:
        """Configure python stdlib logging root logger.

        It's needed to mimic structlog formating for third-party libraries,
        like uvicorn.
        Make sure to disable logging configuration by the library, to force
        them using our root logger.
        Ideally should be called once before anything else.
        """
        processors: list[Processor] = [
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
        ]
        if self.renderer == 'json':
            processors += [
                self.callsite_adder,
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(serializer=json.dumps),
            ]
        else:
            processors += [
                structlog.dev.ConsoleRenderer(),
            ]

        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                self.timestamper,
            ],
            processors=processors,
        )

        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(fmt=formatter)

        logging.basicConfig(
            level=self.level,
            handlers=[handler],
            force=True,
        )

        sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
        sqlalchemy_logger.setLevel(self.sqlalchemy_level)

    def configure_structlog(self) -> None:
        """Configure structlog app logger.

        It uses fast JSON rendering library called orjson.
        Ideally should be called once before anything else.
        """
        processors: list[Processor] = [
            structlog.contextvars.merge_contextvars,
            event_dropper,
            structlog.processors.add_log_level,
            self.timestamper,
        ]
        logger_factory: (
            structlog.WriteLoggerFactory | structlog.BytesLoggerFactory
        )
        if self.renderer == 'json':
            processors += [
                self.callsite_adder,
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(serializer=orjson.dumps),
            ]
            logger_factory = structlog.BytesLoggerFactory()
        else:
            processors += [
                structlog.dev.ConsoleRenderer(),
            ]
            logger_factory = structlog.WriteLoggerFactory()

        bound_logger = structlog.make_filtering_bound_logger(
            min_level=self.level,
        )
        structlog.configure(
            cache_logger_on_first_use=False,
            wrapper_class=bound_logger,
            processors=processors,
            logger_factory=logger_factory,
        )
