# import sqlalchemy as sa
# from sqlalchemy.orm import Mapped, mapped_column, relationship
#
# from app.models.base import DomainSqlModel
#
#
# class GroupsSqlModel(DomainSqlModel):
#     """Groups SQL model."""
#
#     __tablename__ = 'groups'
#
#     name: Mapped[str] = mapped_column(
#         sa.VARCHAR(255),
#         index=True,
#         nullable=False,
#         comment='Name',
#     )
#     owner_id: Mapped[int] = mapped_column(sa.ForeignKey("users.id"), ondelete="SET NULL") #noqa: E501
#     hashed_password: Mapped[str] = mapped_column(
#         sa.VARCHAR(255),
#         nullable=False,
#         comment='hashed password',
#     )
#
#     members = relationship("GroupMember", back_populates="group")
#     reminders = relationship("Reminder", back_populates="group")
