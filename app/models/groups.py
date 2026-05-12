import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import DomainSqlModel


class Groups(DomainSqlModel):
    """Groups SQL model."""

    __tablename__ = 'groups'

    name: Mapped[str] = mapped_column(
        sa.VARCHAR(255),
        index=True,
        nullable=False,
        comment='Name',
    )
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
