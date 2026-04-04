import logging
import os

from alembic import context
from sqlalchemy import URL, engine_from_config, pool

from app.log import LoggingManager
from app.models.base import metadata

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Configure logging as in the app.
# This line sets up loggers basically.
logging_manager = LoggingManager('json', logging.INFO, logging.WARNING)
logging_manager.configure_stdlib()

url = URL.create(
    drivername='postgresql+psycopg',
    username=os.environ.get('DB_USER', 'postgres'),
    password=os.environ.get('DB_PASS', 'postgres'),
    host=os.environ.get('DB_HOST', 'localhost'),
    port=int(os.environ.get('DB_PORT', 5432)),
    database=os.environ.get('DB_NAME', 'postgres_capstone'),
)

config.set_main_option(
    name='sqlalchemy.url',
    value=url.render_as_string(hide_password=False),
)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
