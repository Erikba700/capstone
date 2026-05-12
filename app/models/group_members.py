# import uuid
#
# import sqlalchemy as sa
# from sqlalchemy.orm import Mapped, mapped_column, relationship
#
# from app.models.base import DomainSqlModel
#
#
# class GroupMembers(DomainSqlModel):
#     """Groups SQL model."""
#
#     __tablename__ = 'group_members'
#
#     user: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey(
#         "users.id",
#         ondelete='CASCADE',
#     ), nullable=False)
#     role: Mapped[str] = mapped_column(
#         sa.VARCHAR(50),
#         nullable=False,
#         default='member',
#         server_default='member',
#         comment='Role of the user in the group (e.g., member, admin)',
#     )
#
#     status: Mapped[ProtocolStatus] = mapped_column(
#         sa.Enum(
#             ProtocolStatus,
#             name='protocol_status_enum',
#         ),
#     )
#
#
#     group = relationship("Groups", back_populates="members")
