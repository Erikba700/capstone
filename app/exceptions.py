class DomainError(Exception):
    """Base for domain exceptions with custom message."""

    default_message = 'Internal error'
    status_code = 500

    def __init__(self, message: str = '') -> None:
        self.message = message or self.default_message


class NotFoundError(DomainError):
    """Could not find requested object in data storage."""

    default_message = 'Object not found'
    status_code = 404


class BadRequestError(DomainError):
    """Raised when input data violates business logic or domain rules."""

    default_message = 'Request contains invalid or inconsistent data.'
    status_code = 400


class CreateObjectError(BadRequestError):
    """Could not create object in data storage."""

    default_message = 'Failed to create object'


class ChangeObjectError(BadRequestError):
    """Could not change object in data storage."""

    default_message = 'Failed to change object'


class DeleteObjectError(BadRequestError):
    """Could not delete object in data storage."""

    default_message = 'Failed to delete object'


class UserSuggestionError(BadRequestError):
    """Could not request users suggestion."""

    default_message = 'Failed to suggest users'


class UserGetInfoError(BadRequestError):
    """Could not request info for user."""

    default_message = 'Failed to get user info'


class AuthorizationError(DomainError):
    """Any error related to token validation or user check in Graph API."""

    default_message = 'Failed to authorise user'
    status_code = 403
