from dataclasses import dataclass
from typing import List, Optional, Type

from .specification import (
    Info,
    SecurityScheme,
    SecuritySchemeAPI,
    SecuritySchemeHTTP,
    SecuritySchemeOpenIDConnect,
    Server,
)


@dataclass
class Options:
    """
    :param server: Base URL for the API endpoint.
    :param info: Meta-information for the endpoint specification.
    :param default_security_scheme: Security scheme to apply to endpoints, unless overridden on a per-endpoint basis.
    :param extra_types: Extra types to list in the type catalog in addition to those found in operation signatures.
    """

    server: Server
    info: Info
    default_security_scheme: Optional[SecurityScheme] = None
    extra_types: Optional[List[Type]] = None


@dataclass
class ErrorMessage:
    """
    Encapsulates an error message from an endpoint.

    :param id: A machine-processable identifier for the error.
    :param message: A human-readable description for the error.
    """

    id: str
    message: str


@dataclass
class ErrorResponse:
    """
    Encapsulates an error response from an endpoint.

    :param error: Details related to the error.
    """

    error: ErrorMessage
