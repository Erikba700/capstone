import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_current_user, get_repo, get_shared_tx_repo
from app.entities import NotificationEntity, UserEntity
from app.repos import RepoFactory
from app.schemas.friendship_schemas import (
    FriendshipCreateRequestSchema,
    FriendshipUpdateRequestSchema,
    FriendshipWithUserResponseSchema,
    UserSearchItemSchema,
    UserSearchResponseSchema,
)
from app.services.friendship_service import FriendshipService
from app.services.notifications_service import NotificationService

router = APIRouter(tags=['Friends'])


# ── User search ───────────────────────────────────────────────────────────────


@router.get('/users/search', response_model=UserSearchResponseSchema)
async def search_users(
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_repo)],
    search: Annotated[str, Query(min_length=1)] = '',
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict:
    """Search users by name or email. Excludes the current user."""
    results = await repos.user_pgsql_repo.search(
        search=search,
        exclude_id=user.id,
        page=page,
        page_size=page_size,
    )
    return {
        'users': [UserSearchItemSchema(id=u.id, name=u.name, email=u.email) for u in results],
        'total': len(results),
        'page': page,
        'page_size': page_size,
    }


# ── Friend requests ───────────────────────────────────────────────────────────


@router.post(
    '/friends/requests',
    response_model=FriendshipWithUserResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def send_friend_request(
    schema: FriendshipCreateRequestSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> dict:
    """Send a friend request to another user."""
    service = FriendshipService(repos=repos)
    friendship = await service.send_request(
        requester_id=user.id,
        addressee_id=schema.addressee_id,
    )
    # Notify the addressee
    await _notify(
        repos=repos,
        user_id=schema.addressee_id,
        message=f'{user.name} sent you a friend request',
        sender_email=user.email,
    )
    return await service.enrich_with_other_user(friendship, user.id)


@router.get('/friends/requests/incoming', response_model=list[FriendshipWithUserResponseSchema])
async def get_incoming_requests(
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_repo)],
) -> list[dict]:
    """Get all pending incoming friend requests."""
    service = FriendshipService(repos=repos)
    friendships = await service.list_incoming(user.id)
    return await service.enrich_many(friendships, user.id)


@router.get('/friends/requests/outgoing', response_model=list[FriendshipWithUserResponseSchema])
async def get_outgoing_requests(
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_repo)],
) -> list[dict]:
    """Get all pending outgoing friend requests."""
    service = FriendshipService(repos=repos)
    friendships = await service.list_outgoing(user.id)
    return await service.enrich_many(friendships, user.id)


@router.patch(
    '/friends/requests/{friendship_id}',
    response_model=FriendshipWithUserResponseSchema,
)
async def respond_to_request(
    friendship_id: uuid.UUID,
    schema: FriendshipUpdateRequestSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> dict:
    """Accept or reject an incoming friend request."""
    service = FriendshipService(repos=repos)
    friendship = await service.respond_to_request(
        friendship_id=friendship_id,
        current_user_id=user.id,
        new_status=schema.status,
    )
    # Notify the original requester when accepted or rejected
    if schema.status == 'accepted':
        await _notify(
            repos=repos,
            user_id=friendship.requester_id,
            message=f'{user.name} accepted your friend request',
            sender_email=user.email,
        )
    elif schema.status == 'rejected':
        await _notify(
            repos=repos,
            user_id=friendship.requester_id,
            message=f'{user.name} declined your friend request',
            sender_email=user.email,
        )
    return await service.enrich_with_other_user(friendship, user.id)


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _notify(
    repos: RepoFactory,
    user_id: uuid.UUID,
    message: str,
    sender_email: str,
) -> None:
    """Persist an in-app notification (no reminder required)."""
    notification = NotificationEntity.create_new(
        user_id=user_id,
        message=message,
        creator_email=sender_email,
    )
    notification_service = NotificationService(repos=repos)
    created = await repos.notification_pgsql_repo.insert(notification)
    addressee = await repos.user_pgsql_repo.find_by_id(user_id)
    if addressee:
        success = await notification_service.send_custom_notification(
            recipient=addressee.email,
            subject=message,
            message=message,
        )
        if success:
            await notification_service.mark_notification_as_sent(created)


@router.delete('/friends/requests/{friendship_id}', status_code=status.HTTP_204_NO_CONTENT)
async def cancel_friend_request(
    friendship_id: uuid.UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> None:
    """Cancel a pending outgoing friend request."""
    service = FriendshipService(repos=repos)
    await service.cancel_request(friendship_id=friendship_id, current_user_id=user.id)


# ── Friends ───────────────────────────────────────────────────────────────────


@router.get('/friends', response_model=list[FriendshipWithUserResponseSchema])
async def list_friends(
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_repo)],
) -> list[dict]:
    """List all accepted friends of the current user."""
    service = FriendshipService(repos=repos)
    friendships = await service.list_friends(user.id)
    return await service.enrich_many(friendships, user.id)


@router.delete('/friends/{target_user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def remove_friend(
    target_user_id: uuid.UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> None:
    """Remove an existing friendship."""
    service = FriendshipService(repos=repos)
    await service.unfriend(current_user_id=user.id, target_user_id=target_user_id)
