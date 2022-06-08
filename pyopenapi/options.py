from dataclasses import dataclass
from typing import Callable, ClassVar, Dict, List, Optional

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
    :param property_description_fun: Custom transformation function to apply to class property documentation strings.
    :param captions: User-defined captions for sections such as "Operations" or "Types".
    """

    server: Server
    info: Info
    default_security_scheme: Optional[SecurityScheme] = None
    extra_types: Optional[List[type]] = None
    property_description_fun: Callable[[type, str, str], str] = None
    captions: Dict[str, str] = None

    default_captions: ClassVar[Dict[str, str]] = {
        "Operations": "Operations",
        "Types": "Types",
        "Events": "Events",
        "AdditionalTypes": "Additional types",
        "BadRequest": "The server cannot process the request due a client error (e.g. malformed request syntax).",
        "InternalServerError": "The server encountered an unexpected error when processing the request.",
    }

    def map(self, id: str) -> str:
        "Maps a language-neutral placeholder string to language-dependent text."

        if self.captions is not None:
            text = self.captions.get(id)
            if text is not None:
                return text

        return __class__.default_captions[id]


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
