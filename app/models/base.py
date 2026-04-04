import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

metadata = sa.MetaData()


class SqlModel(DeclarativeBase):
    """Base for all non-domain SQL models."""

    metadata = metadata


class DomainSqlModel(DeclarativeBase):
    """Base for all domain SQL models."""

    metadata = metadata

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True))

    @classmethod
    def get_model_fields(cls) -> set[str]:
        """Retrieve all custom defined fields of a model."""
        return set(cls.__mapper__.column_attrs.keys())

    def asdict(self) -> dict:
        """Convert model to a dict."""
        return {k: getattr(self, k) for k in self.get_model_fields()}
