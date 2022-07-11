from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class WebMethod:
    """
    Additional metadata tied to an endpoint operation function.

    :param route: The URL path pattern associated with this operation which path parameters are substituted into.
    :param public: True if the operation can be invoked without prior authentication.
    :param request_example: A sample request that the operation might take.
    :param response_example: A sample response that the operation might produce.
    """

    route: str
    public: bool = False
    request_example: Optional[Any] = None
    response_example: Optional[Any] = None
