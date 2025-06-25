"""
Generate an OpenAPI specification from a Python class definition

Copyright 2022-2025, Levente Hunyadi

:see: https://github.com/hunyadi/pyopenapi
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class WebMethod:
    """
    Additional metadata tied to an endpoint operation function.

    :param route: The URL path pattern associated with this operation which path parameters are substituted into.
    :param public: True if the operation can be invoked without prior authentication.
    :param request_examples: Sample requests that the operation might take. Pass a list of objects, not JSON.
    :param response_examples: Sample responses that the operation might produce. Pass a list of objects, not JSON.
    """

    route: Optional[str] = None
    public: bool = False
    request_examples: Optional[list[Any]] = None
    response_examples: Optional[list[Any]] = None
