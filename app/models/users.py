import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import DomainSqlModel


class Users(DomainSqlModel):
    """User SQL model."""

    __tablename__ = 'users'

    name: Mapped[str] = mapped_column(
        sa.VARCHAR(255),
        index=True,
        nullable=False,
        comment='Name',
    )
    email: Mapped[str] = mapped_column(
        sa.VARCHAR(255),
        index=True,
        nullable=False,
        unique=True,
        comment='account email',
    )
    hashed_password: Mapped[str] = mapped_column(
        sa.VARCHAR(255),
        nullable=False,
        comment='hashed password',
    )

    # groups = relationship("GroupMembers", back_populates="user")
    owned_reminders = relationship("Reminders", back_populates="owner")
    notifications = relationship("NotificationRecipients", back_populates="user")
