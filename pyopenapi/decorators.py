"""
Generate an OpenAPI specification from a Python class definition

Copyright 2022-2025, Levente Hunyadi

:see: https://github.com/hunyadi/pyopenapi
"""

from typing import Any, Callable, Optional, TypeVar

from .metadata import WebMethod
from .options import *  # noqa: F403
from .utility import Specification as Specification

F = TypeVar("F", bound=Callable[..., Any])


def webmethod(
    route: Optional[str] = None,
    public: Optional[bool] = False,
    request_example: Optional[Any] = None,
    response_example: Optional[Any] = None,
    request_examples: Optional[list[Any]] = None,
    response_examples: Optional[list[Any]] = None,
) -> Callable[[F], F]:
    """
    Decorator that supplies additional metadata to an endpoint operation function.

    :param route: The URL path pattern associated with this operation which path parameters are substituted into.
    :param public: True if the operation can be invoked without prior authentication.
    :param request_example: A sample request that the operation might take.
    :param response_example: A sample response that the operation might produce.
    :param request_examples: Sample requests that the operation might take. Pass a list of objects, not JSON.
    :param response_examples: Sample responses that the operation might produce. Pass a list of objects, not JSON.
    """

    if request_example is not None and request_examples is not None:
        raise ValueError("arguments `request_example` and `request_examples` are exclusive")
    if response_example is not None and response_examples is not None:
        raise ValueError("arguments `response_example` and `response_examples` are exclusive")

    if request_example:
        request_examples = [request_example]
    if response_example:
        response_examples = [response_example]

    def wrap(cls: F) -> F:
        cls.__webmethod__ = WebMethod(route=route, public=public or False, request_examples=request_examples, response_examples=response_examples)  # type: ignore[attr-defined]
        return cls

    return wrap
