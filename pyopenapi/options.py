"""
Generate an OpenAPI specification from a Python class definition

Copyright 2022-2025, Levente Hunyadi

:see: https://github.com/hunyadi/pyopenapi
"""

import dataclasses
from dataclasses import dataclass
from http import HTTPStatus
from typing import Callable, ClassVar, Optional, Union

from .specification import Info, SecurityScheme, Server
from .specification import SecuritySchemeAPI as SecuritySchemeAPI
from .specification import SecuritySchemeHTTP as SecuritySchemeHTTP
from .specification import SecuritySchemeOpenIDConnect as SecuritySchemeOpenIDConnect

HTTPStatusCode = Union[HTTPStatus, int, str]


@dataclass
class Options:
    """
    :param server: Base URL for the API endpoint.
    :param info: Meta-information for the endpoint specification.
    :param version: OpenAPI specification version as a tuple of major, minor, revision.
    :param default_security_scheme: Security scheme to apply to endpoints, unless overridden on a per-endpoint basis.
    :param extra_types: Extra types in addition to those found in operation signatures. Use a dictionary to group related types.
    :param use_examples: Whether to emit examples for operations.
    :param success_responses: Associates operation response types with HTTP status codes.
    :param error_responses: Associates error response types with HTTP status codes.
    :param error_wrapper: True if errors are encapsulated in an error object wrapper.
    :param property_description_fun: Custom transformation function to apply to class property documentation strings.
    :param captions: User-defined captions for sections such as "Operations" or "Types", and (if applicable) groups of extra types.
    """

    server: Server
    info: Info
    version: tuple[int, int, int] = (3, 1, 0)
    default_security_scheme: Optional[SecurityScheme] = None
    extra_types: Union[list[type], dict[str, list[type]], None] = None
    use_examples: bool = True
    success_responses: dict[type, HTTPStatusCode] = dataclasses.field(default_factory=dict)
    error_responses: dict[type, HTTPStatusCode] = dataclasses.field(default_factory=dict)
    error_wrapper: bool = False
    property_description_fun: Optional[Callable[[type, str, str], str]] = None
    captions: Optional[dict[str, str]] = None

    default_captions: ClassVar[dict[str, str]] = {
        "Operations": "Operations",
        "Types": "Types",
        "Events": "Events",
        "AdditionalTypes": "Additional types",
    }

    def map(self, id: str) -> str:
        "Maps a language-neutral placeholder string to language-dependent text."

        if self.captions is not None:
            caption = self.captions.get(id)
            if caption is not None:
                return caption

        caption = self.__class__.default_captions.get(id)
        if caption is not None:
            return caption

        raise KeyError(f"no caption found for ID: {id}")
