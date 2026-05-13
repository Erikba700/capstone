import uuid

import structlog

from app.entities.group import GroupEntity
from app.entities.group_members import GroupMembersEntity, MemberRoles
from app.exceptions import AuthorizationError, BadRequestError, NotFoundError
from app.repos import RepoFactory
from app.schemas.group_schemas import GroupCreateRequestSchema, GroupUpdateRequestSchema

logger = structlog.getLogger(__name__)


class GroupService:
    """Group use cases."""

    def __init__(self, repos: RepoFactory) -> None:
        self.repos = repos

    async def create_group(
        self,
        schema: GroupCreateRequestSchema,
        owner_id: uuid.UUID,
    ) -> GroupEntity:
        """Create a new group and add creator as owner."""
        entity = GroupEntity.create_new(
            name=schema.name,
            owner_id=owner_id,
            description=schema.description,
        )
        group = await self.repos.group_pgsql_repo.insert(entity=entity)

        # Auto-add creator as owner member
        member_entity = GroupMembersEntity.create_new(
            user_id=owner_id,
            group_id=group.id,
            role=MemberRoles.OWNER,
        )
        await self.repos.group_member_pgsql_repo.insert(entity=member_entity)

        logger.info('Created group', group_id=group.id, owner_id=owner_id)
        return group

    async def fetch_group(self, group_id: uuid.UUID) -> GroupEntity:
        """Fetch a group by id or raise NotFoundError."""
        group = await self.repos.group_pgsql_repo.find_by_id(group_id=group_id)
        if group is None:
            msg = 'Group not found'
            raise NotFoundError(msg)
        return group

    async def list_user_groups(self, user_id: uuid.UUID) -> list[GroupEntity]:
        """List all groups the user is a member of."""
        memberships = await self.repos.group_member_pgsql_repo.list_by_user_id(user_id=user_id)
        groups = []
        for m in memberships:
            if m.group_id is None:
                continue
            group = await self.repos.group_pgsql_repo.find_by_id(group_id=m.group_id)
            if group:
                groups.append(group)
        return groups

    async def update_group(
        self,
        group_id: uuid.UUID,
        schema: GroupUpdateRequestSchema,
    ) -> GroupEntity:
        """Update group fields."""
        group = await self.fetch_group(group_id=group_id)
        payload = schema.model_dump(exclude_unset=True)
        if not payload:
            return group
        now = group.generate_current_timestamp()
        updated = group.model_copy(update={**payload, 'updated_at': now})
        return await self.repos.group_pgsql_repo.update(entity=updated)

    async def delete_group(self, group_id: uuid.UUID) -> None:
        """Delete a group."""
        await self.fetch_group(group_id=group_id)
        await self.repos.group_pgsql_repo.delete_by_id(group_id=group_id)

    async def get_membership(
        self,
        group_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> GroupMembersEntity | None:
        """Return the membership record or None."""
        return await self.repos.group_member_pgsql_repo.find_by_group_and_user(
            group_id=group_id,
            user_id=user_id,
        )

    async def require_membership(
        self,
        group_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> GroupMembersEntity:
        """Raise AuthorizationError if user is not a member."""
        membership = await self.get_membership(group_id=group_id, user_id=user_id)
        if membership is None:
            msg = 'You are not a member of this group'
            raise AuthorizationError(msg)
        return membership

    async def require_admin(
        self,
        group_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> GroupMembersEntity:
        """Raise AuthorizationError if user is not admin or owner."""
        membership = await self.require_membership(group_id=group_id, user_id=user_id)
        if membership.role not in (MemberRoles.ADMIN, MemberRoles.OWNER):
            msg = 'Admin or owner role required'
            raise AuthorizationError(msg)
        return membership

    async def require_owner(
        self,
        group_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> GroupMembersEntity:
        """Raise AuthorizationError if user is not owner."""
        membership = await self.require_membership(group_id=group_id, user_id=user_id)
        if membership.role != MemberRoles.OWNER:
            msg = 'Owner role required'
            raise AuthorizationError(msg)
        return membership

    async def list_members(self, group_id: uuid.UUID) -> list[GroupMembersEntity]:
        """List all members of a group."""
        return await self.repos.group_member_pgsql_repo.list_by_group_id(group_id=group_id)

    async def enrich_member(self, member: GroupMembersEntity) -> dict:
        """Enrich a membership record with the member's name and email."""
        data = member.model_dump()
        user = await self.repos.user_pgsql_repo.find_by_id(member.user_id)
        data['user_name'] = user.name if user else 'Unknown'
        data['user_email'] = user.email if user else ''
        return data

    async def enrich_members(self, members: list[GroupMembersEntity]) -> list[dict]:
        """Enrich multiple membership records with user details."""
        return [await self.enrich_member(m) for m in members]

    async def add_member(
        self,
        group_id: uuid.UUID,
        user_id: uuid.UUID,
        role: MemberRoles = MemberRoles.MEMBER,
    ) -> GroupMembersEntity:
        """Add a user to a group. Raises if already a member."""
        existing = await self.get_membership(group_id=group_id, user_id=user_id)
        if existing is not None:
            msg = 'User is already a member of this group'
            raise BadRequestError(msg)
        entity = GroupMembersEntity.create_new(
            user_id=user_id,
            group_id=group_id,
            role=role,
        )
        return await self.repos.group_member_pgsql_repo.insert(entity=entity)

    async def update_member_role(
        self,
        group_id: uuid.UUID,
        target_user_id: uuid.UUID,
        new_role: MemberRoles,
        actor_role: MemberRoles,
    ) -> GroupMembersEntity:
        """Update a member's role with permission checks."""
        target = await self.get_membership(group_id=group_id, user_id=target_user_id)
        if target is None:
            msg = 'Member not found in this group'
            raise NotFoundError(msg)

        # Admins cannot change owner's role
        if target.role == MemberRoles.OWNER and actor_role != MemberRoles.OWNER:
            msg = 'Cannot change the role of the group owner'
            raise AuthorizationError(msg)

        # Admins cannot promote to owner
        if new_role == MemberRoles.OWNER and actor_role != MemberRoles.OWNER:
            msg = 'Only owners can transfer ownership'
            raise AuthorizationError(msg)

        updated = target.model_copy(update={'role': new_role})
        return await self.repos.group_member_pgsql_repo.update(entity=updated)

    async def remove_member(
        self,
        group_id: uuid.UUID,
        target_user_id: uuid.UUID,
        actor_role: MemberRoles,
    ) -> None:
        """Remove a member from a group with permission checks."""
        target = await self.get_membership(group_id=group_id, user_id=target_user_id)
        if target is None:
            msg = 'Member not found in this group'
            raise NotFoundError(msg)

        # Prevent removing owner
        if target.role == MemberRoles.OWNER:
            owners = await self.repos.group_member_pgsql_repo.count_owners(group_id=group_id)
            if owners <= 1:
                msg = 'Cannot remove the last owner of a group'
                raise BadRequestError(msg)

        # Admins can only remove members
        if actor_role == MemberRoles.ADMIN and target.role != MemberRoles.MEMBER:
            msg = 'Admins can only remove regular members'
            raise AuthorizationError(msg)

        await self.repos.group_member_pgsql_repo.delete_by_id(member_id=target.id)
