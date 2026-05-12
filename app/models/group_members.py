import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.group_members import MemberRoles
from app.models.base import DomainSqlModel


class GroupMembers(DomainSqlModel):
    """Group members SQL model."""

    __tablename__ = 'group_members'

    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey(
            'users.id',
            ondelete='CASCADE',
        ),
        nullable=False,
    )
    role: Mapped[MemberRoles] = mapped_column(
        sa.Enum(MemberRoles, name='member_roles_enum', values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=MemberRoles.MEMBER,
        server_default=MemberRoles.MEMBER.value,
    )
    group_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.ForeignKey('groups.id', ondelete='SET NULL'), nullable=True, index=True
    )
    joined_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
