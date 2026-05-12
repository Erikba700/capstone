# import uuid
#
# import sqlalchemy as sa
# from sqlalchemy.orm import Mapped, mapped_column, relationship
#
# from app.models.base import DomainSqlModel
#
#
# class Groups(DomainSqlModel):
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
#     owner_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
#
#     members = relationship("GroupMembers", back_populates="group")
#     reminders = relationship("Reminder", back_populates="group")
