"""PostgreSQL repo for reassignment requests."""

import uuid

import structlog
from sqlalchemy import Select, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Insert, Update

from app.entities.reassignment_request import ReassignmentRequestEntity
from app.models.reassignment_requests import ReassignmentRequests

logger = structlog.getLogger(__name__)


class ReassignmentRequestPgsqlQueries:
    """SQL builders for reassignment_requests."""

    @staticmethod
    def insert_query(data: dict) -> Insert:
        """Insert a new request."""
        return insert(ReassignmentRequests).values(**data).returning(ReassignmentRequests)

    @staticmethod
    def select_by_id_query(request_id: uuid.UUID) -> Select:
        """Select by primary key."""
        return select(ReassignmentRequests).where(ReassignmentRequests.id == request_id)

    @staticmethod
    def select_pending_for_assignee_query(assignee_id: uuid.UUID) -> Select:
        """All pending requests where the current assignee must respond."""
        return (
            select(ReassignmentRequests)
            .where(
                ReassignmentRequests.current_assignee_id == assignee_id,
                ReassignmentRequests.status == 'pending',
            )
            .order_by(ReassignmentRequests.created_at.asc())
        )

    @staticmethod
    def select_pending_for_reminder_and_requester_query(
        reminder_id: uuid.UUID,
        requester_id: uuid.UUID,
    ) -> Select:
        """Check if a pending request already exists for same reminder+requester."""
        return select(ReassignmentRequests).where(
            ReassignmentRequests.reminder_id == reminder_id,
            ReassignmentRequests.requester_id == requester_id,
            ReassignmentRequests.status == 'pending',
        )

    @staticmethod
    def update_query(data: dict) -> Update:
        """Update a request row."""
        return (
            update(ReassignmentRequests)
            .values(**data)
            .where(ReassignmentRequests.id == data['id'])
            .returning(ReassignmentRequests)
        )


class ReassignmentRequestPgsqlRepo:
    """Postgres persistence for reassignment requests."""

    def __init__(
        self,
        session: AsyncSession,
        queries: type[ReassignmentRequestPgsqlQueries] = ReassignmentRequestPgsqlQueries,
    ) -> None:
        self.session = session
        self.queries = queries

    async def insert(self, entity: ReassignmentRequestEntity) -> ReassignmentRequestEntity:
        """Persist a new request."""
        data = entity.model_dump(include=ReassignmentRequests.get_model_fields())
        query = self.queries.insert_query(data)
        result = await self.session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            msg = 'Failed to insert reassignment request'
            raise RuntimeError(msg)
        logger.info('Inserted reassignment request', id=entity.id)
        return ReassignmentRequestEntity.model_validate(instance)

    async def find_by_id(self, request_id: uuid.UUID) -> ReassignmentRequestEntity | None:
        """Find by primary key."""
        instance = await self.session.scalar(self.queries.select_by_id_query(request_id))
        return ReassignmentRequestEntity.model_validate(instance) if instance else None

    async def list_pending_for_assignee(self, assignee_id: uuid.UUID) -> list[ReassignmentRequestEntity]:
        """List all pending requests directed at this assignee."""
        result = await self.session.execute(self.queries.select_pending_for_assignee_query(assignee_id))
        return [ReassignmentRequestEntity.model_validate(r) for r in result.scalars().all()]

    async def find_existing_pending(
        self,
        reminder_id: uuid.UUID,
        requester_id: uuid.UUID,
    ) -> ReassignmentRequestEntity | None:
        """Return existing pending request for same reminder+requester, or None."""
        instance = await self.session.scalar(
            self.queries.select_pending_for_reminder_and_requester_query(reminder_id, requester_id)
        )
        return ReassignmentRequestEntity.model_validate(instance) if instance else None

    async def update(self, entity: ReassignmentRequestEntity) -> ReassignmentRequestEntity:
        """Update a request row."""
        data = entity.model_dump(include=ReassignmentRequests.get_model_fields())
        query = self.queries.update_query(data)
        result = await self.session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            msg = 'Failed to update reassignment request'
            raise RuntimeError(msg)
        return ReassignmentRequestEntity.model_validate(instance)
