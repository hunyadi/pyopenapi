from dataclasses import dataclass


@dataclass
class WebMethod:
    """
    Additional metadata tied to an endpoint operation function.

    :param route: The URL path component associated with the endpoint.
    """

    route: str
