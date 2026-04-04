from typing import Required, TypedDict

from pydantic import BaseModel, ConfigDict, Field


class FeatureConfig(BaseModel):
    """Configuration variables."""

    env: str
    support_link: str = Field(..., alias='supportLink')
    request_enhancement: str = Field(..., alias='requestEnhancement')

    model_config = ConfigDict(
        validate_by_name=True,  # allows using snake_case names in code
        validate_by_alias=True,  # allows using camelCase names in API
    )


class AuthMsalEntity(BaseModel):
    """Entity for msal. Alias required to handle camel case."""

    client_id: str = Field(..., alias='clientID')
    authority: str
    consent_scopes: list[str] = Field(..., alias='consentScopes')
    feature_config: FeatureConfig = Field(..., alias='featureConfig')

    model_config = ConfigDict(
        validate_by_name=True,  # allows using snake_case names in code
        validate_by_alias=True,  # allows using camelCase names in API
    )


class JwksKeys(TypedDict):
    """JwkKeys structure."""

    keys: list[JwkKey]


class JwkKey(TypedDict, total=False):
    """JwkKey structure."""

    kty: str
    use: str
    kid: Required[str]
    x5t: str
    n: str
    e: str
    x5c: list[str]
    issuer: str
    cloud_instance_name: str
