"""
Generate an OpenAPI specification from a Python class definition

Copyright 2021-2026, Levente Hunyadi

:see: https://github.com/hunyadi/pyopenapi
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class WebMethod:
    """
    Additional metadata tied to an endpoint operation function.

    :param route: The URL path pattern associated with this operation which path parameters are substituted into.
    :param public: True if the operation can be invoked without prior authentication.
    :param deprecated: True if consumers should refrain from using the operation.
    :param request_examples: Sample requests that the operation might take. Pass a list of objects, not JSON.
    :param response_examples: Sample responses that the operation might produce. Pass a list of objects, not JSON.
    """

    route: str | None = None
    public: bool = False
    deprecated: bool = False
    request_examples: list[Any] | None = None
    response_examples: list[Any] | None = None
