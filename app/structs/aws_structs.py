from pydantic import BaseModel
from pydantic_core import Url


class PresignedPostUrl(BaseModel):
    """Structure of presinged POST url with fields for multipart/form-data."""

    url: Url
    fields: dict[str, str]
