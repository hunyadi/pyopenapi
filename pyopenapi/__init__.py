from typing import Any, Callable, TypeVar

from .metadata import WebMethod
from .options import *
from .utility import Specification

__version__ = "0.1.5"

T = TypeVar("T")


def webmethod(
    route: str = None,
    public: bool = False,
    request_example: Any = None,
    response_example: Any = None,
) -> Callable[[T], T]:
    """
    Decorator that supplies additional metadata to an endpoint operation function.

    :param route: The URL path pattern associated with this operation which path parameters are substituted into.
    :param public: True if the operation can be invoked without prior authentication.
    :param request_example: A sample request that the operation might take.
    :param response_example: A sample response that the operation might produce.
    """

    def wrap(cls: T) -> T:
        setattr(
            cls,
            "__webmethod__",
            WebMethod(
                route=route,
                public=public,
                request_example=request_example,
                response_example=response_example,
            ),
        )
        return cls

    return wrap
