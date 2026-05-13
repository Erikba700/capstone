import uuid

import structlog

from app.entities.friendship import FriendshipEntity, FriendshipStatus
from app.exceptions import AuthorizationError, BadRequestError, NotFoundError
from app.repos import RepoFactory

logger = structlog.getLogger(__name__)


class FriendshipService:
    """Friendship use cases."""

    def __init__(self, repos: RepoFactory) -> None:
        self.repos = repos

    async def ensure_friend_request_exists(self, friendship_id: uuid.UUID) -> FriendshipEntity:
        """Return the friendship or raise NotFoundError."""
        friendship = await self.repos.friendship_pgsql_repo.find_by_id(friendship_id)
        if friendship is None:
            msg = 'Friend request not found'
            raise NotFoundError(msg)
        return friendship

    async def ensure_friends(self, user_a: uuid.UUID, user_b: uuid.UUID) -> FriendshipEntity:
        """Raise BadRequestError if the two users are not accepted friends."""
        friendship = await self.repos.friendship_pgsql_repo.find_between_users(user_a, user_b)
        if friendship is None or friendship.status != FriendshipStatus.ACCEPTED:
            msg = 'Users are not friends'
            raise BadRequestError(msg)
        return friendship

    async def ensure_not_blocked(self, user_a: uuid.UUID, user_b: uuid.UUID) -> None:
        """Raise BadRequestError if either user has blocked the other."""
        friendship = await self.repos.friendship_pgsql_repo.find_between_users(user_a, user_b)
        if friendship is not None and friendship.status == FriendshipStatus.BLOCKED:
            msg = 'Interaction blocked'
            raise BadRequestError(msg)

    # ── Requests ──────────────────────────────────────────────────────────────

    async def send_request(
        self,
        requester_id: uuid.UUID,
        addressee_id: uuid.UUID,
    ) -> FriendshipEntity:
        """Send a friend request."""
        if requester_id == addressee_id:
            msg = 'Cannot send a friend request to yourself'
            raise BadRequestError(msg)

        # Ensure target user exists
        target = await self.repos.user_pgsql_repo.find_by_id(addressee_id)
        if target is None:
            msg = 'User not found'
            raise BadRequestError(msg)

        # Check for existing relationship
        existing = await self.repos.friendship_pgsql_repo.find_between_users(requester_id, addressee_id)
        if existing is not None:
            if existing.status == FriendshipStatus.PENDING:
                msg = 'Friend request already pending'
                raise BadRequestError(msg)
            if existing.status == FriendshipStatus.ACCEPTED:
                msg = 'Already friends'
                raise BadRequestError(msg)
            if existing.status == FriendshipStatus.BLOCKED:
                msg = 'Cannot send request — user is blocked'
                raise BadRequestError(msg)
            # REJECTED — allow re-requesting by updating the existing row
            reactivated = existing.model_copy(
                update={
                    'requester_id': requester_id,
                    'addressee_id': addressee_id,
                    'status': FriendshipStatus.PENDING,
                    'accepted_at': None,
                }
            )
            return await self.repos.friendship_pgsql_repo.update(reactivated)

        entity = FriendshipEntity.create_new(
            requester_id=requester_id,
            addressee_id=addressee_id,
        )
        friendship = await self.repos.friendship_pgsql_repo.insert(entity)
        logger.info('Friend request sent', requester=requester_id, addressee=addressee_id)
        return friendship

    async def list_incoming(self, user_id: uuid.UUID) -> list[FriendshipEntity]:
        """List pending incoming friend requests."""
        return await self.repos.friendship_pgsql_repo.list_incoming(user_id)

    async def list_outgoing(self, user_id: uuid.UUID) -> list[FriendshipEntity]:
        """List pending outgoing friend requests."""
        return await self.repos.friendship_pgsql_repo.list_outgoing(user_id)

    async def respond_to_request(
        self,
        friendship_id: uuid.UUID,
        current_user_id: uuid.UUID,
        new_status: FriendshipStatus,
    ) -> FriendshipEntity:
        """Accept or reject a friend request. Only the addressee can respond."""
        friendship = await self.ensure_friend_request_exists(friendship_id)

        if friendship.addressee_id != current_user_id:
            msg = 'Only the recipient can respond to this request'
            raise AuthorizationError(msg)

        if friendship.status != FriendshipStatus.PENDING:
            msg = f'Cannot respond to a request with status {friendship.status}'
            raise BadRequestError(msg)

        if new_status == FriendshipStatus.ACCEPTED:
            updated = friendship.accept()
        elif new_status == FriendshipStatus.REJECTED:
            updated = friendship.reject()
        else:
            msg = f'Invalid status for response: {new_status}'
            raise BadRequestError(msg)

        result = await self.repos.friendship_pgsql_repo.update(updated)
        logger.info('Friend request responded', friendship=friendship_id, status=new_status)
        return result

    async def cancel_request(
        self,
        friendship_id: uuid.UUID,
        current_user_id: uuid.UUID,
    ) -> None:
        """Cancel an outgoing friend request. Only the requester can cancel."""
        friendship = await self.ensure_friend_request_exists(friendship_id)

        if friendship.requester_id != current_user_id:
            msg = 'Only the sender can cancel this request'
            raise AuthorizationError(msg)

        if friendship.status != FriendshipStatus.PENDING:
            msg = 'Can only cancel pending requests'
            raise BadRequestError(msg)

        await self.repos.friendship_pgsql_repo.delete_by_id(friendship_id)
        logger.info('Friend request cancelled', friendship=friendship_id)

    # ── Friends ───────────────────────────────────────────────────────────────

    async def list_friends(self, user_id: uuid.UUID) -> list[FriendshipEntity]:
        """List all accepted friends for a user."""
        return await self.repos.friendship_pgsql_repo.list_friends(user_id)

    async def unfriend(self, current_user_id: uuid.UUID, target_user_id: uuid.UUID) -> None:
        """Remove an existing friendship."""
        friendship = await self.repos.friendship_pgsql_repo.find_between_users(current_user_id, target_user_id)
        if friendship is None or friendship.status != FriendshipStatus.ACCEPTED:
            msg = 'Friendship not found'
            raise NotFoundError(msg)
        await self.repos.friendship_pgsql_repo.delete_by_id(friendship.id)
        logger.info('Friendship removed', user=current_user_id, target=target_user_id)

    # ── Enrichment ────────────────────────────────────────────────────────────

    async def enrich_with_other_user(
        self,
        friendship: FriendshipEntity,
        current_user_id: uuid.UUID,
    ) -> dict:
        """Return friendship dict with the other user's info attached."""
        data = friendship.model_dump()
        other_id = friendship.addressee_id if friendship.requester_id == current_user_id else friendship.requester_id
        other = await self.repos.user_pgsql_repo.find_by_id(other_id)
        data['other_user'] = (
            {
                'id': str(other.id),
                'name': other.name,
                'email': other.email,
            }
            if other
            else {'id': str(other_id), 'name': 'Unknown', 'email': ''}
        )
        return data

    async def enrich_many(
        self,
        friendships: list[FriendshipEntity],
        current_user_id: uuid.UUID,
    ) -> list[dict]:
        """Enrich multiple friendship records."""
        return [await self.enrich_with_other_user(f, current_user_id) for f in friendships]
